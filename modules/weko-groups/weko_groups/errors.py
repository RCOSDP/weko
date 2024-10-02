# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Groups is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko groups."""

class WekoGroupsError(Exception):
    """Super class for weko groups error.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko groups error.

        Args:
            ex (Exception, Optional): Original exception object
            msg (str, Optional): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_groups."
        self.msg = msg
        super().__init__(msg, *args)


class WekoGroupsManagementError(WekoGroupsError):
    """Management error of weko groups.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some management error has occurred in weko_groups."
        super().__init__(ex, msg, *args)

