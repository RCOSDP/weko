# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Utils for weko-authors."""

from flask import current_app
from invenio_db import db

from .models import AuthorsPrefixSettings


def get_author_setting_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsPrefixSettings).filter(
            AuthorsPrefixSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.debug(ex)
    return None
