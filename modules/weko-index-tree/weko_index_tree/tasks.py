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
"""Weko Index celery tasks."""

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_oaiserver.models import OAISet


@shared_task(ignore_result=True)
def update_oaiset_setting(info, data):
    """Create/Update oai set setting."""
    def _get_spec(index_info, index_id):
        """Get setspec."""
        index_name = index_info[index_id]['index_name']
        if index_info[index_id]['parent'] != '0':
            setspec, name_path = _get_spec(index_info, index_info[index_id]['parent'])
            return "{}:{}".format(setspec, index_id), "{}->{}".format(name_path, index_name)
        else:
            return index_id, index_name

    try:
        pub_state = data["public_state"] and data["harvest_public_state"]
        if int(data["parent"]) == 0:
            spec = str(data["id"])
            description = data["index_name"]
        else:
            setspec, name_path = _get_spec(info, str(data["parent"]))
            spec = "{}:{}".format(setspec, data["id"])
            description = "{}->{}".format(name_path, data["index_name"])
        with db.session.begin_nested():
            oaiset = OAISet.query.filter_by(id=data["id"]).one_or_none()
            if oaiset:
                if pub_state:
                    oaiset.spec = spec
                    oaiset.name = data["index_name"]
                    oaiset.search_pattern = 'path:"{}"'.format(spec.replace(':', '/'))
                    oaiset.description = description
                    db.session.merge(oaiset)
                else:
                    db.session.delete(oaiset)
            elif pub_state:
                oaiset = OAISet(id=data["id"], spec=spec, name=data["index_name"], description=description)
                oaiset.search_pattern = 'path:"{}"'.format(spec.replace(':', '/'))
                db.session.add(oaiset)
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()

@shared_task(ignore_result=True)
def delete_oaiset_setting(id_list):
    """Delete oai set setting."""
    try:
        e = 0
        batch = 100
        while e <= len(id_list):
            s = e
            e = e + batch
            dct = db.session.query(OAISet).filter(
                OAISet.id.in_(id_list[s:e])). \
                delete(synchronize_session='fetch')
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()
