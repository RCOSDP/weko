# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingserver is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
from flask import Blueprint, Response, request, current_app

from invenio_records.api import Record

blueprint_signposting_api = Blueprint(
    'weko_signpostingserver_api',
    __name__
)

# TODO: recordが存在しない場合の処理
@blueprint_signposting_api.route('/records/<recid>/signposting', methods = ['HEAD'])
def request(recid):
    resp = Response()
    host_url = request.url_root()
    record = Record.get_record(record)
    link = list()
    
    permalink = get_record_permalink(record)
    if not permalink:
        permalink = '{hosturl}/records/{recid}'.\
                    format(hosturl=host_url, recid=recid)
    link.append('<{url}> ; rel="cite-as"'.\
                format(url = permalink))
    link.append('<{url}> ; rel="describedby" ; type="application/json"'.\
                format(url = '{hosturl}/records/{recid}/export/json'.\
                        format(hosturl = host_url, recid = recid)))
    link.append('<{url}> ; rel="describedby" ; type="application/x-bibtex"'.\
                format(url = '{hosturl}/records/{recid}/export/bibtex'.\
                        format(hosturl = host_url, recid = recid)))
    
    oad = current_app.config.get('OAISERVER_METADATA_FORMATS',{})
    
    for _format,_object in oad.items():
        url = "{hosturl}/oai?verb=GetRecord&metadataPrefix={formats}&identifier={recid}".\
            format(hosturl=host_url,formats=_format,recid=record['_oai']['id'])
        link.append('<{url}> ; rel="describedby" ; type="application/xml" ; formats={formats}'.\
                    format(url = url,
                           formats = _object['namespace']))
    link_str=["recid",str(recid)]
    resp.headers['Link'] = ','.join(link_str)
    return resp

def get_record_permalink(record):
    """
    Recordインスタンスから識別子を取得する。
    weko_records_ui.utils.get_record_permalinkと処理は一緒。
    wekoのメソッドを使っていいなら排除
    """
    doi = record.pid_doi
    cnri = record.pid_cnri
    
    if doi or cnri:
        return doi.pid_value if doi else cnri.pid_value
    
    return 