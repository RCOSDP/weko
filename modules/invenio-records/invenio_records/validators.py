# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2021      TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record validators."""

from jsonschema.validators import Draft4Validator, extend, validator_for

PartialDraft4Validator = extend(Draft4Validator, {"required": None})
"""Partial JSON Schema (draft 4) validator.

Special validator that contains the same validation rules of Draft4Validator,
except for required fields.
"""


def _generate_legacy_type_checks(types):
    """Generate new-style type mappings from old-style type mappings.

    Based on the function `jsonschema.validators._generate_legacy_type_checks`
    from jsonschema 3.x.

    :param types: A mapping of type names to their Python types
    :returns: A dictionary of definitions that can be passed to `TypeChecker`s
    """

    def gen_type_check(pytypes):
        def type_check(_checker, instance):
            return isinstance(instance, pytypes)

        return type_check

    return {typename: gen_type_check(pytypes) for (typename, pytypes) in types.items()}


def _create_validator(schema, base_validator_cls=None, custom_checks=None):
    """Create a fitting jsonschema validator class.

    :param schema: The schema for which to create a fitting validator
    :param base_validator_cls: The base :class:`jsonschema.protocols.Validator`
        class to base the new validator class on -- if not specified, the base
        class will be determined by the given schema.
    :param custom_checks: A dictionary with type names and Python types
        to check against, e.g. {"string": str, "object": dict}
    :returns: An fitting :class:`jsonschema.protocols.Validator` class
    """
    validator_cls = base_validator_cls or validator_for(schema)
    if custom_checks:
        type_checker = validator_cls.TYPE_CHECKER.redefine_many(
            _generate_legacy_type_checks(custom_checks)
        )

        validator_cls = extend(
            validator_cls,
            type_checker=type_checker,
        )

    return validator_cls
