# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko handle."""

class WekoHandleError(Exception):
    """Super class for weko handle error.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko handle error.

        Args:
            ex (Exception, Optional): Original exception object
            msg (str, Optional): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_handle."
        self.msg = msg
        super().__init__(msg, *args)


class WekoHandleRegistrationError(WekoHandleError):
    """Registration error of weko handle.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some registration error has occurred in weko_handle."
        super().__init__(ex, msg, *args)


class WekoHandleRetrievalError(WekoHandleError):
    """Retrieval error of weko handle.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some retrival error has occurred in weko_handle."
        super().__init__(ex, msg, *args)

