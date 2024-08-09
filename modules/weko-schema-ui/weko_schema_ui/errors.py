"""Custom errors for weko schema ui."""

class WekoSchemaError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko schema ui error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_schema_ui"
        super().__init__(msg)


class WekoSchemaSettingError(WekoSchemaError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some setting error has occurred in weko_schema_ui"
        super().__init__(ex, msg)


class WekoSchemaConversionError(WekoSchemaError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some schema conversion error has occurred in weko_schema_ui"
        super().__init__(ex, msg)


class WekoOAISchemaError(WekoSchemaError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some OAI schema error has occurred in weko_schema_ui"
        super().__init__(ex, msg)


class WekoSchemaTreeError(WekoSchemaError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some schema tree error has occurred in weko_schema_ui"
        super().__init__(ex, msg)

