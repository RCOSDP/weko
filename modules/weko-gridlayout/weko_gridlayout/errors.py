# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Gridlayout is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko gridlayout."""

class WekoGridLayoutError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko gridlayout error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_gridlayout."
        super().__init__(msg, *args)


class WekoWidgetLayoutError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some layout of wedget error has occurred in weko_gridlayout."
        super().__init__(ex, msg, *args)


class WekoWidgetDataError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some date error has occurred in weko_gridlayout."
        super().__init__(ex, msg, *args)


class WekoWidgetSettingError(WekoGridLayoutError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_gridlayout."
        super().__init__(ex, msg, *args)

