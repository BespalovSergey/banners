from typing import Tuple, Union

import streamlit as st

from motleycrew.tools import MotleyTool
from motleycache import enable_cache, disable_cache
from motleycache.caching import check_is_caching

from tools.dalle_image_generator_tool import DalleImageGeneratorTool
from tools.replicate_image_generation_tool import ReplicateImageGenerationTool
from tools.generate_post_tools.text_generation_tool import PostTextGeneratorTool
from ui.generator_with_ui import UiBannerGeneratorWithText, UiBannerGenerator


DALLE_GENERATOR = "Dalle"
REPLICATE_GENERATOR = "Replicate"

IMAGE_GENERATORS = (REPLICATE_GENERATOR, DALLE_GENERATOR)


def init_image_generator(
    generator_name: str,
    images_dir: str,
    image_size: Tuple[int, int] = (1024, 1024),
    is_enable_cache: bool = False,
    is_text_editor: bool = False,
    **kwargs
) -> MotleyTool:
    if generator_name not in IMAGE_GENERATORS:
        raise ValueError("Image generator {} not found".format(generator_name))

    str_image_size = "{}x{}".format(image_size[0], image_size[1])
    if generator_name == DALLE_GENERATOR:

        is_enabled_motleycache = check_is_caching()

        if is_enable_cache and not is_enabled_motleycache:
            enable_cache()
        elif not is_enable_cache and is_enabled_motleycache:
            disable_cache()

        generator = DalleImageGeneratorTool(
            is_text_editor=is_text_editor,
            dall_e_prompt_template="""{text}""", images_directory=images_dir, size=str_image_size
        )
    else:
        if check_is_caching():
            disable_cache()

        generator = ReplicateImageGenerationTool(
            is_text_editor=is_text_editor,
            model_name=kwargs.get("replicate_model_name", "flux-pro"),
            images_directory=images_dir,
            size=str_image_size,
            width=image_size[0],
            height=image_size[1],
        )
    return generator


def find_remarks(*args) -> Tuple[Union[str | None], Union[str | None]]:
    """
    Find user remarks:
    args: str , key widgets with  remarks
    """
    for widget_key in args:
        remark = st.session_state.get(widget_key, None)
        if remark is not None:
            return remark, widget_key
    return None, None


def navigation_menu():
    """
    Add navigation
    """
    st.sidebar.page_link("ui_main.py", label="Banner generation")
    st.sidebar.page_link("pages/generation_with_text.py", label="Banner generation with text")
    st.sidebar.page_link("pages/painting_image.py", label="Painting image")
    st.sidebar.page_link("pages/generate_post.py", label="Post text generation")


def stop_other_generators(running_generator_key: str):
    """Stopping other running generators"""
    for generator_key in (UiBannerGeneratorWithText.ui_state_name, UiBannerGenerator.ui_state_name, PostTextGeneratorTool.ui_state_name):
        if generator_key == running_generator_key:
            continue

        generator = st.session_state.get(generator_key, None)
        if generator is None:
            continue
        else:
            generator.stop()
            st.session_state[generator_key] = None
