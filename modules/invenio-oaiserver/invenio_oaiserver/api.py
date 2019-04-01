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

"""Schema API."""

from invenio_db import db
from sqlalchemy import *

from .models import Identify


class OaiIdentify():
    """OAI-PMH Identify."""

    @classmethod
    def get_all(cls):
        """Retrieve OAI-Identifi.

        :param
        :returns: the first data of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = Identify.query.order_by(desc(Identify.id))
            return query.first()

    @classmethod
    def get_count(cls):
        """Get the count of Setting."""
        with db.session.no_autoflush:
            # cnt = OAIPMH.query.count()
            return 0
