import os
from typing import Tuple, List

from motleycrew.tasks import SimpleTask
from motleycrew.agents.langchain import ReActToolCallingMotleyAgent
from motleycrew.tools import MotleyTool
from tools.dalle_image_generator_tool import DalleImageGeneratorTool
from tools.image_info_tool import BannerImageParserTool
from tools.image_description_tool import HtmlSloganRecommendTool
from tools.remove_text_tool import RemoveTextTool
from viewers import CliImageViewer
from motleycrew import MotleyCrew
from checkers import BaseChecker
from output_handler import HtmlRenderOutputHandler


class BaseBannerGenerator:

    def __init__(
        self,
        image_description: str,
        images_dir: str,
        slogan: str | None = None,
        html_render_checkers: List[BaseChecker] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        max_review_iterations: int = 5,
        image_generate_tool: MotleyTool = None,
    ):
        self.crew = MotleyCrew()
        self.image_description = image_description
        self.images_dir = os.path.abspath(images_dir)
        self.slogan = slogan
        self.image_size = image_size
        self.tools = []

        if self.slogan:
            self.html_render_output_handler = HtmlRenderOutputHandler(
                checkers=html_render_checkers, work_dir=images_dir, window_size=self.image_size, slogan=self.slogan,
                max_iterations=max_review_iterations
            )

        if not image_generate_tool:
            dalle_image_size = "{}x{}".format(image_size[0], image_size[1])
            image_generate_tool = DalleImageGeneratorTool(viewer=CliImageViewer(scaler=2),
                dall_e_prompt_template="""{text}""", images_directory=self.images_dir, size=dalle_image_size
            )

        self.tools.append(image_generate_tool)

        # image generate
        self.advertising_agent = ReActToolCallingMotleyAgent(
            name="Advertising agent",
            description="Advertising development",
            prompt_prefix="You are an advertising agent who creates banners.",
            verbose=True,
            tools=[image_generate_tool],
        )
        self.generate_banner_task = SimpleTask(
            crew=self.crew,
            name="Generate banner",
            description=f"""Generate one image as image which shows a {self.image_description}, 
                                               based on the slogan '{self.slogan}'.
                                               Return image path. """,
            agent=self.advertising_agent,
        )

    def run(self):
        result = self.crew.run()
        return result


class GptBannerGenerator(BaseBannerGenerator):

    def __init__(
        self,
        image_description: str,
        images_dir: str,
        slogan: str | None = None,
        html_render_checkers: List[BaseChecker] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        max_review_iterations: int = 5
    ):
        super().__init__(image_description, images_dir, slogan, html_render_checkers, image_size, max_review_iterations)

        if self.slogan:
            html_recommend_tool = HtmlSloganRecommendTool(slogan=self.slogan)
            self.tools.append(html_recommend_tool)
            image_info_tool = BannerImageParserTool()

            # html render
            self.html_developer = ReActToolCallingMotleyAgent(
                name="Html coder",
                description="Html developer",
                prompt_prefix=f"""You are an html coder engaged in the layout of beautiful web pages."
                              f"You create all the pages in utf-8 encoding and
                              carefully write down the absolute paths to the images use only a slash as a separator.""",
                # f"You write the paths to the files correctly for {platform.system()} operating system",
                verbose=True,
                tools=[html_recommend_tool],
                output_handler=self.html_render_output_handler,
            )

            create_html_image = SimpleTask(
                crew=self.crew,
                name="Create html screenshot",
                description=f"Make up html code ,the background of which will be the resulting image"
                f"and place the text '{self.slogan}' in the foreground",
                agent=self.html_developer,
            )
            self.generate_banner_task >> create_html_image


class BannerGenerator(BaseBannerGenerator):

    def __init__(
        self,
        image_description: str,
        images_dir: str,
        slogan: str | None = None,
        html_render_checkers: List[BaseChecker] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        font: str = "Arial",
        text_shadow: int | None = None,
        text_background: bool = False,
        max_review_iterations: int = 5,
    ):

        super().__init__(image_description, images_dir, slogan, html_render_checkers, image_size, max_review_iterations)
        self.font = font
        self.text_shadow = text_shadow
        self.text_background = text_background

        if self.slogan:
            image_info_tool = BannerImageParserTool()
            self.tools.append(image_info_tool)
            # html render
            self.html_developer = ReActToolCallingMotleyAgent(
                name="Html coder",
                description="Html developer",
                prompt_prefix=f"""You are an html coder engaged in the layout of beautiful web pages."
                              f"You create all the pages in utf-8 encoding and 
                              carefully write down the absolute paths to the images use only a slash as a separator.""",
                # f"You write the paths to the files correctly for {platform.system()} operating system",
                verbose=True,
                tools=[image_info_tool],
                output_handler=self.html_render_output_handler,
            )
            font_description = "make text font ({}),".format(self.font) if self.font else ""
            text_shadow_description = (
                "make text shadow ({} px),".format(self.text_shadow) if self.text_shadow else ""
            )
            str_use_text_background = "create" if self.text_background else "don't create"
            text_background_description = "{} a frame for the text,".format(str_use_text_background)

            create_html_image = SimpleTask(
                crew=self.crew,
                name="Create html screenshot",
                description=f"Make up html code ,the background of which will be the resulting image"
                f"and place the text '{self.slogan}' in the foreground in SLOGAN LOCATION, "
                f"make the text size  large, text padding center, {font_description} "
                f"{text_shadow_description}, {text_background_description} make the text color contrasting "
                f"with main color of the image, don't use scrolling on the page, ",
                agent=self.html_developer,
            )
            self.generate_banner_task >> create_html_image


class BannerGeneratorWithText(BaseBannerGenerator):

    def __init__(
        self,
        image_description: str,
        text_description: str,
        images_dir: str,
        slogan: str,
        html_render_checkers: List[BaseChecker] = None,
        image_size: Tuple[int, int] = (1024, 1024),
        max_review_iterations: int = 5,
        image_generate_tool: MotleyTool = None,
    ):
        image_description = '''{}.
        Include text "{}" in the image , with next description "{}"'''.format(image_description,
                                                                  slogan,
                                                                  text_description)
        super().__init__(image_description, images_dir, slogan, html_render_checkers, image_size, max_review_iterations,
                         image_generate_tool)

        html_recommend_tool = HtmlSloganRecommendTool(slogan=self.slogan)
        self.tools.append(html_recommend_tool)

        remove_text_tool = RemoveTextTool()
        self.tools.append(remove_text_tool)
        # html render
        self.html_developer = ReActToolCallingMotleyAgent(
            name="Html coder",
            description="Html developer",
            prompt_prefix=f"""You are an html coder engaged in the layout of beautiful web pages.
                          You create all the pages in utf-8 encoding and
                          carefully write down the absolute paths to the images use only a slash as a separator.""",
            # f"You write the paths to the files correctly for {platform.system()} operating system",
            verbose=True,
            tools=[remove_text_tool, html_recommend_tool],
            output_handler=self.html_render_output_handler,
        )
        create_html_image = SimpleTask(
            crew=self.crew,
            name="Create html screenshot",
            description=f"Remove text from the resulting image and make up html code ,the background of "
            f"which will be the cleared image and place the text '{self.slogan}' in the foreground."
            f"Place the text in the coordinates of the deleted text",
            agent=self.html_developer,
        )
        self.generate_banner_task >> create_html_image
