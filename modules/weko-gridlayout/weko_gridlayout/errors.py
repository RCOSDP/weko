"""Custom exceptions for weko_gridlayout."""

class WekoGridLayoutError(Exception):
    def __init__(self, ex=None, msg=None):
        """

        weko gridlayout error initialization.

        :Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_gridlayout."
        super().__init__(msg)


class WekoWedgetDesignError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoWedgetDataError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


