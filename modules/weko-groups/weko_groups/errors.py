"""Custom exceptions for weko_groups."""

class WekoGroupsError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_groups."
        super().__init__(msg)


class WekoGroupsMnageError(WekoGroupsError):
    def __init__(self, ex=None, msg=None):
        super().__init__(ex, msg)


