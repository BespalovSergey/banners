from typing import Any

from motleycrew.tools.image.replicate_tool import ReplicateImageGeneratorTool

from tools.mixins import ViewDecoratorImageGenerationMixin
from viewers import BaseViewer, StreamLitViewer, StreamLitItemView
from utils import convert_image_format


class ReplicateImageGenerationTool(ReplicateImageGeneratorTool, ViewDecoratorImageGenerationMixin):

    def __init__(self, *args, viewer: BaseViewer = None, is_text_editor: bool = True, **kwargs):
        self.viewer = viewer
        super(ReplicateImageGenerationTool, self).__init__(*args, **kwargs)
        ViewDecoratorImageGenerationMixin.__init__(self, is_text_editor)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if isinstance(self.viewer, StreamLitViewer):
            view_data = {"subheader": ("Generated image with description",), "markdown": (args[0],)}
            self.viewer.view(StreamLitItemView(view_data), to_history=True)

    def program_check_tool_results(self, results: Any) -> Any:
        checked_results = []
        for image_path in results:
            checked_image_path = convert_image_format(image_path)
            checked_results.append(checked_image_path)
        return checked_results
