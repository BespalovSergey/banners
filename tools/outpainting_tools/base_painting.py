from abc import ABC, abstractmethod

from PIL import ImageFile
from utils import read_image


class BaseImagePainter(ABC):
    def __init__(self, obj_image_path: str, images_directory: str):
        self.obj_image_path = obj_image_path
        self.images_directory = images_directory
        self.__obj_image = None
        
    @property
    def obj_image(self) -> ImageFile.Image:
        if self.__obj_image is None:
            self.__obj_image = read_image(self.obj_image_path, as_array=False, to_bgr=False)
        return self.__obj_image

    @abstractmethod
    def paint(self, prompt: str):
        pass


class BaseBgRemover(ABC):

    @abstractmethod
    def remove_bg(self, image_path: str):
        pass
