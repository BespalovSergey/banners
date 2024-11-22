from typing import Any

from motleycrew.tools import DallEImageGeneratorTool
from viewers import BaseViewer
from .mixins import ViewDecoratorImageGenerationMixin
from viewers import StreamLitViewer, StreamLiteItemView


class DalleImageGeneratorTool(DallEImageGeneratorTool, ViewDecoratorImageGenerationMixin):

    def __init__(self, *args, viewer: BaseViewer = None, is_text_editor: bool = False, **kwargs):
        self.viewer = viewer
        super(DalleImageGeneratorTool, self).__init__(*args, **kwargs)
        ViewDecoratorImageGenerationMixin.__init__(self, is_text_editor)

    def before_run(self, *args, **kwargs):
        if self.viewer is None:
            return

        if isinstance(self.viewer, StreamLitViewer):
            view_data = {"subheader": ("Generated image with description",), "markdown": (args[0],)}
            self.viewer.view(StreamLiteItemView(view_data), to_history=True)
