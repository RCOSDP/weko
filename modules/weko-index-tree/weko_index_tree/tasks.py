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
from weko_index_tree.models import Index
from weko_handle.api import Handle

@shared_task(ignore_result=True)
def update_oaiset_setting(index_info, data):
    """Create/Update oai set setting."""
    try:
        pub_state = data["public_state"] and data["harvest_public_state"]
        if int(data["parent"]) == 0:
            spec = str(data["id"])
            description = data["index_name"]
        else:
            spec = index_info[2].replace("/", ":")
            description = index_info[4].replace("-/-", "->")
        with db.session.begin_nested():
            current_app.logger.debug("data[id]:{}".format(data["id"]))
            oaiset = OAISet.query.filter_by(id=data["id"]).one_or_none()
            if oaiset:
                if pub_state:
                    oaiset.spec = spec
                    oaiset.name = data["index_name"]
                    oaiset.search_pattern = 'path:"{}"'.format(data["id"])
                    #oaiset.search_pattern = '_oai.sets:"{}"'.format(spec)
                    oaiset.description = description
                    db.session.merge(oaiset)
                else:
                    db.session.delete(oaiset)
            elif pub_state:
                oaiset = OAISet(
                    id=data["id"],
                    spec=spec,
                    name=data["index_name"],
                    description=description)
                oaiset.search_pattern = 'path:"{}"'.format(data["id"])
                #oaiset.search_pattern = '_oai.sets:"{}"'.format(spec)
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
            db.session.query(OAISet).filter(
                OAISet.id.in_(id_list[s:e])). \
                delete(synchronize_session='fetch')
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()


@shared_task(ignore_result=True)
def delete_index_handle(id_list):
    """Delete index handle."""
    try:
        weko_handle = Handle()

        e = 0
        batch = 100
        while e <= len(id_list):
            s = e
            e = e + batch

            # Target deleted records
            cnri_list = db.session.query(Index.cnri).filter(
                Index.id.in_(id_list[s:e]),
                Index.is_deleted.is_(True)
            ).all()

            # call weko_handle::delete_handle() 
            for cnri in cnri_list:
                if cnri is not None:
                    handle = weko_handle.delete_handle(hdl=cnri)
                    if handle is None:
                        current_app.logger.debug('Delete Failed')
                        raise Exception('Delete Failed')

    except Exception as ex:
        current_app.logger.debug(ex)
