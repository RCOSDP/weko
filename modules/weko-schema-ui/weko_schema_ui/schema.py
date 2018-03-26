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

import xmlschema, json, copy

from lxml import etree
from lxml.builder import ElementMaker
from weko_records.api import Mapping
from .api import WekoSchema

from flask import abort, current_app
from collections import OrderedDict
from xmlschema.components import (XsdAtomicRestriction, XsdSingleFacet, XsdPatternsFacet, XsdEnumerationFacet,
                                  XsdGroup, XsdAtomicBuiltin, XsdUnion
                                  )


class SchemaConverter:

    def __init__(self, schemafile, rootname):
        if schemafile is None:
            abort(400, "Error creating Schema: Invalid schema file used")
        if not rootname:
            abort(400, "Error creating Schema: Invalid root name used")

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
            for chd in element.iterchildren():
                ctp = OrderedDict()
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
            abort(400, "Error creating Schema: Can not open xsd file. Please check it!")

        # namespace
        nsp, tagns = get_namespace(schema_data.namespaces)

        # create the xsd json schema
        schema = OrderedDict()

        try:
            # get elements by root name
            path = self.rootname + "/*" if ':' in self.rootname \
                else '{%s}%s/*' % (tagns, nsp if nsp else self.rootname)
            elements = schema_data.findall(path)
            elements = schema_data.findall('*/*') if len(elements) < 1 else elements
        except:
            abort(400, "Error creating Schema: Can not find element")
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


