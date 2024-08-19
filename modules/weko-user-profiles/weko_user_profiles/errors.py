"""Custom errors for weko user profiles."""

class WekoUserProfilesError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko user profiles error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_user_profiles."
        super().__init__(msg, *args)


class WekoUserProfilesEditError(WekoUserProfilesError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some edit error has occurred in weko_user_profiles."
        super().__init__(ex, msg, *args)

