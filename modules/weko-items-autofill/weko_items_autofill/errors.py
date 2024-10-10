# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko items autofill."""

class WekoItemsAutoFillError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko items autofill error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_items_autofill."
        self.msg = msg
        super().__init__(msg, *args)


class WekoItemsAutoFillURLError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some url error has occurred in weko_items_autofill."
        super().__init__(ex, msg, *args)


class WekoItemsAutoFillGettingError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some convertion date error has occurred in weko_items_autofill."
        super().__init__(ex, msg, *args)


class WekoItemsAutoFillConvertionError(WekoItemsAutoFillError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some getting date error has occurred in weko_items_autofill."
        super().__init__(ex, msg, *args)

