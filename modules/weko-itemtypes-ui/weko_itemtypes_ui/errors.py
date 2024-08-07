"""Custom exceptions for weko_itemtypes_ui."""

class WekoItemTypesUiError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_itemtypes_ui."
        super().__init__(msg)


