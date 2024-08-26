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
            self.before_run(*args, **kwargs)
            results = f(*args, **kwargs)
            self.view_results(results, *args, **kwargs)
            return results

        return wrapper

    def before_run(self, *args, **kwargs):
        pass

    def view_results(self, results: Any):
        pass