"""Custom errors for weko sitemap."""

class WekoSitemapError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko sitemap error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_sitemap."
        super().__init__(msg, *args)


class WekoSitemapSettingError(WekoSitemapError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_sitemap."
        super().__init__(ex, msg, *args)

