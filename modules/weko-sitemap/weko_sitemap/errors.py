# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Sitemap is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

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
        self.msg = msg
        super().__init__(msg, *args)


class WekoSitemapSettingError(WekoSitemapError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_sitemap."
        super().__init__(ex, msg, *args)

