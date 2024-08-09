"""Custom errors for weko items autofill."""

class WekoItemsAutoFillError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko items autofill error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_items_autofill."
        super().__init__(msg)


class WekoItemsAutoFillURLError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some url error has occurred in weko_items_autofill."
        super().__init__(ex, msg)


class WekoItemsAutoFillGettingError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some convertion date error has occurred in weko_items_autofill."
        super().__init__(ex, msg)


class WekoItemsAutoFillConvertionError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some getting date error has occurred in weko_items_autofill."
        super().__init__(ex, msg)

