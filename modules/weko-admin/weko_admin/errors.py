# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Admin is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko admin."""

class WekoAdminError(Exception):
    """Superclass for all weko admin errors.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko admin error.

        Args:
            ex (Exception, Optional): Original exception object
            msg (str, Optional): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_admin."
        self.msg = msg
        super().__init__(msg, *args)


class WekoAdminSettingError(WekoAdminError):
    """Setting error in weko admin.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminMailError(WekoAdminError):
    """Feedback mail error in weko admin.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some mail error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminReportError(WekoAdminError):
    """Report error in weko admin.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some report error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminLogAnalysisError(WekoAdminError):
    """Log analysis error in weko admin.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some log analysis error has occurred in weko_admin."
        super().__init__(ex, msg, *args)


class WekoAdminReindexError(WekoAdminError):
    """Reindex error in weko admin.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some reindex error has occurred in weko_admin."
        super().__init__(ex, msg, *args)

