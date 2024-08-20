# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Admin is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko admin."""

class WekoAdminError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko admin error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_admin."
        super().__init__(msg, *args)


class WekoAdminSettingError(WekoAdminError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminMailError(WekoAdminError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some mail error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminReportError(WekoAdminError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some report error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminLogAnalysisError(WekoAdminError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some log analysis error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminReindexError(WekoAdminError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some reindex error has occurred in weko_admin."
        super().__init__(ex, msg, *args)

