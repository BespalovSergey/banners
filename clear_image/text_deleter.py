import logging
from clear_image.inpainter import Inpainter
from clear_image.text_detector import TextDetector


class TextDeleter:
    def __init__(self, text_detector: TextDetector, inpainter: Inpainter):
        self.text_detector = text_detector
        self.inpainter = inpainter

    def delete_text(self, in_image_path: str, out_image_path: str, prompt=Inpainter.DEFAULT_PROMPT, max_retries=5):
        to_inpaint_path = in_image_path
        for i in range(max_retries):
            logging.info(f"Iteration {i} of {max_retries} for image {in_image_path}:")

            logging.info(f"Calling text detector...")
            text_boxes = self.text_detector.detect_text(to_inpaint_path)
            logging.info(f"Detected {len(text_boxes)} text boxes.")

            if not text_boxes:
                if i == 0:
                    return in_image_path
                break

            logging.info(f"Calling in-painting model...")
            self.inpainter.inpaint(to_inpaint_path, text_boxes, prompt, out_image_path)
            import os
            assert os.path.exists(out_image_path)
            to_inpaint_path = out_image_path
        return out_image_path
            
