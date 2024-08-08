"""Custom exceptions for weko_redis."""

class WekoRedisError(Exception):
    def __init__(self, ex=None, msg=None):
        """

        weko redis error initialization.

        :Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_redis."
        super().__init__(msg)


class WekoRedisURLError(WekoRedisError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


