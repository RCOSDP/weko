"""Custom exceptions for weko_admin."""

class WekoAdminError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_admin."
        super().__init__(msg)


class WekoAdminSettingsError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoAdminMailError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoAdminLogAnalysisError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoAdminReindexError(WekoAdminError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


