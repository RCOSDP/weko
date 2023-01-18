# -*- coding: utf-8 -*-

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
