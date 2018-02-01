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

"""Blueprint for schema rest."""

import xmlschema
import json

from flask import abort
from collections import OrderedDict
from xmlschema.components import (XsdAtomicRestriction, XsdSingleFacet, XsdPatternsFacet, XsdEnumerationFacet,
                                  XsdGroup, XsdAtomicBuiltin, XsdUnion
                                  )


class SchemaConventer:

    def __init__(self, schemafile, rootname):
        if schemafile is None:
            abort(405, "Error creating Schema: Invalid schema file used")
        if not rootname:
            abort(405, "Error creating Schema: Invalid root name used")

        self.rootname = rootname
        self.schema, self.namespaces = self.create_schema(schemafile)

    def to_dict(self):
        return json.dumps(self.schema)

    def create_schema(self, schema_file):
        def getXSVal(element_name):  # replace prefix namespace
            if "}" in element_name:
                for k, nsp in schema_data.namespaces.items():
                    if nsp in element_name:
                        if k == "":
                            k = self.rootname.split(":")[-1] if ":" in self.rootname else self.rootname
                        return element_name.replace("{"+nsp+"}", k+":")

            return element_name

        def get_namespace(namespaces):
            pix = tg = ''
            for k, nsp in namespaces.items():
                if k == '':
                    tg = nsp
                    break

            for k, nsp in namespaces.items():
                if tg == nsp and k != '':
                    pix = k
                    break

            return pix, tg

        def get_element_type(type):
            typd = OrderedDict()

            if isinstance(type, XsdAtomicRestriction):
                rstr = typd['restriction'] = OrderedDict()
                for va in type.validators:
                    if isinstance(va, XsdEnumerationFacet):
                        rstr.update(OrderedDict(enumeration=va.enumeration))
                    if isinstance(va, XsdSingleFacet):
                        sf = OrderedDict()
                        vn = va.name.split('(')[0] if "(" in va.name else va.name
                        sf[vn] = va.value
                        rstr.update(sf)

                if isinstance(type.patterns, XsdPatternsFacet):
                    plst = []
                    for pat in type.patterns.patterns:
                        plst.append(pat.pattern)
                    rstr.update(OrderedDict(patterns=plst))

            elif isinstance(type, XsdAtomicBuiltin):
                # print("■ id : %s", type.id)
                pass
            elif isinstance(type, XsdUnion):
                for mt in type.member_types:
                    typd.update(get_element_type(mt))
            elif isinstance(type, XsdGroup):
                pass
            else:
                atrlst = []
                for atrb in type.attributes._attribute_group.values():
                    attrd = OrderedDict(name=getXSVal(atrb.name), ref=atrb.ref, use=atrb.use)
                    if 'lang' not in atrb.name:
                        attrd.update(get_element_type(atrb.type))

                    atrlst.append(attrd)

                if len(atrlst):
                    typd['attributes'] = atrlst
                typd.update(get_element_type(type.content_type))
                pass

            return typd

        def get_elements(element):

            chdsm = OrderedDict()
            ctp = OrderedDict()
            for chd in element.iterchildren():
                chn = getXSVal(chd.name)
                ctp["type"] = OrderedDict(minOccurs=chd.min_occurs, maxOccurs=chd.max_occurs \
                    if chd.max_occurs else 'unbounded')
                ctp["type"].update(get_element_type(chd.type))

                chdsm[chn] = ctp
                chdsm[chn].update(get_elements(chd))

            return chdsm

        # get elements as below
        try:
            schema_file = open(schema_file, encoding='utf-8')
            schema_data = xmlschema.XMLSchema(schema_file)
        except:
            abort(405, "Error creating Schema: Can not open xsd file")

        # namespace
        nsp, tagns = get_namespace(schema_data.namespaces)

        # create the xsd json schema
        schema = OrderedDict()

        try:
            # get elements by root name
            path = self.rootname + "/*" if ':' in self.rootname \
                else '{%s}%s/*' % (tagns, nsp if nsp else self.rootname)
            elements = schema_data.findall(path)
        except:
            abort(405)
        else:
            if len(elements) > 0:
                for ems in elements:

                    # print("%s - %s" % (ems.name, ems.type.name))
                    ename = getXSVal(ems.name)
                    tp = OrderedDict()
                    tp["type"] = OrderedDict(minOccurs=ems.min_occurs, maxOccurs=ems.max_occurs \
                        if ems.max_occurs else 'unbounded')

                    tp["type"].update(get_element_type(ems.type))
                    schema[ename] = tp

                    for pae in schema_data.parent_map:
                        if ems.name == pae.name:
                            schema[ename].update(get_elements(pae))
            else:
                print("no xsd element!!!!")

        return schema, schema_data.namespaces


# if __name__ == '__main__':
#     fschema = "C:\jpcoar_scm\jpcoar_scm.xsd"
#
#     schema = schema(fschema, "jpcoar:jpcoar")
#     kc = schema.to_dict()
#     pass
