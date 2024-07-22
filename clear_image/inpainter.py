"""In-painting models."""
import io
import openai
import requests
import numpy as np

from PIL import Image, ImageDraw
from typing import Sequence

from clear_image.text_detector import TextBox


class Inpainter:
    """Interface for in-painting models."""
  # TODO(julia): Run some experiments to determine the best prompt.
    DEFAULT_PROMPT = "plain background"

    def inpaint(self, in_image_path: str, text_boxes: Sequence[TextBox], prompt: str, out_image_path: str):
        pass


class DalleInpainter(Inpainter):
    """In-painting model that calls the DALL-E API."""

    def __init__(self, openai_key: str):
         self.client = openai.Client(api_key=openai_key)

    @staticmethod
    def _make_mask(text_boxes: Sequence[TextBox], height: int, width: int) -> bytes:
        """Returns an .png where the text boxes are transparent."""

        alpha = np.ones((height, width, 1)) * 255
        for text_box in text_boxes:
            alpha[text_box.y: text_box.y + text_box.h, text_box.x: text_box.x + text_box.w, 0] = 0

        mask = np.zeros((height, width, 3))
        mask = np.concatenate([mask, alpha], axis=2)
        mask = Image.fromarray(mask.astype(np.uint8))

        # Convert mask to bytes.
        bytes_arr = io.BytesIO()
        mask.save(bytes_arr, format="PNG")
        return bytes_arr.getvalue()

    def inpaint(self, in_image_path: str, text_boxes: Sequence[TextBox], prompt: str, out_image_path: str):
        image = Image.open(in_image_path)  # open the image to inspect its size

        # import cv2
        # img = cv2.imread(in_image_path)
        # h, w = img.shape[:2]
        # img = cv2.resize(img, (int(w/2), int(h/2)))
        #
        # for box in text_boxes:
        #     x_max = int(box.x + box.w)
        #     y_max = int(box.y + box.h)
        #
        #     try:
        #       img = cv2.rectangle(img, (int(box.x/2), int(box.y/2)), (int(x_max/2), int(y_max/2) ), (0, 255, 255), 2)
        #     except BaseException:
        #       print("exception")
        #
        #
        # cv2.imshow('img', img)
        # cv2.waitKey(0)
        # print("prompt: ", prompt)
        response = self.client.images.edit(
        image=open(in_image_path, "rb"),
        mask=self._make_mask(text_boxes, image.height, image.width),
        prompt=prompt,
        n=1,
        )
        url = response.data[0].url
        out_image_data = requests.get(url).content
        out_image = Image.open(io.BytesIO(out_image_data))
        out_image.save(out_image_path)
