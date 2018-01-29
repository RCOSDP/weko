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

"""Utilities for converting to MARC21."""

import pkg_resources
from dojson._compat import iteritems, string_types
from lxml import etree
from lxml.builder import ElementMaker

from .api import Mapping


def dumps_etree(records, xslt_filename=None):
    """Dump records into a etree.

    :param records: records
    :param xslt_filename: xslt filename
    """
    E = ElementMaker()

    get_mapping(records)

    def dump_record(record):
        """Dump a single record."""
        root = E.root()

        def make_emt(ky, obj):
            item = etree.Element(ky)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, list):
                        for lst in v:
                            if isinstance(lst, dict):
                                item.append(make_emt(k, lst))
                            else:
                                ele = etree.Element(k)
                                ele.text = lst
                                item.append(ele)

                    elif isinstance(v, (dict)):
                        item.append(make_emt(k, v))
                    elif ky == "control_number" or ky == "_oai":
                        pass
                    else:
                        ele = etree.Element(k)
                        ele.text = v
                        item.append(ele)
            return item

        items = iteritems(record["metadata"])
        for k, v in items:
            root.append(make_emt(k, v))

        return root

    if isinstance(records, dict):
        root = dump_record(records)

    if xslt_filename is not None:
        ns = etree.FunctionNamespace("http://mydomain.org/myfunctions")
        ns["change_name"] = change_name
        ns["tokenize"] = tokenize
        xslt_root = etree.parse(open(xslt_filename))
        transform = etree.XSLT(xslt_root)
        root = transform(root).getroot()

    return root


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


def get_mapping(records):
    """Get mappings.

    :param records: records
    """
    if isinstance(records, dict):
        id = records["metadata"].pop("item_type_id")
        mjson = Mapping.get_record(id)
        mp = mjson.dumps()
        if mjson:
            for k, v in records["metadata"].items():
                if isinstance(v, dict) and k != "_oai":
                    v.update(mp.get(k))


def change_name(context, name):
    """Dump records into a MarcXML file.

    :param context: context
    :param name: record key
    """
    cname = ""

    if name == "description" or name == "date" or name == "version" or \
            name == "geoLocation":
        cname = "datacite:"
    elif name == "title" or name == "rights" or name == "publisher" or \
            name == "language" or name == "type":
        cname = "dc:"
    elif name == "dissertationNumber" or name == "degreeName" or \
            name == "dateGranted":
        cname = "dcndl:"
    elif name == "alternative" or name == "accessRights" or \
            name == "temporal":
        cname = "dcterms:"
    elif name == "versionType":
        cname = "openaire:"
    else:
        cname = "jpcoar:"

    return cname + name


def tokenize(context, s, par):
    """Split s by par.

    :param context: context
    :param s: str
    :param par: key
    """
    return s.split(par)
