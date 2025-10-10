# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signposting is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-signposting."""

import traceback
from flask import Response, current_app
from sqlalchemy.exc import SQLAlchemyError

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError


def requested_signposting(pid, record, template=None, **kwargs):
    """_summary_

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:
    .. code-block:: python
        RECORDS_UI_ENDPOINTS = dict(
            recid_signposting=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                view_imp='weko_signposting.api.requested_signposting',
                methods=['HEAD']
            ),
            recid_signposting=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                # ...
        )
    In addition, please place it above the one that has
    the same route and uses the GET method.
    """
    host_url = current_app.config['THEME_SITEURL']

    links = []
    recid = record['recid']
    record_link = f"{host_url}/records/{recid}"
    permalink = get_record_doi(recid)

    if permalink is not None:
        links.append('<{url}>; rel="cite-as"'.format(url=permalink))

    links.append(
        '<{url}>; rel="describedby"; type="application/json"'
        .format(url=f'{record_link}/export/json')
    )
    links.append(
        '<{url}>; rel="describedby"; type="application/x-bibtex"'
        .format(url=f'{record_link}/export/bibtex')
    )

    oad = current_app.config.get('OAISERVER_METADATA_FORMATS', {})

    for _format, _object in oad.items():
        url = (
            f'{host_url}/oai?verb=GetRecord&metadataPrefix={_format}'
            f'&identifier={record["_oai"]["id"]}'
        )
        links.append(
            f'<{url}>; rel="describedby"; '
            f'type="application/xml"; formats="{_object["namespace"]}"'
        )

    resp = Response()
    resp.headers['Link'] = ', '.join(links)
    return resp


def get_record_doi(recid):
    """Get the uuid of the parent element of the record
    and get the uri of the doi associated with it

    :param string recid: recid
    :return: uri of doi
    :rtype: string | None
    """

    try:
        item_uuid =  PersistentIdentifier.get('recid', str(recid)).object_uuid
        pid = (
            PersistentIdentifier
            .query.filter_by(
                pid_type='doi', object_uuid=item_uuid,
                status=PIDStatus.REGISTERED
            )
            .order_by(db.desc(PersistentIdentifier.created))
            .first()
        )
        if pid is not None:
            return  pid.pid_value

    except PIDDoesNotExistError as ex:
        current_app.logger.error(f"PID does not exist: {recid}")
        traceback.print_exc()
    except SQLAlchemyError as ex:
        current_app.logger.error(f"Failed to get DOI for {recid}.")
        traceback.print_exc()

    return None
