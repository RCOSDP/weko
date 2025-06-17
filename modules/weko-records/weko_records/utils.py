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

"""Item API."""
import copy
import pickle
import re
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict

import pytz
from flask import current_app
from flask_security import current_user
from invenio_i18n.ext import current_i18n
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.ext import pid_exists
from invenio_pidstore.models import PersistentIdentifier
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
from lxml import etree
from weko_admin import config as ad_config
from weko_admin.models import SearchManagement as sm
from weko_schema_ui.schema import SchemaTree

from .api import ItemTypes, Mapping
from .config import COPY_NEW_FIELD, WEKO_TEST_FIELD


def json_loader(data, pid, owner_id=None, with_deleted=False, replace_field=True):
    """Convert the item data and mapping to jpcoar.

    :param data: json from item form post.
    :param pid: pid value.
    :param owner_id: record owner.
    :return: dc, jrc, is_edit
    """

    def _get_author_link(author_link, value):
        """Get author link data."""
        if isinstance(value, list):
            for v in value:
                if (
                    "nameIdentifiers" in v
                    and len(v["nameIdentifiers"]) > 0
                    and "nameIdentifierScheme" in v["nameIdentifiers"][0]
                    and v["nameIdentifiers"][0]["nameIdentifierScheme"] == "WEKO"
                ):
                    author_link.append(v["nameIdentifiers"][0]["nameIdentifier"])
        elif (
            isinstance(value, dict)
            and "nameIdentifiers" in value
            and len(value["nameIdentifiers"]) > 0
            and "nameIdentifierScheme" in value["nameIdentifiers"][0]
            and value["nameIdentifiers"][0]["nameIdentifierScheme"] == "WEKO"
        ):
            author_link.append(value["nameIdentifiers"][0]["nameIdentifier"])
            
    def _set_shared_id(data):
        """set weko_shared_id from shared_user_id"""
        if data.get("weko_shared_id",-1)==-1:
            return dict(weko_shared_id=data.get("shared_user_id",-1))
        else:
            if data.get("shared_user_id",-1)==-1:
                return dict(weko_shared_id=data.get("weko_shared_id"))
            else:
                return dict(weko_shared_id=data.get("shared_user_id"))
            
    dc = OrderedDict()
    jpcoar = OrderedDict()
    item = dict()
    ar = []
    pubdate = None

    if not isinstance(data, dict) or data.get("$schema") is None:
        return

    item_id = pid.object_uuid
    pid = pid.pid_value

    # get item type id
    split_schema_info = data["$schema"].split("/")
    item_type_id = (
        split_schema_info[-2]
        if "A-" in split_schema_info[-1]
        else split_schema_info[-1]
    )

    # get item type mappings
    ojson = ItemTypes.get_record(item_type_id, with_deleted=with_deleted)
    mjson = Mapping.get_record(item_type_id, with_deleted=with_deleted)


    if not (ojson and mjson):
        raise RuntimeError("Item Type {} does not exist.".format(item_type_id))

    mp = mjson.dumps()
    data.get("$schema")
    author_link = []
    for k, v in data.items():
        if k != "pubdate":
            if k == "$schema" or mp.get(k) is None:
                continue

        item.clear()
        try:
            item["attribute_name"] = (
                ojson["properties"][k]["title"]
                if ojson["properties"][k].get("title") is not None
                else k
            )
        except Exception:
            pub_date_setting = {
                "type": "string",
                "title": "Publish Date",
                "format": "datetime",
            }
            ojson["properties"]["pubdate"] = pub_date_setting
            item["attribute_name"] = "Publish Date"
        # set a identifier to add a link on detail page when is a creator field
        # creator = mp.get(k, {}).get('jpcoar_mapping', {})
        # creator = creator.get('creator') if isinstance(
        #     creator, dict) else None
        iscreator = False
        creator = ojson["properties"][k]
        if "object" == creator["type"]:
            creator = creator["properties"]
            if "iscreator" in creator:
                iscreator = True
        elif "array" == creator["type"]:
            creator = creator["items"]["properties"]
            if "iscreator" in creator:
                iscreator = True
        if iscreator:
            item["attribute_type"] = "creator"

        item_data = ojson["properties"][k]
        if "array" == item_data.get("type"):
            properties_data = item_data["items"]["properties"]
            if "filename" in properties_data:
                item["attribute_type"] = "file"

        if isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], dict):
                item["attribute_value_mlt"] = v
                _get_author_link(author_link, v)
            else:
                item["attribute_value"] = v
        elif isinstance(v, dict):
            ar.append(v)
            item["attribute_value_mlt"] = ar
            ar = []
            _get_author_link(author_link, v)
        else:
            item["attribute_value"] = v

        dc[k] = item.copy()
        if k != "pubdate":
            item.update(mp.get(k))
        else:
            pubdate = v
        jpcoar[k] = item.copy()

    # convert to es jpcoar mapping data
    jrc = SchemaTree.get_jpcoar_json(jpcoar,replace_field=replace_field)
    list_key = []
    for k, v in jrc.items():
        if not v:
            list_key.append(k)
    if list_key:
        for key in list_key:
            del jrc[key]
    if dc:
        # get the tile name to detail page
        title = data.get("title")

        if "control_number" in dc:
            del dc["control_number"]

        dc.update(dict(item_title=title))
        dc.update(dict(item_type_id=item_type_id))
        dc.update(dict(control_number=pid))
        dc.update(dict(author_link=author_link))

        if COPY_NEW_FIELD:
            copy_field_test(dc, WEKO_TEST_FIELD, jrc)

        # check oai id value
        is_edit = False
        try:
            oai_value = PersistentIdentifier.get_by_object(
                pid_type="oai",
                object_type="rec",
                object_uuid=PersistentIdentifier.get("recid", pid).object_uuid,
            ).pid_value
            is_edit = pid_exists(oai_value, "oai")
        except PIDDoesNotExistError:
            pass

        if not is_edit:
            oaid = current_pidstore.minters["oaiid"](item_id, dc)
            oai_value = oaid.pid_value
        # relation_ar = []
        # relation_ar.append(dict(value="", item_links="", item_title=""))
        # jrc.update(dict(relation=dict(relationType=relation_ar)))
        # dc.update(dict(relation=dict(relationType=relation_ar)))

        if COPY_NEW_FIELD:
            res = sm.get()
            options = None
            if res:
                detail_condition = res.search_conditions
            else:
                detail_condition = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS[
                    "detail_condition"
                ]

            if is_edit:
                copy_field_test(dc, detail_condition, jrc, oai_value)
            else:
                copy_field_test(dc, detail_condition, jrc)

        # current_app.logger.debug('{0} {1} {2}: {3}'.format(
        #     __file__, 'detail_condition()', 'detail_condition', detail_condition))

        jrc.update(dict(control_number=pid))
        jrc.update(dict(_oai={"id": oai_value}))
        jrc.update(dict(_item_metadata=dc))
        jrc.update(dict(itemtype=ojson.model.item_type_name.name))
        jrc.update(dict(publish_date=pubdate))
        jrc.update(dict(author_link=author_link))

        # save items's creator to check permission
        if current_user:
            current_user_id = current_user.get_id()
        else:
            current_user_id = "1"
        if current_user_id:
            # jrc is saved on elastic
            jrc_weko_creator_id = jrc.get("weko_creator_id", None)
            if not jrc_weko_creator_id:
                # in case first time create record
                jrc.update(dict(weko_creator_id=owner_id or current_user_id))
                jrc.update(_set_shared_id(data))
            else:
                # incase record is end and someone is updating record
                if current_user_id == int(jrc_weko_creator_id):
                    # just allow owner update shared_user_id
                    jrc.update(_set_shared_id(data))

            # dc js saved on postgresql
            dc_owner = dc.get("owner", None)
            if not dc_owner:
                dc.update(_set_shared_id(data))
                dc.update(dict(owner=owner_id or current_user_id))
            else:
                if current_user_id == int(dc_owner):
                    dc.update(_set_shared_id(data))

    del ojson, mjson, item
    return dc, jrc, is_edit


