"""Custom exceptions for weko-deposit."""

class WekoDepositError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko-deposit."
        super().__init__(msg)


class WekoDepositIndexerError(WekoDepositError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


class WekoDepositRegistrarionError(WekoDepositError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


