# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signpostingclient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import requests
import re

def request_signposting(uri):
    r = requests.head(make_signposting_url(uri))
    link = r.headers['Link']
    
    data = create_data_from_signposting(link)
    
    return data

def make_signposting_url(uri):
    return uri+"/signposting"

def create_data_from_signposting(link):
    
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