def copy_field_test(dc, map, jrc, iid=None):
    for k_v in map:
        if type(k_v) is dict:
            if k_v.get("item_value"):
                if dc["item_type_id"] in k_v.get("item_value").keys():
                    for key, val in k_v.get("item_value").items():
                        if dc["item_type_id"] == key:
                            _id = k_v.get("id")
                            _inputType = k_v.get("inputType")
                            current_app.logger.debug(
                                "id: {0} , inputType: {1}  , path: {2}".format(_id, _inputType,val['path'])
                            )
                            if _inputType == "text":
                                if val.get("condition_path") and val.get(
                                    "condition_value"):
                                    txt = get_values_from_dict_with_condition(
                                        dc, val["path"], val["path_type"],
                                        val["condition_path"],
                                        val["condition_value"], iid
                                    )
                                else:
                                    txt = get_values_from_dict(
                                        dc, val["path"], val["path_type"], iid
                                    )

                                if txt:
                                    jrc[k_v.get("id")] = txt
                            elif _inputType == "range":
                                id = k_v.get("id")
                                ranges = []
                                _gte = get_values_from_dict(
                                    dc, val["path"]["gte"], val["path_type"]["gte"], iid
                                )
                                _lte = get_values_from_dict(
                                    dc, val["path"]["lte"], val["path_type"]["lte"], iid
                                )
                                if _gte:
                                    for idx in range(len(_gte)):
                                        a = _gte[idx]
                                        b = None
                                        if idx < len(_lte):
                                            b = _lte[idx]
                                        try:
                                            ranges.append(convert_range_value(a, b))
                                        except:
                                            _error_col = val.get("path", {}).get("gte") \
                                                if val.get("path", {}).get("gte") else val.get("path", {}).get("lte")
                                            raise ValueError(
                                                "can not convert to range value. start:{} end:{}. column: {}".format(
                                                    a, b, _error_col)
                                            )
                                if len(ranges) > 0:
                                    value_range = {id: ranges}
                                    jrc.update(value_range)
                            elif _inputType == "dateRange":
                                id = k_v.get("id")
                                dateRanges = []
                                _gte = get_values_from_dict(
                                    dc, val["path"]["gte"], val["path_type"]["gte"], iid
                                )
                                _lte = get_values_from_dict(
                                    dc, val["path"]["lte"], val["path_type"]["lte"], iid
                                )
                                if _gte:
                                    for idx in range(len(_gte)):
                                        a = _gte[idx]
                                        b = None
                                        if idx < len(_lte):
                                            b = _lte[idx]
                                        try:
                                            dateRanges.append(convert_date_range_value(a, b))
                                        except:
                                            _error_col = val.get("path", {}).get("gte") \
                                                if val.get("path", {}).get("gte") else val.get("path", {}).get("lte")
                                            raise ValueError(
                                                "can not convert to range value. start:{} end:{}. column: {}".format(
                                                    a, b, _error_col)
                                            )
                                if len(dateRanges) > 0:
                                    value_range = {id: dateRanges}
                                    jrc.update(value_range)
                            elif _inputType == "geo_point":
                                geo_point = {k_v.get("id"): {"lat": "", "lon": ""}}
                                geo_point[k_v.get("id")]["lat"] = get_value_from_dict(
                                    dc, val["path"]["lat"], val["path_type"]["lat"], iid
                                )
                                geo_point[k_v.get("id")]["lon"] = get_value_from_dict(
                                    dc, val["path"]["lon"], val["path_type"]["lon"], iid
                                )
                                if (
                                    geo_point[k_v.get("id")]["lat"]
                                    and geo_point[k_v.get("id")]["lon"]
                                ):
                                    jrc.update(geo_point)
                            elif _inputType == "geo_shape":
                                geo_shape = {
                                    k_v.get("id"): {"type": "", "coordinates": ""}
                                }
                                geo_shape[k_v.get("id")]["type"] = get_value_from_dict(
                                    dc,
                                    val["path"]["type"],
                                    val["path_type"]["type"],
                                    iid,
                                )
                                geo_shape[k_v.get("id")][
                                    "coordinates"
                                ] = get_value_from_dict(
                                    dc,
                                    val["path"]["coordinates"],
                                    val["path_type"]["coordinates"],
                                    iid,
                                )
                                if (
                                    geo_shape[k_v.get("id")]["type"]
                                    and geo_shape[k_v.get("id")]["coordinates"]
                                ):
                                    jrc.update(geo_shape)


def convert_range_value(start, end=None):
    """Convert to range value for Elasticsearch

    Args:
        start ([str]): [description]
        end ([str], optional): [description]. Defaults to None.

    Returns:
        [dict]: range value for Elasticsearch
    """
    ret = None
    _start = "gte"
    _end = "lte"
    if end is None:
        start = start.strip()
        ret = {_start: start, _end: start}
    elif start is None:
        end = end.strip()
        ret = {_start: end, _end: end}
    else:
        start = start.strip()
        end = end.strip()
        if start.isdecimal() and end.isdecimal():
            a = int(start)
            b = int(end)
            if a < b:
                ret = {_start: start, _end: end}
            else:
                ret = {_start: end, _end: start}
        else:
            a = float(start)
            b = float(end)

            if a < b:
                ret = {_start: start, _end: end}
            else:
                ret = {_start: end, _end: start}
    return ret


def convert_date_range_value(start, end=None):
    """Convert to dateRange value for Elasticsearch

    Args:
        start ([str]): [description]
        end ([str], optional): [description]. Defaults to None.

    Returns:
        [dict]: dateRange value for Elasticsearch
    """
    ret = None
    _start = "gte"
    _end = "lte"
    pattern = r"^(([0-9]?[0-9]?[0-9]?[0-9]-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01]))/"\
    "([0-9]?[0-9]?[0-9]?[0-9]-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])))|"\
    "(([0-9]?[0-9]?[0-9]?[0-9]-(0?[1-9]|1[0-2]))/([0-9]?[0-9]?[0-9]?[0-9]-(0?[1-9]|1[0-2])))|"\
    "(([0-9]?[0-9]?[0-9]?[0-9])/([0-9]?[0-9]?[0-9]?[0-9]))$"
    p = re.compile(pattern)
    if start is not None:
        start = start.strip()
        ret = makeDateRangeValue(start,start)
        if p.match(start) is not None:
            _tmp = start.split("/")
            if len(_tmp) == 2:
                ret = makeDateRangeValue(_tmp[0], _tmp[1])
        elif end is not None:
            ret = makeDateRangeValue(start, end)
    else:
        if end is not None:
            ret = makeDateRangeValue(end,end)
    return ret


def makeDateRangeValue(start, end):
    """make dataRange value

    Args:
        start ([string]): start date string
        end ([string]): end date string

    Returns:
        [dict]: dateRange value
    """
    _start = "gte"
    _end = "lte"
    start = start.strip()
    start = start.replace('/','-')
    end = end.strip()
    end = end.replace('/','-')
    ret = None
    p2 = re.compile(
        r"^([0-9]?[0-9]?[0-9]?[0-9]-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01]))$"
    )
    p3 = re.compile(r"^([0-9]?[0-9]?[0-9]?[0-9]-(0?[1-9]|1[0-2]))$")
    p4 = re.compile(r"^([0-9]?[0-9]?[0-9]?[0-9])$")

    a = None
    b = None
    if p2.match(start):
        _s = start.split('-')
        a = time.strptime('{:0>4}-{}-{}'.format(_s[0], _s[1], _s[2]), "%Y-%m-%d")
    elif p3.match(start):
        _s = start.split('-')
        a = time.strptime('{:0>4}-{}'.format(_s[0], _s[1]), "%Y-%m")
    elif p4.match(start):
        a = time.strptime('{:0>4}'.format(start), "%Y")

    if p2.match(end):
        _e = end.split('-')
        b = time.strptime('{:0>4}-{}-{}'.format(_e[0], _e[1], _e[2]), "%Y-%m-%d")
    elif p3.match(end):
        _e = end.split('-')
        b = time.strptime('{:0>4}-{}'.format(_e[0], _e[1]), "%Y-%m")
    elif p4.match(end):
        b = time.strptime('{:0>4}'.format(end), "%Y")

    if a is not None and b is not None:
        if a < b:
            ret = {_start: start, _end: end}
        else:
            ret = {_start: end, _end: start}

    return ret


def get_value_from_dict(dc, path, path_type, iid=None):
    ret = None
    if path_type == "xml":
        ret = copy_value_xml_path(dc, path, iid)
    elif path_type == "json":
        ret = copy_value_json_path(dc, path)
    current_app.logger.debug("get_value_from_dict: {0}".format(ret))
    return ret


def get_values_from_dict(dc, path, path_type, iid=None):
    ret = None
    if path_type == "xml":
        ret = copy_value_xml_path(dc, path, iid)
    elif path_type == "json":
        ret = copy_values_json_path(dc, path)

    current_app.logger.debug("get_values_from_dict: {0}".format(ret))
    return ret


def get_values_from_dict_with_condition(dc, path, path_type, condition_path,
                                        condition_value, iid=None):
    """Extracts the values to be used in the advanced search according to the
    conditions.

    The difference between this function and get_values_from_dict() is that it
    does not extract values unless the specified conditions are met.

    The condition is judged by extracting the value specified in condition_path
    for the metadata defined in dc, and then judging whether the value matches
    the condition_value.

    Args:
        dc: Item metadata.
        path: Path to the value to be extracted.
        path_type: json or xml.
        condition_path: Path to the value that is the extraction condition
        condition_value: Condition-determining value.
        iid: Oai id.
    Return:
        Value used in detail search.
    """
    ret = None

    if path_type == "xml":
        ret = copy_value_xml_path(dc, path, iid)
    elif path_type == "json":
        path_tmps = path.split('.')
        cpath_tmps = condition_path.split('.')
        common_path = None
        for index, tmp in enumerate(path_tmps):
            if len(cpath_tmps) > index and tmp == cpath_tmps[index]:
                common_path = '.'.join(path_tmps[0:index + 1])
        if common_path:
            vpath = path.split(common_path + '.')[1]
            cpath = condition_path.split(common_path + '.')[1]
            ret = []
            matches = parse(common_path).find(dc)
            for match in matches:
                cval = copy_value_json_path(match, cpath)
                if condition_value == cval:
                    ret += copy_values_json_path(match, vpath)
            if not ret:
                ret = None

    return ret


def copy_value_xml_path(dc, xml_path, iid=None):
    from invenio_oaiserver.response import getrecord

    try:
        meta_prefix = xml_path[0]
        xpath = xml_path[1]
        if iid:
            # url_for('invenio_oaiserver.response', _external=True)をこの関数で実行した場合エラーが起きました。原因は調査中です。
            xml = etree.tostring(
                getrecord(
                    metadataPrefix=meta_prefix,
                    identifier=iid,
                    verb="GetRecord",
                    url="https://192.168.75.3/oai",
                )
            )
            root = ET.fromstring(xml)
            ns = {
                "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
                "dc": "http://purl.org/dc/elements/1.1/",
                "jpcoar": "https://irdb.nii.ac.jp/schema/jpcoar/1.0/",
                "xml": "http://www.w3.org/XML/1998/namespace",
            }
            copy_value = root.findall(xpath, ns)[0].text
            return str(copy_value)
    except Exception:
        return None


