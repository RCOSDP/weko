"""Custom errors for weko records."""

class WekoRecordsError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko records error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some registration error has occurred in weko_records."
        super().__init__(msg)


class WekoRecordsRegistrationError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some error has occurred in weko_records."
        super().__init__(ex, msg)


class WekoRecordsTypeError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some itemtype error has occurred in weko_records."
        super().__init__(ex, msg)


class WekoRecordsMetadataError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some metadata error has occurred in weko_records."
        super().__init__(ex, msg)


class WekoRecordsSiteError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some  site error has occurred in weko_records."
        super().__init__(ex, msg)


class WekoRecordsLinkError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some item link error has occurred in weko_records."
        super().__init__(ex, msg)


class WekoRecordsEditHistoryError(WekoRecordsError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some itemtype edit history error has occurred in weko_records."
        super().__init__(ex, msg)

