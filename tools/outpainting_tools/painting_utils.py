from typing import Tuple

from PIL import Image, ImageFile
import numpy as np
import torch
import torch.nn.functional as F
from torchvision.transforms.functional import normalize
from transformers import AutoModelForImageSegmentation

from tools.outpainting_tools.base_painting import BaseBgRemover
from utils import read_image


def find_device():
    return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class ModelBgRemover(BaseBgRemover):

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(ModelBgRemover, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(
        self, model_name: str = "briaai/RMBG-1.4", model_input_size: Tuple[int, int] = (1024, 1024)
    ):
        self.model_name = model_name
        self.model_input_size = model_input_size
        self.model = AutoModelForImageSegmentation.from_pretrained(
            self.model_name, trust_remote_code=True
        )
        self.device = find_device()
        self.model.to(self.device)

    def remove_bg(self, input_image: str) -> ImageFile.Image:
        if isinstance(input_image, str):
            orig_image = read_image(input_image, to_bgr=False)
            input_image = read_image(input_image, as_array=False)
        else:
            orig_image = np.array(input_image)

        orig_image_size = orig_image.shape[:2]

        # process mask
        image = self.preprocess_image(orig_image, self.model_input_size).to(self.device)
        result = self.model(image)
        result_image = self.postprocess_image(result[0][0], orig_image_size)

        # create no bg image
        pil_img = Image.fromarray(result_image)
        no_bg_image = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
        no_bg_image.paste(input_image, mask=pil_img)
        return no_bg_image

    def preprocess_image(self, im: np.ndarray, model_input_size: tuple) -> torch.Tensor:
        if len(im.shape) < 3:
            im = im[:, :, np.newaxis]
        im_tensor = torch.tensor(im, dtype=torch.float32).permute(2, 0, 1)
        im_tensor = F.interpolate(
            torch.unsqueeze(im_tensor, 0), size=model_input_size, mode="bilinear"
        )

        image = torch.divide(im_tensor, 255.0)
        image = normalize(image, [0.5, 0.5, 0.5], [1.0, 1.0, 1.0])
        return image

    def postprocess_image(self, result: torch.Tensor, im_size: list) -> np.ndarray:
        result = torch.squeeze(F.interpolate(result, size=im_size, mode="bilinear"), 0)
        ma = torch.max(result)
        mi = torch.min(result)
        result = (result - mi) / (ma - mi)
        im_array = (result * 255).permute(1, 2, 0).cpu().data.numpy().astype(np.uint8)
        im_array = np.squeeze(im_array)
        return im_array
