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

"""WEKO3 module docstring."""
import requests
import xmltodict
from flask import jsonify

romeo_api_base_url = 'http://www.sherpa.ac.uk/romeo/api29.php'


def search_romeo_jtitles(keywords, qtype):
    """Search by title.

    :param keywords:
    :param qtype:
    :return:
    """
    payloads = {
        'jtitle': keywords,
        'qtype': qtype
    }

    response = requests.get(
        romeo_api_base_url,
        params=payloads
    )

    dict_result = xmltodict.parse(response.text, encoding='utf-8') \
        if response.text else {}

    return dict_result


def search_romeo_issn(query):
    """Search journal using ISSN.

    Searching for one journal with the ISSN selected by the user
    to get the journal's Romeo info
    """
    # ISSN contained in the query
    payloads = {
        'issn': query  # ISSN search - Single Result
    }

    response = requests.get(
        romeo_api_base_url,
        params=payloads
    )

    response_body = response.text
    dict_result = xmltodict.parse(response_body, encoding='utf-8') \
        if response.text else {}
    return dict_result


def search_romeo_jtitle(query):
    """Search the journal using query.

    Searching for journals with the input query
    to get their Romeo info
    """
    payloads = {
        'jtitle': query
    }

    response = requests.get(
        romeo_api_base_url,
        params=payloads
    )

    response_body = response.text
    dict_result = xmltodict.parse(response_body, encoding='utf-8')
    return dict_result, jsonify(dict_result)
