"""Custom errors for weko handle."""

class WekoHandleError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko handle error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_handle."
        super().__init__(msg, *args)


class WekoHandleRegistrationError(WekoHandleError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some registration error has occurred in weko_handle."
        super().__init__(ex, msg, *args)


class WekoHandleRetrievalError(WekoHandleError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some retrival error has occurred in weko_handle."
        super().__init__(ex, msg, *args)

