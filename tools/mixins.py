from typing import Callable, Any


class ViewDecoratorToolMixin():

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "tool") or not hasattr(self, 'viewer'):
            return

        if self.viewer is None:
            return

        object.__setattr__(
            self.tool, "_run", self.view_decorator(self.tool._run)
        )

    def view_decorator(self, f: Callable):

        def wrapper(*args, **kwargs):
            results = f(*args, **kwargs)
            self.view_results(results)
            return results

        return wrapper

    def view_results(self, results: Any):
        pass
