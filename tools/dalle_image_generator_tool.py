from typing import Dict, Any

from motleycrew.tools import DallEImageGeneratorTool
from viewers import BaseViewer
from .mixins import ViewDecoratorToolMixin


class DalleImageGeneratorTool(DallEImageGeneratorTool, ViewDecoratorToolMixin):

    def __init__(self, *args, viewer: BaseViewer = None, **kwargs):
        self.viewer = viewer
        super(DalleImageGeneratorTool, self).__init__(*args, **kwargs)
        ViewDecoratorToolMixin.__init__(self)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return
        subheader = "Generated image with description"
        self.viewer.view_caption(subheader, args[0])

    def view_results(self, results: Any, *args, **kwargs):
        if self.viewer is None:
            return
        for img_path in results:
            if img_path.startswith("http"):
                continue
            self.viewer.view(img_path, args[0])
