from typing import Tuple

from motleycrew.tools import MotleyTool
from motleycache import enable_cache, disable_cache
from motleycache.caching import check_is_caching

from tools.dalle_image_generator_tool import DalleImageGeneratorTool
from tools.replicate_image_generation_tool import ReplicateImageGenerationTool


DALLE_GENERATOR = "Dalle"
REPLICATE_GENERATOR = "Replicate"

IMAGE_GENERATORS = (DALLE_GENERATOR, REPLICATE_GENERATOR)
MOTLEY_CACHE_ENABLED = False


def enable_motleycache():
    global MOTLEY_CACHE_ENABLED
    MOTLEY_CACHE_ENABLED = True
    enable_cache()


def disable_motleycache():
    global MOTLEY_CACHE_ENABLED
    MOTLEY_CACHE_ENABLED = False
    disable_cache()


def init_image_generator(
    generator_name: str, images_dir: str, image_size: Tuple[int, int] = (1024, 1024), **kwargs
) -> MotleyTool:
    if generator_name not in IMAGE_GENERATORS:
        raise ValueError("Image generator {} not found".format(generator_name))

    str_image_size = "{}x{}".format(image_size[0], image_size[1])
    if generator_name == DALLE_GENERATOR:

        if MOTLEY_CACHE_ENABLED and not check_is_caching():
            enable_cache()

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
