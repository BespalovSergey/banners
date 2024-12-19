from abc import ABC, abstractmethod
from queue import Queue
from threading import Thread
import time

from utils import show_image
from motleycrew.common.exceptions import InvalidOutput
from tools.image_description_tool import GptImageProcessor
from viewers import StreamLitItemView, StreamLitItemQueueViewer, StreamLitItemFormView


REMARKS_WIDGET_KEY = "remarks"


class BaseChecker(ABC):

    @abstractmethod
    def check(self, image_path: str) -> bool:
        pass


class CliHumanChecker(BaseChecker):

    remarks_prefix = {"recommendation": "ask recommendations how"}
    remarks_postfix = {
        "recommendation": "Need text coordinates (x, y, width, height), color, size, slant text block,"
        " font, add the slogan text to the recommendation request",
    }

    def check(self, image_path: str) -> bool:
        # show image
        q = Queue()
        t = Thread(target=show_image, args=[image_path, q])
        t.start()

        # remarks
        time.sleep(1)
        remarks = []
        features = ("color", "size", "position", "font", "additions", "recommendation")
        for feature in features:
            input_text = "Change text {}? input text {} or press Enter: ".format(feature, feature)
            input_result = input(input_text)
            if input_result:
                prefix = self.remarks_prefix.get(feature, feature)
                postfix = self.remarks_postfix.get(feature, "")
                remark = "    {}: {} {}".format(prefix, input_result, postfix)
                remarks.append(remark)
        q.put(None)

        if remarks:
            remarks_text = "update html text:\n{}".format("\n".join(remarks))
            raise InvalidOutput(remarks_text)
        return True


class GptImageChecker(BaseChecker):

    def __init__(self, text: str = ""):
        self.checked_text = f"'{text}'" or ""

    def check(self, image_path: str) -> bool:
        result_ok_symbols = "THERE ARE NO COMMENTS"
        prompt = """Look at the image, evaluate the quality of the text display {}, 
        and if there are comments recommendations for better display such as (color, size, location, decoration) 
        of the text have come. If the text is displayed well, 
        then they only came {}.""".format(
            self.checked_text, result_ok_symbols
        )

        image_processor = GptImageProcessor(prompt=prompt)
        image_result = image_processor.process_image(image_path)

        if result_ok_symbols.lower() not in image_result.lower():
            raise InvalidOutput(image_result)
        return True


class StreamLitHumanChecker(BaseChecker):

    def __init__(
        self,
        iteration: int = 0,
        viewer: StreamLitItemQueueViewer = None,
        remarks_queue: Queue = None,
    ):
        self.iteration = iteration
        self.viewer = viewer
        self.remarks_queue = remarks_queue

    def check(self, image_path: str) -> bool:
        self.iteration += 1
        if not isinstance(self.viewer, StreamLitItemQueueViewer):
            raise ValueError("Viewer must be init  StreamLitItemQueueViewer")

        start_check_view_data = {
            "subheader": ("Human check: {}".format(self.iteration),),
            "text": ("Image path: {}".format(image_path),),
            "image": (image_path, "Checked image"),
        }
        self.viewer.view(StreamLitItemView(start_check_view_data), to_history=True)

        form_view_items = {
            "text_area": {"label": "Remarks for html generation", "key": REMARKS_WIDGET_KEY},
            "form_submit_button": ("Apply",),
        }

        form_item_view = StreamLitItemFormView(
            form_key="check_form_{}".format(self.iteration),
            items=StreamLitItemView(form_view_items),
        )

        form_view_data = {"form": form_item_view}
        self.viewer.view(StreamLitItemView(form_view_data), to_history=False)

        if self.remarks_queue is None:
            return True

        remarks = self.remarks_queue.get()
        if remarks:
            remarks_title = "Remarks for html generation:"
            remarks_view_data = {"text": (remarks_title,), "markdown": (remarks,)}

            self.viewer.view(StreamLitItemView(remarks_view_data), to_history=True)

            raise InvalidOutput("{}: {}".format(remarks_title, remarks))

        return True
