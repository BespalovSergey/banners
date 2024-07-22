import os
from dotenv import load_dotenv


from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools import MotleyTool

from clear_image.text_deleter import TextDeleter
from clear_image.inpainter import DalleInpainter
from clear_image.text_detector import KerasOcrTextDetector



class TextRemover:

    def __init__(self,):
        self.api_key = os.environ.get("OPENAI_API_KEY")
    def remove_text(self, image_path: str) -> str:
        image_path = image_path.strip()
        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        file_name, ext = os.path.splitext(image_path)
        output_image_path = "{}_remove_text{}".format(file_name,ext)
        text_detector = KerasOcrTextDetector()
        inpainter = DalleInpainter(self.api_key)
        text_deleter = TextDeleter(text_detector, inpainter)
        return text_deleter.delete_text(image_path, output_image_path)


class RemoveTextTool(MotleyTool):

    def __init__(self,):
        """Tool for removing text from image
        """
        remover = TextRemover()
        langchain_tool = create_render_tool(remover)
        super().__init__(langchain_tool)


class RemoveTextToolInput(BaseModel):
    """Input for the RemoveTextTool.

    Attributes:
        image_path (str):
    """

    image_path: str = Field(description="Path to the image")


def create_render_tool(remover: TextRemover):
    """Create langchain tool from TextRemover.remove_text method

    Returns:
        Tool:
    """
    return Tool.from_function(
        func=remover.remove_text,
        name="remove_text",
        description="A tool for removing text from an image",
        args_schema=RemoveTextToolInput,
    )


if __name__ == '__main__':
    load_dotenv()
    image_path = r"C:\Users\User\PycharmProjects\motleycrew\examples\banner_images\72743db5.png"
    tesseract_installation = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    remove_tool = RemoveTextTool(tesseract_installation)
    remove_result = remove_tool.invoke(image_path)
    print("remove result: ", remove_result)
