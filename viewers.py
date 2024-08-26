import os
from abc import ABC, abstractmethod

import cv2
import streamlit as st

from utils import read_image


class BaseViewer(ABC):

    @abstractmethod
    def view(self, *args, **kwargs):
        pass

    def view_caption(self, *args, **kwargs):
        pass


class CliImageViewer(BaseViewer):

    def __init__(self, scaler: int = None):
        self.scaler = scaler

    def view(self, image_path: str, window_name: str = None):
        window_name = window_name or "image"
        img = read_image(image_path)
        if self.scaler:
            h, w = img.shape[:2]
            n_h = int(h / self.scaler)
            n_w = int(w / self.scaler)
            img = cv2.resize(img, (n_w, n_h))
        cv2.imshow(window_name, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class StreamLitImageViewer(BaseViewer):

    def view(self, image_path, img_caption: str = ""):
        st.image(image_path, img_caption)
        st.text("Image path: {}".format(os.path.abspath(image_path)))

    def view_caption(self, subheader: str, text: str = None):
        st.subheader(subheader)
        if text:
            st.markdown(text)
