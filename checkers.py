from abc import ABC, abstractmethod
from queue import Queue
from threading import Thread
import time

from utils import show_image
from motleycrew.common.exceptions import InvalidOutput
from tools.image_description_tool import GptImageProcessor


class BaseChecker(ABC):

    @abstractmethod
    def check(self, image_path: str) -> bool:
        pass


class HumanChecker(BaseChecker):

    def check(self, image_path: str) -> bool:
        # show image
        q = Queue()
        t = Thread(target=show_image, args=[image_path, q])
        t.start()

        # remarks
        time.sleep(1)
        remarks = []
        features = ("color", "size", "position", "font", "additions")
        for feature in features:
            input_text = "Change text {}? input text {} or press Enter: ".format(feature, feature)
            input_result = input(input_text)
            if input_result:
                remark = "    {}: {}".format(feature, input_result)
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
