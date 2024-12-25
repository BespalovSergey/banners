import os
import sys
from threading import Thread
from queue import Queue

import streamlit as st

from ui.ui_utils import find_remarks

from viewers import StreamLitItemView, StreamLitItemQueueViewer

from tools.generate_post_tools.generate_post_mixins import TEXT_GENERATION_REMARKS_WIDGET_KEY
from tools.generate_post_tools.text_generation_tool import PostTextGeneratorTool
from tools.outpainting_tools import ReplicateImagePaintingTool
    
def run_generate(postTextGenerator: PostTextGeneratorTool, render_queue: Queue, prompt: str):
    try:
        postTextGenerator.text_generator.set_prompt(prompt)
        postTextGenerator.invoke(prompt)
    except Exception as e:
        view_data = {"subheader": ("Error:",), "code": (str(e),)}
        render_queue.put(StreamLitItemView(view_data))

def run_paint(painter: ReplicateImagePaintingTool, render_queue: Queue, prompt: str):
    try:
        painter.invoke(prompt)
    except Exception as e:
        view_data = {"subheader": ("Error:",), "code": (str(e),)}
        render_queue.put(StreamLitItemView(view_data))
    # finally:
    #     render_queue.put(None)

class Worker():
    ui_state_name = "worker"
    
    def __init__(
        self, 
        max_remarks_iterations: int,
        genetation_text_prompt: str,
    ):
        self.max_remarks_iterations = max_remarks_iterations
        self.prompt_for_text_generator = genetation_text_prompt
        self._history = []
        self._render_queue = Queue()
        self._remarks_queue = Queue()
        self.new_prompt = ""
    
    @property
    def render_queue(self):
        return self._render_queue
    
    def save_history(self, item: StreamLitItemView):
        self._history.append(item)

    def get_history(self):
        return self._history

    def reset_view(self):
        self._render_queue.put(None)
        self._render_queue.join()

    def stop(self):
        self._remarks_queue.put(None)
        self._render_queue.put(None)
    
    def run_post_text_generator(self):
        generator = PostTextGeneratorTool(
            max_remarks_iterations = self.max_remarks_iterations,
            history_storage = self,
            render_queue = self._render_queue
        )
        
        t = Thread(target=run_generate, args=(generator, self._render_queue, self.prompt_for_text_generator))
        st.session_state[PostTextGeneratorTool.ui_state_name] = generator
        t.start()
        
    def get_previous_history(self):
        viewer = StreamLitItemQueueViewer(self._render_queue)
        history = self.get_history()
        for view_item in history:
            viewer.view(view_item, to_history=False)
    
    def get_remarks(self):
        text_generator = st.session_state.get(PostTextGeneratorTool.ui_state_name)
        
        remarks, widget_key = find_remarks(TEXT_GENERATION_REMARKS_WIDGET_KEY)
        if remarks:
            text_generator.put_remarks(remarks)
            if widget_key:
                st.session_state[widget_key] = None
        else:
            text_generator.put_remarks(None)
    
    def continue_generation(self):
        text_generator = st.session_state.get(PostTextGeneratorTool.ui_state_name)
        text_generator.finish_event.wait()
        new_prompt = text_generator.get_new_prompt_with_remarks()  
        
        if new_prompt == "":
            text_generator.remarks_completed_event.set()
        else:
            generator = st.session_state.get(PostTextGeneratorTool.ui_state_name)
            t = Thread(target=run_generate, args=(generator, self._render_queue, new_prompt))
            t.start()
        
    def init_image_genarator(self):
        st.header("Painting images")

        self.select_model_label = "Select image generation model"
        self.prompt_label = "Prompt"
        self.negative_prompt_label = "Negative prompt"
        self.file_upload_label = "Image"
        self.product_size_label = "Object size"
        self.num_image_label = "Num images"
        self.seed_label = "Seed"
        self.scale_label = "Scale"
        self.images_dir_label = "Image dir"
        self.guidance_scale_label = "Guidance scale"
        self.num_inference_steps_label = "Num inference steps"
        # self.is_image_text_editor_label = "View with text editor"

        self.product_size_items = ["Original"]
        for val in (0.6, 0.5, 0.4, 0.3, 0.2):
            self.product_size_items.append("{} * width".format(val))

        with st.form("new_form"):
            st.selectbox(
                self.select_model_label,
                options=["Replicate",],
                index=0
            )
            self.prompt = st.text_area(self.prompt_label, "do not change background, make a professional light for food photo", height=200)
            self.negative_prompt = st.text_area(self.negative_prompt_label, "do not change background, make a professional light for food photo", height=200)
            self.file_image = st.file_uploader(self.file_upload_label, type=['png', 'jpg'])
            # self.is_image_text_editor = st.toggle(self.is_image_text_editor_label, True)
            
            with st.expander("Image generation settings"):
                self.num_image = st.number_input(self.num_image_label, 1, 4, 1, 1)
                self.product_size = st.selectbox(self.product_size_label, self.product_size_items, index=2)
                self.seed = st.number_input(self.seed_label, 0, 1000000, 0, 1)
                self.scale = st.number_input(self.scale_label, 1, 4, 3, 1)
                self.guidance_scale = st.number_input(self.guidance_scale_label, 1.0, 20.0, 7.5, 0.1)
                self.num_inference_steps = st.number_input(self.num_inference_steps_label, 1, 100, 20, 1)
                self.images_dir = st.text_input(self.images_dir_label, "painting_images")

            self.submited = st.form_submit_button("Submit")
    
    
    def run_image_genarator(self):
        if self.submited:
            st.success("Image generation parameters submitted!")
            
            is_valid_fields = True
            for text, label in (
                (self.prompt, self.prompt_label),
                (self.file_image, self.file_upload_label),
                (self.images_dir, self.images_dir_label),
            ):
                if not text:
                    st.text("{} field required".format(label))
                    is_valid_fields = False

            if not is_valid_fields:
                return

            # images dir
            if not os.path.exists(self.images_dir):
                os.makedirs(self.images_dir, exist_ok=True)
            self.images_dir = os.path.abspath(self.images_dir)
            
            # render_queue = Queue()
            
            painter_kwargs = {
                "product_size": self.product_size,
                "negative_prompt": self.negative_prompt,
                "image_num": self.num_image,
                "scale": self.scale,
                "guidance_scale": self.guidance_scale,
                "num_inference_steps": self.num_inference_steps
            }
            if self.seed > 0:
                painter_kwargs["manual_seed"] = self.seed

            painter = ReplicateImagePaintingTool(
                images_directory=self.images_dir,
                original_image=self.file_image,
                # is_text_editor=self.is_image_text_editor,
                is_text_editor=False,
                **painter_kwargs
            )
            
            st.session_state["painter"] = painter
            
            painter.set_viewer(StreamLitItemQueueViewer(self._render_queue, storage=self))

            t = Thread(target=run_paint, args=(painter, self._render_queue, self.prompt))
            t.start()
