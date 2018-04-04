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

import re
import pytz

from flask import current_app
from invenio_pidstore import current_pidstore
from invenio_pidstore.ext import pid_exists
from collections import OrderedDict
from .api import ItemTypes, Mapping


def save_item_metadata(rejson, pid):
    """Save the item.

    :param rejson: json from item form post.
    :param pid: pid value.
    """
    dc = OrderedDict()
    ju = OrderedDict()
    item = dict()
    ar = []

    if not isinstance(rejson, dict) or rejson.get("$schema") is None:
        return

    item_id = pid.object_uuid
    pid = pid.pid_value

    # find the item type identifier
    index = rejson["$schema"].rfind('/')
    item_type_id = rejson["$schema"][index + 1:]

    # get itemtype mapping file json data
    ojson = ItemTypes.get_record(item_type_id)
    mjson = Mapping.get_record(item_type_id)
    # fjson = FilesMetadata.get_records(pid)

    # sort items
    rejson = sort_records(rejson, ojson.model.form)
    if ojson and mjson:
        mp = mjson.dumps()
        rejson.get("$schema")
        for k, v in rejson.items():
            if k == "$schema" or mp.get(k) is None:
                continue

            item.clear()
            item["attribute_name"] = ojson["properties"][k]["title"] \
                if ojson["properties"][k].get("title") is not None else k
            if isinstance(v, list):
                if len(v) > 0 and isinstance(v[0], dict):
                    item["attribute_value_mlt"] = v
                else:
                    item["attribute_value"] = v
            elif isinstance(v, dict):
                ar.append(v)
                item["attribute_value_mlt"] = ar
                ar = []
            else:
                item["attribute_value"] = v

            dc[k] = item.copy()
            item.update(mp.get(k))
            ju[k] = item.copy()

    if dc:
        # get the tile name to detail page
        title = rejson.get("title_ja") or rejson.get("title_en")

        if 'control_number' in dc:
            del dc['control_number']

        dc.update(dict(item_title=title))
        dc.update(dict(item_type_id=item_type_id))
        dc.update(dict(control_number=pid))

        # convert to junii2 schema for es
        current_app.logger.debug(ju)
        jrc = to_junii2(ju, ojson.model)

        make_itemlist_desc(jrc)

        oai_value = current_app.config.get('OAISERVER_ID_PREFIX', '') + str(pid)
        is_edit = pid_exists(oai_value, 'oai')
        if not is_edit:
            oaid = current_pidstore.minters['oaiid'](item_id, dc)
            oai_value = oaid.pid_value

        jrc.update(dict(control_number=pid))
        jrc.update(dict(_oai={"id": oai_value}))
        jrc.update(dict(_item_metadata=dc))
        jrc.update(dict(itemtype=ojson.model.item_type_name.name))

    del ojson, mjson
    return dc, jrc, is_edit


def set_timestamp(jrc, created, updated):
    jrc.update(
        {"_created": pytz.utc.localize(created)
            .isoformat() if created else None})

    jrc.update(
        {"_updated": pytz.utc.localize(updated)
            .isoformat() if updated else None})


def to_junii2(records, model):
    """
    Convert to junii2 json.
    :param records:
    :param render:
    :return: j
    """
    render = model.render
    meta_lst = render.get("meta_list", {}) if isinstance(render, dict) else {}
    meta_fix = render.get("meta_fix", {}) if isinstance(render, dict) else {}
    op_flg = False if (len(meta_lst) == 0 or len(meta_fix) == 0) else True

    j = dict()
    op = dict()
    ttp = dict()
    _v = "@value"
    idx = 0

    def analysis(field):
        index = 1
        exp = (",",)
        return exp[0], field.split(exp[0])

    def merge_field(key, val, k):
        """
        Merge duble key.
        :param key: junii2 key
        :param val: value of list
        :param k:   item key
        :return:
        """
        nonlocal idx
        # if exist key
        arr = j.get(key)
        arr2 = op.get(key)
        opts = (meta_lst.get(k) or meta_fix.get(k) or {}).get("option", {})
        opts['_ori_key'] = k
        opts['_ori_title'] = (meta_lst.get(k) or meta_fix.get(k) or {}).get(
            "title", "")
        ttp.update({k: key})
        if arr:
            if isinstance(arr, list):
                if isinstance(val, list):
                    arr.extend(val)
                else:
                    arr.append(val)
            else:
                tmp = []
                tmp.append(arr)
                if isinstance(val, list):
                    tmp.extend(val)
                else:
                    tmp.append(val)
                j[key] = tmp

            if op_flg:
                if isinstance(arr2, dict):
                    if not arr2.get('0'):
                        op[key] = {}
                        op[key].update({'0': arr2})
                    idx = len(op[key])
                    if isinstance(val, list):
                        for i in range(len(val)):
                            idx = idx + i
                            op[key].update({str(idx): opts})
                    else:
                        op[key].update({str(idx): opts})
        else:
            j[key] = val
            if op_flg:
                if isinstance(val, list):
                    op[key] = {}
                    for i in range(len(val)):
                        op[key].update({str(i): opts})
                else:
                    op[key] = opts

    for k, y in records.items():
        if isinstance(y, dict) and not re.match("^_\*?", k):
            mpdic = y.get("junii2_mapping")
            if isinstance(mpdic, dict):
                # List or string
                atr_v = y.get('attribute_value')
                # List of dict
                atr_vm = y.get('attribute_value_mlt')
                for k1, v1 in mpdic.items():
                    if atr_v:
                        if isinstance(atr_v, list):
                            # checkbox array
                            merge_field(k1, ','.join(atr_v), k)
                        else:
                            merge_field(k1, atr_v, k)
                    elif atr_vm:
                        if isinstance(v1, dict) and _v in v1:
                            # filemeta
                            vle = v1.get(_v)
                            if isinstance(vle, str):
                                # if vl have expression or formula
                                exp, lk = analysis(vle)
                                alt = []
                                for lst in atr_vm:
                                    if isinstance(lst, dict):
                                        ava = ""
                                        for val in lk:
                                            ava = ava + exp + lst.get(val)
                                        alt.append(ava[1:])
                                merge_field(k1, alt, k)
                        elif isinstance(v1, str):
                            atr_vm_str = ''
                            for atr_vm_li in atr_vm:
                                if isinstance(atr_vm_li,
                                              dict) and 'interim' in atr_vm_li:
                                    # text array
                                    atr_vm_str = atr_vm_str + atr_vm_li.get(
                                        'interim') + ','
                            atr_vm_str = atr_vm_str[:-1] if len(
                                atr_vm_str) > 0 else atr_vm_str
                            merge_field(k1, atr_vm_str, k)
    if len(op) > 0:
        j.update({"_options": sort_op(op, ttp, model.form)})
    return j


