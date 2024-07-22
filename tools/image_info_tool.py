import os
from typing import Tuple

import cv2
import numpy as np
from sklearn.cluster import KMeans

from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

from motleycrew.tools import MotleyTool


class BannerImageParser:

    def __init__(self, num_clusters: int = 5, point_threshold=0.1):
        self.num_clusters = num_clusters
        self.point_threshold = point_threshold

    def parse_image(self, image_path: str):
        image_path = image_path.strip()
        if not os.path.exists(image_path):
            raise FileNotFoundError(image_path)

        image_info = []

        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        #image_size
        h, w = img.shape[:2]
        str_image_size = "WIDTH: {} px\nHEIGHT: {} px".format(w, h)
        image_info.append(str_image_size)

        # slogan location
        img_slice, location = self.get_slogan_location(img)
        str_slogan_location = "SLOGAN LOCATION: {}".format(location)
        image_info.append(str_slogan_location)
        str_slogan_mask = "Edited area y1: {}\nEdited area y2: {}".format(img_slice[0], img_slice[1])
        image_info.append(str_slogan_mask)

        # find main color
        color = self.get_color(img[img_slice[0]: img_slice[1], ...])
        str_color = "COLOR rgb: {}".format(", ".join([str(c) for c in color]))
        image_info.append(str_color)
        return "\n".join(image_info)

    def get_color(self, image: np.array) -> Tuple[int, int, int]:

        reshape = image.reshape((image.shape[0] * image.shape[1], 3))
        cluster = KMeans(n_clusters=self.num_clusters).fit(reshape)
        labels = np.arange(0, len(np.unique(cluster.labels_)) + 1)
        (hist, _) = np.histogram(cluster.labels_, bins=labels)
        color_max_args = np.argmax(hist)
        color = cluster.cluster_centers_[color_max_args]
        color = [int(c) for c in color]
        return color

    def get_slogan_location(self, img: np.array) -> Tuple[Tuple[int, int], str]:
        h, w = img.shape[:2]
        _img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _img = np.float32(_img)
        dest = cv2.cornerHarris(_img, 2, 5, 0.07)
        dest = cv2.dilate(dest, None)
        points = dest > self.point_threshold * dest.max()

        locations = ["top", "center", "bottom"]
        borders = [int(v)for v in np.linspace(0, h, 4)]
        points_locations = []
        for i, location in zip(range(1, len(borders)+1), locations):
            points_slice = (borders[i-1], borders[i])
            num_points = np.sum(points[points_slice[0]: points_slice[1], ...])
            points_locations.append((num_points, points_slice, location))

        points_locations = sorted(points_locations, key=lambda x: x[0])
        return_data = points_locations[0][1:]
        return return_data


class BannerImageParserTool(MotleyTool):

    def __init__(self):
        """Tool for banner parse image
        """
        renderer = BannerImageParser(num_clusters=2)
        langchain_tool = create_render_tool(renderer)
        super().__init__(langchain_tool)


class BannerImageParserToolInput(BaseModel):
    """Input for the HTMLRenderTool.

    Attributes:
        html (str):
    """

    image_path: str = Field(description="Path to the image")


def create_render_tool(parser: BannerImageParser):
    """Create langchain tool from HTMLRenderer.render_image method

    Returns:
        Tool:
    """
    return Tool.from_function(
        func=parser.parse_image,
        name="image_info_tool",
        description="A tool that returns the size of the image, the location of the text (SLOGAN LOCATION) "
                    "and the main color",
        args_schema=BannerImageParserToolInput,
    )
