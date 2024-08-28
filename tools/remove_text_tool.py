import os
from typing import List, Tuple, Any

import cv2
import numpy as np


from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools import MotleyTool

from clear_image.text_deleter import TextDeleter
from clear_image.inpainter import DalleInpainter, Inpainter
from clear_image.text_detector import KerasOcrTextDetector, TextBox
from utils import get_points_density, combining_mask_boxes, read_image, bbox_w_h_to_x_max_y_max
from .mixins import ViewDecoratorToolMixin
from viewers import BaseViewer, StreamLitItemQueueViewer, StreamLiteItemView


class TextRemover:

    def __init__(self, num_text_areas: int = 5, point_threshold: float = 0.1):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.num_text_areas = num_text_areas
        self.point_threshold = point_threshold
        self.bboxes = []
        self.text_area = None
        super().__init__()

    def remove_text(self, image_path: str) -> str:
        self.bboxes.clear()
        self.text_area = None
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

        if text_deleter.text_bboxes:
            boxes = self.find_text_boxes(image_path, inpainter, text_deleter.text_bboxes)
            self.bboxes = boxes
        else:
            text_area = self.find_discharged_area(image_path)
            self.text_area = text_area
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

        combining_mask = combining_mask_boxes(mask, kernel=(20, 20), iterations=1)
        num_labels, labels_im = cv2.connectedComponents(combining_mask)

        boxes = []
        for label in range(1, num_labels):  # Start from 1 to skip the background
            x, y, w, h = cv2.boundingRect((labels_im == label).astype(np.uint8))
            boxes.append((x, y, w, h))

        boxes.sort(key=lambda x: x[2] * x[3], reverse=True)
        return boxes

    def find_discharged_area(self, image_path: str) -> Tuple[int, int, int, int]:
        img = cv2.imread(image_path)
        h, w = img.shape[:2]

        areas_data = get_points_density(img, self.num_text_areas, self.point_threshold)

        y, y_max = areas_data[1][0]
        x = int(w * 0.05)
        x_max = w - x
        return x, y, x_max - x, y_max - y


class RemoveTextTool(MotleyTool, ViewDecoratorToolMixin):

    def __init__(self, viewer: BaseViewer = None):
        """Tool for removing text from image"""
        self.viewer = viewer
        self.remover = TextRemover()
        langchain_tool = create_render_tool(self.remover)
        MotleyTool.__init__(self, langchain_tool)
        ViewDecoratorToolMixin.__init__(self)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if not isinstance(self.viewer, StreamLitItemQueueViewer):
            return

        view_data = {
            "subheader": ("Removing text from image",),
            "text": ("Image path: {}".format(os.path.abspath(args[0])),),
        }
        self.viewer.view(StreamLiteItemView(view_data), to_history=True)

    def view_results(self, results: Any, *args, **kwargs):
        if self.viewer is None:
            return

        if not isinstance(self.viewer, StreamLitItemQueueViewer):
            return

        img = read_image(args[0], to_bgr=False)
        bboxes = self.remover.bboxes or [self.remover.text_area]
        for box in bboxes:
            x_min, y_min, x_max, y_max = bbox_w_h_to_x_max_y_max(box)
            img = cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)

        caption = "Text bound boxes" if self.remover.bboxes else "Text Area"
        view_data = {"image": (img, caption)}
        self.viewer.view(StreamLiteItemView(view_data), to_history=True)


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
