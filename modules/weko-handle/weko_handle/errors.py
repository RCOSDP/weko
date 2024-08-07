"""Custom exceptions for weko_handle."""

class WekoHandleError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_handle."
        super().__init__(msg)


class WekoHandleRegisstrationError(WekoHandleError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