def copy_value_json_path(meta, jsonpath):
    """extract a value from metadata using jsonpath

    Args:
        meta (OrderedDict): item metadata
        jsonpath (string): jsonpath for values extraction

    Returns:
        string: extracted value from metadata
    """
    match_value = None
    try:
        matches = parse(jsonpath).find(meta)
        match_value = [match.value for match in matches]
        current_app.logger.debug(
            "jsonpath: {0},meta: {1}, match_value: {2}".format(
                jsonpath, meta, match_value
            )
        )
        return match_value[0]
    except Exception:
        return match_value


def copy_values_json_path(meta, jsonpath):
    """extract values from metadata using jsonpath

    Args:
        meta (OrderedDict): item metadata
        jsonpath (string): jsonpath for values extraction

    Returns:
        list: extracted values from metadata
    """
    match_value = None
    try:
        matches = parse(jsonpath).find(meta)
        match_value = [match.value for match in matches]
        current_app.logger.debug(
            "jsonpath: {0}, meta: {1}, match_value: {2}".format(
                jsonpath, meta, match_value
            )
        )
        return match_value
    except Exception:
        return match_value


def set_timestamp(jrc, created, updated):
    """Set timestamp."""
    jrc.update(
        {"_created": pytz.utc.localize(created).isoformat() if created else None}
    )

    jrc.update(
        {"_updated": pytz.utc.localize(updated).isoformat() if updated else None}
    )


def sort_records(records, form):
    """Sort records.

    :param records:
    :param form:
    :return:
    """
    odd = OrderedDict()
    if isinstance(records, dict) and isinstance(form, list):
        for k in find_items(form):
            val = records.get(k[0])
            if val:
                odd.update({k[0]: val})
        # save schema link
        odd.update({"$schema": records.get("$schema")})
        del records
        return odd
    else:
        return records


def sort_op(record, kd, form):
    """Sort options dict.

    :param record:
    :param kd:
    :param form:
    :return:
    """
    odd = OrderedDict()
    if isinstance(record, dict) and isinstance(form, list):
        index = 0
        for k in find_items(form):
            # mapping target key
            key = kd.get(k[0])
            if not odd.get(key) and record.get(key):
                index += 1
                val = record.pop(key, {})
                val["index"] = index
                odd.update({key: val})

        record.clear()
        del record
        return odd
    else:
        return record


def find_items(form):
    """Find sorted items into a list.

    :param form:
    :return: lst
    """
    lst = []

    def find_key(node):
        if isinstance(node, dict):
            key = node.get("key")
            title = node.get("title", "")
            try:
                # Try catch for case this function is called from celery app
                current_lang = current_i18n.language
            except Exception:
                current_lang = "en"
            title_i18n = node.get("title_i18n", {}).get(current_lang, title)
            option = {
                "required": node.get("required", False),
                "show_list": node.get("isShowList", False),
                "specify_newline": node.get("isSpecifyNewline", False),
                "hide": node.get("isHide", False),
                "non_display": node.get("isNonDisplay", False),
            }
            val = ""
            if key:
                yield [key, title, title_i18n, option, val]
            for v in node.values():
                if isinstance(v, list):
                    for k in find_key(v):
                        yield k
        elif isinstance(node, list):
            for n in node:
                for k in find_key(n):
                    yield k

    for x in find_key(form):
        lst.append(x)

    return lst


def get_all_items(nlst, klst, is_get_name=False):
    """Convert and sort item list.

    :param nlst:
    :param klst:
    :param is_get_name:
    :return: alst
    """

    def get_name(key):
        for lst in klst:
            key_arr = lst[0].split(".")
            k = key_arr[-1]
            if key != k:
                continue
            item_name = lst[1]
            if len(key_arr) >= 3:
                parent_key = key_arr[-2].replace("[]", "")
                parent_key_name = get_name(parent_key)
                if item_name and parent_key_name:
                    item_name = item_name + "." + get_name(parent_key)

            return item_name

    def get_items(nlst):
        _list = []

        if isinstance(nlst, list):
            for lst in nlst:
                _list.append(get_items(lst))
        if isinstance(nlst, dict):
            d = {}
            for k, v in nlst.items():
                if isinstance(v, str):
                    d[k] = v
                    if is_get_name:
                        item_name = get_name(k)
                        if item_name:
                            d[k + ".name"] = item_name
                else:
                    _list.append(get_items(v))
            _list.append(d)

        return _list

    to_orderdict(nlst, klst)
    alst = get_items(nlst)

    return alst


def get_all_items2(nlst, klst):
    """Convert and sort item list(original).

    :param nlst:
    :param klst:
    :return: alst
    
    :note 
    """
    alst = []

    def get_items(nlst):
        if isinstance(nlst, dict):
            for k, v in nlst.items():
                if isinstance(v, str):
                    alst.append({k: v})
                else:
                    get_items(v)
        elif isinstance(nlst, list):
            for ix,lst in enumerate(nlst):
                get_items(lst)
    
    def get_items2(nlst):
        ret = []
        if isinstance(nlst, dict):
            for k, v in nlst.items():
                if isinstance(v, str):
                    ret.append({k: v})
                else:
                    tmp = get_items2(v)
                    ret.append(tmp)
        elif isinstance(nlst, list):
            for ix,lst in enumerate(nlst):
                tmp = get_items2(lst)
                ret.append(tmp)
        return ret
                        
    to_orderdict(nlst, klst, True)
    get_items(nlst)
    return alst


def to_orderdict(alst, klst, is_full_key=False):
    """Sort item list.

    :param alst:
    :param klst:
    """
    if isinstance(alst, list):
        for i in range(len(alst)):
            if isinstance(alst[i], dict):
                alst.insert(i, OrderedDict(alst.pop(i)))
                to_orderdict(alst[i], klst, is_full_key)
    elif isinstance(alst, dict):
        nlst = []
        if isinstance(klst, list):
            for lst in klst:
                key = lst[0] if is_full_key else lst[0].split(".")[-1]
                val = alst.pop(key, {})
                if val:
                    if isinstance(val, dict):
                        val = OrderedDict(val)
                    nlst.append({lst[0]: val})
                if not alst:
                    break

            while len(nlst) > 0:
                alst.update(nlst.pop(0))

            for k, v in alst.items():
                if not isinstance(v, str):
                    to_orderdict(v, klst, is_full_key)


def get_options_and_order_list(item_type_id, item_type_data=None):
    """Get Options by item type id.

    :param item_type_id:
    :param item_type_data:
    :return: options dict and sorted list
    """
    meta_options = {}
    solst = []
    if item_type_data is None:
        item_type_data = ItemTypes.get_record(item_type_id)
    if item_type_data:
        solst = find_items(item_type_data.model.form)
        meta_options = item_type_data.model.render.get("meta_fix")
        meta_options.update(item_type_data.model.render.get("meta_list"))
    return solst, meta_options


