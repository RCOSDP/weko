# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Generated field."""

from __future__ import absolute_import, print_function

import warnings

from .marshmallow_contrib import Function, Method


class GeneratedValue(object):
    """Sentinel value class forcing marshmallow missing field generation."""

    pass


class ForcedFieldDeserializeMixin(object):
    """Mixin that forces deserialization of marshmallow fields."""

    def __init__(self, *args, **kwargs):
        """Override the "missing" parameter."""
        if 'missing' in kwargs:
            obj_name = '{self.__module__}.{self.__class__.__name__}'.format(
                self=self)
            mixin_name = '{mixin.__module__}.{mixin.__name__}'.format(
                mixin=ForcedFieldDeserializeMixin)
            warnings.warn(
                '[{obj_name}] is overriding the "missing" argument via '
                '[{mixin_name}] in order to enforce deserialization of the '
                'Marshmallow field. The value "{original_missing}" will be '
                'overridden.'.format(
                    obj_name=obj_name, mixin_name=mixin_name,
                    original_missing=kwargs['missing']),
                RuntimeWarning)
        # Setting "missing" to some value forces the call to ``.deserialize``
        kwargs['missing'] = GeneratedValue
        super(ForcedFieldDeserializeMixin, self).__init__(*args, **kwargs)


class GenFunction(ForcedFieldDeserializeMixin, Function):
    """Function field which is always deserialized."""

    pass


class GenMethod(ForcedFieldDeserializeMixin, Method):
    """Method field which is always deserialized."""

    pass