class SchemaTree:

    def __init__(self, record, schema_name):
        """

        :param record: item metadata
        :param schema_name: schema name
        """
        self._record = record["metadata"]
        self._schema_name = schema_name
        self._schema_obj = self.get_mapping_data()
        self._v = "@value"
        self._atr = "@attributes"

    def get_mapping_data(self):
        """
        :return:
        """
        rec = WekoSchema.get_record_by_name(self._schema_name)

        if not rec:
            return None

        def get_mapping():

            if isinstance(self._record, dict):
                id = self._record.pop("item_type_id")
                self._record.pop("_buckets", {})
                self._record.pop("_deposit", {})
                mjson = Mapping.get_record(id)
                mp = mjson.dumps()
                if mjson:
                    for k, v in self._record.items():
                        if isinstance(v, dict) and k != "_oai":
                            v.update({self._schema_name: mp.get(k).get(self._schema_name)})

        # inject mappings info to record
        get_mapping()
        rec.model.xsd = json.loads(rec.model.xsd, object_pairs_hook=OrderedDict)
        return rec

    def create_xml(self):
        """
        create schema xml tree
        :return:
        """
        def get_element(str):
            return str.split(":")[-1] if ":" in str else str

        def get_value_list():

            def analysis(field):
                exp = (',')
                return exp[0], field.split(exp[0])

            def set_value(nd, nv):
                if isinstance(nd, dict):
                    for ke, va in nd.items():
                        if ke != self._atr:
                            if isinstance(va, str):
                                nd[ke] = {self._v: nv}
                                return
                            else:
                                if len(va) == 0 or (va.get(self._atr) and not va.get(self._v) and len(va) == 1):
                                    va.update({self._v: nv})
                                    return

                            set_value(va, nv)

            # def set_key_value(nd, nk, nv):
            #     if isinstance(nd, dict):
            #         for ke, va in nd.items():
            #             if ke != self._atr:
            #                 if ke == nk:
            #                     nd[ke] = nv
            #                     return
            #                 set_key_value(va, nk, nv)

            def get_key_value(nd):
                if isinstance(nd, dict):
                    for ke, va in nd.items():
                        if ke != self._atr:
                            if isinstance(va, str):
                                yield nd
                            for z in get_key_value(va):
                                yield z

            vlst = []
            for k, v in self._record.items():
                if isinstance(v, dict):
                    # Dict
                    mpdic = v.get(self._schema_name)
                    # List or string
                    atr_v = v.get('attribute_value')
                    # List of dict
                    atr_vm = v.get('attribute_value_mlt')
                    if atr_v:
                        set_value(mpdic, atr_v)
                        vlst.append(mpdic)
                    elif atr_vm:
                        if isinstance(mpdic, dict):
                            for lst in atr_vm:
                                if isinstance(lst, dict):
                                    for ky, vl in mpdic.items():
                                        vlc = copy.deepcopy(vl)
                                        for z in get_key_value(vlc):
                                            # if vl have expression or formula
                                            exp, lk = analysis(z.get(self._v))
                                            ava = ""
                                            for val in lk:
                                                ava = ava + exp + lst.get(val)
                                            z[self._v] = ava[1:]

                                        vlst.append({ky: vlc})

            return vlst

        def check_node(node):
            if isinstance(node, dict):
                if node.get(self._v):
                    return True
                else:
                    for ve in node.values():
                        if check_node(ve):
                            return True

        def get_prefix(str):
            if "{" in str:
                return str
            pre = str.split(":")
            if len(pre) > 1:
                if ns.get(pre[0]):
                    pre = str.replace(pre[0] + ":", "{" + ns.get(pre[0]) + "}")
                else:
                    return pre[1]
            else:
                pre = str
            return pre

        def set_children(kname, node, tree):
            if isinstance(node, dict):
                val = node.get(self._v)
                if val:
                    atr = node.get(self._atr)
                    for lst in val:
                        index = val.index(lst)
                        chld = etree.Element(kname, None, ns)
                        chld.text = lst
                        if atr and len(atr) > index:
                            for k2, v2 in atr[index].items():
                                chld.set(get_prefix(k2), v2)
                        tree.append(chld)
                else:
                    if check_node(node):
                        chld = etree.Element(kname, None, ns)
                        # @ attributes only
                        atr = node.get(self._atr)
                        if atr:
                            for k2, v2 in atr.items():
                                chld.set(get_prefix(k2), v2)

                        tree.append(chld)

                        for k1, v1 in node.items():
                            if k1 != self._atr:
                                k1 = get_prefix(k1)
                                set_children(k1, v1, chld)

        if not self._schema_obj:
            E = ElementMaker()
            root = E.Weko()
            root.text = "Sorry! This Item has not been mappinged."
            return root

        node_tree = self.find_nodes(get_value_list())
        ns = self._schema_obj.model.namespaces
        if not ns.get("xml"):
            ns.update({"xml": "http://www.w3.org/XML/1998/namespace"})
        rootname = self._schema_obj.get('root_name')
        if ":" in rootname:
            rootname = rootname.split(":")[-1]
            E = ElementMaker(namespace=ns.pop(""), nsmap=ns)
        else:
            namespace = ns.pop("")
            ns.update({None: namespace})
            E = ElementMaker(namespace=namespace, nsmap=ns)
        # Create root element
        root = E(rootname)

        # Create sub element
        for k, v in node_tree.items():
            # print(k)
            # if "rightsHolder" in k:
            k = get_prefix(k)
            set_children(k, v, root)

        return root

    def to_list(self):
        """Get a elementName List
        :param xsd: schema dict
        """
        elst = []
        klst = []

        def get_element(str):
            return str.split(":")[-1] if ":" in str else str

        def get_key_list(nodes):
            # if no child
            if len(nodes.keys()) == 1:
                str = ""
                for lst in klst:
                    str = str + "." + get_element(lst)
                elst.append(str[1:])

                klst.pop(-1)
                return

            for k, v in nodes.items():
                if k != "type" and isinstance(v, dict):
                    klst.append(k)
                    get_key_list(v)

            if len(klst) > 0:
                klst.pop(-1)

        get_key_list(self._schema_obj.model.xsd)

        return elst

    def get_node(self, dc, key=None):
        """
        Create generator for get node
        :param dc:
        :param key:
        :return: node
        """

        if key:
            yield key

        if isinstance(dc, dict):
            for k, v in dc.items():
                for x in self.get_node(v, k):
                    yield x

    def find_nodes(self, mlst):
        """"""
        def get_generator(nlst):
            gdc.clear()

            for lst in mlst:
                if isinstance(lst, dict):
                    gdc['g' + str(mlst.index(lst))] = items_node(lst, nlst)
            return gdc

        def del_type(nid):
            if isinstance(nid, dict):
                if nid.get("type"):
                    nid.pop("type")
                for v in nid.values():
                    del_type(v)

        def cut_pre(str):
            return str.split(':')[-1] if ':' in str else str

        def items_node(nid, nlst, index=0):
            if len(nlst) > index:
                if isinstance(nid, dict):
                    for k3, v3 in nid.items():
                        if len(nlst) > index:
                            if cut_pre(k3) == nlst[index]:
                                index = index + 1
                                yield v3
                                for x in items_node(v3, nlst, index):
                                    yield x

        gdc = OrderedDict()
        vlst = []
        alst = []
        ndic = copy.deepcopy(self._schema_obj.model.xsd)
        # delete type dict
        del_type(ndic)
        tlst = self.to_list()

        for path in tlst:
            path = path.split(".")
            get_generator(path)
            # root node generator
            for node in items_node(ndic, path):
                for k in gdc.keys():
                    try:
                        gp = gdc[k]
                        if not isinstance(gp, str):
                            d = next(gp)

                            val = d.get(self._v)
                            atr = d.get(self._atr)
                            if len(node) == 0:
                                if val:
                                    vlst.append(val)
                                if atr:
                                    alst.append(atr)
                            else:
                                if not node.get(self._atr) and atr:
                                    node.update(OrderedDict({self._atr: atr}))
                    except StopIteration:
                        gdc[k] = ""

                if len(vlst) > 0:
                    odd = OrderedDict()
                    odd[self._v] = vlst.copy()
                    if len(alst) > 0:
                        odd[self._atr] = alst.copy()
                    node.update(odd)
                    vlst.clear()
                    alst.clear()
        return ndic

