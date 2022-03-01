# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingserver is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
from flask import Blueprint, Response, request, current_app, redirect

from invenio_records.api import Record
from weko_inbox_sender.utils import get_record_permalink, get_records_pid
blueprint_signposting_api = Blueprint(
    'weko_signpostingserver_api',
    __name__
)


# TODO: recordが存在しない場合の処理
@blueprint_signposting_api.route('/records/<recid>/signposting',
                                 methods=['HEAD']
                                 )
def requested_signposting(recid):
    resp = Response()
    host_url = outside_url(request.host_url)
    record = Record.get_record(get_records_pid(str(recid)))
    link = list()

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
