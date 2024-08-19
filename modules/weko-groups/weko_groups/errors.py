"""Custom errors for weko groups."""

class WekoGroupsError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko groups error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_groups."
        super().__init__(msg, *args)


class WekoGroupsManagementError(WekoGroupsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Somemanagement error has occurred in weko_groups."
        super().__init__(ex, msg, *args)