def make_itemlist_desc(es_record):
    rlt = ""
    src = es_record
    op = src.pop("_options", {})
    ignore_meta = ('title', 'alternative', 'fullTextURL')
    if isinstance(op, dict):
        src["_comment"] = []
        for k, v in sorted(op.items(),
                           key=lambda x: x[1]['index'] if x[1].get(
                               'index') else x[0]):
            if k in ignore_meta:
                continue
            # item value
            vals = src.get(k)
            if isinstance(vals, list):
                # index, options
                v.pop('index', "")
                for k1, v1 in sorted(v.items()):
                    i = int(k1)
                    if i < len(vals):
                        crtf = v1.get("crtf")
                        showlist = v1.get("showlist")
                        hidden = v1.get("hidden")
                        is_show = False if hidden else showlist
                        # list index value
                        if is_show:
                            rlt = rlt + ((vals[i] + ",") if not crtf
                                         else vals[i] + "\n")
            elif isinstance(vals, str):
                crtf = v.get("crtf")
                showlist = v.get("showlist")
                hidden = v.get("hidden")
                is_show = False if hidden else showlist
                if is_show:
                    rlt = rlt + ((vals + ",") if not crtf
                                 else vals + "\n")
        if len(rlt) > 0:
            if rlt[-1] == ',':
                rlt = rlt[:-1]
            src['_comment'] = rlt.split('\n')
            if len(src['_comment'][-1]) == 0:
                src['_comment'].pop()


def sort_records(records, form):
    """
    sort records
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
    """
    sort options dict
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
                val['index'] = index
                odd.update({key: val})

        record.clear()
        del record
        return odd
    else:
        return record


def find_items(form):
    """
    find sorted items into a list
    :param form:
    :return: lst
    """
    lst = []

    def find_key(node):
        if isinstance(node, dict):
            key = node.get('key')
            title = node.get('title')
            # type = node.get('type')
            if key:
                # title = title[title.rfind('.')+1:]
                yield [key, title or ""]
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


def get_all_items(nlst, klst):
    """
    convert and sort item list
    :param nlst:
    :param klst:
    :return: alst
    """
    alst = []

    def get_name(key):
        for lst in klst:
            k = lst[0].split('.')[-1]
            if key == k:
                return lst[1]

    def get_items(nlst):
        if isinstance(nlst, dict):
            for k, v in nlst.items():
                if isinstance(v, str):
                    alst.append({get_name(k): v})
                else:
                    get_items(v)
        elif isinstance(nlst, list):
            for lst in nlst:
                get_items(lst)

    to_orderdict(nlst, klst)
    get_items(nlst)
    return alst


def to_orderdict(alst, klst):
    """
    sort item list
    :param alst:
    :param klst:
    """
    if isinstance(alst, list):
        for i in range(len(alst)):
            if isinstance(alst[i], dict):
                alst.insert(i, OrderedDict(alst.pop(i)))
                to_orderdict(alst[i], klst)
    elif isinstance(alst, dict):
        nlst=[]
        if isinstance(klst, list):
            for lst in klst:
                key = lst[0].split('.')[-1]
                val = alst.pop(key, {})
                if val:
                    if isinstance(val, dict):
                        val = OrderedDict(val)
                    nlst.append({key: val})
                if not alst:
                    break

            while len(nlst) > 0:
                alst.update(nlst.pop(0))

            for k, v in alst.items():
                if not isinstance(v, str):
                    to_orderdict(v, klst)
