from typing import Callable, Any
from threading import Event
from queue import Queue
from viewers import StreamLitViewer, SpinnerStreamLitItemView, StreamLitItemView, StreamLitItemFormView
from exceptions import RunStopException

import streamlit as st

TEXT_GENERATION_REMARKS_WIDGET_KEY = "text_generation_remark"


class ViewDecoratorToolMixin:

    preloader_text = ""

    def __init__(self, *args, **kwargs):
        self.stop_event = None
        self.new_prompt_with_remarks: str = ""
        
        self.finish_event = Event()
        
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
            
            self.finish_event.set()
            
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
                self.stop_event.clear()
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
    
    def get_new_prompt_with_remarks(self) -> str:
        return self.new_prompt_with_remarks
    
    

class ViewDecoratorRemarksMixin(ViewDecoratorToolMixin):

    def __init__(self, remark_queue: Queue = None):
        self.remark_queue = remark_queue
        super().__init__()

    def put_remarks(self, remark: str):
        self.remark_queue.put(remark)

    def set_remark_queue(self, q: Queue):
        self.remark_queue = q


class ViewDecoratorPostTextGenerationMixin(ViewDecoratorRemarksMixin):
    def __init__(self):
        self._remarks_queue = Queue()
        ViewDecoratorRemarksMixin.__init__(self, remark_queue=self._remarks_queue)

    # preface_remark = (
    #     "It is necessary to regenerate the text taking into account the following remarks"
    # )
    
    # preface_remark = (
    #     "С указанным в кавычках текстом необходимо сделать следующее: "
    # )
    
    remarks_title = "Remarks for text generation:"

    preloader_text = "Generation text ..."

    def human_check_results(self, results: Any) -> Any:
            
        if self.remark_queue is None or not isinstance(self.viewer, StreamLitViewer):
            return results

        if self.remarks_iterations == self.max_remarks_iterations:
            self.stop()
            return results

        form_view_items = {
            "text_area": {
                "label": "Remarks for text generation",
                "key": TEXT_GENERATION_REMARKS_WIDGET_KEY,
            },
            "form_submit_button": ("Apply",),
        }

        form_item_view = StreamLitItemFormView(
            form_key="check_text_generation",
            items=StreamLitItemView(form_view_items),
        )
        form_data = {"form": form_item_view}
        self.viewer.view(StreamLitItemView(form_data), to_history=False)
        remarks = self.remark_queue.get()
        
        if not remarks:
            self.new_prompt_with_remarks = ""
            return results

        remarks_view_data = {"text": (self.remarks_title,), "markdown": (remarks,)}
        self.viewer.view(StreamLitItemView(remarks_view_data))

        # results_remarks = '"{}". {}: {}'.format(results, self.preface_remark, remarks)
        # results_remarks = f'"{results}". {self.preface_remark}: {remarks}'
        # results_remarks = f'"{results}". {remarks}.'
        results_remarks = f"Исправь следующий текст поста согласно замечаниям: '{remarks}'. Вот текущий текст: '{results}'"
        
        self.remarks_iterations += 1
        self.new_prompt_with_remarks = results_remarks
        
        return results

    def view_generated_text(self, result_text: str):
        if isinstance(self.viewer, StreamLitViewer):
            view_data = {
                "markdown": (f"### Generated Text:\n{result_text}",),
            }
            self.viewer.view(StreamLitItemView(view_data), to_history=True)
        else:
            self.viewer.view(result_text)
    
    def view_results(self, results: Any, *args, **kwargs):
        
        if self.viewer is None:
            return
        
        self.view_generated_text(result_text=results)
