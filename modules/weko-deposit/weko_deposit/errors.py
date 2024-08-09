"""Custom errors for weko deposit."""

class WekoDepositError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko deposit error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_deposit."
        super().__init__(msg)


class WekoDepositIndexerError(WekoDepositError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some indexer error has occurred in weko_deposit."
        super().__init__(ex, msg)


class WekoDepositRegistrationError(WekoDepositError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some registration error has occurred in weko_deposit."
        super().__init__(ex, msg)


class WekoDepositStorageError(WekoDepositError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some storage error has occurred in weko_deposit."
        super().__init__(ex, msg)

