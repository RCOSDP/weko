# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio custom schema fields tests."""

import pytest
from invenio_pidstore.models import PersistentIdentifier as PIDModel
from invenio_records import Record
from marshmallow import missing

from invenio_records_rest.schemas import StrictKeysMixin
from invenio_records_rest.schemas.fields import DateString, GenFunction, \
    GenMethod, PersistentIdentifier, SanitizedHTML, SanitizedUnicode, \
    TrimmedString


class CustomFieldSchema(StrictKeysMixin):
    """Test schema."""

    date_string_field = DateString(attribute='date_string_field')
    sanitized_html_field = SanitizedHTML(attribute='sanitized_html_field')
    sanitized_unicode_field = SanitizedUnicode(
        attribute='sanitized_unicode_field')
    trimmed_string_field = TrimmedString(
        attribute='trimmed_string_field')
    gen_function_field = GenFunction(
        lambda o: 'serialize_gen_function_field',
        lambda o: 'deserialize_gen_function_field',
    )
    gen_method_field = GenMethod(
        'serialize_gen_method_field',
        'deserialize_gen_method_field')
    persistent_identifier_field = PersistentIdentifier()

    def serialize_gen_method_field(self, obj):
        """Serialize a value for the GenMethod field."""
        return 'serialize_gen_method_field'

    def deserialize_gen_method_field(self, value):
        """Deserialize a value for the GenMethod field."""
        return 'deserialize_gen_method_field'


def test_load_custom_fields(app):
    """Test loading of custom fields."""
    rec = Record({'date_string_field': '27.10.1999',
                  'sanitized_html_field': 'an <script>evil()</script> example',
                  # Zero-width space, Line Tabulation, Escape, Cancel
                  'sanitized_unicode_field': u'\u200b\u000b\u001b\u0018',
                  'trimmed_string_field': 'so much trailing whitespace    '})
    recid = PIDModel(pid_type='recid', pid_value='12345')
    # ensure only valid keys are given
    CustomFieldSchema().check_unknown_fields(rec, rec)
    loaded_data = CustomFieldSchema(context={'pid': recid}).load(rec).data
    if 'metadata' in loaded_data:
        values = loaded_data['metadata'].values()
    else:
        values = loaded_data.values()
    assert set(values) == \
        set(['1999-10-27', 'so much trailing whitespace',
             'an evil() example', u'', '12345',
             'deserialize_gen_method_field', 'deserialize_gen_function_field'])


def test_custom_generated_fields():
    """Test fields.generated fields."""

    with pytest.warns(RuntimeWarning):
        def serialize_func(obj, ctx):
            return ctx.get('func-foo', obj.get('func-bar', missing))

        def deserialize_func(value, ctx, data):
            return ctx.get('func-foo', data.get('func-bar', missing))

        class GeneratedFieldsSchema(StrictKeysMixin):
            """Test schema."""

            gen_function = GenFunction(
                serialize=serialize_func,
                deserialize=deserialize_func,
            )

            gen_method = GenMethod(
                serialize='_serialize_gen_method',
                deserialize='_desererialize_gen_method',
                missing='raises-warning',
            )

            def _serialize_gen_method(self, obj):
                # "meth-foo" from context or "meth-bar" from the object
                return self.context.get(
                    'meth-foo', obj.get('meth-bar', missing))

            def _desererialize_gen_method(self, value, data):
                # "meth-foo" from context or "meth-bar" from the data
                return self.context.get(
                    'meth-foo', data.get('meth-bar', missing))

    ctx = {
        'func-foo': 'ctx-func-value',
        'meth-foo': 'ctx-meth-value',
    }
    data = {
        'func-bar': 'data-func-value',
        'meth-bar': 'data-meth-value',
        'gen_function': 'original-func-value',
        'gen_method': 'original-meth-value',
    }

    # No context, no data
    assert GeneratedFieldsSchema().load({}).data == {}
    assert GeneratedFieldsSchema().dump({}).data == {}

    # Only context
    assert GeneratedFieldsSchema(context=ctx).load({}).data == {
        'gen_function': 'ctx-func-value',
        'gen_method': 'ctx-meth-value',
    }
    assert GeneratedFieldsSchema(context=ctx).dump({}).data == {
        'gen_function': 'ctx-func-value',
        'gen_method': 'ctx-meth-value',
    }

    # Only data
    assert GeneratedFieldsSchema().load(data).data == {
        'gen_function': 'data-func-value',
        'gen_method': 'data-meth-value',
    }
    assert GeneratedFieldsSchema().dump(data).data == {
        'gen_function': 'data-func-value',
        'gen_method': 'data-meth-value',
    }

    # Context and data
    assert GeneratedFieldsSchema(context=ctx).load(data).data == {
        'gen_function': 'ctx-func-value',
        'gen_method': 'ctx-meth-value',
    }
    assert GeneratedFieldsSchema(context=ctx).dump(data).data == {
        'gen_function': 'ctx-func-value',
        'gen_method': 'ctx-meth-value',
    }
