"""Custom errors for weko gridlayout."""

class WekoGridLayoutError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko gridlayout error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_gridlayout."
        super().__init__(msg)


class WekoWidgetLayoutError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some layout of wedget error has occurred in weko_gridlayout."
        super().__init__(ex, msg)


class WekoWidgetDataError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some date error has occurred in weko_gridlayout."
        super().__init__(ex, msg)


class WekoWidgetSettingError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some setting error has occurred in weko_gridlayout."
        super().__init__(ex, msg)

