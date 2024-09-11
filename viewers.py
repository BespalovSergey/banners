from abc import ABC, abstractmethod
from typing import Any
from queue import Queue

import cv2
import streamlit as st

from utils import read_image


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

    def view(self, image_path: str, window_name: str = None, **kwargs):
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


# Streamlit classes and functions

class StreamLiteItemView:

    def __init__(self, data: dict):
        self.__data = data

    @property
    def data(self):
        return self.__data


class SpinnerStreamLitItemView:

    def __init__(self, text: str):
        self.__text = text

    @property
    def text(self):
        return self.__text


class StreamLitItemFormView:
    def __init__(self, form_key: str, items: StreamLiteItemView):
        self.form_key = form_key
        self.items = items


def streamlit_render(view_data: StreamLiteItemView):
    for func_name, args in view_data.data.items():
        if func_name == "form":
            streamlit_render_form(args)
            continue

        func = getattr(st, func_name, None)

        if func is None:
            continue

        if isinstance(args, dict):
            func(**args)
        else:
            func(*args)


def streamlit_render_form(form_item: StreamLitItemFormView):
    with st.form(key=form_item.form_key):
        streamlit_render(form_item.items)


def streamlit_queue_render(q: Queue, exit_value: Any = None):
    is_wait_view_data = True
    view_data = None
    while True:
        if is_wait_view_data:
            view_data = q.get()
        else:
            is_wait_view_data = True

        if view_data == exit_value:
            q.task_done()
            break

        if not isinstance(view_data, (StreamLiteItemView, SpinnerStreamLitItemView)):
            q.task_done()
            continue

        if isinstance(view_data, SpinnerStreamLitItemView):
            with st.spinner(view_data.text):
                q.task_done()
                view_data = q.get()
                is_wait_view_data = False
        elif isinstance(view_data, StreamLiteItemView):
            streamlit_render(view_data)
            q.task_done()


class StreamLitViewer(BaseViewer):

    def __init__(self, history_storage: Any = None):
        self.history_storage = history_storage

    def view(self, *args, **kwargs):
        pass

    def to_history(self, history_item: StreamLiteItemView):
        if self.history_storage is None:
            return
        self.history_storage.save_history(history_item)


class StreamLitItemViewer(StreamLitViewer):

    def view(self, view_data: StreamLiteItemView, *args, to_history: bool = True,  **kwargs):
        if to_history:
            self.to_history(view_data)
        streamlit_render(view_data)


class StreamLitItemQueueViewer(StreamLitViewer):

    def __init__(self, view_queue: Queue, storage: Any = None):
        self.view_queue = view_queue
        super().__init__(history_storage=storage)

    def view(self, view_data: StreamLiteItemView, *args, to_history: bool = True,  **kwargs):
        if to_history:
            self.to_history(view_data)
        self.view_queue.put(view_data)



