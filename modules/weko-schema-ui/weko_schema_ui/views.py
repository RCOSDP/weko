# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Blueprint for weko-schema-ui."""

from flask import Blueprint

blueprint = Blueprint(
    'weko_schema_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)
