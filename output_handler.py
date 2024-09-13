from typing import Tuple, List, Optional, Union
from pathlib import Path
from datetime import datetime
import asyncio

from motleycrew.common.exceptions import InvalidOutput
from motleycrew.agents import MotleyOutputHandler
from playwright.async_api import async_playwright


from checkers import BaseChecker
from viewers import (
    BaseViewer,
    StreamLitItemQueueViewer,
    StreamLiteItemView,
    SpinnerStreamLitItemView,
)

from motleycrew.common import logger


class BannerHtmlRenderer():

    def __init__(
        self, work_dir: str, headless: bool = True, window_size: Optional[Tuple[int, int]] = None
    ):

        self.work_dir = Path(work_dir).resolve()
        self.html_dir = self.work_dir / "html"
        self.images_dir = self.work_dir / "images"
        self.headless = headless
        self.window_size = window_size
        if self.window_size:
            self.__view_size = {"width": window_size[0], "height": window_size[0]}
        else:
            self.__view_size = None
        self.__changed_event_loop = False

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

        logger.info("Taking screenshot")

        try:
            loop = self.__find_async_loop()
            url = "file://{}".format(html_path)
            loop.run_until_complete(self.__render_image(url, image_path))
        except Exception as e:
            logger.error("Failed to render image from HTML code {}".format(image_path))
            raise e

        logger.info("Saved the rendered HTML screenshot to {}".format(image_path))

        return image_path

    def __find_async_loop(self):
        if not self.__changed_event_loop:
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            self.__changed_event_loop = True
            return loop

        try:
            loop = asyncio.get_running_loop()
        except Exception:
            loop = asyncio.get_event_loop()

        return loop

    async def __render_image(self, url: str, image_path):

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            if self.__view_size:
                await page.set_viewport_size(self.__view_size)

            await page.goto(url)
            await page.screenshot(path=image_path, full_page=True)
            await browser.close()

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
            html = html[: close_tag_idx + 1]

        for o, n in ((r"\'", r"'"), (r"\"", r'"')):
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
        viewer: BaseViewer = None,
        *args,
        **kwargs
    ):
        super().__init__(max_iterations=max_iterations)
        self.renderer = BannerHtmlRenderer(*args, **kwargs)
        self.checkers = checkers or []
        self.slogan = (slogan,)
        self.viewer = viewer
        self.iteration = 0

    def handle_output(self, output: str):
        # check html tags
        self.iteration += 1
        view_data = {
            "subheader": ("Html output handler iteration: {}".format(self.iteration),),
            "code": (output,),
        }
        self.streamlit_view(StreamLiteItemView(view_data))

        checked_tags = ("html", "head")
        is_html = False
        for tag in checked_tags:
            open_tag = "<{}>".format(tag)
            close_tag = "</{}>".format(tag)
            if open_tag in output or close_tag in output:
                is_html = True
                break
        if not is_html:
            msg = "Html tags not found"
            view_data = {"text": ("Invalid output: {}".format(msg),)}
            self.streamlit_view(StreamLiteItemView(view_data))
            raise InvalidOutput(msg)

        self.streamlit_view(SpinnerStreamLitItemView("Rendering image ..."))

        try:
            output = self.renderer.render_image(output)
        except Exception as e:
            view_data = {"error": ("Render image error: {}".format(str(e)),)}
            self.streamlit_view(StreamLiteItemView(view_data))
            return {"checked_output": "Render image error"}

        for checker in self.checkers:
            checker.check(output)

        return {"checked_output": output}

    def streamlit_view(self, item_view: Union[StreamLiteItemView, SpinnerStreamLitItemView]):
        if isinstance(self.viewer, StreamLitItemQueueViewer):
            self.viewer.view(item_view)