async def sort_meta_data_by_options(
    record_hit,
    settings,
    item_type_data,
):
    """Reset metadata by '_options'.

    :param record_hit:
    :param settings:
    :param item_type_data:
    """
    
    from weko_deposit.api import _FormatSysBibliographicInformation
    from weko_records_ui.permissions import check_file_download_permission
    from weko_records_ui.utils import hide_item_metadata
    from weko_search_ui.utils import get_data_by_property

    from weko_records.serializers.utils import get_mapping

    web_screen_lang = current_i18n.language

    def convert_data_to_dict(solst):
        """Convert solst to dict."""
        solst_dict_array = []
        for lst in solst:
            key = lst[0].replace("[]", "")
            option = meta_options.get(key, {}).get("option")
            temp = {
                "key": key,
                "title": lst[1],
                "title_ja": lst[2],
                "option": lst[3],
                "parent_option": option,
                "value": "",
            }
            solst_dict_array.append(temp)
        return solst_dict_array

    def get_author_comment(data_result, key, result, is_specify_newline_array):
        value = data_result[key].get(key, {}).get("value", [])
        value = [x for x in value if x]
        if len(value) > 0:
            is_specify_newline = False
            for specify_newline in is_specify_newline_array:
                if key in specify_newline:
                    is_specify_newline = specify_newline[key]
            if is_specify_newline:
                result.append(",".join(value))
            else:
                if len(result) == 0:
                    result.append(",".join(value))
                else:
                    result[-1] += "," + ",".join(value)
        
        return result

    def data_comment(result, data_result, stt_key, is_specify_newline_array):
        list_author_key = current_app.config["WEKO_RECORDS_AUTHOR_KEYS"]
        for idx, key in enumerate(stt_key):
            lang_id = ""
            if key in data_result and data_result[key] is not None:
                if key in list_author_key:
                    result = get_author_comment(
                        data_result, key, result, is_specify_newline_array
                    )
                else:
                    if "lang_id" in data_result[key]:
                        lang_id = (
                            data_result[key].get("lang_id")
                            if "[]" not in data_result[key].get("lang_id")
                            else data_result[key].get("lang_id").replace("[]", "")
                        )
                    data = ""
                    if (
                        "stt" in data_result[key]
                        and data_result[key].get("stt") is not None
                    ):
                        data = data_result[key].get("stt")
                    else:
                        data = data_result.get(key)
                    for idx2, d in enumerate(data):
                        if d not in "lang" and d not in "lang_id":
                            lang_arr = []
                            if "lang" in data_result[key]:
                                lang_arr = data_result[key].get("lang")
                            if (
                                (key in data_result)
                                and (d in data_result[key])
                                and ("value" in data_result[key][d])
                            ):
                                value_arr = data_result[key][d]["value"]
                                value = selected_value_by_language(
                                    lang_arr,
                                    value_arr,
                                    lang_id,
                                    d.replace("[]", ""),
                                    web_screen_lang,
                                    _item_metadata,
                                )
                                if value is not None and len(value) > 0:
                                    for index, n in enumerate(is_specify_newline_array):
                                        if d in n:
                                            if n[d] or len(result) == 0:
                                                result.append(value)
                                            else:
                                                result[-1] += "," + value
                                            break
        return result

    def get_comment(solst_dict_array, hide_email_flag, _item_metadata, src, solst):
        """Check and get info."""

        def get_option_value(option_type, parent_option, child_option):
            """Get value of option by option type, prioritized parent.

            @param option_type: show_list, specify_newline, hide, required
            @return: True or False
            """
            return (
                parent_option.get(option_type)
                if parent_option and parent_option.get(option_type)
                else child_option.get(option_type)
            )

        from weko_items_ui.utils import del_hide_sub_item
        result = []
        data_result = {}
        stt_key = []
        _ignore_items = list()
        _license_dict = current_app.config["WEKO_RECORDS_UI_LICENSE_DICT"]
        is_specify_newline_array = []
        bibliographic_key = None
        author_key = None
        author_data = {}
        if _license_dict:
            _ignore_items.append(_license_dict[0].get("value"))
        for i, s in enumerate(solst_dict_array):
            if not s['key']:
                continue
            value = s["value"]
            option = s["option"]
            parent_option = s["parent_option"]
            parent_key = s["key"].replace('[]', '').split('.')[0]
            del_hide_sub_item(parent_key, mlt, hide_list)
            # Get 'show list', 'specify newline', 'hide' flag.
            is_show_list = get_option_value("show_list", parent_option, option)
            is_specify_newline = get_option_value(
                "specify_newline", parent_option, option
            )
            is_hide = get_option_value("hide", parent_option, option)
            # Get hide email flag
            if (
                "creatorMails.creatorMail" in s["key"]
                or "contributorMails.contributorMail" in s["key"]
                or "mails.mail" in s["key"]
            ):
                is_hide = is_hide | hide_email_flag
            # Get creator flag.
            is_author = src.get(s["key"], {}).get("attribute_type", {}) == "creator"

            if author_key and author_key in s["key"]:
                stt_key, data_result, is_specify_newline_array = add_author(
                    author_data,
                    stt_key,
                    is_specify_newline_array,
                    s,
                    value,
                    data_result,
                    is_specify_newline,
                    is_hide,
                    is_show_list,
                )
            elif is_author:
                # Format creator data to display on item list
                author_key = s["key"]
                attr_mlt = src.get(s["key"], {}).get("attribute_value_mlt", {})
                del_hide_sub_item(parent_key, attr_mlt, hide_list)
                author_data = get_show_list_author(
                    solst_dict_array, hide_email_flag, author_key, attr_mlt
                )
                sub_author_key = s["key"].split(".")[-1]
            elif (
                bibliographic_key is None
                and is_show_list
                and "bibliographic_titles" in s["key"]
            ):
                # Format bibliographic data to display on item list
                bibliographic_key = s["key"].split(".")[0].replace("[]", "")
                mlt_bibliographic = src.get(bibliographic_key, {}).get(
                    "attribute_value_mlt"
                )
                if mlt_bibliographic:
                    del_hide_sub_item(parent_key, mlt_bibliographic, hide_list)
                    sys_bibliographic = _FormatSysBibliographicInformation(
                        pickle.loads(pickle.dumps(mlt_bibliographic, -1)), pickle.loads(pickle.dumps(solst, -1))
                    )
                    stt_key, data_result, is_specify_newline_array = add_biographic(
                        sys_bibliographic,
                        bibliographic_key,
                        s,
                        stt_key,
                        data_result,
                        is_specify_newline_array,
                    )
            elif (
                not (bibliographic_key and bibliographic_key in s["key"])
                and value
                and value not in _ignore_items
                and (
                    (not is_hide and is_show_list)
                    or s["title"] in current_app.config["WEKO_RECORDS_LANGUAGE_TITLES"]
                )
                and s["key"]
                and s["title"] != current_app.config["WEKO_RECORDS_TITLE_TITLE"]
            ):
                data_result, stt_key = get_value_and_lang_by_key(
                    s["key"], solst_dict_array, data_result, stt_key
                )
                
                is_specify_newline_array.append({s["key"]: is_specify_newline})

        if len(data_result) > 0:
            result = data_comment(
                result, data_result, stt_key, is_specify_newline_array
            )
        
        return result

    
    def get_value_by_selected_language(values,lang_key,current_lang):
        dict = convert_array_to_dict(values,lang_key)
        if dict.get(current_lang):
            return dict.get(current_lang)
        elif dict.get("None"):
            return dict.get("None")
        elif dict.get("en"):
            return dict.get("en")
  
    def get_creator_comments(key,meta_options,creators,is_hide_email):
        """
        TODO: affiliationは未実装
        TODO: nameIdentifiersのhide設定。現状属性がhideであればすべてhide。
        """
        ret = []
        current_lang = current_i18n.language
        dict = convert_array_to_dict(meta_options,"key")
        for creator in creators:
            if creator.get("creatorMails"):
                opt = dict["{}.{}".format(key,"creatorMails")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')|is_hide_email):
                        creator.pop("creatorMails")
                opt = dict["{}.{}.{}".format(key,"creatorMails","creatorMail")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')|is_hide_email):
                        if creator.get("creatorMails"):
                            creator.pop("creatorMails")
            
            if creator.get("familyNames"):
                opt = dict["{}.{}".format(key,"familyNames")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        creator.pop("familyNames")
                    else:
                        creator["familyNames"] = get_value_by_selected_language(creator["familyNames"],"familyNameLang",current_lang)
                opt = dict["{}.{}.{}".format(key,"familyNames","familyName")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        if creator.get("familyNames"):
                            creator.pop("familyNames")
                        
            if creator.get("creatorNames"):
                opt = dict["{}.{}".format(key,"creatorNames")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        creator.pop("creatorNames")
                    else:
                        creator["creatorNames"] = get_value_by_selected_language(creator["creatorNames"],"creatorNameLang",current_lang)
                
                opt = dict["{}.{}.{}".format(key,"creatorNames","creatorName")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        if creator.get("creatorNames"):
                            creator.pop("creatorNames")
            
            if creator.get("givenNames"):
                opt = dict["{}.{}".format(key,"givenNames")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        creator.pop("givenNames")
                    else:
                        creator["givenNames"] = get_value_by_selected_language(creator["givenNames"],"givenNameLang",current_lang)
                opt = dict["{}.{}.{}".format(key,"givenNames","givenName")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        if creator.get("givenNames"):
                            creator.pop("givenNames")
            
            if creator.get("nameIdentifiers"):
                opt = dict["{}.{}".format(key,"nameIdentifiers")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        creator.pop("nameIdentifiers")
                opt = dict["{}.{}.{}".format(key,"nameIdentifiers","nameIdentifierScheme")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        if creator.get("nameIdentifiers"):
                            creator.pop("nameIdentifiers")
                        
                opt = dict["{}.{}.{}".format(key,"nameIdentifiers","nameIdentifierURI")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        if creator.get("nameIdentifiers"):
                            creator.pop("nameIdentifiers")
                            
                opt = dict["{}.{}.{}".format(key,"nameIdentifiers","nameIdentifier")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        if creator.get("nameIdentifiers"):
                            creator.pop("nameIdentifiers")        

            if creator.get("creatorAffiliations"):
                opt = dict["{}.{}".format(key,"creatorAffiliations")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        creator.pop("creatorAffiliations")
            
            if creator.get("affiliationNameIdentifiers"):
                opt = dict["{}.{}".format(key,"affiliationNameIdentifiers")]
                if opt.get('option'):
                    _opt = opt.get('option')    
                    if (_opt.get('hide') | _opt.get('non_display')):
                        creator.pop("affiliationNameIdentifiers")
        
            # current_app.logger.error("creator:{}".format(creator))
            ret.append(creator)
                    
        return ret
                
            
            
        
    
    def get_file_comments(record, files):
        """Check and get file info."""

        def __get_label_extension():
            _label = f.get("url", {}).get("label")
            _filename = f.get("filename", "")
            _extension = ""
            if not _label and not f.get("version_id"):
                _label = f.get("url", {}).get("url", "")
            elif not _label:
                _label = _filename
            if f.get("version_id"):
                _idx = _filename.rfind(".") + 1
                _extension = _filename[_idx:] if _idx > 0 else "unknown"
            return _label, _extension

        result = []
        for f in files:
            label, extension = __get_label_extension()
            if "open_restricted" == f.get("accessrole", ""):
                if label:
                    result.append({"label": label, "extention": extension, "url": ""})
            elif label and (
                not extension or check_file_download_permission(record, f, False)
            ):
                file_url = f.get("url", {}).get("url", "")
                if extension and file_url:
                    file_url = replace_fqdn(file_url)
                result.append({"label": label, "extention": extension, "url": file_url})
        return result

    def get_file_thumbnail(thumbnails):
        """Get file thumbnail."""
        thumbnail = {}
        if thumbnails and len(thumbnails) > 0:
            subitem_thumbnails = thumbnails[0].get("subitem_thumbnail")
            if subitem_thumbnails and len(subitem_thumbnails) > 0:
                thumbnail = {
                    "thumbnail_label": subitem_thumbnails[0].get("thumbnail_label", ""),
                    "thumbnail_width": current_app.config[
                        "WEKO_RECORDS_UI_DEFAULT_MAX_WIDTH_THUMBNAIL"
                    ],
                }
        return thumbnail

    def append_parent_key(key, attribute_value_mlt):
        """Update parent key attribute_value_mlt."""

        def get_parent_key(key):
            """Get root key in string key."""
            parent_key = key
            key_arr = key.split(".")
            if len(key_arr) >= 2:
                del key_arr[-1]
                parent_key = ".".join(key_arr)
            return parent_key

        def append_parent_key_all_type(parent_key, attr_val_mlt):
            """Append parent key for all sub key in array and dict."""
            if isinstance(attr_val_mlt, dict):
                return append_parent_key_for_dict(parent_key, attr_val_mlt)
            if isinstance(attr_val_mlt, list):
                return append_parent_key_for_list(parent_key, attr_val_mlt)

        def append_parent_key_for_dict(parent_key, attr_val_mlt):
            """Append parent key for all sub key in dict."""
            mlt_temp = {}
            for attr_key, attr_val in attr_val_mlt.items():
                # Join parent and child key. Ex: parent_key_01.sub_key_01
                parent_key_temp = "{}.{}".format(parent_key, attr_key)
                mlt_temp.update({parent_key_temp: attr_val})
                if isinstance(attr_val, dict):
                    attr_val_temp = append_parent_key_for_dict(
                        parent_key_temp, attr_val
                    )
                    mlt_temp[parent_key_temp] = attr_val_temp
                if isinstance(attr_val, list):
                    attr_val_temp = append_parent_key_for_list(
                        parent_key_temp, attr_val
                    )
                    mlt_temp[parent_key_temp] = attr_val_temp
            return mlt_temp

        def append_parent_key_for_list(parent_key, attr_val_mlt):
            """Append parent key for all sub key in array."""
            mlt_temp_arr = []
            for item in attr_val_mlt:
                if isinstance(item, dict):
                    mlt_temp = append_parent_key_for_dict(parent_key, item)
                    mlt_temp_arr.append(mlt_temp)
                if isinstance(item, list):
                    mlt_temp = append_parent_key_for_list(parent_key, item)
                    mlt_temp_arr.append(mlt_temp)
            attr_val_mlt = mlt_temp_arr
            return attr_val_mlt

        # Get root key.
        parent_key = get_parent_key(key)
        # Append parent key for all sub key.
        attribute_value_mlt = append_parent_key_all_type(
            parent_key, attribute_value_mlt
        )
        return attribute_value_mlt

    def get_title_option(solst_dict_array):
        """Get option of title."""
        parent_option, child_option = {}, {}
        for item in solst_dict_array:
            if "." in item.get("key") and item.get("title") == "Title":
                parent_option = item.get("parent_option",{}) if item.get("parent_option") else {}
                child_option = item.get("option",{}) if item.get("option") else {}
                break
        show_list = (
            parent_option.get("show_list")
            if parent_option.get("show_list")
            else child_option.get("show_list")
        )
        specify_newline = (
            parent_option.get("crtf")
            if parent_option.get("crtf")
            else child_option.get("specify_newline")
        )
        option = {"show_list": show_list, "specify_newline": specify_newline}
        return option

    try:
        src_default = pickle.loads(pickle.dumps(record_hit["_source"].get("_item_metadata"), -1))
        _item_metadata = pickle.loads(pickle.dumps(record_hit["_source"], -1))
        src = record_hit["_source"]["_item_metadata"]
        item_type_id = record_hit["_source"].get("item_type_id") or src.get(
            "item_type_id"
        )
        
        # selected title
        from weko_items_ui.utils import get_hide_list_by_schema_form

        item_type = ItemTypes.get_by_id(item_type_id)
        hide_list = []
        if item_type:
            solst, meta_options = get_options_and_order_list(
                item_type_id, item_type_data=ItemTypes(item_type.schema, model=item_type))
            hide_list = get_hide_list_by_schema_form(schemaform=item_type.render.get('table_row_map', {}).get('form', []))
        else:
            solst, meta_options = get_options_and_order_list(item_type_id)
        item_map = get_mapping(item_type_id, "jpcoar_mapping", item_type=item_type)
        title_value_key = 'title.@value'
        title_lang_key = 'title.@attributes.xml:lang'
        title_languages = []
        title_values = []
        _title_key_str = ''
        _title_key1_str = ''
        if title_value_key in item_map:
            if title_lang_key in item_map:
                # get language
                title_languages, _title_key_str = get_data_by_property(
                    src, item_map, title_lang_key)
            # get value
            title_values, _title_key1_str = get_data_by_property(
                src, item_map, title_value_key)
        if title_languages and len(title_languages) > 0:
            result = selected_value_by_language(
                title_languages, title_values, _title_key_str, _title_key1_str, web_screen_lang, _item_metadata, meta_options, hide_list
            )
            if result is not None:
                for idx, val in enumerate(record_hit["_source"]["title"]):
                    if val == result:
                        arr = []
                        record_hit["_source"]["title"][idx] = record_hit["_source"]["title"][0]
                        record_hit["_source"]["title"][0] = result
                        arr.append(result)
                        record_hit["_source"]["_comment"] = arr
                        break
        elif title_values and len(title_values) > 0:
            record_hit["_source"]["_comment"] = [title_values[0]]
            record_hit["_source"]["title"][0] = title_values[0]

        if not item_type_id:
            return

        solst_dict_array = convert_data_to_dict(solst)
        files_info = []
        creator_info = None
        thumbnail = None
        hide_item_metadata(src, settings, item_type_data)
        # Set value and parent option
        for lst in solst:
            key = lst[0]
            val = src.get(key)
            option = meta_options.get(key, {}).get("option")
            if not val or not option:
                continue
            mlt = val.get("attribute_value_mlt", [])
            
            if mlt:
                if (
                    val.get("attribute_type", "") == "file"
                    and not option.get("hidden")
                    and option.get("showlist")
                ):
                    files_info = get_file_comments(src, mlt)
                    continue
                is_thumbnail = any("subitem_thumbnail" in data for data in mlt)
                if is_thumbnail and not option.get("hidden") and option.get("showlist"):
                    thumbnail = get_file_thumbnail(mlt)
                    continue
                
                
                if (
                    val.get("attribute_type", "") == "creator"
                    and not option.get("hidden")
                    and option.get("showlist")
                ):
                    is_hide_email = not settings.items_display_email
                    creator_info = get_creator_comments(key,solst_dict_array,mlt,is_hide_email)
                    continue
                
                mlt = append_parent_key(key, mlt)
                meta_data = get_all_items2(mlt, solst)
                for m in meta_data:
                    for s in solst_dict_array:
                        s_key = s.get("key")
                        
                        tmp = m.get(s_key)
                        if tmp:
                            s["value"] = (
                                tmp
                                if not s["value"]
                                else "{}{} {}".format(
                                    s["value"],
                                    current_app.config.get(
                                        "WEKO_RECORDS_SYSTEM_COMMA", ""
                                    ),
                                    tmp,
                                )
                            )
                            s["parent_option"] = {
                                "required": option.get("required"),
                                "show_list": option.get("showlist"),
                                "specify_newline": option.get("crtf"),
                                "hide": option.get("hidden"),
                            }
                            break
        
        # Format data to display on item list
        items = get_comment(
            solst_dict_array,
            not settings.items_display_email,
            _item_metadata,
            src_default,
            solst,
        )
        
        if "file" in record_hit["_source"]:
            record_hit["_source"].pop("file")

        # Title do not display if show list is false.
        title_option = get_title_option(solst_dict_array)
        if not title_option.get("show_list"):
            record_hit["_source"]["_comment"] = []
        if items and len(items) > 0:
            if record_hit["_source"].get("_comment"):
                record_hit["_source"]["_comment"].extend(items)
            else:
                record_hit["_source"]["_comment"] = items
        if files_info:
            record_hit["_source"]["_files_info"] = files_info
        if thumbnail:
            record_hit["_source"]["_thumbnail"] = thumbnail
        if creator_info:
            record_hit["_source"]["_creator_info"] = creator_info
    except Exception:
        current_app.logger.exception(
            "Record serialization failed {}.".format(
                str(record_hit["_source"].get("control_number"))
            )
        )


def convert_array_to_dict(solst_dict_array,key):
    dict = {}
    idx = 0
    for item in solst_dict_array:
        if item.get(key):
            item['idx']=idx
            dict[item.get(key)] = item
        else:
            item['idx']=idx
            dict['None'] = item
        idx=idx+1
    return dict
    

def get_keywords_data_load(str):
    """Get a json of item type info.

    :return: dict of item type info
    """
    try:
        return [(x.name, x.id) for x in ItemTypes.get_latest()]
    except BaseException:
        pass
    return []


def is_valid_openaire_type(resource_type, communities):
    """Check if the OpenAIRE subtype is corresponding with other metadata.

    :param resource_type: Dictionary corresponding to 'resource_type'.
    :param communities: list of communities identifiers
    :returns: True if the 'openaire_subtype' (if it exists) is valid w.r.t.
        the `resource_type.type` and the selected communities, False otherwise.
    """
    if "openaire_subtype" not in resource_type:
        return True
    oa_subtype = resource_type["openaire_subtype"]
    prefix = oa_subtype.split(":")[0] if ":" in oa_subtype else ""

    cfg = current_openaire.openaire_communities
    defined_comms = [c for c in cfg.get(prefix, {}).get("communities", [])]
    type_ = resource_type["type"]
    subtypes = cfg.get(prefix, {}).get("types", {}).get(type_, [])
    # Check if the OA subtype is defined in config and at least one of its
    # corresponding communities is present
    is_defined = any(t["id"] == oa_subtype for t in subtypes)
    comms_match = len(set(communities) & set(defined_comms))
    return is_defined and comms_match


def check_has_attribute_value(node):
    """Check has value in items.

    :param node:
    :return: boolean
    """
    try:
        if isinstance(node, list):
            for lst in node:
                return check_has_attribute_value(lst)
        elif isinstance(node, dict) and bool(node):
            for val in node.values():
                if val:
                    if isinstance(val, str):
                        return True
                    else:
                        return check_has_attribute_value(val)
        return False
    except BaseException as e:
        current_app.logger.error("Function check_has_attribute_value error:", e)
        return False

def set_file_date(root_key, solst, metadata, attr_lst):
    """set date.dateValue to attribute_value_mlt."""
    prop_name = ""
    for lst in solst:
        keys = lst[0].replace("[]", "").split(".")
        if keys[0].startswith(root_key) and keys[-1] == "dateValue":
            name = lst[2]
            if name:
                prop_name = name
            else:
                prop_name = lst[1]

    for i, d in enumerate(metadata):
        if isinstance(d, dict):
            date_elem = d.get("date")
            if date_elem and len(date_elem) > 0:
                date_value = date_elem[0].get("dateValue")
                attr_lst[i][0].insert(0,[{prop_name:date_value}])

def get_attribute_value_all_items(
    root_key,
    nlst,
    klst,
    is_author=False,
    hide_email_flag=True,
    non_display_flag=False,
    one_line_flag=False,
):
    """Convert and sort item list.

    :param root_key:
    :param nlst:
    :param klst:
    :param is_author:
    :param hide_email_flag:
    :param non_display_flag:
    :param one_line_flag:
    :return: alst
    """
    name_mapping = {}

    def get_name_mapping():
        """Create key & title mapping."""
        for lst in klst:
            keys = lst[0].replace("[]", "").split(".")
            if keys[0].startswith(root_key):
                key = keys[-1]
                name = lst[2] if not is_author else "{}.{}".format(key, lst[2])
                name_mapping[key] = {
                    "multi_lang": name,
                    "item_name": lst[1],
                    "non_display": lst[3].get("non_display", False),
                }

    def get_name(key, multi_lang_flag=True):
        """Get multi-lang title."""
        if key in name_mapping:
            name = (
                name_mapping[key]["multi_lang"]
                if multi_lang_flag
                else name_mapping[key]["item_name"]
            )
            return name
        else:
            return ""

    def change_temporal_format(value):
        """Change temporal format."""
        if "/" in value:
            result = []
            temp = value.split("/")
            for v in temp:
                r = change_date_format(v)
                if r:
                    result.append(r)
                else:
                    result = []
                    break
            if result:
                return str.join(" - ", result)
            else:
                return value
        else:
            result = change_date_format(value)
            return result if result else value

    def change_date_format(value):
        """Change date format from yyyy-MM-dd to yyyy/MM/dd."""
        result = None
        y_re = re.compile(r"^\d{4}$")
        ym_re = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
        ymd_re = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
        if y_re.match(value) or ym_re.match(value) or ymd_re.match(value):
            result = value.replace("-", "/")
        return result

    def get_value(data):
        """Get value for display one line flag."""
        temp_data = data.copy()
        lang_key = None
        value_key = None
        event_key = None
        date_key = None
        non_display_list = []
        key_list = list(data.keys())
        for k in key_list:
            item_name = ""
            flag = False
            if k in name_mapping:
                item_name = name_mapping[k]["item_name"]
                flag = name_mapping[k]["non_display"]
            if item_name in current_app.config["WEKO_RECORDS_LANGUAGE_TITLES"]:
                lang_key = k
            elif item_name in current_app.config["WEKO_RECORDS_EVENT_TITLES"]:
                event_key = k
            elif (
                not flag
                and item_name in current_app.config["WEKO_RECORDS_TIME_PERIOD_TITLES"]
            ):
                date_key = k
            elif not flag:
                if value_key:
                    value_key = None
                    break
                value_key = k
            if flag:
                non_display_list.append(k)
                temp_data.pop(k)

        data_type = None
        data_key = None
        split_data = "none"
        return_data = ""
        if date_key and event_key:
            data_type = "event"
            data_key = date_key
            split_data = data[event_key]
            date_value = change_temporal_format(data[date_key])
            if event_key in non_display_list:
                return_data = date_value
            else:
                return_data = "{}({})".format(date_value, data[event_key])
        elif date_key and (len(list(temp_data.keys())) == 1 or lang_key):
            data_type = "event"
            data_key = date_key
            split_data = "none_event"
            return_data = change_temporal_format(data[date_key])
        elif value_key and lang_key:
            data_type = "lang"
            data_key = value_key
            split_data = data[lang_key]
            if lang_key in non_display_list:
                return_data = data[value_key]
            else:
                return_data = "{}({})".format(data[value_key], data[lang_key])
        elif value_key and len(list(temp_data.keys())) == 1:
            data_type = "lang"
            data_key = value_key
            split_data = "none_lang"
            return_data = data[value_key]

        return data_type, data_key, split_data, return_data

    def to_sort_dict(alst, klst):
        """Sort item list.

        :param alst:
        :param klst:
        """
        if isinstance(klst, list):
            result = []
            try:
                if one_line_flag:
                    if isinstance(alst, list):
                        data_split = {}
                        value_key = None
                        data_type = None
                        for a in alst:
                            t, k, l, v = get_value(a)
                            if t == "lang":
                                if l in data_split:
                                    temp = data_split[l]
                                else:
                                    temp = []
                                    data_split[l] = temp
                                data_type = t
                                value_key = k
                                temp.append(v)
                            elif t == "event":
                                if "data" not in data_split:
                                    temp = []
                                    data_split["data"] = temp
                                else:
                                    temp = data_split["data"]
                                if l == "start":
                                    if "start" in data_split:
                                        temp.append(data_split.pop("start"))
                                    data_split["start"] = v
                                elif l == "end":
                                    if "start" in data_split:
                                        v = "{} - {}".format(data_split.pop("start"), v)
                                    temp.append(v)
                                else:
                                    if "start" in data_split:
                                        temp.append(data_split.pop("start"))
                                    temp.append(v)
                                data_type = t
                                value_key = k
                            else:
                                data_type = None
                                result = []
                                break
                        if data_type == "lang":
                            for k, v in data_split.items():
                                data_split[k] = str.join(", ", v)
                            result.append(
                                [{value_key: str.join("\n", list(data_split.values()))}]
                            )
                        elif data_type == "event":
                            if "start" in data_split:
                                data_split["data"].append(data_split.pop("start"))
                            result.append(
                                [{value_key: str.join(", ", data_split["data"])}]
                            )
                    elif isinstance(alst, dict):
                        data_type, value_key, l, v = get_value(alst)
                        if data_type is not None and value_key:
                            result.append([{value_key: v}])
                    if result:
                        return result
                if isinstance(alst, list):
                    for a in alst:
                        result.append(to_sort_dict(a, klst))
                else:
                    temp = []
                    for lst in klst:
                        keys = lst[0].split(".")
                        if keys[0].replace('[]', '') != root_key:
                            continue
                        key = keys[-1]
                        val = alst.pop(key, {})
                        name = get_name(key, False) or ""
                        hide = lst[3].get("hide") or (
                            non_display_flag and lst[3].get("non_display", False)
                        )

                        if key in ("creatorMail", "contributorMail", "mail"):
                            hide = hide | hide_email_flag
                        if val and (isinstance(val, str) or (key == "nameIdentifier")):
                            if (
                                name
                                in current_app.config["WEKO_RECORDS_TIME_PERIOD_TITLES"]
                            ):
                                val = change_temporal_format(val)
                            if not hide:
                                temp.append({key: val})
                        elif (
                            isinstance(val, list)
                            and len(val) > 0
                            and isinstance(val[0], str)
                        ):
                            if not hide:
                                temp.append({key: val})
                        else:
                            if check_has_attribute_value(val):
                                if not hide:
                                    res = to_sort_dict(val, klst)
                                    temp.append({key: res})
                        if not alst:
                            break
                    result.append(temp)
                return result
            except BaseException as e:
                current_app.logger.error("Function to_sort_dict error: ", e)
                return result

    def set_attribute_value(nlst):
        _list = []
        try:
            if isinstance(nlst, list):
                for lst in nlst:
                    _list.append(set_attribute_value(lst))
            # check OrderedDict is dict and not empty
            elif isinstance(nlst, dict) and bool(nlst):
                d = {}
                for key, val in nlst.items():
                    item_name = get_name(key) or ""
                    if val and (isinstance(val, str) or (key == "nameIdentifier")):
                        # the last children level
                        d[item_name] = val
                    elif (
                        isinstance(val, list)
                        and len(val) > 0
                        and isinstance(val[0], str)
                    ):
                        d[item_name] = ", ".join(val)
                    else:
                        # parents level
                        # check if have any child
                        if check_has_attribute_value(val):
                            d[item_name] = set_attribute_value(val)
                _list.append(d)
            return _list
        except BaseException as e:
            current_app.logger.error("Function set_node error: ", e)
            return _list

    get_name_mapping()
    orderdict = to_sort_dict(nlst, klst)
    alst = set_attribute_value(orderdict)

    return alst


def check_input_value(old, new):
    """Check different between old and new data.

    @param old:
    @param new:
    @return:
    """
    diff = False
    for k in old.keys():
        if old[k]["input_value"] != new[k]["input_value"]:
            diff = True
            break
    return diff


def remove_key(removed_key, item_val):
    """Remove removed_key out of item_val.

    @param removed_key:
    @param item_val:
    @return:
    """
    if not isinstance(item_val, dict):
        return
    if removed_key in item_val.keys():
        del item_val[removed_key]
    for k, v in item_val.items():
        remove_key(removed_key, v)


def remove_keys(excluded_keys, item_val):
    """Remove removed_key out of item_val.

    @param excluded_keys:
    @param item_val:
    @return:
    """
    if not isinstance(item_val, dict):
        return
    key_list = item_val.keys()
    for excluded_key in excluded_keys:
        if excluded_key in key_list:
            del item_val[excluded_key]
    for k, v in item_val.items():
        remove_keys(excluded_keys, v)


def remove_multiple(schema):
    """Remove multiple of schema.

    @param schema:
    @return:
    """
    for k in schema["properties"].keys():
        if "maxItems" and "minItems" in schema["properties"][k].keys():
            del schema["properties"][k]["maxItems"]
            del schema["properties"][k]["minItems"]
        if "items" in schema["properties"][k].keys():
            schema["properties"][k] = schema["properties"][k]["items"]


def check_to_upgrade_version(old_render, new_render):
    """Check upgrade or keep version by checking different renders data.

    @param old_render:
    @param new_render:
    @return:
    """
    if old_render.get("meta_list").keys() != new_render.get("meta_list").keys():
        return True
    # Check diff input value:
    if check_input_value(old_render.get("meta_list"), new_render.get("meta_list")):
        return True
    # Check diff schema
    old_schema = old_render.get("table_row_map").get("schema")
    new_schema = new_render.get("table_row_map").get("schema")

    excluded_keys = current_app.config["WEKO_ITEMTYPE_EXCLUDED_KEYS"]
    remove_keys(excluded_keys, old_schema)
    remove_keys(excluded_keys, new_schema)

    remove_multiple(old_schema)
    remove_multiple(new_schema)
    if old_schema != new_schema:
        return True
    return False


def remove_weko2_special_character(s: str):
    """Remove special character of WEKO2.

    :param s:
    """

    def __remove_special_character(_s_str: str):
        pattern = r"(^(&EMPTY&,|,&EMPTY&)|(&EMPTY&,|,&EMPTY&)$|&EMPTY&)"
        _s_str = re.sub(pattern, "", _s_str)
        if _s_str == ",":
            return ""
        return _s_str.strip() if _s_str != "," else ""

    s = s.strip()
    esc_str = ""
    for i in s:
        if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
            esc_str += i
    esc_str = __remove_special_character(esc_str)
    return esc_str


def selected_value_by_language(
    lang_array, value_array, lang_key_str, val_key_str, lang_selected, _item_metadata, meta_option={}, hide_list=[]
):
    """Select value by language.

    @param lang_array:
    @param value_array:
    @param lang_id:
    @param val_id:
    @param lang_selected:
    @param _item_metadata:
    @param meta_option:
    @param hide_list:
    @return:
    """
    result = None
    lang_key_list = lang_key_str.split(",")
    val_key_list = val_key_str.split(",")
    
    for val_key in val_key_list:
        val_parent_key = val_key.split(".")[0]
        val_sub_key = val_key.split(".")[-1]
        prop_hidden = meta_option.get(val_parent_key, {}).get('option', {}).get('hidden', False)
        for h in hide_list:
            if h.startswith(val_parent_key) and h.endswith(val_sub_key):
                prop_hidden = True

        for lang_key in lang_key_list:
            if val_parent_key == lang_key.split(".")[0]:
                if (
                    lang_array is not None
                    and (value_array is not None and len(value_array) > 0)
                    and isinstance(lang_selected, str)
                    and not prop_hidden
                ):
                    if len(lang_array) > 0:
                        for idx, lang in enumerate(lang_array):
                            lang_array[idx] = lang.strip()
                    if lang_selected in lang_array:  # Web screen display language
                        value = check_info_in_metadata(
                            lang_key, val_key, lang_selected, _item_metadata
                        )
                        if value is not None:
                            result = value

                    if len(value_array)>len(lang_array): # First title without language code
                        result = check_info_in_metadata(lang_key, val_key, None, _item_metadata)
                    
                    if not result and "ja-Latn" in lang_array:  # ja_Latn
                        value = check_info_in_metadata(
                            lang_key, val_key, "ja-Latn", _item_metadata
                        )
                        if value is not None:
                            result = value
                    if not result and "en" in lang_array and (
                        lang_selected != "ja"
                        or not current_app.config.get("WEKO_RECORDS_UI_LANG_DISP_FLG", False)
                    ):  # English
                        value = check_info_in_metadata(lang_key, val_key, "en", _item_metadata)
                        if value is not None:
                            result = value
                    # 1st language when registering items
                    if not result and len(lang_array) > 0:
                        noreturn = False
                        for idx, lg in enumerate(lang_array):
                            if current_app.config.get(
                                "WEKO_RECORDS_UI_LANG_DISP_FLG", False
                            ) and (
                                (lg == "ja" and lang_selected == "en")
                                or (lg == "en" and lang_selected == "ja")
                            ):
                                noreturn = True
                                break
                            if len(lg) > 0:
                                value = check_info_in_metadata(
                                    lang_key, val_key, lg, _item_metadata
                                )
                                if value is not None:
                                    result = value
                        if noreturn:
                            result = None
                    # 1st value when registering without language
                    if not result and len(value_array) > 0:
                        result = check_info_in_metadata(lang_key, val_key, None, _item_metadata)
            if not result:
                break
        if not result:
            if (
                (value_array is not None and len(value_array) > 0)
                and isinstance(lang_selected, str)
                and not prop_hidden
            ):
                result = check_info_in_metadata('', val_key, None, _item_metadata)
        if result:
            break
    return result


def check_info_in_metadata(str_key_lang, str_key_val, str_lang, metadata):
    """Check language and info corresponding in metadata.

    @param str_key_lang:
    @param str_key_val:
    @param str_lang:
    @param metadata:
    @return
    """
    if (
        (str_lang is None or len(str_lang) > 0)
        and len(metadata) > 0
        and str_key_val is not None
        and len(str_key_val) > 0
    ):
        if "." in str_key_lang:
            str_key_lang = str_key_lang.split(".")
        if "." in str_key_val:
            str_key_val = str_key_val.split(".")
        metadata = (
            metadata.get("_item_metadata") if "_item_metadata" in metadata else metadata
        )
        if str_key_val[0] in metadata:
            obj = metadata.get(str_key_val[0])
            if not isinstance(obj,list):
                obj = obj.get("attribute_value_mlt",obj)
            save = obj
            for ob in str_key_val:
                if (
                    ob not in str_key_val[0]
                    and ob not in str_key_val[len(str_key_val) - 1]
                ):
                    for x in save:
                        if x.get(ob):
                            save = x.get(ob)
            
            if isinstance(save, list):
                for s in save:
                    if s is not None and str_lang is None:
                        value = s
                        if isinstance(s,dict):
                            value = s.get(str_key_val[len(str_key_val) - 1])
                            if value:
                                value.strip()
                                if len(value) > 0:
                                    return value
                    
                    if (
                        s and str_key_lang 
                        and isinstance(s, dict)
                        and s.get(str_key_lang[-1])
                        and s.get(str_key_val[-1])
                    ):
                        if (
                            s.get(str_key_lang[-1]).strip() == str_lang.strip()
                            and str_key_val[-1] in s
                            and len(s.get(str_key_val[-1]).strip()) > 0
                        ):
                            return s.get(str_key_val[-1])
            elif isinstance(save, dict):
                if (
                    save.get(str_key_lang[-1])
                    and save.get(str_key_val[-1])
                    and save.get(str_key_lang[-1]).strip() == str_lang.strip()
                ):
                    return save.get(str_key_val[-1])

    return None


def get_value_and_lang_by_key(key, data_json, data_result, stt_key):
    """Get value and lang in json by key.

    @param key:
    @param data_json:
    @param data_result:
    @param stt_key:
    @return:
    """
    sys_comma = current_app.config.get("WEKO_RECORDS_SYSTEM_COMMA", "")
    if (
        (key is not None)
        and isinstance(key, str)
        and (data_json is not None)
        and (data_result is not None)
    ):
        save_key = ""
        key_split = key.split(".")
        if len(key_split) > 1:
            for i, k in enumerate(key_split):
                if k == key_split[len(key_split) - 1] and i == (len(key_split) - 1):
                    break
                save_key += str(k + ".") if i < len(key_split) - 2 else str(k)
        for j in data_json:
            if key == j["key"]:
                flag = False
                if save_key not in data_result.keys():
                    stt_key.append(save_key)
                    data_result = {**data_result, **{save_key: {}}}
                if (
                    save_key in data_result.keys()
                    and (j["title"].strip() in "Language")
                    or (j["title_ja"].strip() in "Language")
                    or (j["title_ja"].strip() in "言語")
                    or (j["title"].strip() in "言語")
                ):
                    data_result[save_key] = {
                        **data_result[save_key],
                        **{"lang": j["value"].split(sys_comma), "lang_id": key},
                    }
                    flag = True
                if key not in data_result[save_key] and not flag:
                    if "stt" not in data_result[save_key]:
                        data_result[save_key] = {**data_result[save_key], **{"stt": []}}
                    if "stt" in data_result[save_key]:
                        data_result[save_key]["stt"].append(key)
                    data_result[save_key] = {
                        **data_result[save_key],
                        **{key: {"value": j["value"].split(sys_comma)}},
                    }
        return data_result, stt_key
    else:
        return None


def get_value_by_selected_lang(source_title, current_lang):
    """Get value by selected lang.

    @param source_title: e.g. {'None Language': 'test', 'ja': 'テスト'}
    @param current_lang: e.g. 'ja'
    @return: e.g. 'テスト'
    """
    value_en = None
    value_latn = None
    title_data_langs = []
    title_data_langs_none = []
    for key, value in source_title.items():
        title = {}
        if not value:
            continue
        elif current_lang == key:
            return value
        else:
            title[key] = value
            if key == "en":
                value_en = value
            elif key == "ja-Latn":
                value_latn = value
            elif key == "None Language":
                title_data_langs_none.append(title)
            elif key:
                title_data_langs.append(title)

    if len(title_data_langs_none)>0:
        source = list(source_title.values())[0]
        target = list(title_data_langs_none[0].values())[0] 
        if source==target:
            return target
        
    if value_latn:
        return value_latn

    if value_en and (
        current_lang != "ja"
        or not current_app.config.get("WEKO_RECORDS_UI_LANG_DISP_FLG", False)
    ):
        return value_en

    if len(title_data_langs) > 0:
        if current_lang == "en":
            for t in title_data_langs:
                if list(t)[0] != "ja" or not current_app.config.get(
                    "WEKO_RECORDS_UI_LANG_DISP_FLG", False
                ):
                    return list(t.values())[0]
        else:
            return list(title_data_langs[0].values())[0]

    if len(title_data_langs_none) > 0:
        return list(title_data_langs_none[0].values())[0]
    else:
        return None


def get_show_list_author(solst_dict_array, hide_email_flag, author_key, creates):
    """Get show list author.

    @param solst_dict_array:
    @param hide_email_flag:
    @param author_key:
    @param creates:
    @return:
    """
    remove_show_list_create = []
    for s in solst_dict_array:
        option = s["option"]
        parent_option = s["parent_option"]
        is_show_list = (
            parent_option.get("show_list")
            if parent_option and parent_option.get("show_list")
            else option.get("show_list")
        )
        is_hide = (
            parent_option.get("hide")
            if parent_option and parent_option.get("hide")
            else option.get("hide")
        )
        if (
            "creatorMails[].creatorMail" in s["key"]
            or "contributorMails[].contributorMail" in s["key"]
            or "mails[].mail" in s["key"]
        ):
            is_hide = is_hide | hide_email_flag

        if author_key != s["key"] and author_key in s["key"]:
            sub_author_key = s["key"].split(".")[-1]
            key_creator = ["creatorName", "familyName", "givenName"]
            if sub_author_key in key_creator and (is_hide or not is_show_list):
                remove_show_list_create.append(sub_author_key + "s")

    return format_creates(creates, remove_show_list_create)


def format_creates(creates, hide_creator_keys):
    """Format creates.

    @param creates:
    @param hide_creator_keys:
    @return:
    """
    current_lang = current_i18n.language
    result_ends = []
    for create in creates:
        result_end = {}
        # get creator comments
        result_end = get_creator(create, result_end, hide_creator_keys, current_lang)
        # get alternatives comments
        if "creatorAlternatives" in create:
            alternatives_key = current_app.config["WEKO_RECORDS_ALTERNATIVE_NAME_KEYS"]
            result_end = get_author_has_language(
                create["creatorAlternatives"],
                result_end,
                current_lang,
                alternatives_key,
            )
        # get affiliations comments
        if "creatorAffiliations" in create:
            affiliation_key = current_app.config["WEKO_RECORDS_AFFILIATION_NAME_KEYS"]
            result_end = get_affiliation(
                create["creatorAffiliations"], result_end, current_lang, affiliation_key
            )
        result_ends.append(result_end)
    return result_ends


def get_creator(create, result_end, hide_creator_keys, current_lang):
    """Get creator, family name, given name.

    @param create:
    @param result_end:
    @param hide_creator_keys:
    @param current_lang:
    @return:
    """
    creates_key = {
        "creatorNames": ["creatorName", "creatorNameLang"],
        "familyNames": ["familyName", "familyNameLang"],
        "givenNames": ["givenName", "givenNameLang"],
    }
    if hide_creator_keys:
        for key in hide_creator_keys:
            if creates_key:
                del creates_key[key]
    result = get_creator_by_languages(creates_key, create)
    creator = get_value_by_selected_lang(result, current_lang)
    if creator:
        for key, value in creates_key.items():
            if key in creator:
                if value[0] not in result_end:
                    result_end[value[0]] = []
                if isinstance(creator, dict):
                    result_end[value[0]].append(creator[key])
    return result_end


def get_creator_by_languages(creates_key, create):
    """Get creator data by languages.

    @param creates_key:
    @param create:
    @return:
    """
    result = {}
    for key, value in creates_key.items():
        if key in create:
            is_added = []
            for val in create[key]:
                key_data = val.get(value[1], "None Language")
                value_data = val.get(value[0])
                if not value_data:
                    continue
                if key_data not in is_added:
                    if key_data not in result:
                        result[key_data] = {}
                        result[key_data][key] = value_data
                        is_added.append(key_data)
                    else:
                        result[key_data][key] = value_data
                        is_added.append(key_data)
    return result


def get_affiliation(affiliations, result_end, current_lang, affiliation_key):
    """Get affiliation show list.

    @param affiliations:
    @param result_end:
    @param current_lang:
    @param affiliation_key:
    @return:
    """
    for name_affiliation in affiliations:
        for key, value in name_affiliation.items():
            if key == "affiliationNames":
                result_end = get_author_has_language(
                    value, result_end, current_lang, affiliation_key
                )
    return result_end


def get_author_has_language(creator, result_end, current_lang, map_keys):
    """Get author has language.

    @param creator:
    @param result_end:
    @param current_lang:
    @param map_keys:
    @return:
    """
    result = {}
    is_added = []
    for val in creator:
        key_data = val.get(map_keys[1], "None Language")
        value_data = val.get(map_keys[0])
        if not value_data:
            continue
        if key_data not in is_added:
            if key_data not in result:
                result[key_data] = []
                result[key_data].append(value_data)
                is_added.append(key_data)
            else:
                result[key_data].append(value_data)
                is_added.append(key_data)
    alternative = get_value_by_selected_lang(result, current_lang)
    if alternative:
        if map_keys[0] not in result_end:
            result_end[map_keys[0]] = []
        if isinstance(alternative, str):
            result_end[map_keys[0]].append(alternative)
        elif isinstance(alternative, list):
            result_end[map_keys[0]] += alternative

    return result_end


def add_author(
    author_data,
    stt_key,
    is_specify_newline_array,
    s,
    value,
    data_result,
    is_specify_newline,
    is_hide,
    is_show_list,
):
    """Add author in show list result.

    @param author_data:
    @param stt_key:
    @param is_specify_newline_array:
    @param s:
    @param value:
    @param data_result:
    @param is_specify_newline:
    @param is_hide:
    @param is_show_list:
    @return:
    """
    list_author_key = current_app.config["WEKO_RECORDS_AUTHOR_KEYS"]
    sub_author_key = s["key"].split(".")[-1]
    if (
        sub_author_key in current_app.config["WEKO_RECORDS_AUTHOR_NONE_LANG_KEYS"]
        and not is_hide
        and is_show_list
    ):
        stt_key.append(sub_author_key)
        is_specify_newline_array.append({sub_author_key: is_specify_newline})
        data_result.update({sub_author_key: {sub_author_key: {"value": [value]}}})
    elif (
        sub_author_key in list_author_key
        and sub_author_key in author_data
        and not is_hide
        and is_show_list
    ):
        stt_key.append(sub_author_key)
        is_specify_newline_array.append({sub_author_key: is_specify_newline})
        data_result.update(
            {sub_author_key: {sub_author_key: {"value": author_data[sub_author_key]}}}
        )
    return stt_key, data_result, is_specify_newline_array


def convert_bibliographic(data_sys_bibliographic):
    """Add author in show list result.

    @param data_sys_bibliographic:
    @return:
    """
    list_data = []
    for bibliographic_value in data_sys_bibliographic:
        if bibliographic_value.get("title_attribute_name"):
            list_data.append(bibliographic_value.get("title_attribute_name"))
        for magazine in bibliographic_value.get("magazine_attribute_name"):
            for key in magazine:
                list_data.append(key + " " + magazine[key])
    return ", ".join(list_data)


def add_biographic(
    sys_bibliographic,
    bibliographic_key,
    s,
    stt_key,
    data_result,
    is_specify_newline_array,
):
    """Add author in show list result.

    @param sys_bibliographic:
    @param bibliographic_key:
    @param is_specify_newline_array:
    @param s:
    @param stt_key:
    @param data_result:
    @return:
    """
    bibliographic = convert_bibliographic(
        sys_bibliographic.get_bibliographic_list(True)
    )
    stt_key.append(bibliographic_key)
    is_specify_newline_array.append({s["key"]: True})
    data_result.update({bibliographic_key: {s["key"]: {"value": [bibliographic]}}})

    return stt_key, data_result, is_specify_newline_array


def custom_record_medata_for_export(record_metadata: dict):
    """Custom record mata for export.

    :param record_metadata:
    """
    from weko_records_ui.utils import (
        display_oaiset_path,
        hide_item_metadata,
        replace_license_free,
    )

    hide_item_metadata(record_metadata)
    replace_license_free(record_metadata)
    display_oaiset_path(record_metadata)


def replace_fqdn(url_path: str, host_url: str = None) -> str:
    """Replace to new FQDN.

    Args:
        url_path (str): string url.
        host_url (str): string host.

    Returns:
        (str): URL with FQDN replaced.

    """
    if host_url is None:
        host_url = current_app.config["THEME_SITEURL"]
    url_pattern = r"^http[s]{0,1}:\/\/"
    if re.search(url_pattern, url_path) is None:
        url_path = host_url + url_path
    elif host_url not in url_path:
        if host_url[-1] != "/":
            host_url = host_url + "/"
        pattern = r"https?:\/\/([\w-]+(\.\w)*)+(:\d+)?\/"
        url_path = re.sub(pattern, host_url, url_path)
    return url_path


def replace_fqdn_of_file_metadata(file_metadata_lst: list, file_url: list = None):
    """Replace FQDN of file metadata.

    Args:
        file_metadata_lst (list): File metadata list.
        file_url (list): File metadata list.
    """
    for file in file_metadata_lst:
        if file.get("url", {}).get("url"):
            if file.get("version_id"):
                file["url"]["url"] = replace_fqdn(file["url"]["url"])
            elif isinstance(file_url, list):
                file_url.append(file["url"]["url"])
