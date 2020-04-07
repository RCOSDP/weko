# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Configuration for weko-itemtypes-ui."""

from flask_babelex import lazy_gettext as _

# TODO: Delete if not being used
WEKO_ITEMTYPES_UI_BASE_TEMPLATE = 'weko_itemtypes_ui/base.html'
"""Default base template for the item type page."""

WEKO_ITEMTYPES_UI_ADMIN_REGISTER_TEMPLATE = \
    'weko_itemtypes_ui/admin/create_itemtype.html'
"""Register template for the item type page."""

WEKO_ITEMTYPES_UI_ADMIN_CREATE_PROPERTY = \
    'weko_itemtypes_ui/admin/create_property.html'
"""Create property template."""

WEKO_ITEMTYPES_UI_ADMIN_MAPPING_TEMPLATE = \
    'weko_itemtypes_ui/admin/create_mapping.html'
"""Mapping template for the item type page."""

WEKO_ITEMTYPES_UI_ADMIN_ERROR_TEMPLATE = 'weko_itemtypes_ui/admin/error.html'
"""Error template for the item type page."""

WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES = {
    '1': {'name': _('Text Field'), 'value': 'text'},
    '2': {'name': _('Text Area'), 'value': 'textarea'},
    '3': {'name': _('Check Box'), 'value': 'checkboxes'},
    '4': {'name': _('Radio Button'), 'value': 'radios'},
    '5': {'name': _('List Box'), 'value': 'select'},
    '6': {'name': _('Date'), 'value': 'datetime'}
}
"""Default properties of the item type."""

WEKO_BILLING_FILE_ACCESS = 1
"""Show billing file property in list."""

WEKO_BILLING_FILE_PROP_ID = 103
"""Id of billing file property."""

WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES_IDS = [3, 60, 62, 102]
"""Ids of default properties
    3 = Right Holder
    60 = Creator / Author
    62 = Contributor
    102 = Bibliographic information
"""
