from typing import Dict, Any

from motleycrew.tools import DallEImageGeneratorTool
from viewers import BaseViewer
from .mixins import ViewDecoratorToolMixin


class DalleImageGeneratorTool(DallEImageGeneratorTool, ViewDecoratorToolMixin):

    def __init__(self, *args, viewer: BaseViewer = None, **kwargs):
        self.viewer = viewer
        super(DalleImageGeneratorTool, self).__init__(*args, **kwargs)
        ViewDecoratorToolMixin.__init__(self)

    def view_results(self, results: Any):
        if self.viewer is None:
            return
        for img_path in results:
            if img_path.startswith("http"):
                continue
            self.viewer.view(img_path)
