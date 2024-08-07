"""Custom exceptions for weko_user_profiles."""

class WekoUserProfilesError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_user_profiles."
        super().__init__(msg)


