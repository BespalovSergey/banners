from typing import Any

from motleycrew.tools.image.replicate_tool import ReplicateImageGeneratorTool

from .mixins import ViewDecoratorImageGenerationMixin
from viewers import BaseViewer, StreamLitViewer, StreamLiteItemView
from utils import convert_image_format


class ReplicateImageGenerationTool(ReplicateImageGeneratorTool, ViewDecoratorImageGenerationMixin):

    def __init__(self, *args, viewer: BaseViewer = None, **kwargs):
        self.viewer = viewer
        super(ReplicateImageGenerationTool, self).__init__(*args, **kwargs)
        ViewDecoratorImageGenerationMixin.__init__(self)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if isinstance(self.viewer, StreamLitViewer):
            view_data = {"subheader": ("Generated image with description",), "markdown": (args[0],)}
            self.viewer.view(StreamLiteItemView(view_data), to_history=True)

    def view_results(self, results: Any, *args, **kwargs):
        if self.viewer is None:
            return
        for img_path in results:
            if img_path.startswith("http"):
                continue

            if isinstance(self.viewer, StreamLitViewer):
                view_data = {"image": (img_path, args[0])}
                self.viewer.view(StreamLiteItemView(view_data), to_history=True)
            else:
                self.viewer.view(img_path)

    def program_check_tool_results(self, results: Any) -> Any:
        checked_results = []
        for image_path in results:
            checked_image_path = convert_image_format(image_path)
            checked_results.append(checked_image_path)
        return checked_results

    def human_check_results(self, results: Any) -> Any:
        return results
