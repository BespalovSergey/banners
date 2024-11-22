from typing import Callable, Any
from threading import Event
from queue import Queue
from viewers import StreamLitViewer, SpinnerStreamLitItemView, StreamLiteItemView, StreamLitItemFormView
from exceptions import RunStopException


IMAGE_GENERATION_REMARKS_WIDGET_KEY = "image_generation_remark"


class ViewDecoratorToolMixin:

    preloader_text = ""

    def __init__(self, *args, **kwargs):
        self.stop_event = None
        if not hasattr(self, "tool") or not hasattr(self, "viewer"):
            return

        object.__setattr__(self.tool, "_run", self.view_decorator(self.tool._run))

    def view_decorator(self, f: Callable):

        def wrapper(*args, config=None, **kwargs):
            except_message_template = "Stop on tool {}, {}".format(self.name, "{}")

            self.check_stopping(except_message_template.format("before tool run"))

            self.before_run(*args, **kwargs)
            results = self.execute_tool(f, *args, config=config, **kwargs)
            self.check_stopping(except_message_template.format("after tool run"))

            results = self.program_check_tool_results(results)
            self.view_results(results, *args, **kwargs)
            results = self.human_check_results(results)
            return results

        return wrapper

    def execute_tool(self, f: Callable, *args, **kwargs) -> Any:
        if isinstance(self.viewer, StreamLitViewer):
            preloader_text = self.preloader_text or "Executing {} tool".format(self.name)
            self.viewer.view(SpinnerStreamLitItemView(text=preloader_text), to_history=False)
        return f(*args, **kwargs)

    def check_stopping(self, exception_message: str):
        if isinstance(self.stop_event, Event):
            if self.stop_event.is_set():
                raise RunStopException(exception_message)

    def before_run(self, *args, **kwargs):
        pass

    def view_results(self, results: Any, *args, **kwargs):
        pass

    def set_viewer(self, viewer: "BaseViewer"):
        self.viewer = viewer

    def program_check_tool_results(self, results: Any) -> Any:
        return results

    def human_check_results(self, results: Any) -> Any:
        return results

    def set_stop_event(self, e: Event):
        self.stop_event = e


class ViewDecoratorRemarksMixin(ViewDecoratorToolMixin):

    def __init__(self, remark_queue: Queue = None):
        self.remark_queue = remark_queue
        super().__init__()

    def set_remark_queue(self, q: Queue):
        self.remark_queue = q


class ViewDecoratorImageGenerationMixin(ViewDecoratorRemarksMixin):

    def __init__(self, is_text_editor: bool = False):
        self.is_text_editor = is_text_editor
        ViewDecoratorRemarksMixin.__init__(self)

    preface_remark = (
        "It is necessary to regenerate the images taking into account the following remarks"
    )
    remarks_title = "Remarks for image generation:"

    preloader_text = "Generation image ..."

    def human_check_results(self, results: Any) -> Any:
        if self.remark_queue is None or not isinstance(self.viewer, StreamLitViewer):
            return results

        form_view_items = {
            "text_area": {
                "label": "Remarks for image generation",
                "key": IMAGE_GENERATION_REMARKS_WIDGET_KEY,
            },
            "form_submit_button": ("Apply",),
        }

        form_item_view = StreamLitItemFormView(
            form_key="check_image_generation",
            items=StreamLiteItemView(form_view_items),
        )
        form_data = {"form": form_item_view}
        self.viewer.view(StreamLiteItemView(form_data), to_history=False)
        remarks = self.remark_queue.get()
        if not remarks:
            return results

        remarks_view_data = {"text": (self.remarks_title,), "markdown": (remarks,)}
        self.viewer.view(StreamLiteItemView(remarks_view_data))

        results = "{}: {}".format(self.preface_remark, remarks)
        return results

    def view_image(self, img_path: str, *args):
        if isinstance(self.viewer, StreamLitViewer):
            if self.is_text_editor:
                view_data = {"image_text_editor": (img_path,)}
            else:
                view_data = {"image": (img_path, args[0])}

            self.viewer.view(StreamLiteItemView(view_data), to_history=True)
        else:
            self.viewer.view(img_path)

    def view_results(self, results: Any, *args, **kwargs):
        if self.viewer is None:
            return
        for img_path in results:
            if img_path.startswith("http"):
                continue
            self.view_image(img_path, *args)
