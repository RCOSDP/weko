# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingclient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import requests
import re
from flask import current_app,url_for

def request_signposting(uri):
    """get data from signposting

    :param str uri: item url
    :return: data from signposting
    :rtype: list
    """
    data = list()
    try:
        r = requests.head(make_signposting_url(uri))
        r.raise_for_status()

    except requests.exceptions.RequestException as e:
        current_app.logger.exception(str(e))
        print(e)
    else:
        link = r.headers['Link']
        data = create_data_from_signposting(link)
    
    return data

def make_signposting_url(uri):
    """make url for signposting from item url

    :param str uri: item url
    :return: url for signposting
    :rtype: str
    """
    #return uri+"/signposting"
    import re
    print(url_for("weko_signpostingserver_api.requested_signposting",recid="2"))
    return re.sub("https://(.*)/records","https://172.19.0.6:443/records",uri)+"/signposting"
    #return uri+"/signposting"

def create_data_from_signposting(link):
    """create list data from string

    :param str link: string from signposting
    :return: data
    :rtype: list
    """
    lines = link.split(',')
    data = list()
    for line in lines:
        d=dict()
        for l in line.split(';'):
            if re.search(r'<(.*)>',l):
                d['url'] = re.search(r'<(.*)>',l).group(1).strip()
            else:
                d[l.split('=')[0].strip()]=l.split('=')[1].strip(' "')
        data.append(d)
    return data
