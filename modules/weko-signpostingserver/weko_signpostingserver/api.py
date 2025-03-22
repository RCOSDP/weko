# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingserver is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
from flask import Blueprint, Response, request, current_app, redirect

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_db import db
from invenio_records.api import Record


def requested_signposting(pid, record, template=None, **kwargs):
    """_summary_

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:
    .. code-block:: python
        RECORDS_UI_ENDPOINTS = dict(
            recid_signposting=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                view_imp='weko_signpostingserver.api.requested_signposting',
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
    resp = Response()
    host_url = outside_url(request.host_url)
    link = list()
    recid = record['recid']
    permalink = outside_url(get_record_permalink(recid))
    if not permalink:
        permalink = '{hosturl}records/{recid}'.\
                    format(hosturl=host_url, recid=recid)
    link.append('<{url}> ; rel="cite-as"'.
                format(url=permalink))
    link.append('<{url}> ; rel="describedby" ; type="application/json"'.
                format(url='{hosturl}records/{recid}/export/json'.
                           format(hosturl=host_url, recid=recid)))
    link.append('<{url}> ; rel="describedby" ; type="application/x-bibtex"'.
                format(url='{hosturl}records/{recid}/export/bibtex'.
                           format(hosturl=host_url, recid=recid)))

    oad = current_app.config.get('OAISERVER_METADATA_FORMATS', {})

    for _format, _object in oad.items():
        url = '{hosturl}oai?verb=GetRecord&metadataPrefix='\
              '{formats}&identifier={recid}'.\
              format(hosturl=host_url,
                     formats=_format,
                     recid=record['_oai']['id']
                     )
        link.append('<{url}> ; rel="describedby" ; '
                    'type="application/xml" ; formats="{formats}"'.
                    format(url=url,
                           formats=_object['namespace']))
    resp.headers['Link'] = ','.join(link)
    return resp


def outside_url(url):
    if 'nginx' in url:
        return url.replace('nginx', current_app.config['WEB_HOST'])
    else:
        return url


def get_record_permalink(recid_p):
    """Get the uuid of the parent element of the record
    and get the uri of the doi associated with it

    :param string recid_p: recid
    :return: uri of doi
    :rtype: string
    """
    uuid_p = \
        PersistentIdentifier.get('parent',
                                 'parent:'+str(recid_p)
                                 ).object_uuid
    try:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='doi',
            object_uuid=uuid_p,
            status=PIDStatus.REGISTERED
        ).order_by(
            db.desc(PersistentIdentifier.created)
        ).first()
        if pid is None:
            return '{host_url}records/{recid}'.format(
                host_url=current_app.config['THEME_SITEURL'] + '/', recid=recid_p)
        else:
            return pid.pid_value
    except PIDDoesNotExistError as e:
        return '{host_url}records/{recid}'.format(
            host_url=current_app.config['THEME_SITEURL'] + '/', recid=recid_p)
