# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Gridlayout is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko gridlayout."""

class WekoGridLayoutError(Exception):
    """Super class for weko gridlayout error.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko gridlayout error.

        Args:
            ex (Exception, Optional): Original exception object
            msg (str, Optional): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_gridlayout."
        self.msg = msg
        super().__init__(msg, *args)


class WekoWidgetLayoutError(WekoGridLayoutError):
    """Layout error of wedget in weko gridlayout.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some layout of wedget error has occurred in weko_gridlayout."
        super().__init__(ex, msg, *args)


class WekoWidgetDataError(WekoGridLayoutError):
    """Data error of wedget in weko gridlayout.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some data error has occurred in weko_gridlayout."
        super().__init__(ex, msg, *args)


class WekoWidgetSettingError(WekoGridLayoutError):
    """Setting error of wedget in weko gridlayout.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_gridlayout."
        super().__init__(ex, msg, *args)

