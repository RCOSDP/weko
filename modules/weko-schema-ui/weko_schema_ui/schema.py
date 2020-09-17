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

import copy
import json
from collections import Iterable, OrderedDict
from functools import partial

import redis
import xmlschema
from flask import abort, current_app, request, url_for
from lxml import etree
from lxml.builder import ElementMaker
from simplekv.memory.redisstore import RedisStore
from weko_records.api import Mapping
from xmlschema.validators import XsdAnyAttribute, XsdAnyElement, \
    XsdAtomicBuiltin, XsdAtomicRestriction, XsdAttribute, \
    XsdEnumerationFacet, XsdGroup, XsdPatternsFacet, XsdSingleFacet, \
    XsdUnion

from .api import WekoSchema


class SchemaConverter:
    """SchemaConverter."""

    def __init__(self, schemafile, rootname):
        """Init."""
        if schemafile is None:
            abort(400, "Error creating Schema: Invalid schema file used")
        if not rootname:
            abort(400, "Error creating Schema: Invalid root name used")

        self.rootname = rootname
        self.schema, self.namespaces, self.target_namespace = \
            self.create_schema(schemafile)

    def to_dict(self):
        """To_dict."""
        return json.dumps(self.schema)

    def create_schema(self, schema_file):
        """Create_schema."""
        def getXSVal(element_name):  # replace prefix namespace
            if (element_name is not None
                and isinstance(element_name, Iterable)
                    and "}" in element_name):
                for k, nsp in schema_data.namespaces.items():
                    if nsp in element_name:
                        if k == "":
                            k = self.rootname.split(
                                ":")[
                                -1] if ":" in self.rootname else self.rootname
                        return element_name.replace("{" + nsp + "}",
                                                    k + ":")
            return element_name

        def get_element_type(type):
            typd = OrderedDict()
            if isinstance(type, XsdAtomicRestriction):
                rstr = typd['restriction'] = OrderedDict()
                for va in type.validators:
                    if isinstance(va, XsdEnumerationFacet):
                        rstr.update(OrderedDict(enumeration=va.enumeration))
                    if isinstance(va, XsdSingleFacet):
                        sf = OrderedDict()
                        vn = va.elem.tag.split(
                            '}')[-1] if "}" in va.elem.tag else va.elem.tag
                        sf[vn] = va.value
                        rstr.update(sf)

                if isinstance(type.patterns, XsdPatternsFacet):
                    plst = []
                    for pat in type.patterns.patterns:
                        plst.append(pat.pattern)
                    rstr.update(OrderedDict(patterns=plst))
            elif isinstance(type, XsdAtomicBuiltin):
                pass
            elif isinstance(type, XsdAnyAttribute):
                pass
            elif isinstance(type, XsdUnion):
                for mt in type.member_types:
                    typd.update(get_element_type(mt))
            elif isinstance(type, XsdGroup):
                pass
            else:
                atrlst = []
                if hasattr(type, 'attributes'):
                    for atrb in type.attributes._attribute_group.values():
                        attrd = OrderedDict(
                            name=getXSVal(
                                atrb.name),
                            ref=None if not hasattr(atrb, 'ref') else atrb.ref,
                            use=None if not hasattr(atrb, 'use') else atrb.use)
                        if is_get_only_target_namespace and \
                                attrd.get('name', None) == 'xml-lang':
                            continue
                        if not isinstance(atrb, XsdAnyAttribute):
                            if 'lang' not in atrb.name:
                                attrd.update(get_element_type(atrb.type))
                            atrlst.append(attrd)
                if len(atrlst):
                    typd['attributes'] = atrlst
                if hasattr(type, 'content_type'):
                    typd.update(get_element_type(type.content_type))
                pass

            return typd

        def is_valid_element(element_name):
            is_valid = True
            if is_get_only_target_namespace:
                if str(element_name).find(tagns) != -1:
                    is_valid = True
                else:
                    is_valid = False
            return is_valid

        def get_elements(element):
            chdsm = OrderedDict()
            for chd in element.iterchildren():
                if (chd not in ignore_list
                    and not getXSVal(element.name).__eq__(getXSVal(chd.name))
                    and is_valid_element(chd.name)
                        and not isinstance(chd, XsdAnyElement)):
                    ctp = OrderedDict()
                    chn = getXSVal(chd.name)
                    ctp["type"] = OrderedDict(
                        minOccurs=chd.min_occurs,
                        maxOccurs=chd.max_occurs if chd.max_occurs
                        else 'unbounded')
                    ctp["type"].update(get_element_type(chd.type))
                    chdsm[chn] = ctp
                    chdsm[chn].update(get_elements(chd))

            return chdsm

        # get elements as below
        try:
            schema_file = open(schema_file, encoding='utf-8')
            schema_data = xmlschema.XMLSchema(schema_file)
        except Exception as ex:
            current_app.logger.error(ex)
            abort(
                400, "Error creating Schema: "
                     "Can not open xsd file. Please check it!")

        # namespace
        nsp, tagns = schema_data.target_prefix, schema_data.target_namespace
        # root node name is got by target namespace and expected root name
        root_node_name = '{' + tagns + '}' + self.rootname
        # Important note:
        # this variable is used for ddi_codeBook schema
        # because we just get elements of target namespace(ddi:codebook) only
        # when you import new schema and want to get elements of specific target
        # namespace,please modify this variable to be suitable for your purpose
        is_get_only_target_namespace = True if tagns.__contains__(
            'ddi:codebook') else False
        # create the xsd json schema
        schema = OrderedDict()

        try:
            # get all elements
            elements = schema_data.findall('*')
            # ignore some attribute that is not necessary at present usage
            ignore_list = []
            # find and ignore unused elements
            for Xsd_global_group in schema_data.groups:
                for global_element in schema_data.groups[Xsd_global_group]:
                    ignore_list.append(global_element)

        except Exception as ex:
            current_app.logger.error(str(ex))
            abort(400, "Error creating Schema: Can not find element")
        else:
            if len(elements) > 0:
                for ems in elements:
                    if ems.name.__eq__(root_node_name):
                        for chd in ems.iterchildren():
                            ename = getXSVal(chd.name)
                            tp = OrderedDict()
                            tp["type"] = OrderedDict(
                                minOccurs=chd.min_occurs,
                                maxOccurs=chd.max_occurs if chd.max_occurs
                                else 'unbounded')
                            tp["type"].update(get_element_type(chd.type))
                            schema[ename] = tp
                            schema[ename].update(get_elements(chd))
            else:
                abort(400, "Error creating Schema: No xsd element")
        return schema, schema_data.namespaces, nsp


