"""Custom errors for weko itemtypes ui."""

class WekoItemTypesUiError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko itemtypes ui error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_itemtypes_ui."
        super().__init__(msg)


class WekoItemTypesUiManagementError(WekoItemTypesUiError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some management error has occurred in weko_itemtypes_ui."
        super().__init__(ex, msg)


class WekoItemTypesUiPropertyError(WekoItemTypesUiError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some property error has occurred in weko_itemtypes_ui."
        super().__init__(ex, msg)


class WekoItemTypesUiMappingError(WekoItemTypesUiError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some mapping error has occurred in weko_itemtypes_ui."
        super().__init__(ex, msg)

