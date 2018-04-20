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

import redis
import xmlschema, json, copy

from lxml import etree
from lxml.builder import ElementMaker
from weko_records.api import Mapping
from .api import WekoSchema

from flask import abort, current_app, url_for, request
from collections import OrderedDict
from simplekv.memory.redisstore import RedisStore
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
        self._root_name, self._ns, self._schema_obj = self.get_mapping_data()
        self._v = "@value"
        self._atr = "@attributes"

    def get_mapping_data(self):
        """
         Get mapping info and return  schema and schema's root name namespace
        :return: root name, namespace and schema
        """
        # Get Schema info
        rec = cache_schema(self._schema_name)

        if not rec:
            return None, None, None

        def get_mapping():

            if isinstance(self._record, dict):
                id = self._record.pop("item_type_id")
                self._record.pop("_buckets", {})
                self._record.pop("_deposit", {})
                mjson = Mapping.get_record(id)
                mp = mjson.dumps()
                if mjson:
                    for k, v in self._record.items():
                        if isinstance(v, dict) and mp.get(k) and k != "_oai":
                            v.update({self._schema_name: mp.get(k).get(self._schema_name)})

        # inject mappings info to record
        get_mapping()
        return rec.get('root_name'), rec.get('namespaces'), rec.get('schema')

    def create_xml(self):
        """
        create schema xml tree
        :return:
        """
        def get_element(str):
            return str.split(":")[-1] if ":" in str else str

        def get_value_list():

            def analysis(field):
                exp = (',', )
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

            def get_sub_item_value(atr_vm, key, p=None):
                if isinstance(atr_vm, dict):
                    for ke, va in atr_vm.items():
                        if key == ke:
                            yield va, id(p)
                        else:
                            for z, w in get_sub_item_value(va, key, atr_vm):
                                yield z, w
                elif isinstance(atr_vm, list):
                    for n in atr_vm:
                        for k, x in get_sub_item_value(n, key, atr_vm):
                            yield k, x

            def get_url(z, key, val):
                if 'filemeta' in key:
                    attr = z.get(self._atr, {})
                    attr = attr.get('jpcoar:objectType', '') or attr.get('objectType', '')
                    if 'fulltext' in attr:
                        pid = self._record.get('control_number')
                        return request.host_url[:-1] + url_for('invenio_records_ui.recid_files',
                                                               pid_value=pid, filename=val)
                    else:
                        return val
                else:
                    return val

            def get_key_value(nd, key=None):
                if isinstance(nd, dict):
                    for ke, va in nd.items():
                        if ke == self._v or isinstance(va, str):
                            yield nd, key
                        else:
                            for z, y in get_key_value(va, ke):
                                yield z, y

            def get_exp_value(atr_list):
                if isinstance(atr_list, list):
                    for lst in atr_list:
                        if isinstance(lst, list):
                            for x, y in get_exp_value(lst):
                                yield x, y
                        elif isinstance(lst, str):
                            yield lst, atr_list

            def get_items_value_lst(atr_vm, key):
                klst = []
                blst = []
                parent_id = 0
                for k2, p2 in get_sub_item_value(atr_vm, key):
                    if parent_id != p2 and parent_id != 0:
                        klst.append(blst)
                        blst = []
                    blst.append(k2)
                    parent_id = p2
                if blst:
                    klst.append(blst)
                return klst

            def get_atr_value_lst(node, atr_vm):
                for k1, v1 in node.items():
                    if 'item' not in v1:
                        continue
                    klst = get_items_value_lst(atr_vm, v1)
                    if klst:
                        node[k1] = klst

            def get_mapping_value(mpdic, atr_vm, k):
                vlst = []
                for ky, vl in mpdic.items():
                    vlc = copy.deepcopy(vl)
                    for z, y in get_key_value(vlc):
                        # if it`s attributes node
                        if y == self._atr:
                            get_atr_value_lst(z, atr_vm)
                        else:
                            if not z.get(self._v):
                                continue

                            # check expression or formula
                            exp, lk = analysis(z.get(self._v))
                            # if not have expression or formula
                            if len(lk) == 1:
                                nlst = get_items_value_lst(atr_vm, lk[0].strip())
                                if nlst:
                                    z[self._v] = nlst
                            else:
                                nlst = []
                                for val in lk:
                                    klst = get_items_value_lst(atr_vm, val.strip())
                                    nlst.append(klst)

                                if nlst:
                                    ava = ""
                                    is_next = True
                                    glst = []
                                    for lst in nlst:
                                        glst.append(get_exp_value(lst))

                                    mlst = []
                                    vst = []
                                    mc = 0
                                    while is_next:
                                        ctp = ()
                                        cnt = 0
                                        ava = ""
                                        for g in glst:
                                            try:
                                                eval, p = next(g)
                                                ctp += (len(p), )
                                                ava = ava + exp + eval
                                            except StopIteration:
                                                cnt += 1

                                        if cnt == len(glst):
                                            is_next = False
                                            mlst.append(vst)
                                        else:
                                            mc = max(ctp)
                                            if ava:
                                                if len(vst) == mc:
                                                    mlst.append(vst)
                                                    vst = []
                                                vst.append(ava[1:])

                                    z[self._v] = mlst
                    vlst.append({ky: vlc})
                return vlst

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
                        if isinstance(atr_v, list):
                            atr_v = [atr_v]
                        elif isinstance(atr_v, str):
                            atr_v = [[atr_v]]
                        set_value(mpdic, atr_v)
                        vlst.append(mpdic)
                    elif atr_vm:
                        if isinstance(atr_vm, list) and isinstance(mpdic, dict):
                            for lst in atr_vm:
                                vlst.extend(get_mapping_value(mpdic, lst, k))
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

        def get_atr_list(node):
            nlst = []

            def get_max_count(node):
                if isinstance(node, dict):
                    cnt = ()
                    for k, v in node.items():
                        if isinstance(v, list):
                            cnt += (len(v),)
                    if cnt:
                        return max(cnt)
                    return 0

            if isinstance(node, dict):
                cnt = get_max_count(node)
                for i in range(cnt):
                    attr = OrderedDict()
                    for k, v in node.items():
                        if isinstance(v, list):
                            if len(v) > i:
                                attr.update({k: v[i]})
                    nlst.append(attr)

            return nlst

        def set_children(kname, node, tree, index=0):
            if isinstance(node, dict):
                val = node.get(self._v)
                # the last children level
                if val:
                    atr = get_atr_list(node.get(self._atr))
                    if atr:
                        atr = get_atr_list(atr[index])
                    for i in range(len(val[index])):
                        chld = etree.Element(kname, None, ns)
                        chld.text = val[index][i]
                        if len(atr) > i:
                            for k2, v2 in atr[i].items():
                                chld.set(get_prefix(k2), v2)
                        tree.append(chld)
                else:
                    # parents level
                    # if have any child
                    if check_node(node):
                        # @ attributes only
                        atr = get_atr_list(node.get(self._atr))
                        if atr:
                            atr = get_atr_list(atr[index])
                            for i, obj in enumerate(atr):
                                chld = etree.Element(kname, None, ns)
                                tree.append(chld)
                                for k2, v2 in obj.items():
                                    chld.set(get_prefix(k2), v2)

                                for k1, v1 in node.items():
                                    if k1 != self._atr:
                                        k1 = get_prefix(k1)
                                        set_children(k1, v1, chld, i)
                        else:
                            chld = etree.Element(kname, None, ns)
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
        ns = self._ns
        if not ns.get("xml"):
            ns.update({"xml": "http://www.w3.org/XML/1998/namespace"})
        rootname = self._root_name
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
        for lst in node_tree:
            for k, v in lst.items():
                # print(k)
                # if "rightsHolder" in k:
                k = get_prefix(k)
                set_children(k, v, root)

        return root

    def to_list(self):
        """Get a elementName List
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

        get_key_list(self._schema_obj)

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

        def get_node_dic(key):
            for lst in mlst:
                if isinstance(lst, dict):
                    value = lst.get(key)
                    if value:
                        yield value

        def get_path_list(key):
            klst =[]
            plst = self.to_list()
            for i in range(len(plst)):
                if key in plst[i].split('.')[0]:
                    klst.append(plst[i])
            return klst



        gdc = OrderedDict()
        vlst = []
        alst = []
        ndic = copy.deepcopy(self._schema_obj)
        # delete type dict
        del_type(ndic)
        tlst = self.to_list()

        # start
        # ---------------------------------------------------------------------------------------------------
        nlst = []
        for k, v in ndic.items():
            key = cut_pre(k)
            # get nested path list
            klst = get_path_list(key)
            # get mappinged list
            for x in get_node_dic(key):
                nv = copy.deepcopy(v)
                for kst in klst:
                    kst = kst.split(".")
                    gene = items_node({key: x}, kst)
                    # iter nested path(nodes)
                    for node in items_node({k: nv}, kst):
                        try:
                            d = next(gene)
                            if isinstance(d, dict):
                                val = d.get(self._v)
                                atr = d.get(self._atr)
                                # if it's the last node
                                if val:
                                    if isinstance(val, list):
                                        node.update({self._v: val})
                                    elif isinstance(val, str):
                                        node.update({self._v: [[val]]})
                                if atr:
                                    if isinstance(atr, dict):
                                        for k1, v1 in atr.items():
                                            if isinstance(v1, str):
                                                atr[k1] = [[v1]]
                                        node.update({self._atr: atr})
                        except StopIteration:
                            pass
                nlst.append({k: nv})
        return nlst
        # end
        # ---------------------------------------------------------------------------------------------------


def cache_schema(schema_name, delete=False):
    """
    cache the schema to Redis
    :param schema_name:
    :return:
    """

    def get_schema():
        rec = WekoSchema.get_record_by_name(schema_name)
        if rec:
            dstore = dict()
            dstore['root_name'] = rec.get('root_name')
            dstore['namespaces'] = rec.model.namespaces.copy()
            dstore['schema'] = json.loads(rec.model.xsd, object_pairs_hook=OrderedDict)
            rec.model.namespaces.clear()
            del rec
            return dstore

    try:
        # schema cached on Redis by schema name
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = current_app.config[
            'WEKO_SCHEMA_CACHE_PREFIX'].format(schema_name=schema_name)
        data_str = datastore.get(cache_key)
        data = json.loads(data_str.decode('utf-8'), object_pairs_hook=OrderedDict)
        if delete:
            datastore.delete(cache_key)
    except:
        try:
            schema = get_schema()
            if schema:
                datastore.put(cache_key, json.dumps(schema))
        except:
            return get_schema()
        else:
            return schema
    return data


def delete_schema_cache(schema_name):
    """
    delete schema cache on redis
    :param schema_name:
    :return:
    """
    try:
        # schema cached on Redis by schema name
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = current_app.config[
            'WEKO_SCHEMA_CACHE_PREFIX'].format(schema_name=schema_name)
        datastore.delete(cache_key)
    except:
        pass


def schema_list_render(pid=None, **kwargs):
    """
    return records for template
    :param pid:
    :param kwargs:
    :return: records
    """

    lst = WekoSchema.get_all()

    records = []
    for r in lst:
        sc = r.form_data.copy()
        sc.update(dict(schema_name=r.schema_name))
        sc.update(dict(pid=str(r.id)))
        sc.update(dict(dis="disabled" if r.isfixed else None))
        records.append(sc)

    del lst

    return records


def delete_schema(pid):
    """
    delete schema by pid
    :param pid:
    :return:
    """
    return WekoSchema.delete_by_id(pid)


def reset_oai_metadata_formats(app):
    """
    reset oaiserver metadata formats dict
    :return:
    """

    @app.before_first_request
    def set_metadata_formats():
        oad = app.config.get('OAISERVER_METADATA_FORMATS', {})
        if isinstance(oad, dict):
            try:
                obj = WekoSchema.get_all()
            except:
                pass
            else:
                if isinstance(obj, list):
                    sel = list(oad.values())[0].get('serializer')
                    for lst in obj:
                        schema_name = lst.schema_name.split('_')[0]
                        if not oad.get(schema_name):
                            scm = dict()
                            if isinstance(lst.namespaces, dict):
                                ns = lst.namespaces.get('') or lst.namespaces.get(schema_name)
                                scm.update({'namespace': ns})
                            scm.update({'schema': lst.schema_location})
                            scm.update({'serializer': (sel[0], {'schema_type': schema_name})})
                            oad.update({schema_name: scm})
                        else:
                            if isinstance(lst.namespaces, dict):
                                ns = lst.namespaces.get('') or lst.namespaces.get(schema_name)
                                if ns:
                                    oad[schema_name]['namespace'] = ns
                            if lst.schema_location:
                                oad[schema_name]['schema'] = lst.schema_location
