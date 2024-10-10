# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Theme is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko theme."""

class WekoThemeError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko theme error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg  is None:
            msg = "Some error has occurred in weko_theme."
        self.msg = msg
        super().__init__(msg, *args)


class WekoThemeSettingError(WekoThemeError):
    def __init__(self, ex=None, msg=None, *args):
        if msg  is None:
            msg = "Some setting error has occurred in weko_theme."
        super().__init__(ex, msg, *args)

