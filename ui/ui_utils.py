from typing import Tuple, Union

import streamlit as st

from motleycrew.tools import MotleyTool
from motleycache import enable_cache, disable_cache
from motleycache.caching import check_is_caching

from tools.dalle_image_generator_tool import DalleImageGeneratorTool
from tools.replicate_image_generation_tool import ReplicateImageGenerationTool


DALLE_GENERATOR = "Dalle"
REPLICATE_GENERATOR = "Replicate"

IMAGE_GENERATORS = (REPLICATE_GENERATOR, DALLE_GENERATOR)


def init_image_generator(
    generator_name: str,
    images_dir: str,
    image_size: Tuple[int, int] = (1024, 1024),
    is_enable_cache: bool = False,
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
            dall_e_prompt_template="""{text}""", images_directory=images_dir, size=str_image_size
        )
    else:
        if check_is_caching():
            disable_cache()

        generator = ReplicateImageGenerationTool(
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
