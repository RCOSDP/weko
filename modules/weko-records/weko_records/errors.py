# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko records."""

class WekoRecordsError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko records error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_records."
        super().__init__(msg, *args)


class WekoRecordsRegistrationError(WekoRecordsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some registration error has occurred in weko_records."
        super().__init__(ex, msg, *args)


class WekoRecordsTypeError(WekoRecordsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some itemtype error has occurred in weko_records."
        super().__init__(ex, msg, *args)


class WekoRecordsMetadataError(WekoRecordsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some metadata error has occurred in weko_records."
        super().__init__(ex, msg, *args)


class WekoRecordsSiteLicenseError(WekoRecordsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some site lisence error has occurred in weko_records."
        super().__init__(ex, msg, *args)


class WekoRecordsLinkError(WekoRecordsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some item link error has occurred in weko_records."
        super().__init__(ex, msg, *args)


class WekoRecordsEditHistoryError(WekoRecordsError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some itemtype edit history error has occurred in "\
                "weko_records."
        super().__init__(ex, msg, *args)

