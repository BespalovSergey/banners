from typing import Callable, Any


class ViewDecoratorToolMixin():

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "tool") or not hasattr(self, 'viewer'):
            return

        object.__setattr__(
            self.tool, "_run", self.view_decorator(self.tool._run)
        )

    def view_decorator(self, f: Callable):

        def wrapper(*args, config=None, **kwargs):
            self.before_run(*args, **kwargs)
            results = f(*args, config=config, **kwargs)
            self.view_results(results, *args, **kwargs)
            return results

        return wrapper

    def before_run(self, *args, **kwargs):
        pass

    def view_results(self, results: Any, *args, **kwargs):
        pass

    def set_viewer(self, viewer: "BaseViewer"):
        self.viewer = viewer
