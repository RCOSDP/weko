# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging views."""

from flask import Blueprint,current_app
from invenio_db import db

blueprint = Blueprint(
    "weko_logging",
    __name__,
    template_folder="templates",
    static_folder="static",
)

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_logging dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()