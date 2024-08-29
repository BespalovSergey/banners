from typing import List, Tuple
from threading import Event
from queue import Queue


from motleycrew.tools import MotleyTool
from generator import BannerGeneratorWithText
from checkers import BaseChecker
from viewers import StreamLitItemQueueViewer, StreamLiteItemView
from exceptions import RunStopException, GeneratorIsRunException
from utils import clear_queue


class UiBannerGeneratorWithText(BannerGeneratorWithText):
    ui_state_name = "ui_banner_generator_with_text"

    def __init__(
        self,
        image_description: str,
        text_description: str,
        images_dir: str,
        slogan: str,
        html_render_checkers: List[BaseChecker] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        max_review_iterations: int = 5,
        image_generate_tool: MotleyTool = None,
    ):
        super().__init__(
            image_description=image_description,
            text_description=text_description,
            images_dir=images_dir,
            slogan=slogan,
            html_render_checkers=html_render_checkers,
            image_size=image_size,
            max_review_iterations=max_review_iterations,
            image_generate_tool=image_generate_tool,
        )

        self.__is_run = False
        self.__render_queue = Queue()
        self.__remarks_queue = Queue()
        self.__stop_event = Event()
        self._history = []

        for checker in html_render_checkers:
            if hasattr(checker, "viewer"):
                checker.viewer = StreamLitItemQueueViewer(self.__render_queue, self)

            if hasattr(checker, "remarks_queue"):
                checker.remarks_queue = self.__remarks_queue

        self.html_render_output_handler.viewer = StreamLitItemQueueViewer(self.__render_queue, self)

        for tool in self.tools:
            if hasattr(tool, "set_viewer") and tool.viewer is None:
                tool.set_viewer(StreamLitItemQueueViewer(self.__render_queue, self))

            if hasattr(tool, "set_remark_queue"):
                tool.set_remark_queue(self.__remarks_queue)

            if hasattr(tool, "set_stop_event"):
                tool.set_stop_event(self.__stop_event)

    def run(self):
        if self.__is_run:
            raise GeneratorIsRunException

        self.__is_run = True
        result = None
        clear_queue(self.__render_queue)
        clear_queue(self.__remarks_queue)
        self.__stop_event.clear()

        try:
            result = super().run()
        except RunStopException as e:
            pass
        except Exception as e:
            view_data = {"subheader": ("Error:",), "code": (str(e),)}
            self.__render_queue.put(StreamLiteItemView(view_data))
        finally:
            self.__render_queue.put(None)
            self.__remarks_queue.put(None)
            self.__is_run = False

        return result

    @property
    def render_queue(self):
        return self.__render_queue

    @property
    def is_run(self):
        return self.__is_run

    def save_history(self, item: StreamLiteItemView):
        self._history.append(item)

    def get_history(self):
        return self._history

    def clear_history(self):
        self._history.clear()

    def put_remarks(self, remark: str):
        self.__remarks_queue.put(remark)

    def reset_view(self):
        self.__render_queue.put(None)
        if not self.__stop_event.is_set():
            self.__render_queue.join()

    def stop(self):
        self.__remarks_queue.put(None)
        if not self.__stop_event.is_set():
            self.__stop_event.set()
        self.reset_view()
