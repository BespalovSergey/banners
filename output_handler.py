from typing import Tuple, List
from datetime import datetime

from motleycrew.common.exceptions import InvalidOutput
from motleycrew.agents import MotleyOutputHandler
from motleycrew.tools.html_render_tool import HTMLRenderer

from checkers import BaseChecker

from selenium import webdriver
from motleycrew.common import logger


class BannerHtmlRenderer(HTMLRenderer):

    def render_image(self, html: str, file_name: str | None = None):
        """Create image with png extension from html code

        Args:
            html (str): html code for rendering image
            file_name (str): file name with not extension
        Returns:
            file path to created image
        """

        html = self.prepare_html(html)
        logger.info("Trying to render image from HTML code")
        html_path, image_path = self.build_save_file_paths(file_name)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Saved the HTML code to {}".format(html_path))

        browser = webdriver.Chrome(options=self.options, service=self.service)
        try:
            if self.window_size:
                logger.info("Setting window size to {}".format(self.window_size))
                browser.set_window_size(*self.window_size)

            url = "file://{}".format(html_path)
            browser.get(url)

            logger.info("Taking screenshot")
            is_created_img = browser.get_screenshot_as_file(image_path)
        finally:
            browser.close()
            browser.quit()

        if not is_created_img:
            logger.error("Failed to render image from HTML code {}".format(image_path))
            return "Failed to render image from HTML code"

        logger.info("Saved the rendered HTML screenshot to {}".format(image_path))

        return image_path
    
    def prepare_html(self, html: str) -> str:
        """Clears the html code from unnecessary characters at the beginning and end of the code

                Args:
                    html (str): html code

                Returns:
                    html (str): html code
                """
        if not html:
            return html

        # clear start and end html
        open_tag_idx = html.find("<")
        if open_tag_idx > 0:
            html = html[open_tag_idx:]

        close_tag_idx = html.rfind(">")
        if open_tag_idx > -1:
            html = html[:close_tag_idx + 1]

        for o, n in ((r"\'", r"'"), (r'\"', r'"')):
            html = html.replace(o, n)

        return html

    def build_save_file_paths(self, file_name: str | None = None) -> Tuple[str, str]:
        """Builds paths to html and image files

        Args:
            file_name (str): file name with not extension

        Returns:
            tuple[str, str]: html file path and image file path
        """

        # check exists dirs:
        for _dir in (self.work_dir, self.html_dir, self.images_dir):
            if not _dir.exists():
                _dir.mkdir(parents=True)

        file_name = file_name or datetime.now().strftime("%Y_%m_%d__%H_%M")
        html_path = self.html_dir / "{}.html".format(file_name)
        image_path = self.images_dir / "{}.png".format(file_name)

        return str(html_path), str(image_path)


class HtmlRenderOutputHandler(MotleyOutputHandler):

    def __init__(
        self,
        checkers: List[BaseChecker] = None,
        slogan: str = None,
        max_iterations: int = 5,
        *args,
        **kwargs
    ):
        super().__init__(max_iterations=max_iterations)
        self.renderer = BannerHtmlRenderer(*args, **kwargs)
        self.checkers = checkers or []
        self.slogan = slogan

    def handle_output(self, output: str):
        # check html tags
        checked_tags = ("html", "head")
        is_html = False
        for tag in checked_tags:
            open_tag = "<{}>".format(tag)
            close_tag = "</{}>".format(tag)
            if open_tag in output or close_tag in output:
                is_html = True
                break
        if not is_html:
            raise InvalidOutput("Html tags not found")

        output = self.renderer.render_image(output)
        for checker in self.checkers:
            checker.check(output)

        return {"checked_output": output}
