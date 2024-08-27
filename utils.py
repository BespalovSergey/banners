from queue import Queue
from typing import List, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageFile

STREAMLIT_HISTORY_KEY = "view_history_steps"


def show_image(image_path: str, q: Queue):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (512, 512))
    window_name = "banner image"
    cv2.imshow(window_name, img)
    while True:
        try:
            q.get(block=False)
        except Exception:
            cv2.waitKey(1000)
        else:
            break
    cv2.destroyAllWindows()


def find_singular_points(image: np.array, point_threshold: float = 0.1) -> np.array:
    """Returns numpy array dtype: bool with singular points"""
    _img = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _img = np.float32(_img)
    dest = cv2.cornerHarris(_img, 2, 5, 0.07)
    dest = cv2.dilate(dest, None)
    points = dest > point_threshold * dest.max()
    return points


def get_points_density(
    image: np.array, num_locations: int = 3, point_threshold: float = 0.1
) -> Tuple[List[int], List[Tuple[int, int]]]:
    """Returns the number of singular points in each area of the image, dividing the image with horizontal lines"""

    points = find_singular_points(image, point_threshold)

    h, w = image.shape[:2]
    borders = [int(v) for v in np.linspace(0, h, num_locations + 1)]

    points_density = []
    coords_area = []

    for i in range(1, len(borders)):
        points_slice = (borders[i - 1], borders[i])
        num_points = np.sum(points[points_slice[0]: points_slice[1], ...])
        points_density.append(num_points)
        coords_area.append(points_slice)

    return points_density, coords_area


def combining_mask_boxes(mask: np.array, kernel: tuple = (20, 20), iterations: int = 1):
    _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel)
    dilated_mask = cv2.dilate(binary_mask, kernel, iterations=iterations)

    return dilated_mask


def read_image(image_path: str, as_array: bool = True, to_bgr: bool = True) -> Union[np.ndarray | ImageFile.ImageFile]:
    img = Image.open(image_path)

    if as_array:
        img = np.array(img)
        if to_bgr:
            num_channels = img.shape[2]
            if num_channels == 3:
                img = img[:, :, (2, 1, 0)]
            elif num_channels == 4:
                img = img[:, :, (2, 1, 0, 3)]

        img = img.copy()

    return img


def bbox_w_h_to_x_max_y_max(box: tuple):
    x_min = box[0]
    y_min = box[1]
    x_max = box[2] - box[0]
    y_max = box[3] - box[1]
    return x_min, y_min, x_max, y_max
