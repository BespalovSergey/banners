"""Interfaces for text detection."""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Sequence
from PIL import Image

import pytesseract
from keras_ocr.pipeline import Pipeline
from keras_ocr.tools import drawAnnotations


@dataclass
class TextBox:
  x: int
  y: int
  h: int
  w: int
  text: str = None


class TextDetector:
  def detect_text(self, image_filename: str) -> Sequence[TextBox]:
    pass


class TesseractTextDetector(TextDetector):
  """Uses the `tesseract` OCR library from Google to do text detection."""

  def __init__(self, tesseract_path: str):
    """
    Args:
      tesseract_path: The path where the `tesseract` library is installed, e.g. "/usr/bin/tesseract".
    """
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

  def detect_text(self, image_filename: str) -> Sequence[TextBox]:
    image = Image.open(image_filename)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    boxes = [TextBox(l, top, w, h, text)
             for l, top, w, h, text in zip(data["left"], data["top"], data["width"], data["height"], data["text"])
             if text.strip()]
    return boxes


class KerasOcrTextDetector(TextDetector):

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(KerasOcrTextDetector, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.pipeline = Pipeline()

    def detect_text(self, image_filename: str) -> Sequence[TextBox]:
        prediction_groups = self.pipeline.recognize([image_filename])

        boxes = []
        for group in prediction_groups:
            for text, coords  in group:
                x_min = int(np.min(coords[:, 0]))
                x_max = int(np.max(coords[:, 0]))
                w = x_max - x_min

                y_min = int(np.min(coords[:, 1]))
                y_max = int(np.max(coords[:, 1]))
                h = y_max - y_min

                box = TextBox(x_min, y_min, h, w, text=text)
                boxes.append(box)

        return boxes
