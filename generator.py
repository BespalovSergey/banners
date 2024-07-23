from typing import Tuple

from motleycrew.tasks import SimpleTask
from motleycrew.agents.langchain import ReActToolCallingMotleyAgent
from motleycrew.tools.image.dall_e import DallEImageGeneratorTool
from tools.image_info_tool import BannerImageParserTool
from tools.image_description_tool import HtmlSloganRecommendTool
from tools.remove_text_tool import RemoveTextTool
from motleycrew import MotleyCrew
from output_handler import HtmlRenderOutputHandler


class BaseBannerGenerator:

    def __init__(
        self,
        image_description: str,
        images_dir: str,
        slogan: str | None = None,
        image_size: Tuple[int, int] = (1024, 1024),
    ):
        self.crew = MotleyCrew()
        self.image_description = image_description
        self.images_dir = images_dir
        self.slogan = slogan
        self.image_size = image_size

        dalle_image_size = "{}x{}".format(image_size[0], image_size[1])
        image_generate_tool = DallEImageGeneratorTool(
            dall_e_prompt_template="""{text}""",
            images_directory=images_dir, size=dalle_image_size
        )
        # image generate
        self.advertising_agent = ReActToolCallingMotleyAgent (
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
        image_size: Tuple[int, int] = (1024, 1024),
    ):
        super().__init__(image_description, images_dir, slogan, image_size)

        if self.slogan:
            html_recommend_tool = HtmlSloganRecommendTool(slogan=self.slogan)
            remove_text_tool = RemoveTextTool()
            html_render_output_handler = HtmlRenderOutputHandler(
                gpt_check=True, work_dir=images_dir, window_size=self.image_size, slogan=self.slogan
            )
            # html render
            self.html_developer = ReActToolCallingMotleyAgent (
                name="Html coder",
                description="Html developer",
                prompt_prefix=f"""You are an html coder engaged in the layout of beautiful web pages."
                              f"You create all the pages in utf-8 encoding and
                              carefully write down the absolute paths to the images use only a slash as a separator.""",
                # f"You write the paths to the files correctly for {platform.system()} operating system",
                verbose=True,
                tools=[html_recommend_tool],
                output_handler=html_render_output_handler,
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
        image_size: Tuple[int, int] = (1024, 1024),
        font: str = "Arial",
        text_shadow: int | None = None,
        text_background: bool = False,
    ):

        super().__init__(image_description, images_dir, slogan, image_size)
        self.font = font
        self.text_shadow = text_shadow
        self.text_background = text_background

        if self.slogan:
            html_render_output_handler = HtmlRenderOutputHandler(
                work_dir=images_dir, window_size=self.image_size
            )
            image_info_tool = BannerImageParserTool()
            # html render
            self.html_developer = ReActToolCallingMotleyAgent (
                name="Html coder",
                description="Html developer",
                prompt_prefix=f"""You are an html coder engaged in the layout of beautiful web pages."
                              f"You create all the pages in utf-8 encoding and 
                              carefully write down the absolute paths to the images use only a slash as a separator.""",
                # f"You write the paths to the files correctly for {platform.system()} operating system",
                verbose=True,
                tools=[image_info_tool],
                output_handler=html_render_output_handler,
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
        image_size: Tuple[int, int] = (1024, 1024),

    ):
        image_description = '''{}. 
        Include text "{}" in the image , with next description "{}"'''.format(image_description,
                                                                  slogan,
                                                                  text_description)
        super().__init__(image_description, images_dir, slogan, image_size)

        html_recommend_tool = HtmlSloganRecommendTool(slogan=self.slogan)
        remove_text_tool = RemoveTextTool()
        html_render_output_handler = HtmlRenderOutputHandler(
            gpt_check=True, work_dir=images_dir, window_size=self.image_size, slogan=self.slogan
        )
        # html render
        self.html_developer = ReActToolCallingMotleyAgent (
            name="Html coder",
            description="Html developer",
            prompt_prefix=f"""You are an html coder engaged in the layout of beautiful web pages."
                                      f"You create all the pages in utf-8 encoding and
                                      carefully write down the absolute paths to the images use only a slash as a separator.""",
            # f"You write the paths to the files correctly for {platform.system()} operating system",
            verbose=True,
            tools=[remove_text_tool, html_recommend_tool],
            output_handler=html_render_output_handler,
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