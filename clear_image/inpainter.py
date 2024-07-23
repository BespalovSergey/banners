"""In-painting models."""
import io
from abc import ABC, abstractmethod
import openai
import requests
import numpy as np

from PIL import Image, ImageDraw
from typing import Sequence

from clear_image.text_detector import TextBox


class Inpainter(ABC):
    """Interface for in-painting models."""
    DEFAULT_PROMPT = "plain background"

    @abstractmethod
    def inpaint(self, in_image_path: str, text_boxes: Sequence[TextBox], prompt: str, out_image_path: str):
        pass

    @abstractmethod
    def _make_mask(self, text_boxes: Sequence[TextBox], height: int, width: int) -> np.array:
        pass

    @abstractmethod
    def _make_mask_as_bytes(self, text_boxes: Sequence[TextBox], height: int, width: int) -> bytes:
        pass


class DalleInpainter(Inpainter):
    """In-painting model that calls the DALL-E API."""

    def __init__(self, openai_key: str):
         self.client = openai.Client(api_key=openai_key)

    def _make_mask(self, text_boxes: Sequence[TextBox], height: int, width: int) -> np.array:
        """Returns an .png where the text boxes are transparent."""

        alpha = np.ones((height, width, 1)) * 255
        for text_box in text_boxes:
            alpha[text_box.y: text_box.y + text_box.h, text_box.x: text_box.x + text_box.w, 0] = 0

        mask = np.zeros((height, width, 3))
        mask = np.concatenate([mask, alpha], axis=2)
        mask = mask.astype(np.uint8)
        return mask

    def _make_mask_as_bytes(self, text_boxes: Sequence[TextBox], height: int, width: int) -> bytes:
        mask = self._make_mask(text_boxes, height, width)
        mask = Image.fromarray(mask)

        bytes_arr = io.BytesIO()
        mask.save(bytes_arr, format="PNG")
        return bytes_arr.getvalue()

    def inpaint(self, in_image_path: str, text_boxes: Sequence[TextBox], prompt: str, out_image_path: str):
        image = Image.open(in_image_path)  # open the image to inspect its size

        response = self.client.images.edit(
        image=open(in_image_path, "rb"),
        mask=self._make_mask_as_bytes(text_boxes, image.height, image.width),
        prompt=prompt,
        n=1,
        )
        url = response.data[0].url
        out_image_data = requests.get(url).content
        out_image = Image.open(io.BytesIO(out_image_data))
        out_image.save(out_image_path)
