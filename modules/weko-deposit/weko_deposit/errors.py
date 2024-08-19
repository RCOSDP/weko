"""Custom errors for weko deposit."""

class WekoDepositError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko deposit error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_deposit."
        super().__init__(msg, *args)


class WekoDepositIndexerError(WekoDepositError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some indexer error has occurred in weko_deposit."
        super().__init__(ex, msg, *args)


class WekoDepositRegistrationError(WekoDepositError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some registration error has occurred in weko_deposit."
        super().__init__(ex, msg, *args)


class WekoDepositStorageError(WekoDepositError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some storage error has occurred in weko_deposit."
        super().__init__(ex, msg, *args)

