import os

from queue import Queue

from langchain.agents import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools.tool import MotleyTool

from tools.generate_post_tools.generate_post_mixins import ViewDecoratorPostTextGenerationMixin

from viewers import StreamLitViewer, StreamLitItemView

from openai import OpenAI

from viewers import StreamLitItemQueueViewer


from threading import Event

class PostTextGenerator():

    def __init__(
        self,
        model_name: str = "OpenAI_gpt_4",
    ):
        self.client = self._initialize_openai_client()
        self.model_name = model_name

    def set_prompt(self, prompt: str):
        self.prompt_text = prompt
    
    def _initialize_openai_client(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise Exception("OPENAI_API_KEY NOT FOUND")
        return OpenAI()

    def generate_post(self, description: str) -> str:
        
        completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional assistant for writing russian text for restaurants posts in social networks."},
                {"role": "user", "content": description}
            ]
        )
        
        generated_text = completion.choices[0].message.content
        return generated_text



class PostTextGeneratorToolInput(BaseModel):
    """Input for the Post-Text-Generator tool."""

    description: str = Field(description="post text description")


class PostTextGeneratorTool(MotleyTool, ViewDecoratorPostTextGenerationMixin):
    ui_state_name = "post_text_generator"
    
    def __init__(
        self,
        max_remarks_iterations: str
    ):
        self._render_queue = Queue()
        self.viewer = StreamLitItemQueueViewer(self._render_queue, self)
        self._history = []
        self.my_stop_event = Event()
        self.remarks_iterations: int = 0
        self.max_remarks_iterations = max_remarks_iterations

        self.text_generator = PostTextGenerator()
        
        langchain_tool = create_replicate_image_painter_langchain_tool(self.text_generator)

        super().__init__(langchain_tool)
        ViewDecoratorPostTextGenerationMixin.__init__(self)
        self.set_stop_event(self.my_stop_event)

    @property
    def render_queue(self):
        return self._render_queue
    
    def save_history(self, item: StreamLitItemView):
        self._history.append(item)

    def get_history(self):
        return self._history
    
    def reset_view(self):
        self._render_queue.put(None)

    def stop(self):
        self._remarks_queue.put(None)
        self._render_queue.put(None)
        if not self.my_stop_event.is_set():
            self.my_stop_event.set()
        # self.reset_view()
        
    
    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if isinstance(self.viewer, StreamLitViewer) and self.remarks_iterations < 1:
            view_data = {
                "subheader": ("Post text generator model:",),
                "text": (self.text_generator.model_name,),
            }
            self.viewer.view(StreamLitItemView(view_data), to_history=True)

            view_data = {
                "subheader": ("Prompt:",), 
                "markdown": (self.text_generator.prompt_text,)
            }
            self.viewer.view(StreamLitItemView(view_data), to_history=True)


def create_replicate_image_painter_langchain_tool(text_generator: PostTextGenerator):

    return Tool(
        name=f"{text_generator.model_name}_post_text_generator",
        func=text_generator.generate_post,
        description=f"A wrapper around the {text_generator.model_name} text generation model. It is used when it is necessary to generate russian text for post in social networks. ",
        args_schema=PostTextGeneratorToolInput,
    )