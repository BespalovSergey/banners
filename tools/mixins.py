from typing import Callable, Any
from queue import Queue
from viewers import StreamLitViewer, StreamLiteItemView, StreamLitItemFormView


IMAGE_GENERATION_REMARKS_WIDGET_KEY = "image_generation_remark"


class ViewDecoratorToolMixin:

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "tool") or not hasattr(self, "viewer"):
            return

        object.__setattr__(self.tool, "_run", self.view_decorator(self.tool._run))

    def view_decorator(self, f: Callable):

        def wrapper(*args, config=None, **kwargs):
            self.before_run(*args, **kwargs)
            results = f(*args, config=config, **kwargs)
            results = self.program_check_tool_results(results)
            self.view_results(results, *args, **kwargs)
            results = self.human_check_results(results)
            return results

        return wrapper

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


class ViewDecoratorRemarksMixin(ViewDecoratorToolMixin):

    def __init__(self, remark_queue: Queue = None):
        self.remark_queue = remark_queue
        super().__init__()

    def set_remark_queue(self, q: Queue):
        self.remark_queue = q


class ViewDecoratorImageGenerationMixin(ViewDecoratorRemarksMixin):

    preface_remark = (
        "It is necessary to regenerate the images taking into account the following remarks"
    )
    remarks_title = "Remarks for image generation:"

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
