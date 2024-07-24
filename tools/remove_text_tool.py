import os
from typing import List, Tuple

import cv2
import numpy as np
from dotenv import load_dotenv


from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools import MotleyTool

from clear_image.text_deleter import TextDeleter
from clear_image.inpainter import DalleInpainter, Inpainter
from clear_image.text_detector import KerasOcrTextDetector, TextBox
from utils import get_points_density


class TextRemover:

    def __init__(self, num_text_areas: int = 5, point_threshold: float = 0.1):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.num_text_areas = num_text_areas
        self.point_threshold = point_threshold

    def remove_text(self, image_path: str) -> str:
        image_path = image_path.strip()
        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        file_name, ext = os.path.splitext(image_path)
        output_image_path = "{}_remove_text{}".format(file_name, ext)
        text_detector = KerasOcrTextDetector()
        inpainter = DalleInpainter(self.api_key)
        text_deleter = TextDeleter(text_detector, inpainter)
        ret_image_path = text_deleter.delete_text(image_path, output_image_path)

        ret_rows = ["Clear image path: {}".format(ret_image_path)]

        boxes = []
        if text_deleter.text_bboxes:
            boxes = self.find_text_boxes(image_path, inpainter, text_deleter.text_bboxes)
        else:
            text_area = self.find_discharged_area(image_path)
            boxes = [text_area]

        if boxes:
            ret_rows.append("Text boxes:")
            text_box_template = "    text box: x: {}, y: {}, width: {}, height: {}"
            for box in boxes:
                ret_rows.append(text_box_template.format(*box))
        else:
            ret_rows.append("Text boxes not found")

        return "\n".join(ret_rows)

    def find_text_boxes(
        self, image_path: str, inpainter: Inpainter, text_boxes: List[TextBox]
    ) -> List[Tuple[int, int, int, int]]:
        img = cv2.imread(image_path)
        h, w = img.shape[:2]

        img_mask = inpainter._make_mask(text_boxes, h, w)
        mask = img_mask[:, :, 3]
        img_mask[img_mask[:, :, 3] == 0] = (127, 127, 127, 127)

        _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
        dilated_mask = cv2.dilate(binary_mask, kernel, iterations=1)
        num_labels, labels_im = cv2.connectedComponents(dilated_mask)

        boxes = []
        for label in range(1, num_labels):  # Start from 1 to skip the background
            x, y, w, h = cv2.boundingRect((labels_im == label).astype(np.uint8))
            boxes.append((x, y, w, h))
            img_mask = cv2.rectangle(img_mask, (x, y), (x + w, y + h), (255, 0, 0), 3)

        boxes.sort(key=lambda x: x[2] * x[3], reverse=True)
        return boxes

    def find_discharged_area(self, image_path: str) -> Tuple[int, int, int, int]:
        img = cv2.imread(image_path)
        h, w = img.shape[:2]

        areas_data = get_points_density(img, self.num_text_areas, self.point_threshold)
        for d in areas_data:
            print(d)
        y, y_max = areas_data[1][0]
        x = int(w * 0.05)
        x_max = w - x
        return x, y, x_max - x, y_max - y


class RemoveTextTool(MotleyTool):

    def __init__(
        self,
    ):
        """Tool for removing text from image"""
        remover = TextRemover()
        langchain_tool = create_render_tool(remover)
        super().__init__(langchain_tool)


class RemoveTextToolInput(BaseModel):
    """Input for the RemoveTextTool.

    Attributes:
        image_path (str):
    """

    image_path: str = Field(description="Path to the image")


def create_render_tool(remover: TextRemover):
    """Create langchain tool from TextRemover.remove_text method

    Returns:
        Tool:
    """
    return Tool.from_function(
        func=remover.remove_text,
        name="remove_text",
        description="""A tool for removing text from an image. 
                    Returns the path to the cleared image and text coordinate blocks in the format, (x, y, width, heigth)""",
        args_schema=RemoveTextToolInput,
    )
