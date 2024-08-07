"""Custom exceptions for weko_schema_ui."""

class WekoSchemaError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_schema_ui."
        super().__init__(msg)


class WekoSchemaConversionError(WekoSchemaError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


