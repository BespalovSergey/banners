import os
import sys
from threading import Thread
from queue import Queue

from motleycrew.common.logging import logger, configure_logging
from dotenv import load_dotenv

sys.path.append(os.path.abspath("."))

import streamlit as st

from tools.outpainting_tools import ReplicateImagePaintingTool
from viewers import StreamLitItemQueueViewer, streamlit_queue_render
from ui.ui_utils import navigation_menu


configure_logging(verbose=True)
load_dotenv()

# init sidebar width
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"]{
    min-width: 25%;
    max-width: 25%;
    }
    """,
    unsafe_allow_html=True,
)


def run_paint(painter: ReplicateImagePaintingTool, render_queue: Queue, prompt: str):
    painter.invoke(prompt)
    render_queue.put(None)


def main():
    navigation_menu()

    st.header("Painting images")

    prompt_label = "Prompt"
    negative_prompt_label = "Negative prompt"
    file_upload_label = "Image"
    product_size_label = "Object size"
    num_image_label = "Num images"
    seed_label = "Seed"
    scale_label = "Scale"
    images_dir_label = "Image dir"
    guidance_scale_label = "Guidance scale"
    num_inference_steps_label = "Num inference steps"

    product_size_items = ["Original"]
    for val in (0.6, 0.5, 0.4, 0.3, 0.2):
        product_size_items.append("{} * width".format(val))

    with st.sidebar.form("form"):
        prompt = st.text_area(prompt_label, "Test prompt", height=200)
        negative_prompt = st.text_area(negative_prompt_label, "Test negative prompt", height=200)
        file_image = st.file_uploader(file_upload_label, type=['png', 'jpg'])
        with st.expander("Image generation settings"):
            num_image = st.number_input(num_image_label, 1, 4, 1, 1)
            product_size = st.selectbox(product_size_label, product_size_items, index=2)
            seed = st.number_input(seed_label, 0, 1000000, 0, 1)
            scale = st.number_input(scale_label, 1, 4, 3, 1)
            guidance_scale = st.number_input(guidance_scale_label, 1.0, 20.0, 7.5, 0.1)
            num_inference_steps = st.number_input(num_inference_steps_label, 1, 100, 20, 1)
            images_dir = st.text_input(images_dir_label, "painting_images")

        col1, col2 = st.columns((0.4, 0.6))
        with col1:
            submited = st.form_submit_button("Submit")
        with col2:
            clear_submited = st.form_submit_button("Clear results")

    if clear_submited:
        return

    if submited:

        # check fields:
        is_valid_fields = True
        for text, label in (
            (prompt, prompt_label),
            (file_image, file_upload_label),
            (images_dir, images_dir_label),
        ):
            if not text:
                st.text("{} field required".format(label))
                is_valid_fields = False

        if not is_valid_fields:
            return

        # images dir
        if not os.path.exists(images_dir):
            os.makedirs(images_dir, exist_ok=True)
        images_dir = os.path.abspath(images_dir)
        render_queue = Queue()
        painter_kwargs = {
            "product_size": product_size,
            "negative_prompt": negative_prompt,
            "image_num": num_image,
            "scale": scale,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps
        }
        if seed > 0:
            painter_kwargs["manual_seed"] = seed

        painter = ReplicateImagePaintingTool(images_directory=images_dir, original_image=file_image, **painter_kwargs)
        painter.set_viewer(StreamLitItemQueueViewer(render_queue))

        t = Thread(target=run_paint, args=(painter, render_queue, prompt))
        t.start()

        streamlit_queue_render(render_queue)

main()
