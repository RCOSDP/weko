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

"""Utilities for convert XML."""

from flask import abort
from lxml import etree
from lxml.builder import ElementMaker
from weko_records.api import Mapping
from .api import WekoSchema
import re


def dumps_etree(record, schema_type = None):
    """Dump records into a etree.

    :param records: records
    :param schema_type: schema type
    """
    if schema_type:
        scname = schema_type if re.search("\*?_mapping", schema_type) in schema_type else schema_type + "_mapping"

        # get xsd schema
        rec = WekoSchema.get_record_by_name(scname)
        if rec:
            # inject mappings info to record
            get_mapping(record, scname)
            return create_xml(record, rec.xsd, rec.namespaces)
        else:
            abort(410)
    else:
        abort(410)


def create_xml(record, xsd, ns):
    """"""
    E = ElementMaker(namespace=ns.get(""), nsmap=ns)

    for el in xsd.items():
        if isinstance(el, dict()):
            pass
        elif isinstance(el, str):
            ""
    klst = []
    def get_key_list(kn, nodes):
        # if no child
        if isinstance(nodes, str) and len(nodes.keys()) == 1:
            return [j for j in nodes.keys()]

        for k, v in nodes.items():
            if k != "type" and isinstance(v, dict):
                klst.append(get_key_list(k, v))




    def dump_record(nodes):
        """"""

        # if no child
        if isinstance(nodes, str) and len(nodes.keys()) == 1:
            return [j for j in nodes.keys()]

        for k, v in nodes.items():
            if k != "type" and isinstance(v, dict):
                dump_record(v)


def get_value(record, key):
    vlst = []
    def get_key(r):

        if isinstance(r, str):
            return record

        for k, v in r.items():
            vlst.append(get_key(v))

    return vlst


def get_mapping(records, smn):
    """Get mappings.

    :param smn: schema mapping name
    :param records: records
    """
    if isinstance(records, dict):
        id = records["metadata"].pop("item_type_id")
        mjson = Mapping.get_record(id)
        mp = mjson.dumps()
        if mjson:
            for k, v in records["metadata"].items():
                if isinstance(v, dict) and k != "_oai":
                    v.update({smn: mp.get(k).get(smn)})




def dumps_etree(records, schema_name=None):
    """Dump records into a etree.

    :param records: records
    :param schema_name: xslt filename
    """

def dumps(records, xslt_filename=None, **kwargs):
    """Dump records into a MarcXML file.

    :param records: records
    :param xslt_filename: xslt filename
    """
    root = dumps_etree(records=records, xslt_filename=xslt_filename)
    return etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8',
        **kwargs
    )
