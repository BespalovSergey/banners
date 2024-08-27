from typing import List, Tuple


from motleycrew.tools import MotleyTool
from generator import BannerGeneratorWithText
from checkers import BaseChecker
from viewers import StreamLitItemViewer


class UiBannerGeneratorWithText(BannerGeneratorWithText):

    ui_state_name = "ui_banner_generator_with_text"

    def __init__(
        self,
        image_description: str,
        text_description: str,
        images_dir: str,
        slogan: str,
        html_render_checkers: List[BaseChecker] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        max_review_iterations: int = 5,
        image_generate_tool: MotleyTool = None
    ):
        super().__init__(
            image_description=image_description,
            text_description=text_description,
            images_dir=images_dir,
            slogan=slogan,
            html_render_checkers=html_render_checkers,
            image_size=image_size,
            max_review_iterations=max_review_iterations,
            image_generate_tool=image_generate_tool
        )

        for tool in self.tools:
            if hasattr(tool, "set_viewer") and tool.viewer is None:
                tool.set_viewer(StreamLitItemViewer())

