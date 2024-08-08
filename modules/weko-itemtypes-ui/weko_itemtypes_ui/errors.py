"""Custom exceptions for weko_itemtypes_ui."""

class WekoItemTypesUiError(Exception):
    def __init__(self, ex=None, msg=None):
        """

        weko item-type ui error initialization.

        :Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_itemtypes_ui."
        super().__init__(msg)


