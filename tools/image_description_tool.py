import os
from typing import Any
import base64

import openai
from langchain.tools import Tool, StructuredTool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools import MotleyTool

from .mixins import ViewDecoratorToolMixin
from viewers import StreamLitItemViewer, BaseViewer


class GptImageProcessor:

    def __init__(self, prompt: str, model: str = "gpt-4o", max_tokens: int = 400):
        self.prompt = prompt
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise Exception("OPENAI_API_KEY NOT FOUND")

        self.client = openai.Client(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def process_image(self, image_path: str, prompt: str = None) -> str:
        image_path = image_path.strip()
        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        _, img_ext = os.path.splitext(image_path)
        img_ext = img_ext[1:]

        base64_image = self.encode_image(image_path)
        prompt = prompt or self.prompt

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{img_ext};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        response = self.client.chat.completions.create(messages=messages,
                                                       model=self.model,
                                                       max_tokens=self.max_tokens)

        chat_message = response.choices[0].message
        return chat_message.content


class HtmlSloganRecommendTool(MotleyTool, ViewDecoratorToolMixin):

    def __init__(self, slogan: str, viewer: BaseViewer = None):
        """Tool for banner parse image
        """
        self.viewer = viewer
        prompt = '''Briefly describe the image, and give recommendations on generating html code to place 
        the text '{}' above the image. It is necessary to get recommendations on 
        (color, font, size, location and decoration) of the text.
        NOTE: not return html code example'''.format(slogan)
        renderer = GptImageProcessor(prompt=prompt)
        langchain_tool = create_render_tool(renderer)
        super().__init__(langchain_tool)
        ViewDecoratorToolMixin.__init__(self)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if not isinstance(self.viewer, StreamLitItemViewer):
            return

    def view_results(self, results: Any, *args, **kwargs):
        if self.viewer is None:
            return

        if not isinstance(self.viewer, StreamLitItemViewer):
            return


class HtmlSloganRecommendToolInput(BaseModel):
    """Input for the HtmlSloganRecommendTool.

    Attributes:
        image_path (str):
        prompt (str):
    """

    image_path: str = Field(description="Path to the image")
    prompt: str = Field(default=None, description="Recommendation, wish for formatting text in html code")


def create_render_tool(processor: GptImageProcessor):
    """Create langchain tool from GptImageProcessor.process_image method

    Returns:
        Tool:
    """
    return StructuredTool.from_function(
        func=processor.process_image,
        name="gpt_html_slogan_recommend",
        description="A tool for getting image description and  hints when creating html code placing and "
                    "configuring the visualization parameters of the text above the image.",
        args_schema=HtmlSloganRecommendToolInput,
    )
