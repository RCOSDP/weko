# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Schea-Ui is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom errors for weko schema ui."""

class WekoSchemaError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko schema ui error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_schema_ui."
        self.msg = msg
        super().__init__(msg, *args)


class WekoSchemaSettingError(WekoSchemaError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_schema_ui."
        super().__init__(ex, msg, *args)


class WekoSchemaConversionError(WekoSchemaError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some schema conversion error has occurred in weko_schema_ui."
        super().__init__(ex, msg, *args)


class WekoOAISchemaError(WekoSchemaError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some OAI schema error has occurred in weko_schema_ui."
        super().__init__(ex, msg, *args)


class WekoItemtypeSchemaError(WekoSchemaError):
    def __init__(self, ex=None, msg=None, *args):
        if not msg:
            msg = "Some itemtype schema error has occurred in weko_schema_ui."
        super().__init__(ex, msg, *args)


class WekoSchemaTreeError(WekoSchemaError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some schema tree error has occurred in weko_schema_ui."
        super().__init__(ex, msg, *args)

