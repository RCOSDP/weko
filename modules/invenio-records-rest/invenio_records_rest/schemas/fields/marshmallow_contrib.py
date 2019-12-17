# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Contributed Marshmallow fields."""

from __future__ import absolute_import, print_function

import functools
import inspect

from marshmallow import fields, utils


def _get_func_args(func):
    """Get a list of the arguments a function or method has."""
    if isinstance(func, functools.partial):
        return _get_func_args(func.func)
    if inspect.isfunction(func) or inspect.ismethod(func):
        return list(inspect.getargspec(func).args)
    if callable(func):
        return list(inspect.getargspec(func.__call__).args)


class Function(fields.Function):
    """Enhanced marshmallow Function field.

    The main difference between the original marshmallow.fields.Function is for
    the ``deserialize`` function, which can now also point to a three-argument
    function, with the third argument being the original data that was passed
    to ``Schema.load``. The following example better demonstrates how this
    works:

    .. code-block:: python

        def serialize_foo(obj, context):
            return {'serialize_args': {'obj': obj, 'context': context}}

        def deserialize_foo(value, context, data):
            return {'deserialize_args': {
                'value': value, 'context': context, 'data': data}}

        class FooSchema(marshmallow.Schema):

            foo = Function(serialize_foo, deserialize_foo)

        FooSchema().dump({'foo': 42}).data
        {'foo': {
            'serialize_args': {
                'obj': {'foo': 42},
                'context': {}  # no context was passed
            }
        }}

        FooSchema().load({'foo': 42}).data
        {'foo': {
            'deserialize_args': {
                'value': 42,
                'context': {},  # no context was passed
                'data': {'foo': 42},
            }
        }}
    """

    def _deserialize(self, value, attr, data):
        if self.deserialize_func:
            return self._call_or_raise(
                self.deserialize_func, value, attr, data)
        return value

    def _call_or_raise(self, func, value, attr, data=None):
        func_args_len = len(_get_func_args(func))
        if func_args_len > 2:
            return func(value, self.parent.context, data)
        elif func_args_len > 1:
            return func(value, self.parent.context)
        else:
            return func(value)


class Method(fields.Method):
    """Enhanced marshmallow Method field.

    The main difference between the original marshmallow.fields.Method is for
    the ``deserialize`` method, which can now also point to a two-argument
    method, with the second argument being the original data that was passed to
    ``Schema.load``. The following example better demonstrates how this works:

    .. code-block:: python

        class BarSchema(marshmallow.Schema):

            bar = Method('serialize_bar', 'deserialize_bar')

            # Exactly the same behavior as in ``marshmallow.fields.Method``
            def serialize_bar(self, obj):
                return {'serialize_args': {'obj': obj}}

            def deserialize_bar(self, value, data):
                return {'deserialize_args': {'value': value, 'data': data}}

        BarSchema().dump({'bar': 42}).data
        {'bar': {
            'serialize_args': {
                'obj': {'bar': 42}
            }
        }}

        BarSchema().load({'bar': 42}).data
        {'bar': {
            'deserialize_args': {
                'data': {'bar': 42},
                'value': 42
            }
        }}
    """

    def _deserialize(self, value, attr, data):
        if self.deserialize_method_name:
            try:
                method = utils.callable_or_raise(
                    getattr(self.parent, self.deserialize_method_name, None)
                )
                method_args_len = len(_get_func_args(method))
                if method_args_len > 2:
                    return method(value, data)
                return method(value)
            except AttributeError:
                pass
        return value
