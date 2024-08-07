"""Custom exceptions for weko_items_autofill."""

class WekoItemsAutoFillError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_items_autofill."
        super().__init__(msg)


class WekoItemsAutoFillURLError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


