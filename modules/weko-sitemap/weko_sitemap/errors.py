"""Custom exceptions for weko_sitemap."""

class WekoSitemapError(Exception):
    def __init__(self, ex=None, msg=None):
        if ex:
            self.exception = ex
        if not msg:
            msg = "Some error has occurred in weko_sitemap."
        super().__init__(msg)


