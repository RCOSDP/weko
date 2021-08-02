# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Validation for import weko-authors."""

import importlib
from functools import reduce
from operator import getitem

from flask_babelex import gettext as _
from invenio_db import db

from weko_authors.models import AuthorsPrefixSettings


def validate_by_extend_validator(values=[], validator={}):
    """Validate by specify validator.

    Args:
        values (list, optional): List values. Defaults to [].
        validator (dict, optional): Validator information. Defaults to {}.

    Returns:
        list: List error messages.

    """
    errors = []
    if values and validator:
        _class = importlib.import_module(validator.get('class_name'))
        _func = getattr(_class, validator.get('func_name'))
        errors = _func(values)
    return errors


def validate_required(item, values=[], required={}):
    """Validate required.

    Args:
        item (object): Author metadata.
        values (list, optional): List values. Defaults to [].
        required (object, optional): Require info. Defaults to {}.

    Returns:
        list: List metadata paths are errors.

    """
    errors_key = []
    if_cond = required.get('if', [])
    if if_cond:
        for val in values:
            reduce_keys = val['reduce_keys']
            uplevel_data = reduce(getitem, reduce_keys[:-1], item)
            check = [cond for cond in if_cond if uplevel_data.get(cond)]
            if check and not val['value']:
                errors_key.append(val['key'])
    return errors_key


def validate_map(values=[], _map=[]):
    """Validate data in a map.

    Args:
        values (list, optional): List values. Defaults to [].
        _map (list, optional): List allowed values. Defaults to [].

    Returns:
        list: List metadata paths are errors.

    """
    errors_key = []
    if values and _map:
        for val in values:
            if val['value'] and val['value'] not in _map:
                errors_key.append(val['key'])
    return errors_key


def validate_identifier_scheme(values=[]):
    """Validate Identifier Scheme.

    Args:
        values (list, optional): List values with key path. Defaults to [].

    Returns:
        list: List errors message.

    """
    errors = []
    err_mgs = _("Specified Identifier Scheme '{}' does not exist.")
    if values:
        with db.session.no_autoflush:
            authors_prefix = AuthorsPrefixSettings.query.all()
            schemes = [prefix.scheme for prefix in authors_prefix]
            for val in values:
                if val['value'] and val['value'] not in schemes:
                    errors.append(err_mgs.format(val['value']))
    return errors


def validate_external_author_identifier(item, values=[],
                                        existed_external_authors_id={}):
    """Validate external author identifier.

    Args:
        item (object): Author metadata.
        values (list, optional): List values. Defaults to [].
        existed_external_authors_id (object, optional): Existed external
            author id. Defaults to {}.

    Returns:
        list: List metadata paths are warning.

    """
    warnings = []
    msg = _('External author identifier exists in DB.<br/>{}')
    for val in values:
        reduce_keys = val['reduce_keys']
        idType = reduce(getitem, reduce_keys[:-1], item)['idType']
        authorId = reduce(getitem, reduce_keys[:-1], item)['authorId']
        if idType and authorId:
            weko_ids_has_authorId = existed_external_authors_id \
                .get(idType, {}) \
                .get(authorId, [])
            if weko_ids_has_authorId \
                    and item.get('pk_id') not in weko_ids_has_authorId:
                warnings.append(authorId)
    if warnings:
        return msg.format('<br/>'.join(warnings))
    return None
