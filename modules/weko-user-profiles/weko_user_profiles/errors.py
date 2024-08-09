"""Custom errors for weko user profiles."""

class WekoUserProfilesError(Exception):
    def __init__(self, ex=None, msg=None):
        """Constructor.

        Initialize theweko user profiles error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_user_profiles."
        super().__init__(msg)


class WekoUserProfilesEditError(WekoUserProfilesError):
    def __init__(self, ex=None, msg=None):
        if msg is None:
            msg = "Some edit error has occurred in weko_user_profiles."
        super().__init__(ex, msg)

