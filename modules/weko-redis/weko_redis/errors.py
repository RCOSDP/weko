"""Custom errors for weko redis."""

class WekoRedisError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko redis error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_redis."
        super().__init__(msg, *args)


class WekoRedisConnectionError(WekoRedisError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some connection error has occurred in weko_redis."
        super().__init__(ex, msg, *args)