class SchemaTree:
    """Schematree."""

    def __init__(self, record=None, schema_name=None):
        """
        Init.

        :param record: item metadata
        :param schema_name: schema name

        """
        self._record = record["metadata"] \
            if record and record.get("metadata") else None
        self._schema_name = schema_name if schema_name else None
        if self._record:
            self._root_name, self._ns, self._schema_obj, self._item_type_id = \
                self.get_mapping_data()
        self._v = "@value"
        self._atr = "@attributes"
        self._atr_lang = "xml:lang"
        self._special_lang = 'ja-Kana'
        self._special_lang_default = 'ja'
        # nodes need be be separated to multiple nodes by language
        self._separate_nodes = None
        self._location = ''
        self._target_namespace = ''
        schemas = WekoSchema.get_all()
        if self._record and self._item_type_id:
            self._ignore_list_all, self._ignore_list = \
                self.get_ignore_item_from_option()
        for schema in schemas:
            if self._schema_name == schema.schema_name:
                self._location = schema.schema_location
                self._target_namespace = schema.target_namespace

    def get_ignore_item_from_option(self):
        """Get all keys of properties that is enable Hide option in metadata."""
        ignore_list_parents = []
        ignore_list_all = []
        ignore_dict_all = {}
        from weko_records.utils import get_options_and_order_list
        ignore_list_all, meta_options = \
            get_options_and_order_list(self._item_type_id)
        for key, val in meta_options.items():
            hidden = val.get('option').get('hidden')
            if hidden:
                ignore_list_parents.append(key)
        for element_info in ignore_list_all:
            element_info[0] = element_info[0].replace("[]", "")
            # only get hide option
            ignore_dict_all[element_info[0]] = element_info[3].get("hide")
        return ignore_dict_all, ignore_list_parents

    def get_mapping_data(self):
        """
         Get mapping info and return  schema and schema's root name namespace.

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
                self.item_type_mapping = mjson
                mp = mjson.dumps()
                if mjson:
                    for k, v in self._record.items():
                        if isinstance(v, dict) and mp.get(k) and k != "_oai":
                            v.update({self._schema_name: mp.get(
                                k).get(self._schema_name)})
                return id

        # inject mappings info to record
        item_type_id = get_mapping()
        return rec.get('root_name'), rec.get('namespaces'), rec.get(
            'schema'), item_type_id

    def __converter(self, node):
        description_type = "descriptionType"
        _need_to_nested = ('subjectScheme', 'dateType', 'identifierType',
                           'objectType', description_type)

        def list_reduce(olst):
            if isinstance(olst, list):
                for lst in olst:
                    if isinstance(lst, str):
                        yield lst
                    else:
                        for x in list_reduce(lst):
                            yield x

        def get_attr(x):
            return x.split(':')[-1]

        def create_json(name, node1, node2):
            return {name: node1, "value": node2}

        def _check_description_type(_attr, _alst):
            """Check description type.

            :param _attr: attribute value.
            :param _alst: attribute type list.
            :return: True if the description type has value.
            """
            is_valid = True
            _attr_type = _alst[0]
            if _attr_type == description_type\
                    and len(list(list_reduce([_attr.get(_attr_type)]))) == 0:
                is_valid = False
            return is_valid

        def json_reduce(node):
            if isinstance(node, dict):
                val = node.get(self._v)
                attr = node.get(self._atr)
                if val:
                    alst = list(
                        filter(
                            lambda x: get_attr(x) in _need_to_nested,
                            attr.keys())) if attr else []
                    if attr and alst and _check_description_type(attr, alst):
                        return list(map(partial(
                            create_json, get_attr(alst[0])),
                            list_reduce([attr.get(alst[0])]),
                            list(list_reduce(val)))
                        )

                    return list(list_reduce(val))
                else:
                    for k, v in node.items():
                        if k != self._atr:
                            node[k] = json_reduce(v)
                    return node

        json_reduce(node)
        return node

    @classmethod
    def get_jpcoar_json(cls, records, schema_name="jpcoar_mapping"):
        """
        Find elements values and return a jpcoar json.

        :param records:
        :param schema_name: default set jpcoar_mapping
        :return: json

        """
        obj = cls(schema_name=schema_name)
        obj._record = records
        obj._ignore_list = []
        obj._ignore_list_all = []
        vlst = list(map(obj.__converter,
                        filter(lambda x: isinstance(x, dict),
                               obj.__get_value_list())))

        from .utils import json_merge_all
        return json_merge_all(vlst)

    def __get_value_list(self, remove_empty=False):
        """Find values to a list."""
        def analysis(field):
            exp = (',',)
            return exp[0], field.split(exp[0])

        def set_value(nd, nv):
            if isinstance(nd, dict):
                for ke, va in nd.items():
                    if ke != self._atr:
                        if isinstance(va, str):
                            nd[ke] = {self._v: nv}
                            return
                        else:
                            if len(va) == 0 or \
                                (va.get(self._atr)
                                 and not va.get(self._v) and len(va) == 1):
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

        def get_value_from_content_by_mapping_key(atr_vm, list_key):
            # In case has more than 1 key
            # for ex:"subitem_1551257025236.subitem_1551257043769"
            if isinstance(list_key, list) and len(list_key) > 1:
                key = list_key.pop(0)
                if isinstance(atr_vm, dict) and atr_vm.get(key):
                    for a, b in get_value_from_content_by_mapping_key(
                            atr_vm.get(key), list_key):
                        yield a, b
                elif isinstance(atr_vm, list):
                    for i in atr_vm:
                        if i.get(key):
                            for a, b in get_value_from_content_by_mapping_key(
                                    i.get(key), list_key):
                                yield a, b
            elif isinstance(list_key, list) and len(list_key) == 1:
                try:
                    key = list_key[0]
                    if isinstance(atr_vm, dict):
                        if atr_vm.get(key) is None:
                            yield None, id(key)
                        else:
                            yield atr_vm[key], id(key)
                    elif isinstance(atr_vm, list):
                        for i in atr_vm:
                            if i.get(key) is None:
                                yield None, id(key)
                            else:
                                yield i[key], id(key)
                except Exception:
                    import traceback
                    traceback.print_exc()

        def get_url(z, key, val):
            # If related to file, process, otherwise return row value
            if key and 'filemeta' in key:
                attr = z.get(self._atr, {})
                attr = attr.get(
                    'jpcoar:objectType', '') or attr.get(
                    'objectType', '')
                if 'fulltext' in attr:
                    pid = self._record.get('control_number')
                    if pid:
                        return request.host_url[:-1] + url_for(
                            'invenio_records_ui.recid_files', pid_value=pid,
                            filename=val)
                    else:
                        return val
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

        def get_items_value_lst(atr_vm, key, rlst, z=None, kn=None):
            klst = []
            blst = []
            parent_id = 0
            list_subitem_key = []
            if '.' in key:
                list_subitem_key = key.split('.')
            else:
                list_subitem_key.append(key)
            for value, identify in get_value_from_content_by_mapping_key(
                    atr_vm.copy(), list_subitem_key):
                if parent_id != identify and parent_id != 0:
                    klst.append(blst)
                    blst = []
                rlst.append(value)
                # something related to FILE
                blst.append(get_url(z, kn, value))
                parent_id = identify
            if blst:
                klst.append(blst)
            return klst

        def analyze_value_with_exp(nlst, exp):
            """Get many value with exp """
            is_next = True
            glst = []
            for lst in nlst:
                glst.append(get_exp_value(lst))
            mlst = []
            vst = []
            while is_next:
                ctp = ()
                cnt = 0
                ava = ""
                for g in glst:
                    try:
                        eval, p = next(g)
                        ctp += (len(p),)
                        ava = ava + exp + eval
                    except StopIteration:
                        cnt += 1

                if cnt == len(glst):
                    is_next = False
                    mlst.append(vst)
                else:
                    if ava:
                        if exp in ava:
                            ava_arr = ava.split(exp)
                            for av in ava_arr:
                                if av:
                                    vst.append(av)
                        else:
                            vst.append(ava[1:])
            return mlst

        def get_atr_value_lst(node, atr_vm, rlst):
            for k1, v1 in node.items():
                # if 'item' not in v1:
                #     continue
                if isinstance(v1, str):
                    exp, lk = analysis(v1)
                    if len(lk) == 1:
                        klst = get_items_value_lst(atr_vm, v1, rlst)
                        if klst:
                            node[k1] = klst
                    elif len(lk) > 1:
                        nlst = []
                        for val in lk:
                            klst = get_items_value_lst(atr_vm, val, rlst)
                            if klst:
                                nlst.append(klst)
                        node[k1] = analyze_value_with_exp(nlst, exp)

        def get_mapping_value(mpdic, atr_vm, k, atr_name):
            remain_keys = []

            def remove_empty_tag(mp):
                if isinstance(mp, str) and (not mp or mp not in remain_keys):
                    return True
                elif isinstance(mp, dict):
                    remove_list = []
                    for it in mp:
                        if remove_empty_tag(mp[it]):
                            remove_list.append(it)
                    for it in remove_list:
                        mp.pop(it)
                elif isinstance(mp, list):
                    for it in mp:
                        if remove_empty_tag(it):
                            mp.remove(it)
                return False

            def get_type_item(item_type_mapping, atr_name):
                type_item = None
                if atr_name == 'contributor':
                    type_item = 'contributorType'
                elif atr_name == 'relation':
                    type_item = 'relationType'
                for k, v in self.item_type_mapping.items():
                    jpcoar = v.get("jpcoar_mapping")
                    if isinstance(jpcoar, dict):
                        if atr_name in jpcoar.keys():
                            value = jpcoar[atr_name]
                            if '@attributes' in value.keys():
                                attr = value['@attributes']
                                if type_item in attr:
                                    return attr[type_item]

            def get_item_by_type(temporary, type_item):
                """Get Contributor and Relation by Type."""
                key_level_1 = None
                key_level_2 = None
                key_level_3 = None
                if type_item == "Distributor":
                    key_level_1 = 'citation'
                    key_level_2 = 'distStmt'
                    key_level_3 = 'distrbtr'
                elif type_item == 'Other':
                    key_level_1 = 'citation'
                    key_level_2 = 'distStmt'
                    key_level_3 = 'depositr'
                elif type_item == "DataCollector":
                    key_level_1 = 'method'
                    key_level_2 = 'dataColl'
                    key_level_3 = 'dataCollector'
                elif type_item == 'isReferencedBy':
                    key_level_1 = 'othrStdyMat'
                    key_level_2 = 'relPubl'
                elif type_item == 'isSupplementedBy':
                    key_level_1 = 'othrStdyMat'
                    key_level_2 = 'relStdy'
                elif type_item == 'isPartOf':
                    key_level_1 = 'citation'
                    key_level_2 = 'serStmt'
                    key_level_3 = 'serName'

                if isinstance(temporary, dict):
                    if key_level_3:
                        for k, v in temporary.items():
                            if k == key_level_1:
                                value_of_stdydscr = {k: v}
                                if key_level_3 in \
                                    value_of_stdydscr[key_level_1][
                                        key_level_2].keys():
                                    value_of_stdydscr[key_level_1][
                                        key_level_2] = {
                                        key_level_3:
                                            value_of_stdydscr[key_level_1][
                                                key_level_2][key_level_3]}
                                    temporary = value_of_stdydscr
                                    return temporary
                    else:
                        for k, v in temporary.items():
                            if k == key_level_1:
                                value_of_stdydscr = {k: v}
                                if key_level_2 in value_of_stdydscr[
                                        key_level_1].keys():
                                    value_of_stdydscr[key_level_1] = {
                                        key_level_2:
                                            value_of_stdydscr[key_level_1][
                                                key_level_2]}
                                    temporary = value_of_stdydscr
                                    return temporary

            def handle_type_ddi(atr_name, list_type, vlst):
                key_item_type = get_type_item(
                    self.item_type_mapping, atr_name.lower())
                if key_item_type in atr_vm.keys():
                    item_type = atr_vm[key_item_type]
                    if item_type in list_type:
                        vlst[0]['stdyDscr'] = get_item_by_type(
                            vlst[0]['stdyDscr'], item_type)
                    else:
                        vlst[0]['stdyDscr'] = {}
                else:
                    vlst[0]['stdyDscr'] = {}
                return vlst[0]['stdyDscr']

            def clean_none_value(dct):
                clean = {}
                for k, v in dct.items():
                    if isinstance(v, dict):
                        # check if @value has value
                        ddi_schema = self._schema_name == current_app.config[
                            'WEKO_SCHEMA_DDI_SCHEMA_NAME']
                        node_val = v.get(self._v, None)
                        node_att = v.get(self._atr, None)
                        if isinstance(node_val, list) and node_val[0]:
                            # get index of None value
                            lst_none_idx = [idx for idx, val in
                                            enumerate(node_val[0]) if
                                            val is None or val == '']
                            if not ddi_schema:
                                if len(lst_none_idx) > 0:
                                    # delete all None element in @value
                                    lst_val_idx = list(set(
                                        range(len(node_val[0])))
                                        - set(lst_none_idx))
                                    node_val[0] = [val for idx, val in
                                                   enumerate(node_val[0])
                                                   if idx in lst_val_idx]
                                    # delete all None element in all
                                    # @attributes
                                    for key, val in v.get(self._atr,
                                                          {}).items():
                                        val[0] = [val for idx, val
                                                  in enumerate(val[0])
                                                  if idx in lst_val_idx]
                            else:
                                if not v.get(self._atr, {}).items():
                                    lst_val_idx = \
                                        list(set(range(len(node_val[0])))
                                             - set(lst_none_idx))
                                    node_val[0] = [v for idx, v
                                                   in enumerate(node_val[0])
                                                   if idx in lst_val_idx]
                            clean[k] = v
                        elif ddi_schema and not node_val and node_att and \
                                node_att[next(iter(node_att))][0]:
                            # Add len(node_att) None elements to value
                            # in order to display att later
                            v[self._v] = [[None] * len(
                                node_att[next(iter(node_att))][0])]
                            clean[k] = v
                        else:
                            nested = clean_none_value(v)
                            if len(nested.keys()) > 0:
                                clean[k] = nested
                return clean

            vlst = []
            for ky, vl in mpdic.items():
                vlc = copy.deepcopy(vl)
                for node_result, node_result_key in get_key_value(vlc):
                    if node_result_key == self._atr:
                        get_atr_value_lst(node_result, atr_vm, remain_keys)
                    else:
                        if not node_result.get(self._v):
                            continue

                        # check expression or formula
                        # exp = ,
                        # lk = subitem_1551255702686
                        exp, lk = analysis(node_result.get(self._v))
                        # if not have expression or formula
                        if len(lk) == 1:
                            nlst = get_items_value_lst(
                                atr_vm.copy(), lk[0].strip(), remain_keys,
                                node_result, k)
                            if nlst:
                                # [['Update PDF 3']]
                                node_result[self._v] = nlst
                            else:
                                continue
                        else:
                            nlst = []
                            for val in lk:
                                klst = get_items_value_lst(
                                    atr_vm, val.strip(), remain_keys,
                                    node_result, k)
                                nlst.append(klst)

                            if nlst:
                                node_result[self._v] = analyze_value_with_exp(nlst, exp)
                if remove_empty:
                    remove_empty_tag(vlc)
                vlst.append({ky: vlc})

            for vlist_item in vlst:
                attr_of_parent_item = {}
                for k, v in vlist_item.items():
                    # get attribute of parent Node if any
                    if self._atr in v:
                        attr_of_parent_item = {self._atr: v[self._atr]}
                # remove None value
                # for ddi_mapping, we need to keep attribute data
                # even if value data is None
                vlist_item = clean_none_value(vlist_item)

                if vlist_item:
                    for k, v in vlist_item.items():
                        if attr_of_parent_item:
                            v.update(attr_of_parent_item)

                if isinstance(atr_vm, dict) and isinstance(vlist_item, list) \
                        and 'stdyDscr' in vlist_item.keys():
                    if atr_name == 'Contributor':
                        list_contributor_type = ['Distributor', 'Other',
                                                 'DataCollector']
                        vlist_item['stdyDscr'] = handle_type_ddi(
                            atr_name,
                            list_contributor_type,
                            vlist_item
                        )
                    elif atr_name == 'Relation':
                        list_relation_type = ['isReferencedBy',
                                              'isSupplementedBy',
                                              'isPartOf']
                        vlist_item['stdyDscr'] = handle_type_ddi(
                            atr_name,
                            list_relation_type,
                            vlist_item)
            return vlst

        def remove_hide_data(obj, parentkey):
            """Remove all item that is set as hide."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if self._ignore_list_all.get(parentkey + "." + k, None):
                        obj[k] = None
                    elif isinstance(v, dict):
                        remove_hide_data(v, parentkey + "." + k)
                    elif isinstance(v, list):
                        for i in v:
                            remove_hide_data(i, parentkey + "." + k)

        vlst = []
        for key_item_parent, value_item_parent in self._record.items():
            if key_item_parent != 'pubdate' and isinstance(value_item_parent,
                                                           dict):
                # Dict
                # get value of the combination between record and \
                # mapping data that is inited at __init__ function
                mpdic = value_item_parent.get(
                    self._schema_name) \
                    if self._schema_name in value_item_parent else ''
                if mpdic is "" or (
                    self._ignore_list and key_item_parent
                        in self._ignore_list):
                    continue
                # List or string
                atr_v = value_item_parent.get('attribute_value')
                # List of dict
                atr_vm = value_item_parent.get('attribute_value_mlt')
                # attr of name
                atr_name = value_item_parent.get('attribute_name')
                if atr_v:
                    if isinstance(atr_v, list):
                        atr_v = [atr_v]
                    elif isinstance(atr_v, str):
                        atr_v = [[atr_v]]
                    set_value(mpdic, atr_v)
                    vlst.append(mpdic)
                elif atr_vm and atr_name:
                    if isinstance(atr_vm, list) and isinstance(mpdic, dict):
                        for atr_vm_item in atr_vm:
                            if self._ignore_list_all:
                                remove_hide_data(atr_vm_item, key_item_parent)
                            vlst_child = get_mapping_value(mpdic, atr_vm_item,
                                                           key_item_parent,
                                                           atr_name)
                            if vlst_child[0]:
                                vlst.extend(vlst_child)
        return vlst

    def create_xml(self):
        """
        Create schema xml tree.

        :return:

        """
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

        def set_children(kname, node, tree, parent_keys,
                         current_lang=None, index=0):
            if kname == 'type':
                return
            current_separate_key_node = None
            if self._separate_nodes:
                for separate_node_key in self._separate_nodes.keys():
                    if separate_node_key.split('.') == parent_keys:
                        current_separate_key_node = separate_node_key
            # current lang is None means current node(or its parents)
            # no need to be separated
            if current_separate_key_node and current_lang:
                existed_attr = node.get(self._atr, None)
                if not existed_attr:
                    existed_attr = {}
                    node.update({self._atr: existed_attr})
                att_lang = {self._atr_lang: [[current_lang]]}
                existed_attr.update(att_lang)
                node.update(existed_attr)
            if current_lang is None and current_separate_key_node:
                for lang in self._separate_nodes.get(
                        current_separate_key_node):
                    set_children(kname, node, tree, parent_keys, lang)
            else:
                if isinstance(node, dict):
                    val = node.get(self._v)
                    node_type = node.get('type')
                    mandatory = True if node_type.get(
                        'minOccurs') == 1 else False
                    repeatable = False if node_type.get(
                        'maxOccurs') == 1 else True
                    # the last children level
                    if val:
                        if node.get(self._atr):
                            atr = get_atr_list(node.get(self._atr))
                            for altt in atr:
                                if altt:
                                    # atr = get_atr_list(atr[index])
                                    atrt = get_atr_list(altt)
                                    clone_val, clone_atr = recorrect_node(
                                        val[index],
                                        atrt,
                                        current_lang,
                                        mandatory,
                                        repeatable)
                                    for i in range(len(clone_val)):
                                        chld = etree.Element(kname, None, ns)
                                        chld.text = clone_val[i]
                                        if len(clone_atr) > i:
                                            for k2, v2 in clone_atr[i].items():
                                                if v2 is None:
                                                    continue
                                                chld.set(get_prefix(k2), v2)
                                        tree.append(chld)
                                    index += 1
                        else:
                            for i in range(len(val[index])):
                                chld = etree.Element(kname, None, ns)
                                chld.text = val[index][i]
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
                                        if v2 is None:
                                            continue
                                        chld.set(get_prefix(k2), v2)

                                    for k1, v1 in node.items():
                                        if k1 != self._atr:
                                            k1 = get_prefix(k1)
                                            clone_lst = parent_keys.copy()
                                            clone_lst.append(k1)
                                            set_children(k1, v1, chld,
                                                         clone_lst,
                                                         current_lang, i)
                            else:
                                nodes = [node]
                                if bool(node) and not [i for i in node.values()
                                                       if
                                                       i and (not i.get
                                                              (self._v)
                                                              or not i.get(
                                                                  self._atr))]:
                                    multi = max(
                                        [len(attr) for n in node.values()
                                         if n and n.get(self._atr)
                                         and isinstance(n.get(self._atr), dict)
                                         for attr
                                         in n.get(self._atr).values()])
                                    if int(multi) > 1:
                                        multi_nodes = [copy.deepcopy(node)
                                                       for _ in
                                                       range(int(multi))]
                                        for idx, item in enumerate(
                                                multi_nodes):
                                            for nd in item.values():
                                                nd[self._v] = \
                                                    [nd[self._v][idx]]
                                                for key in nd.get(self._atr):
                                                    nd.get(self._atr)[key] = [
                                                        nd.get(self._atr)[key][
                                                            idx]]
                                        nodes = multi_nodes
                                for val in nodes:
                                    child = etree.Element(kname, None, ns)
                                    tree.append(child)

                                    for k1, v1 in val.items():
                                        if k1 != self._atr:
                                            k1 = get_prefix(k1)
                                            clone_lst = parent_keys.copy()
                                            clone_lst.append(k1)
                                            set_children(k1, v1, child,
                                                         clone_lst,
                                                         current_lang)

        def recorrect_node(val, attr, current_lang, mandatory=True,
                           repeatable=False):
            if not current_lang:
                return val, attr
            val_result = []
            att_result = []

            remove_lst = []
            none_lst = []
            current_lst = []
            for i in range(len(val)):
                att_lang = self._atr_lang in attr[i].keys()
                if att_lang and attr[i].get(
                    self._atr_lang) and attr[i].get(
                    self._atr_lang) == self._special_lang and \
                        current_lang == self._special_lang_default:
                    current_lst.append(i)
                elif att_lang and attr[i].get(
                    self._atr_lang) and attr[i].get(
                        self._atr_lang) != current_lang:
                    remove_lst.append(i)
                elif att_lang and attr[
                        i].get(self._atr_lang) is None:
                    none_lst.append(i)
                else:
                    current_lst.append(i)

            # Remove all diff
            for i in range(len(val)):
                if i not in remove_lst:
                    val_result.append(val[i])
                    att_result.append(attr[i])

            # Get the first one of others
            if mandatory and len(val) - len(remove_lst) == 0:
                val_result = [val[0]]
                att_result = [attr[0]]

            if not repeatable:
                len_current_list = len(val) - len(remove_lst) - len(none_lst)
                # Get the first one of current
                if len_current_list > 1:
                    val_result = [val[current_lst[0]]]
                    att_result = [attr[current_lst[0]]]
                elif len_current_list == 0:
                    if len(none_lst) > 0:
                        val_result = [val[none_lst[0]]]
                        att_result = [attr[none_lst[0]]]
                    else:
                        val_result = [val[remove_lst[0]]]
                        att_result = [attr[remove_lst[0]]]

            return val_result, att_result

        def merge_json_xml(json, dct):
            if isinstance(json, dict):
                for k, v in json.items():
                    if k in dct:
                        merge_json_xml(json[k], dct[k])
                    else:
                        dct[k] = json[k]
            elif isinstance(json, list):
                for i in json:
                    if isinstance(i, list):
                        dct[0] += i
                    else:
                        merge_json_xml(i, dct)

        # Function Remove custom scheme
        def remove_custom_scheme(name_identifier, v,
                                 lst_name_identifier_default):
            if '@attributes' in name_identifier and \
                    name_identifier['@attributes'].get('nameIdentifierScheme'):
                element_first = 0
                lst_name_identifier_scheme = name_identifier[
                    '@attributes']['nameIdentifierScheme'][element_first]
                lst_value = []
                if '@value' in name_identifier:
                    lst_value = name_identifier['@value'][element_first]
                if name_identifier['@attributes'].\
                        get("nameIdentifierURI", None):
                    lst_name_identifier_uri = name_identifier[
                        '@attributes']['nameIdentifierURI'][element_first]
                index_remove_items = []
                total_remove_items = len(lst_name_identifier_scheme)
                for identifior_item in lst_name_identifier_scheme:
                    if identifior_item not in lst_name_identifier_default:
                        index_remove_items.extend([
                            lst_name_identifier_scheme.index(identifior_item)])
                if len(index_remove_items) == total_remove_items:
                    del v['jpcoar:nameIdentifier']
                    if 'jpcoar:affiliation' in v:
                        del v['jpcoar:affiliation']
                else:
                    for index in index_remove_items[::-1]:
                        lst_name_identifier_scheme.pop(index)
                        if len(lst_value) == total_remove_items:
                            lst_value.pop(index)
                            total_remove_items = total_remove_items - 1
                        if lst_name_identifier_uri:
                            lst_name_identifier_uri.pop(index)

        if not self._schema_obj:
            E = ElementMaker()
            root = E.Weko()
            root.text = "Sorry! This Item has not been mappinged."
            return root

        list_json_xml = self.__get_value_list(remove_empty=True)
        if self._schema_name == current_app.config[
                'WEKO_SCHEMA_DDI_SCHEMA_NAME']:
            dct_xml = dict()
            list_dict = list()
            for json_child in list_json_xml:
                merge_json_xml(json_child, dct_xml)
            list_dict.append(dct_xml)
            list_json_xml = list_dict
            self._separate_nodes = {'stdyDscr.citation': set(),
                                    'stdyDscr.stdyInfo': set(),
                                    'stdyDscr.method': set(),
                                    'stdyDscr.dataAccs': set(),
                                    'stdyDscr.othrStdyMat': set()}
        node_tree = self.find_nodes(list_json_xml)
        ns = self._ns
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        ns.update({'xml': "http://www.w3.org/XML/1998/namespace"})
        ns.update({'xsi': xsi})
        rootname = self._root_name
        if ":" in rootname:
            rootname = rootname.split(":")[-1]
        ns.update({None: ns.pop('')})
        if not self._target_namespace:
            self._target_namespace = None
        E = ElementMaker(namespace=ns[self._target_namespace], nsmap=ns)
        # Create root element
        root = E(rootname)
        root.attrib['{{{pre}}}schemaLocation'.format(pre=xsi)] = self._location

        # Create sub element
        indetifier_keys = ['jpcoar:creator', 'jpcoar:contributor',
                           'jpcoar:rightsHolder']
        affiliation_key = 'jpcoar:affiliation'
        name_identifier_key = 'jpcoar:nameIdentifier'
        # Remove all None languages and check special case
        if self._separate_nodes:
            for key, val in self._separate_nodes.items():
                if self._special_lang in val:
                    if self._special_lang_default not in val:
                        val.add(self._special_lang_default)
                    val.remove(self._special_lang)
                if None in val:
                    val.remove(None)
                # Just add an empty element in case there is no language
                if len(val) == 0:
                    val.add('')
        for lst in node_tree:
            for k, v in lst.items():
                # Remove items that are not set as controlled vocabulary
                if k in indetifier_keys:
                    lst_name_identifier_default = current_app.config[
                        'WEKO_SCHEMA_UI_LIST_SCHEME']
                    remove_custom_scheme(v[name_identifier_key], v,
                                         lst_name_identifier_default)
                    if affiliation_key in v:
                        lst_name_affiliation_default = current_app.config[
                            'WEKO_SCHEMA_UI_LIST_SCHEME_AFFILIATION']
                        remove_custom_scheme(
                            v[affiliation_key][name_identifier_key], v,
                            lst_name_affiliation_default)
                k = get_prefix(k)
                set_children(k, v, root, [k])
        return root

    def to_list(self):
        """Get a elementName List."""
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
        Create generator for get node.

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
        """Find_nodes."""
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
            klst = []
            plst = self.to_list()
            for i in range(len(plst)):
                if key in plst[i].split('.')[0]:
                    klst.append(plst[i])
            return klst

        gdc = OrderedDict()
        vlst = []
        alst = []
        ndic = copy.deepcopy(self._schema_obj)
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
                    current_separate_key = None
                    if self._separate_nodes:
                        for nodes_key, nodes_val in \
                                self._separate_nodes.items():
                            if kst.startswith(nodes_key):
                                current_separate_key = nodes_key
                                break
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
                                        if self._atr_lang in atr.keys() \
                                            and current_separate_key and \
                                                atr.get(self._atr_lang)[0]:
                                            self._separate_nodes.get(
                                                current_separate_key).update(
                                                atr.get(self._atr_lang)[0])
                                        for k1, v1 in atr.items():
                                            if isinstance(v1, str):
                                                atr[k1] = [[v1]]
                                        node.update({self._atr: atr})
                        except StopIteration:
                            pass
                nlst.append({k: nv})
        return nlst
        # end


