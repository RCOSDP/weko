"""Custom errors for weko admin."""

class WekoAdminError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko admin error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_admin."
        super().__init__(msg)


class WekoAdminSettingError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some setting error has occurred in weko_admin."
        super().__init__(ex, msg)


class WekoAdminMailError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some mail error has occurred in weko_admin."
        super().__init__(ex, msg)


class WekoAdminReportError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some report error has occurred in weko_admin."
        super().__init__(ex, msg)


class WekoAdminLogAnalysisError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some log analysis error has occurred in weko_admin."
        super().__init__(ex, msg)


class WekoAdminReindexError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some reindex error has occurred in weko_admin."
        super().__init__(ex, msg)

