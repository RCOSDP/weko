"""Custom errors for weko redis."""

class WekoRedisError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko redis error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_redis."
        super().__init__(msg)


class WekoRedisConnectionError(WekoRedisError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some connection error has occurred in weko_redis."
        super().__init__(ex, msg)

