"""Custom exceptions for weko_records."""

class WekoRecordsError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_records."
        super().__init__(msg)


class WekoRecordsTypeError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoRecordsMetadataError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoRecordsSiteError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoRecordsLinkError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


