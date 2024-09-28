# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Deposit is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko deposit."""

class WekoDepositError(Exception):
    """Super class for weko deposit errors.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko deposit error.

        Args:
            ex (Exception, Optional): Original exception object
            msg (str, Optional): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_deposit."
        self.msg = msg
        super().__init__(msg, *args)


class WekoDepositIndexerError(WekoDepositError):
    """Indexer error in weko deposit.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some indexer error has occurred in weko_deposit."
        super().__init__(ex, msg, *args)


class WekoDepositRegistrationError(WekoDepositError):
    """Registration error in weko deposit.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some registration error has occurred in weko_deposit."
        super().__init__(ex, msg, *args)


class WekoDepositStorageError(WekoDepositError):
    """Storage error in weko deposit.

    Attributes:
        exception (Exception, Optional): Original exception object.
        msg (str): Error message
    """
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some storage error has occurred in weko_deposit."
        super().__init__(ex, msg, *args)

