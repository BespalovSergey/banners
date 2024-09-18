import os
import sys
from threading import Thread

from motleycrew.common.logging import logger, configure_logging
from dotenv import load_dotenv

sys.path.append(os.path.abspath("."))

import streamlit as st

from checkers import StreamLitHumanChecker, REMARKS_WIDGET_KEY
from tools.mixins import IMAGE_GENERATION_REMARKS_WIDGET_KEY
from generator_with_ui import UiBannerGenerator
from ui_utils import IMAGE_GENERATORS, init_image_generator, find_remarks, navigation_menu, stop_other_generators
from viewers import StreamLitItemQueueViewer, streamlit_queue_render

from motleycache.http_cache import FORCED_CACHE_BLACKLIST

FORCED_CACHE_BLACKLIST.append("*//api.openai.com/v1/images/edits*")

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


def main():
    navigation_menu()

    generator_key = UiBannerGenerator.ui_state_name
    stop_other_generators(generator_key)

    st.header("Banner generation")
    generator = st.session_state.get(generator_key)

    image_generator_label = "Image generator"
    image_description_label = "Image description"
    slogan_label = "Slogan"
    images_dir_label = "Image dir"

    with st.sidebar.form("form"):
        image_description = st.text_area(image_description_label, "Sun day", height=200)
        slogan = st.text_area(slogan_label, "Good day")
        max_review_iterations = st.number_input("Output handler iterations", 1, 100, 5)
        image_size = (1024, 1024)
        with st.expander("Image generation settings"):
            images_dir = st.text_input(images_dir_label, "banner_images")
            image_generator_name = st.selectbox(image_generator_label, IMAGE_GENERATORS)
            is_enable_cache = st.toggle("Enable motleycache (does not work with Replicate)")

        col1, col2 = st.columns((0.4, 0.6))
        with col1:
            submited = st.form_submit_button("Submit")
        with col2:
            clear_submited = st.form_submit_button("Clear results")

    if clear_submited:
        if generator is not None:
            generator.stop()
            generator = None
            st.session_state[generator_key] = generator
        return

    if submited:
        if generator is not None:
            generator.stop()

        # check fields:
        is_valid_fields = True
        for text, label in (
            (image_description, image_description_label),
            (slogan, slogan_label),
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

        image_generate_tool = init_image_generator(image_generator_name, images_dir, image_size, is_enable_cache)

        generator = UiBannerGenerator(
            image_description=image_description,
            images_dir=images_dir,
            slogan=slogan,
            max_review_iterations=max_review_iterations,
            html_render_checkers=[StreamLitHumanChecker()],
            image_generate_tool=image_generate_tool,
        )
        st.session_state[generator_key] = generator
        t = Thread(target=generator.generate)
        t.start()

    elif generator is not None:
        generator.reset_view()
        viewer = StreamLitItemQueueViewer(generator.render_queue)
        history = generator.get_history()
        for view_item in history:
            viewer.view(view_item, to_history=False)

        remarks, widget_key = find_remarks(REMARKS_WIDGET_KEY, IMAGE_GENERATION_REMARKS_WIDGET_KEY)
        if remarks:
            generator.put_remarks(remarks)
            if widget_key:
                st.session_state[widget_key] = None
        else:
            generator.put_remarks(None)

    if generator:
        streamlit_queue_render(generator.render_queue)


main()
