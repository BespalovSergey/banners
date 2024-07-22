from motleycrew.common.exceptions import InvalidOutput
from motleycrew.agents import MotleyOutputHandler
from motleycrew.tools.html_render_tool import HTMLRenderer

from checkers import HumanChecker, GptImageChecker


class HtmlRenderOutputHandler(MotleyOutputHandler):

    def __init__(
        self, human_check: bool = True, gpt_check: bool = False, slogan: str = None, *args, **kwargs
    ):
        super().__init__()
        self.renderer = HTMLRenderer(*args, **kwargs)
        self.human_check = human_check
        self.gpt_check = gpt_check
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

        if self.gpt_check:
            output_checker = GptImageChecker(text=self.slogan)
            output_checker.check(output)

        if self.human_check:
            output_checker = HumanChecker()
            output_checker.check(output)

        return {"checked_output": output}
