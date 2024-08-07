"""Custom exceptions for weko_theme."""

class WekoThemeError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_theme."
        super().__init__(msg)


