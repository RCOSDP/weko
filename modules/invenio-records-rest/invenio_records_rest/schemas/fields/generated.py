# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Generated field."""

import warnings

from marshmallow import missing as missing_

from invenio_records_rest.utils import marshmallow_major_version

from .marshmallow_contrib import Function, Method


class GeneratedValue(object):
    """Sentinel value class forcing marshmallow missing field generation."""

    pass


class ForcedFieldDeserializeMixin(object):
    """Mixin that forces deserialization of marshmallow fields."""

    if marshmallow_major_version < 3:

        def __init__(self, *args, **kwargs):
            """Override the "missing" parameter."""
            if "missing" in kwargs:
                obj_name = "{self.__module__}.{self.__class__.__name__}".format(
                    self=self
                )
                mixin_name = "{mixin.__module__}.{mixin.__name__}".format(
                    mixin=ForcedFieldDeserializeMixin
                )
                warnings.warn(
                    '[{obj_name}] is overriding the "missing" argument via '
                    "[{mixin_name}] in order to enforce deserialization of"
                    'the Marshmallow field. The value "{original_missing}"'
                    "will be overridden.".format(
                        obj_name=obj_name,
                        mixin_name=mixin_name,
                        original_missing=kwargs["missing"],
                    ),
                    RuntimeWarning,
                )
            # Setting "missing" to some value forces the call
            # to ``.deserialize``
            kwargs["missing"] = GeneratedValue
            super().__init__(*args, **kwargs)

    # Overriding default deserializer since we need to deserialize an
    # initially non-existent field. In this implementation the checks are
    # removed since we expect our deserializer to provide the value.
    def deserialize(self, *args, **kwargs):
        """Deserialize field."""
        # Proceed with deserialization, skipping all checks.
        output = self._deserialize(*args, **kwargs)
        self._validate(output)
        return output


class GenFunction(ForcedFieldDeserializeMixin, Function):
    """Function field which is always deserialized."""

    pass


class GenMethod(ForcedFieldDeserializeMixin, Method):
    """Method field which is always deserialized."""

    pass
