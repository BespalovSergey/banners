import os
from abc import ABC, abstractmethod
from typing import Any

import cv2
import streamlit as st

from utils import read_image, STREAMLIT_HISTORY_KEY


class BaseViewer(ABC):

    @abstractmethod
    def view(self, *args, **kwargs):
        pass

    def view_caption(self, *args, **kwargs):
        pass

    def to_history(self, history_item: Any):
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


# Streamlit classes

class StreamLiteItemView:

    def __init__(self, data: dict):
        self.__data = data

    @property
    def data(self):
        return self.__data


class StreamLitViewer(BaseViewer):

    def view(self, *args, **kwargs):
        pass

    def to_history(self, history_item: StreamLiteItemView):
        if st.session_state.get(STREAMLIT_HISTORY_KEY, None) is None:
            st.session_state[STREAMLIT_HISTORY_KEY] = []
        st.session_state.get(STREAMLIT_HISTORY_KEY).append(history_item)


class StreamLitImageViewer(StreamLitViewer):

    def view(self, image_path, img_caption: str = ""):
        st.image(image_path, img_caption)
        st.text("Image path: {}".format(os.path.abspath(image_path)))

    def view_caption(self, subheader: str, text: str = None):
        st.subheader(subheader)
        if text:
            st.markdown(text)


class StreamLitItemViewer(StreamLitViewer):

    def view(self, view_data: StreamLiteItemView, *args, to_history: bool = False,  **kwargs):
        if to_history:
            self.to_history(view_data)

        self._view_item(view_data)

    def view_caption(self, view_data: StreamLiteItemView, *args, to_history: bool = False,  **kwargs):
        if to_history:
            self.to_history(view_data)
        self._view_item(view_data)

    @staticmethod
    def _view_item(view_data: StreamLiteItemView, *args, **kwargs):
        for func_name, args in view_data.data.items():
            print("item viewer: ", func_name, args)

            func = getattr(st, func_name, None)
            if func is None:
                print("func is None")
                continue
            print("run func: ", func_name)
            func(*args)