def cache_schema(schema_name, delete=False):
    """
    Cache the schema to Redis.

    :param schema_name:
    :return:

    """
    def get_schema():
        try:
            rec = WekoSchema.get_record_by_name(schema_name)
            if rec:
                dstore = dict()
                dstore['root_name'] = rec.get('root_name')
                dstore['target_namespace'] = rec.get('target_namespace')
                dstore['schema_location'] = rec.get('schema_location')
                dstore['namespaces'] = rec.model.namespaces.copy()
                dstore['schema'] = json.loads(
                    rec.model.xsd, object_pairs_hook=OrderedDict)
                rec.model.namespaces.clear()
                del rec
                return dstore
        except BaseException:
            return None

    try:
        # schema cached on Redis by schema name
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = current_app.config[
            'WEKO_SCHEMA_CACHE_PREFIX'].format(schema_name=schema_name)
        data_str = datastore.get(cache_key)
        data = json.loads(
            data_str.decode('utf-8'),
            object_pairs_hook=OrderedDict)
        if delete:
            datastore.delete(cache_key)
    except BaseException as ex:
        try:
            schema = get_schema()
            if schema:
                datastore.put(cache_key, json.dumps(schema))
        except BaseException:
            return get_schema()
        else:
            return schema
    return data


def delete_schema_cache(schema_name):
    """
    Delete schema cache on redis.

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
    except BaseException:
        pass


def schema_list_render(pid=None, **kwargs):
    """
    Return records for template.

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
    Delete schema by pid.

    :param pid:
    :return:

    """
    return WekoSchema.delete_by_id(pid)


def get_oai_metadata_formats(app):
    """Get oai metadata formats."""
    oad = app.config.get('OAISERVER_METADATA_FORMATS', {}).copy()
    if isinstance(oad, dict):
        try:
            obj = WekoSchema.get_all()
        except BaseException:
            pass
        else:
            if isinstance(obj, list):
                sel = list(oad.values())[0].get('serializer')
                for lst in obj:
                    if lst.schema_name.endswith('_mapping'):
                        schema_name = lst.schema_name[:-8]
                    if not oad.get(schema_name):
                        scm = dict()
                        if isinstance(lst.namespaces, dict):
                            ns = lst.namespaces.get(
                                '') or lst.namespaces.get(schema_name)
                            scm.update({'namespace': ns})
                        scm.update({'schema': lst.schema_location})
                        scm.update(
                            {'serializer': (
                                sel[0], {'schema_type': schema_name})})
                        oad.update({schema_name: scm})
                    else:
                        if isinstance(lst.namespaces, dict):
                            ns = lst.namespaces.get(
                                '') or lst.namespaces.get(schema_name)
                            if ns:
                                oad[schema_name]['namespace'] = ns
                        if lst.schema_location:
                            oad[schema_name]['schema'] = lst.schema_location
    return oad
