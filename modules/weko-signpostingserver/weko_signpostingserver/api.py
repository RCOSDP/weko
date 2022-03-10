# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingserver is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
from flask import Blueprint, Response, request, current_app, redirect

from invenio_records.api import Record
from weko_inbox_sender.utils import get_record_permalink


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
