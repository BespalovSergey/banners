import os
import io
from typing import List, Any

import replicate

from langchain.agents import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools.image.download_image import download_image
from motleycrew.tools.tool import MotleyTool

from tools.outpainting_tools.base_painting import BaseImagePainter
from tools.outpainting_tools.painting_utils import ModelBgRemover
from tools.mixins import ViewDecoratorImageGenerationMixin
from viewers import BaseViewer, StreamLitViewer, StreamLitItemView
from utils import get_current_time_file_name


class ReplicateImagePainter(BaseImagePainter):

    def __init__(
        self,
        obj_image_path: str | io.BytesIO,
        images_directory: str,
        model_name: str = "logerzhu/ad-inpaint:b1c17d148455c1fda435ababe9ab1e03bc0d917cc3cf4251916f22c45c83c7df",
        **kwargs,
    ):
        self.model_name = model_name

        super(ReplicateImagePainter, self).__init__(obj_image_path, images_directory)
        self.bg_remover = ModelBgRemover()
        self.kwargs = kwargs

        # create image directory
        os.makedirs(images_directory, exist_ok=True)
        self.no_bg_dir = os.path.join(images_directory, "no_bg_images")
        os.makedirs(self.no_bg_dir, exist_ok=True)
        self.result_images_dir = os.path.join(self.images_directory, "result_images")
        os.makedirs(self.result_images_dir, exist_ok=True)

        # init files names core
        if isinstance(obj_image_path, str):
            file_name = os.path.split(obj_image_path)[-1]
            self.file_name_core = ".".join(file_name.split(".")[:-1])
        else:
            self.file_name_core = ".".join(obj_image_path.name.split(".")[:-1])

        self.__no_bg_image = None
        self.__no_bg_image_path = None

    @property
    def no_bg_image(self):
        if self.__no_bg_image is None:
            self.__make_no_bg_image()
        return self.__no_bg_image

    @property
    def no_bg_image_path(self):
        if (
            self.__no_bg_image_path is None
            or self.__no_bg_image is None
            or not os.path.exists(self.__no_bg_image_path)
        ):
            self.__make_no_bg_image()
        return self.__no_bg_image_path

    def __make_no_bg_image(self):
        self.__no_bg_image = self.bg_remover.remove_bg(self.obj_image)
        self.__no_bg_image_path = os.path.join(self.no_bg_dir, "{}.png".format(self.file_name_core))
        self.__no_bg_image.save(self.__no_bg_image_path)

    def paint(self, description: str) -> List[str]:

        image = open(self.no_bg_image_path, "rb")
        run_input = {
            "prompt": description,
            "image_path": image,
            "image_num": 1,
            "pixel": "512 * 512",
            "product_size": "0.5 * width",
        }
        run_input.update(self.kwargs)

        image_file_paths = []
        img_urls = replicate.run(self.model_name, input=run_input)

        for i, url in enumerate(img_urls):
            if i == 0:
                continue
            image_file_path_not_ext = self.create_image_file_path(
                self.result_images_dir, file_ext=""
            )[:-1]
            image_file_path = download_image(url, image_file_path_not_ext)
            if image_file_path:
                image_file_paths.append(image_file_path)
        return image_file_paths

    def create_image_file_path(
        self, target_dir: str, file_ext: str = "png", dt_format: str = "%d.%m.%Y_%H.%M.%S.%f"
    ):

        file_name = get_current_time_file_name(
            file_ext, postfix_name=self.file_name_core, dt_format=dt_format
        )
        return os.path.join(target_dir, file_name)


class ImagePaintingToolInput(BaseModel):
    """Input for the Dall-E tool."""

    description: str = Field(description="image description")


class ReplicateImagePaintingTool(MotleyTool, ViewDecoratorImageGenerationMixin):
    def __init__(
        self,
        original_image: str,
        images_directory: str,
        model_name: str = None,
        viewer: BaseViewer = None,
        is_text_editor: bool = True,
        **kwargs,
    ):
        """
        A tool for painting  background images from original image and text descriptions resulting image
        using the Replicate API.
        :param model_name:  full model name supported by replicate
        :param original_image: the path to original image or BytesIo
        :param images_directory: the directory to save the images to
        :param kwargs: model-specific parameters
        """
        self.model_name = model_name
        self.viewer = viewer

        if model_name is not None:
            self.image_painter = ReplicateImagePainter(
                model_name=model_name,
                obj_image_path=original_image,
                images_directory=images_directory,
                **kwargs,
            )
        else:
            self.image_painter = ReplicateImagePainter(
                obj_image_path=original_image, images_directory=images_directory, **kwargs
            )
        langchain_tool = create_replicate_image_painter_langchain_tool(self.image_painter)

        super().__init__(langchain_tool)
        ViewDecoratorImageGenerationMixin.__init__(self, is_text_editor)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if isinstance(self.viewer, StreamLitViewer):
            view_data = {
                "subheader": ("Object image",),
                "image": (self.image_painter.no_bg_image_path,),
            }
            self.viewer.view(StreamLitItemView(view_data), to_history=True)

            view_data = {"subheader": ("Generated image with description",), "markdown": (args[0],)}
            self.viewer.view(StreamLitItemView(view_data), to_history=True)


def create_replicate_image_painter_langchain_tool(image_painter: ReplicateImagePainter):

    return Tool(
        name=f"{image_painter.model_name}_image_painter",
        func=image_painter.paint,
        description=f"A wrapper around the {image_painter.model_name} image painting model. It is used when it is necessary to finish drawing an image based on the original one. "
        "Input should be an resulting image description.",
        args_schema=ImagePaintingToolInput,
    )
