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
from redis import sentinel
import xmlschema
from flask import abort, current_app, request, url_for
from lxml import etree
from lxml.builder import ElementMaker
from simplekv.memory.redisstore import RedisStore
from weko_records.api import ItemLink, Mapping, ItemTypes
from weko_redis import RedisConnection
from xmlschema.validators import XsdAnyAttribute, XsdAnyElement, \
    XsdAtomicBuiltin, XsdAtomicRestriction, XsdEnumerationFacet, XsdGroup, \
    XsdPatternsFacet, XsdSingleFacet, XsdUnion

from .api import WekoSchema
from .models import OAIServerSchema


class SchemaConverter:
    """SchemaConverter."""

    def __init__(self, schemafile, rootname):
        """Init."""
        if schemafile is None:
            abort(400, "Error creating Schema: Invalid schema file used")
        if not rootname:
            abort(400, "Error creating Schema: Invalid root name used")

        # current_app.logger.error("schemafile:{}".format(schemafile))
        # current_app.logger.error("rootname:{}".format(rootname))

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
            version_type = current_app.config['WEKO_SCHEMA_VERSION_TYPE']
            if element_name == version_type['original']:
                element_name = version_type['modified']
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
            elif isinstance(type, XsdAtomicBuiltin) or \
                isinstance(type, XsdAnyAttribute) or \
                    isinstance(type, XsdGroup):
                return typd
            elif isinstance(type, XsdUnion):
                for mt in type.member_types:
                    typd.update(get_element_type(mt))
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
        # current_app.logger.debug("record: {0}".format(record))
        # record: {'links': {}, 'updated': '2021-12-04T11:56:48.821270+00:00', 'created': '2021-12-04T11:56:36.873504+00:00', 'metadata': {'_oai': {'id': 'oai:weko3.example.org:00000003', 'sets': ['1638615863439']}, 'path': ['1638615863439'], 'owner': '1', 'recid': '3', 'title': ['dd'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-12-01'}, '_buckets': {'deposit': 'f60ad379-930c-4808-aee9-3454c707c2ed'}, '_deposit': {'id': '3', 'pid': {'type': 'depid', 'value': '3', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'dd', 'author_link': [], 'item_type_id': '15', 'publish_date': '2021-12-01', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'dd', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/3', 'subitem_systemidt_identifier_type': 'URI'}]}}}}, 'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/3', 'subitem_systemidt_identifier_type': 'URI'}]}}}
        # current_app.logger.debug("schema_name: {0}".format(schema_name))
        # schema_name: jpcoar_mapping
        
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
        self._aff = "jpcoar:affiliation"
        # nodes need be be separated to multiple nodes by language
        self._separate_nodes = None
        self._location = ''
        self._target_namespace = ''
        schemas = WekoSchema.get_all()
        self._item_type = None
        if self._record and self._item_type_id:
            self._ignore_list_all, self._ignore_list = \
                self.get_ignore_item_from_option()
            self._item_type = ItemTypes.get_by_id(self._item_type_id)
        if isinstance(schemas, list):
            for schema in schemas:
                if isinstance(schema, OAIServerSchema) and self._schema_name == schema.schema_name:
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
        if isinstance(meta_options, dict):
            for key, val in meta_options.items():
                hidden = val.get('option', {}).get('hidden', False)
                if hidden:
                    ignore_list_parents.append(key)
        for element_info in ignore_list_all:
            if len(element_info) >= 4:
                element_info[0] = element_info[0].replace("[]", "")
                # only get hide option
                ignore_dict_all[element_info[0]] = element_info[3].get("hide", False)
        return ignore_dict_all, ignore_list_parents

    def get_mapping_data(self):
        """
         Get mapping info and return  schema and schema's root name namespace.

        :return: root name, namespace and schema

        """
        # Get Schema info
        rec = cache_schema(self._schema_name)

        if not rec:
            return None, None, None, None

        def get_mapping():

            if isinstance(self._record, dict):
                _id = self._record.pop("item_type_id")
                self._record.pop("_buckets", {})
                self._record.pop("_deposit", {})
                mjson = Mapping.get_record(_id)
                self.item_type_mapping = mjson
                if isinstance(mjson, Mapping):
                    mp = mjson.dumps()
                    if isinstance(mp, dict):
                        for k, v in mp.items():
                            if k in self._record:
                                self._record[k].update({self._schema_name: v.get(self._schema_name)})
                            else:
                                self._record[k] = {self._schema_name: v.get(self._schema_name)}
                return _id


        # inject mappings info to record
        item_type_id = get_mapping()
        return rec.get('root_name'), rec.get('namespaces'), rec.get(
            'schema'), item_type_id

    def __converter(self, node):
        description_type = "descriptionType"
        _need_to_nested = ('subjectScheme', 'dateType', 'identifierType',
                           'objectType', description_type)
        _need_to_nested_key = ('subject', 'date', 'identifier', 'relatedIdentifier'
                               'identifierRegistration', 'sourceIdentifier', 'URI')
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
            # current_app.logger.debug("_attr:{0}".format(_attr))
            # current_app.logger.debug("_alst:{0}".format(_alst))
            is_valid = True
            _attr_type = _alst[0]
            if _attr_type == description_type\
                    and len(list(list_reduce([_attr.get(_attr_type)]))) == 0:
                is_valid = False
            return is_valid

        def json_reduce(node, field=None):
            if isinstance(node, dict):
                val = node.get(self._v)
                attr = node.get(self._atr)
                if val:
                    alst = list(
                        filter(
                            lambda x: get_attr(x) in _need_to_nested,
                            attr.keys())) if attr else []
                    if attr and alst and _check_description_type(attr, alst):
                        _partial = partial(create_json, get_attr(alst[0]))
                        list_val = list(list_reduce(val))
                        list_attr = list(list_reduce([attr.get(alst[0])]))
                        if list_val and list_attr:
                            return list(map(_partial, list_attr, list_val))
                        else:
                            if list_val:
                                return list(map(
                                    lambda x: {'value': x}, list_val))
                            elif list_attr:
                                return list(map(
                                    lambda x: {get_attr(alst[0]): x},
                                    list_attr))
                            else:
                                return []
                    elif field in _need_to_nested_key:
                        return list(map(lambda x: {"value": x}, list(list_reduce(val))))
                    return list(list_reduce(val))
                else:
                    for k, v in node.items():
                        if k != self._atr:
                            node[k] = json_reduce(v, field=k)
                    return node

        json_reduce(node)
        return node

    @classmethod
    def get_jpcoar_json(cls, records, schema_name="jpcoar_mapping", replace_field=True):
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
                               obj.__get_value_list(replace_field=replace_field))))

        from .utils import json_merge_all
        return json_merge_all(vlst)

    def __get_value_list(self, remove_empty=False, replace_field=True):
        """Find values to a list."""
        def analysis(field):
            exp = (',',)
            return exp[0], field.split(exp[0])

        def set_value(nd, nv):
            """
            set_value [summary]

            [extended_summary]

            Args:
                nd ([type]): [description]
                nv ([type]): [description]
            """
            # current_app.logger.debug("nd: {0}".format(nd))
            # nd: {'date': {'@value': '=hogehoge', '@attributes': {'dateType': '=hoge'}}}
            # current_app.logger.debug("nv: {0}".format(nv))
            # nv: [['2021-12-01']]
            if isinstance(nd, dict):
                for ke, va in nd.items():
                    # current_app.logger.debug("ke:{0}".format(ke))
                    # ke:@value
                    # current_app.logger.debug("va:{0}".format(va))
                    # va:=hogehoge
                    if ke != self._atr:
                        if isinstance(va, str):
                            nd[ke] = nv if ke == self._v else {self._v: nv}
                            # current_app.logger.debug(
                            #     "self._v:{0}".format(self._v))
                            # self._v:@value
                            # current_app.logger.debug("nv:{0}".format(nv))
                            # nv:[['2021-12-01']]
                            # current_app.logger.debug("ke:{0}".format(ke))
                            # ke:@value
                            # current_app.logger.debug("nd:{0}".format(nd))
                            # nd:{'@value': [['2021-12-01']], '@attributes': {'dateType': '=hoge'}}
                            return
                        else:
                            if len(va) == 0 or \
                                (va.get(self._atr)
                                 and not va.get(self._v) and len(va) == 1):
                                # current_app.logger.debug(
                                #     "self._v".format(self._v))
                                # current_app.logger.debug("nv".format(nv))
                                va.update({self._v: nv})
                                return

                        set_value(va, nv)

        # def get_sub_item_value(atr_vm, key, p=None):
        #     # current_app.logger.debug("atr_vm:{0}".format(atr_vm))
        #     # current_app.logger.debug("key:{0}".format(key))
        #     # current_app.logger.debug("p:{0}".format(p))
        #     if isinstance(atr_vm, dict):
        #         for ke, va in atr_vm.items():
        #             if key == ke:
        #                 yield va, id(p)
        #             else:
        #                 for z, w in get_sub_item_value(va, key, atr_vm):
        #                     yield z, w
        #     elif isinstance(atr_vm, list):
        #         for n in atr_vm:
        #             for k, x in get_sub_item_value(n, key, atr_vm):
        #                 yield k, x

        def get_value_from_content_by_mapping_key(atr_vm, list_key):
            # current_app.logger.debug("atr_vm: {0}".format(atr_vm))
            #atr_vm: {'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}
            #atr_vm: {'subitem_1551255647225': 'dd', 'subitem_1551255648112': 'ja'}
            #atr_vm: {'subitem_1551255647225': 'dd', 'subitem_1551255648112': 'ja'}
            #atr_vm: {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            # current_app.logger.debug("list_key:{0}".format(list_key))
            # list_key:['subitem_systemidt_identifier']
            # list_key:['=dddddd']
            # list_key:['=ddd']
            # list_key:['resourcetype']

            # In case has more than 1 key
            # for ex:"subitem_1551257025236.subitem_1551257043769"
            if isinstance(list_key, list) and len(list_key) > 1:
                key = list_key.pop(0)
                if isinstance(atr_vm, dict):
                    if atr_vm.get(key):
                        for a, b in get_value_from_content_by_mapping_key(
                                atr_vm.get(key), list_key):
                            yield a, b
                    else:
                        if list_key[-1].startswith("="):
                            yield list_key[-1][1:], id(list_key[-1])
                elif isinstance(atr_vm, list):
                    if key not in set([x for atr_ in atr_vm for x in list(atr_.keys())]):
                        if list_key[-1].startswith("="):
                            yield list_key[-1][1:], id(list_key[-1])
                    else:
                        for i in atr_vm:
                            if isinstance(i, dict) and i.get(key):
                                for a, b in get_value_from_content_by_mapping_key(
                                        i.get(key), list_key):
                                    yield a, b
            elif isinstance(list_key, list) and len(list_key) == 1:
                try:
                    key = list_key[0]
                    if key.startswith("="):
                        # mapping by fixed value
                        # current_app.logger.debug(
                        #     "key[1:] :{0}".format(key[1:]))
                        # current_app.logger.debug(
                        #     "id(key) :{0}".format(id(key)))
                        yield key[1:], id(key)
                    elif isinstance(atr_vm, dict):
                        if atr_vm.get(key) is None:
                            yield None, id(key)
                        else:
                            # In case of checkboxes, stored data will be
                            # [a,b,c]
                            if isinstance(atr_vm[key], list):
                                for i in atr_vm[key]:
                                    yield i, id(key)
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
            # current_app.logger.debug("z:{0}".format(z))
            # z:{'@value': 'resourcetype', '@attributes': {'rdf:resource': 'resourceuri'}}
            # current_app.logger.debug("key:{0}".format(key))
            # key:item_1617258105262
            # current_app.logger.debug("val:{0}".format(val))
            # val:conference paper
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
            # current_app.logger.debug("nd:{0}".format(nd))
            # nd:{'@value': '=dddddd', '@attributes': {'xml:lang': '=ddd'}}
            # current_app.logger.debug("key:{0}".format(key))
            # key:None
            if isinstance(nd, dict):
                for ke, va in nd.items():
                    if ke == self._v or isinstance(va, str):
                        yield nd, key
                    else:
                        for z, y in get_key_value(va, ke):
                            yield z, y

        def get_exp_value(atr_list):
            # current_app.logger.debug("atr_list:{0}".format(atr_list))
            if isinstance(atr_list, list):
                for lst in atr_list:
                    if isinstance(lst, list):
                        for x, y in get_exp_value(lst):
                            yield x, y
                    elif isinstance(lst, str):
                        yield lst, atr_list

        def get_items_value_lst(atr_vm, key, rlst, z=None, kn=None):
            # current_app.logger.debug("atr_vm:{0}".format(atr_vm))
            # atr_vm:{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            # current_app.logger.debug("key:{0}".format(key))
            # key:resourceuri
            # current_app.logger.debug("rlst:{0}".format(rlst))
            # rlst:['conference paper']
            # current_app.logger.debug("z:{0}".format(z))
            # z:None
            # current_app.logger.debug("kn:{0}".format(kn))
            # kn:None
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
                if list_subitem_key[-1] == 'licensetype':
                    # Convert license value to license code
                    for lic in current_app.config[
                            'WEKO_RECORDS_UI_LICENSE_DICT']:
                        if lic.get('value') == value:
                            value = lic.get('code')
                            break
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
            """Get many value with exp."""
            # current_app.logger.debug("nlst:{0}".format(nlst))
            # current_app.logger.debug("exp:{0}".format(exp))
            is_next = True
            glst = []
            for lst in nlst:
                glst.append(get_exp_value(lst))
            mlst = []
            vst = []
            exp = '\\' + exp
            while is_next:
                cnt = 0
                ava = ""
                for g in glst:
                    try:
                        _eval, _ = next(g)
                        ava = ava + exp + _eval
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
            # current_app.logger.debug("node:{0}".format(node))
            # node:{'rdf:resource': 'resourceuri'}
            # current_app.logger.debug('atr_vm:{0}'.format(atr_vm))
            # atr_vm:{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            # current_app.logger.debug('rlst:{0}'.format(rlst))
            # rlst:['conference paper']

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
            # current_app.logger.debug('mpdic:{0}'.format(mpdic))
            # mpdic:{'type': {'@value': 'resourcetype', '@attributes': {'rdf:resource': 'resourceuri'}}}
            # current_app.logger.debug('atr_vm:{0}'.format(atr_vm))
            # atr_vm:{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            # current_app.logger.debug('k:{0}'.format(k))
            # k:item_1617258105262
            # current_app.logger.debug('atr_name:{0}'.format(atr_name))
            # atr_name:Resource Type

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
                    jpcoar = v.get('jpcoar_mapping')
                    if isinstance(jpcoar, dict) and atr_name in jpcoar.keys():
                        value = jpcoar[atr_name]
                        if self._atr in value.keys():
                            attr = value[self._atr]
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
                        vlst['stdyDscr'] = get_item_by_type(
                            vlst['stdyDscr'], item_type)
                    else:
                        vlst['stdyDscr'] = {}
                else:
                    vlst['stdyDscr'] = {}
                return vlst['stdyDscr']

            def clean_none_value(dct):
                # current_app.logger.debug("dct:{0}".format(dct))
                # dct:{'type': {'@value': [['conference paper']], '@attributes': {'rdf:resource': [['http://purl.org/coar/resource_type/c_5794']]}}}
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
                                        if(type(val[0]) is not str):
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
                                node_result[self._v] = analyze_value_with_exp(
                                    nlst, exp)
                if remove_empty:
                    remove_empty_tag(vlc)
                vlst.append({ky: vlc})

            for vlist_item in vlst:
                attr_of_parent_item = {}
                for k, v in vlist_item.items():
                    # get attribute of parent Node if any
                    if v is not None and self._atr in v:
                        attr_of_parent_item = {self._atr: v[self._atr]}
                # remove None value
                # for ddi_mapping, we need to keep attribute data
                # even if value data is None
                vlist_item = clean_none_value(vlist_item)

                if vlist_item:
                    for k, v in vlist_item.items():
                        if attr_of_parent_item:
                            v.update(attr_of_parent_item)

                if isinstance(atr_vm, dict) and isinstance(vlist_item, dict) \
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
            # current_app.logger.debug("obj:{0}".format(obj))
            # obj:{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            # current_app.logger.debug("parentkey:{0}".format(parentkey))
            # parentkey:item_1617258105262

            if isinstance(obj, dict):
                for k, v in obj.items():
                    if self._ignore_list_all.get(parentkey + "." + k, None):
                        obj[k] = None
                    elif isinstance(v, dict):
                        remove_hide_data(v, parentkey + "." + k)
                    elif isinstance(v, list):
                        for i in v:
                            remove_hide_data(i, parentkey + "." + k)

        def replace_resource_type_for_jpcoar_v1(atr_vm_item):
            # current_app.logger.debug('atr_vm_item:{0}'.format(atr_vm_item))
            # atr_vm_item:{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            if 'resourcetype' in atr_vm_item and \
                    'resourceuri' in atr_vm_item and \
                    atr_vm_item['resourcetype'] in current_app.config[
                        'WEKO_SCHEMA_JPCOAR_V1_RESOURCE_TYPE_REPLACE']:
                new_type = current_app.config[
                    'WEKO_SCHEMA_JPCOAR_V1_RESOURCE_TYPE_REPLACE'][atr_vm_item['resourcetype']]
                atr_vm_item['resourcetype'] = new_type
                atr_vm_item['resourceuri'] = current_app.config[
                    'RESOURCE_TYPE_URI'][new_type]

        def replace_resource_type_for_jpcoar_v2(atr_vm_item):
            # current_app.logger.debug('atr_vm_item:{0}'.format(atr_vm_item))
            # atr_vm_item:{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}
            if 'resourcetype' in atr_vm_item and \
                    'resourceuri' in atr_vm_item and \
                    atr_vm_item['resourcetype'] in current_app.config[
                        'WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE']:
                new_type = current_app.config[
                    'WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE'][atr_vm_item['resourcetype']]
                atr_vm_item['resourcetype'] = new_type
                atr_vm_item['resourceuri'] = current_app.config[
                    'RESOURCE_TYPE_URI'][new_type]

        def replace_nameIdentifierScheme_for_jpcoar_v1(atr_vm_item):
            if 'nameIdentifiers' in atr_vm_item and atr_vm_item['nameIdentifiers'] is not None:
                for idx,val in enumerate(atr_vm_item['nameIdentifiers']):
                    if 'nameIdentifierScheme' in val and val['nameIdentifierScheme'] in current_app.config['WEKO_SCHEMA_JPCOAR_V1_NAMEIDSCHEME_REPLACE']:
                        new_type = current_app.config[
                        'WEKO_SCHEMA_JPCOAR_V1_NAMEIDSCHEME_REPLACE'][val['nameIdentifierScheme']]
                        val['nameIdentifierScheme'] = new_type

        def replace_nameIdentifierScheme_for_jpcoar_v2(atr_vm_item):
            if 'nameIdentifiers' in atr_vm_item and atr_vm_item['nameIdentifiers'] is not None:
                for idx,val in enumerate(atr_vm_item['nameIdentifiers']):
                    if 'nameIdentifier' in val and val['nameIdentifier'] in current_app.config['WEKO_SCHEMA_JPCOAR_V2_NAMEIDSCHEME_REPLACE']:
                        new_type = current_app.config[
                        'WEKO_SCHEMA_JPCOAR_V2_NAMEIDSCHEME_REPLACE'][val['nameIdentifier']]
                        val['nameIdentifier'] = new_type
                    
                

        vlst = []
             
        for key_item_parent, value_item_parent in sorted(self._record.items()):
            if isinstance(value_item_parent, dict):
                # Dict
                # get value of the combination between record and \
                # mapping data that is inited at __init__ function
                mpdic = value_item_parent.get(
                    self._schema_name) \
                    if self._schema_name in value_item_parent else ''
                if mpdic == "" or (
                    self._ignore_list and key_item_parent
                        in self._ignore_list):
                    continue
                # List or string
                atr_v = value_item_parent.get('attribute_value')
                # List of dict
                atr_vm = value_item_parent.get('attribute_value_mlt',[])
                # attr of name
                atr_name = value_item_parent.get('attribute_name')

                if atr_v:
                    if isinstance(atr_v, list):
                        atr_v = [atr_v]
                    elif isinstance(atr_v, str):
                        atr_v = [[atr_v]]
                    set_value(mpdic, atr_v)
                    # current_app.logger.debug("mpdic:{0}".format(mpdic))
                    vlst.append(mpdic)
                elif isinstance(atr_vm, list) and isinstance(mpdic, dict):
                    if len(atr_vm) > 0:
                        for atr_vm_item in atr_vm:
                            if self._ignore_list_all:
                                remove_hide_data(atr_vm_item, key_item_parent)
                            if self._schema_name == current_app.config[
                                    'WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME'] and replace_field:
                                replace_resource_type_for_jpcoar_v1(atr_vm_item)
                                replace_nameIdentifierScheme_for_jpcoar_v1(atr_vm_item)
                            if self._schema_name == current_app.config[
                                    'WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME'] and replace_field:
                                replace_resource_type_for_jpcoar_v2(atr_vm_item)
                                replace_nameIdentifierScheme_for_jpcoar_v2(atr_vm_item)
                            vlst_child = get_mapping_value(mpdic, atr_vm_item,
                                                           key_item_parent,
                                                           atr_name)
                            if vlst_child and vlst_child[0]:
                                vlst.extend(vlst_child)
                    else:
                        # current_app.logger.error(item_type.schema["properties"][key_item_parent])
                        atr_name = ""
                        if self._item_type and self._item_type.schema:
                            if "properties" in self._item_type.schema:
                                if key_item_parent in self._item_type.schema.get("properties"):
                                    if "title" in  self._item_type.schema.get("properties").get(key_item_parent):
                                        atr_name = self._item_type.schema["properties"][key_item_parent]["title"]
                        vlst_child = get_mapping_value(mpdic, {},
                                                           key_item_parent,
                                                           atr_name)
                        if vlst_child and vlst_child[0]:
                            vlst.extend(vlst_child)
        return vlst

    def create_xml(self):
        """
        Create schema xml tree.

        :return:

        """
        jpcoar_affname = 'jpcoar:affiliationName'
        jpcoar_nameidt = 'jpcoar:nameIdentifier'

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
            """
            get_atr_list [summary]

            [extended_summary]

            Args:
                node ([type]): [description]

            Returns:
                [type]: [description]
            """
            # current_app.logger.debug("node:{0}".format(node))
            # node:{'dateType': [['=hoge']]}
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
                        if isinstance(v, list) and len(v) > i:
                            # current_app.logger.debug("k:{0}".format(k))
                            # current_app.logger.debug("v[i]:{0}".format(v[i]))
                            if isinstance(v[i], str):
                                if (v[i]).startswith("="):
                                    v[i] = (v[i]).replace("=", "")
                            attr.update({k: v[i]})
                    nlst.append(attr)

            return nlst

        def set_children(kname, node, tree, parent_keys,
                         current_lang=None, index=0,
                         creator_idx=-1, contributor_idx=-1):
            """Set childrent xml.

            Args:
                kname ([type]): [description]
                node ([type]): [description]
                tree ([type]): [description]
                parent_keys ([type]): [description]
                current_lang ([type], optional): [description].
                    Defaults to None.
                index (int, optional): [description]. Defaults to 0.
                creator_idx (int, optional): [description]. Defaults to -1.
                contributor_idx (int, optional): [description]. Defaults to -1.
            """
            # current_app.logger.debug("kname:{0}".format(kname))
            # kname:{https://schema.datacite.org/meta/kernel-4/}date
            # current_app.logger.debug("node:{0}".format(node))
            # node:OrderedDict([('type', OrderedDict([('maxOccurs', 'unbounded'), ('minOccurs', 0), ('attributes', [OrderedDict([('use', 'required'), ('name', 'dateType'), ('ref', None), ('restriction', OrderedDict([('enumeration', ['Accepted', 'Available', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid'])]))])])])), ('@value', [['2021-12-01']]), ('@attributes', {'dateType': [['=hoge']]})])
            # current_app.logger.debug("tree:{0}".format(tree))
            # tree:<Element {https://github.com/JPCOAR/schema/blob/master/1.0/}jpcoar at 0x7f1e63203dc8>
            # current_app.logger.debug("parent_keys:{0}".format(parent_keys))
            # parent_keys:['{https://schema.datacite.org/meta/kernel-4/}date']
            # current_app.logger.debug("current_lang:{0}".format(current_lang))
            # current_lang:None
            # current_app.logger.debug("index:{0}".format(index))
            # index:0
            # current_app.logger.debug("creator_idx:{0}".format(creator_idx))
            # creator_idx:-1
            # current_app.logger.debug(
            #     "contributor_idx:{0}".format(contributor_idx))
            # contributor_idx:-1

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

                                    # Check affiliation node
                                    if node.get(self._aff):
                                        if creator_idx >= 0:
                                            numbs_child = count_aff_childs(
                                                'creator', creator_idx)
                                        elif contributor_idx >= 0:
                                            numbs_child = count_aff_childs(
                                                'contributor', contributor_idx)
                                        else:
                                            numbs_child = []

                                        for k1, v1 in node.items():
                                            if k1 != self._atr:
                                                # Handle affiliation node
                                                if k1 == self._aff \
                                                        and numbs_child:
                                                    create_affiliation(
                                                        numbs_child, k1, v1,
                                                        chld, parent_keys,
                                                        current_lang)
                                                else:
                                                    k1 = get_prefix(k1)
                                                    clone_lst = \
                                                        parent_keys.copy()
                                                    clone_lst.append(k1)
                                                    set_children(k1, v1, chld,
                                                                 clone_lst,
                                                                 current_lang)
                                    else:
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

                                    # Check affiliation node
                                    if val.get(self._aff):
                                        if creator_idx >= 0:
                                            numbs_child = count_aff_childs(
                                                'creator', creator_idx)
                                        elif contributor_idx >= 0:
                                            numbs_child = count_aff_childs(
                                                'contributor', contributor_idx)
                                        else:
                                            numbs_child = []

                                        for k1, v1 in val.items():
                                            if k1 != self._atr:
                                                # Handle affiliation node
                                                if k1 == self._aff \
                                                        and numbs_child:
                                                    create_affiliation(
                                                        numbs_child, k1, v1,
                                                        child, parent_keys,
                                                        current_lang)
                                                else:
                                                    k1 = get_prefix(k1)
                                                    clone_lst = \
                                                        parent_keys.copy()
                                                    clone_lst.append(k1)
                                                    set_children(k1, v1, child,
                                                                 clone_lst,
                                                                 current_lang)
                                    else:
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
            # current_app.logger.debug("val:{0}".format(val))
            # val:['2021-12-01']
            # current_app.logger.debug("attr:{0}".format(attr))
            # attr:[OrderedDict([('dateType', '=hoge')])]
            # current_app.logger.debug("current_lang:{0}".format(current_lang))
            # current_lang:None
            # current_app.logger.debug("mandatory:{0}".format(mandatory))
            # mandatory:False
            # current_app.logger.debug("repeatable:{0}".format(repeatable))
            # repeatable:True

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
            if self._atr in name_identifier and \
                    name_identifier[self._atr].get('nameIdentifierScheme'):
                element_first = 0
                lst_name_identifier_scheme = name_identifier[
                    self._atr]['nameIdentifierScheme'][element_first]
                lst_value = []
                if self._v in name_identifier:
                    lst_value = name_identifier[self._v][element_first]
                if name_identifier[self._atr].\
                        get("nameIdentifierURI", None):
                    lst_name_identifier_uri = name_identifier[
                        self._atr]['nameIdentifierURI'][element_first]
                index_remove_items = []
                total_remove_items = len(lst_name_identifier_scheme)
                for identifior_item in lst_name_identifier_scheme:
                    if identifior_item not in lst_name_identifier_default:
                        index_remove_items.extend([
                            lst_name_identifier_scheme.index(identifior_item)])
                if len(index_remove_items) == total_remove_items:
                    if jpcoar_nameidt in v:
                        del v[jpcoar_nameidt]
                else:
                    for index in index_remove_items[::-1]:
                        lst_name_identifier_scheme.pop(index)
                        if len(lst_value) == total_remove_items:
                            lst_value.pop(index)
                            total_remove_items = total_remove_items - 1
                        if lst_name_identifier_uri and \
                                index < len(lst_name_identifier_uri):
                            lst_name_identifier_uri.pop(index)

        def count_aff_childs(key, creator_idx):
            """Count number of affiliationName and affiliationNameIdentifier.

            Returns:
                ret [type]: [description] Counter affiliation metadata.

            """
            ret = []
            _item_key = "creatorAffiliations"
            _name_keys = "affiliationNames"
            _name_key = "affiliationName"
            _idtf_keys = "affiliationNameIdentifiers"
            _idtf_key = "affiliationNameIdentifier"
            if key == "contributor":
                _item_key = "contributorAffiliations"
                _name_keys = "contributorAffiliationNames"
                _name_key = "contributorAffiliationName"
                _idtf_keys = "contributorAffiliationNameIdentifiers"
                _idtf_key = "contributorAffiliationNameIdentifier"

            for _item in self._record.values():
                if isinstance(_item, dict) and _item.get(self._schema_name) \
                        and _item.get(self._schema_name, {}).get(key):
                    if creator_idx >= len(_item.get("attribute_value_mlt", [])):
                        return None

                    aff_data = _item.get("attribute_value_mlt")[creator_idx]
                    if not aff_data or not aff_data.get(_item_key, None):
                        return None

                    for _subitem in aff_data.get(_item_key, []):
                        _len_affname = 0
                        _len_nameidt = 0
                        if _subitem.get(_name_keys):
                            for item in _subitem.get(_name_keys, []):
                                if item.get(_name_key):
                                    _len_affname += 1
                        if _subitem.get(_idtf_keys):
                            for item in _subitem.get(_idtf_keys, []):
                                if item.get(_idtf_key):
                                    _len_nameidt += 1

                        ret.append({
                            jpcoar_affname: _len_affname,
                            jpcoar_nameidt: _len_nameidt
                        })

            return ret

        def create_affiliation(numbs_child, k, v, child,
                               parent_keys, current_lang):
            """Seperate jpcoar:affiliation by metadata structure.

            Args:
                numbs_child ([type]): [description]
                k ([type]): [description]
                v ([type]): [description]
                child ([type]): [description]
                parent_keys ([type]): [description]
                current_lang ([type], optional): [description].
            """
            count_name = 0
            count_idtf = 0
            for _child in numbs_child:
                _value = copy.deepcopy(v)
                len_name = _child[jpcoar_affname]
                if len_name > 0:
                    _data = _value[jpcoar_affname][self._v][0]
                    _lang = None
                    if self._atr in _value[jpcoar_affname]:
                        _lang = _value[jpcoar_affname][self._atr].get(
                            "xml:lang", [])
                    _max_len_name = len(_data) \
                        if len(_data) < count_name + len_name \
                        else count_name + len_name
                    _value[jpcoar_affname][self._v][0] = _data[
                        count_name:_max_len_name]
                    if _lang and len(_lang) > 0:
                        _value[jpcoar_affname][self._atr]["xml:lang"][0] \
                            = _lang[0][count_name:_max_len_name]
                    count_name += _max_len_name
                else:
                    if _value[jpcoar_affname].get(self._v):
                        _value[jpcoar_affname][self._v] = [[]]

                len_idtf = _child[jpcoar_nameidt]
                if len_idtf > 0:
                    _data = _value[jpcoar_nameidt][self._v][0]
                    _schm = _value[jpcoar_nameidt][self._atr].get(
                        "nameIdentifierScheme", [])
                    _urli = _value[jpcoar_nameidt][self._atr].get(
                        "nameIdentifierURI", [])
                    _max_len_idtf = len(_data) \
                        if len(_data) < count_idtf + len_idtf \
                        else count_idtf + len_idtf
                    _value[jpcoar_nameidt][self._v][
                        0] = _data[count_idtf:_max_len_idtf]
                    if _schm:
                        _value[jpcoar_nameidt][self._atr][
                            "nameIdentifierScheme"][0] \
                            = _schm[0][count_idtf:_max_len_idtf]
                    if _urli:
                        _value[jpcoar_nameidt][self._atr][
                            "nameIdentifierURI"][0] \
                            = _urli[0][count_idtf:_max_len_idtf]
                    count_idtf += _max_len_idtf
                else:
                    if _value[jpcoar_nameidt].get(self._v):
                        _value[jpcoar_nameidt][self._v] = [[]]

                k1 = get_prefix(k)
                clone_lst = parent_keys.copy()
                clone_lst.append(k1)
                set_children(k1, _value, child,
                             clone_lst,
                             current_lang)

        if not self._schema_obj:
            E = ElementMaker()
            root = E.Weko()
            root.text = "Sorry! This Item has not been mappinged."
            return root
        self.support_for_output_xml(self._record)
        self.__remove_files_do_not_publish()
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
        else:
            self.__build_jpcoar_relation(list_json_xml)

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
        # Initial counter of creator and contributor node
        # Start counter from -1 to can use as index
        creator_idx = -1
        contributor_idx = -1
        for lst in node_tree:
            # Each creator/contributor node increasing by one
            if lst.get('jpcoar:creator'):
                creator_idx += 1
                contributor_idx = -1
            elif lst.get('jpcoar:contributor'):
                creator_idx = -1
                contributor_idx += 1
            else:
                creator_idx = -1
                contributor_idx = -1

            for k, v in lst.items():
                # Remove items that are not set as controlled vocabulary
                if k in indetifier_keys:
                    lst_name_identifier_default = current_app.config[
                        'WEKO_SCHEMA_UI_LIST_SCHEME']
                    remove_custom_scheme(v[jpcoar_nameidt], v,
                                         lst_name_identifier_default)
                    if self._aff in v:
                        lst_name_affiliation_default = current_app.config[
                            'WEKO_SCHEMA_UI_LIST_SCHEME_AFFILIATION']
                        remove_custom_scheme(
                            v[self._aff][jpcoar_nameidt], v,
                            lst_name_affiliation_default)
                k = get_prefix(k)
                set_children(k, v, root, [k], None, 0,
                             creator_idx, contributor_idx)
        return root

    def __remove_files_do_not_publish(self):
        """Remove files do not publish."""
        def __get_file_permissions(files_json):
            new_files = []
            for file in files_json:
                if 'open_no' not in file.get('accessrole', []):
                    new_files.append(file)
            return new_files

        for k, v in self._record.items():
            if (isinstance(v, dict)
                and v.get("attribute_type") == "file"
                    and v.get("attribute_value_mlt")):
                v['attribute_value_mlt'] = __get_file_permissions(
                    v.get("attribute_value_mlt"))

    def __build_jpcoar_relation(self, list_json_xml):
        """Build JPCOAR relation.

        :param list_json_xml:
        """
        def __build_relation(data):
            """Build relation.

            :param data:
            """
            relation_tmp = {
                "relation": {}
            }
            _relation = relation_tmp['relation']
            reference_type = data.get('reference_type')
            url = data.get('url')
            identifierType = data.get('identifierType')
            if reference_type in current_app.config[
                    'WEKO_SCHEMA_RELATION_TYPE']:
                _relation.update({
                    self._atr: {"relationType": [[reference_type]]}
                })
            if url and identifierType:
                _relation.update({
                    "relatedIdentifier": {
                        self._atr: {
                            "identifierType": identifierType
                        },
                        self._v: url
                    }
                })
            list_json_xml.append(relation_tmp.copy())

        item_links = ItemLink.get_item_link_info_output_xml(
            self._record.get("recid"))
        if isinstance(item_links, list):
            for item in item_links:
                __build_relation(item)

    def support_for_output_xml(self, data):
        """Support for output XML.

        :param data:
        """
        from weko_records.utils import remove_weko2_special_character
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = remove_weko2_special_character(v)
                else:
                    self.support_for_output_xml(v)
        elif isinstance(data, list):
            for i in range(len(data)):
                if isinstance(data[i], str):
                    data[i] = remove_weko2_special_character(data[i])
                else:
                    self.support_for_output_xml(data[i])

    def to_list(self):
        """Get a elementName List."""
        elst = []
        klst = []

        def get_element(str):
            return str.split(":")[-1] if ":" in str else str

        def get_key_list(nodes):
            # if no child
            if len(nodes.keys()) == 1:
                _str = ""
                for lst in klst:
                    _str = _str + "." + get_element(lst)
                elst.append(_str[1:])

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

    # def get_node(self, dc, key=None):
    #     """
    #     Create generator for get node.

    #     :param dc:
    #     :param key:
    #     :return: node

    #     """
    #     if key:
    #         yield key

    #     if isinstance(dc, dict):
    #         for k, v in dc.items():
    #             for x in self.get_node(v, k):
    #                 yield x

    def find_nodes(self, mlst):
        """Find_nodes."""
        # def del_type(nid):
        #     if isinstance(nid, dict):
        #         if nid.get("type"):
        #             nid.pop("type")
        #         for v in nid.values():
        #             del_type(v)

        def cut_pre(str):
            return str.split(':')[-1] if ':' in str else str

        def items_node(nid, nlst, index=0):
            if len(nlst) > index and isinstance(nid, dict):
                for k3, v3 in nid.items():
                    if len(nlst) > index and cut_pre(k3) == nlst[index]:
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

        ndic = copy.deepcopy(self._schema_obj)
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
                                if atr and isinstance(atr, dict):
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
                version_type = current_app.config['WEKO_SCHEMA_VERSION_TYPE']
                publisher_type = current_app.config['WEKO_SCHEMA_PUBLISHER_TYPE']
                date_type = current_app.config['WEKO_SCHEMA_DATE_TYPE']
                if k == version_type['modified']:
                    nlst.append({version_type['original']: nv})
                elif k == publisher_type['modified']:
                    nlst.append({publisher_type['original']: nv})
                elif k == date_type['modified']:
                    nlst.append({date_type['original']: nv})
                else:
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
                
                # why use clear()?
                rec.model.namespaces.clear()
                del rec
                
                return dstore
        except BaseException:
            return None

    try:
        # schema cached on Redis by schema name
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
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
                datastore.put(cache_key, json.dumps(schema).encode("utf-8"))
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
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
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
    if isinstance(lst, list):
        for r in lst:
            if isinstance(r, OAIServerSchema):
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
                    if not isinstance(lst, OAIServerSchema):
                        continue
                    if lst.schema_name and lst.schema_name.endswith('_mapping'):
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
