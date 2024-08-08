"""Custom exceptions for weko_theme."""

class WekoThemeError(Exception):
    def __init__(self, ex=None, msg=None):
        """

        weko theme error initialization.

        :Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_theme."
        super().__init__(msg)


