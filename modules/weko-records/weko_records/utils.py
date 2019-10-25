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
from collections import OrderedDict

import pytz
from flask import current_app
from flask_security import current_user
from invenio_pidstore import current_pidstore
from invenio_pidstore.ext import pid_exists
from weko_schema_ui.schema import SchemaTree

from .api import ItemTypes, Mapping


def json_loader(data, pid):
    """Convert the item data and mapping to jpcoar.

    :param data: json from item form post.
    :param pid: pid value.
    :return: dc, jrc, is_edit
    """
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
    index = data["$schema"].rfind('/')
    item_type_id = data["$schema"][index + 1:]

    # get item type mappings
    ojson = ItemTypes.get_record(item_type_id)
    mjson = Mapping.get_record(item_type_id)

    if ojson and mjson:
        mp = mjson.dumps()
        data.get("$schema")
        for k, v in data.items():
            if k != "pubdate":
                if k == "$schema" or mp.get(k) is None:
                    continue

            item.clear()
            try:
                item["attribute_name"] = ojson["properties"][k]["title"] \
                    if ojson["properties"][k].get("title") is not None else k
            except Exception:
                pub_date_setting = {
                    "type": "string",
                    "title": "Publish Date",
                    "format": "datetime"
                }
                ojson["properties"]["pubdate"] = pub_date_setting
                item["attribute_name"] = 'Publish Date'
            # set a identifier to add a link on detail page when is a creator field
            # creator = mp.get(k, {}).get('jpcoar_mapping', {})
            # creator = creator.get('creator') if isinstance(
            #     creator, dict) else None
            iscreator = False
            creator = ojson["properties"][k]
            if 'object' == creator["type"]:
                creator = creator["properties"]
                if 'iscreator' in creator:
                    iscreator = True
            elif 'array' == creator["type"]:
                creator = creator['items']["properties"]
                if 'iscreator' in creator:
                    iscreator = True
            if iscreator:
                item["attribute_type"] = 'creator'

            item_data = ojson["properties"][k]
            if 'array' == item_data.get('type'):
                properties_data = item_data['items']['properties']
                if 'filename' in properties_data:
                    item["attribute_type"] = 'file'

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
            if k != "pubdate":
                item.update(mp.get(k))
            else:
                pubdate = v
            jpcoar[k] = item.copy()

    # convert to es jpcoar mapping data
    jrc = SchemaTree.get_jpcoar_json(jpcoar)

    if dc:
        # get the tile name to detail page
        title = data.get("title")

        if 'control_number' in dc:
            del dc['control_number']

        dc.update(dict(item_title=title))
        dc.update(dict(item_type_id=item_type_id))
        dc.update(dict(control_number=pid))

        oai_value = current_app.config.get(
            'OAISERVER_ID_PREFIX', '') + str(pid)
        is_edit = pid_exists(oai_value, 'oai')
        if not is_edit:
            oaid = current_pidstore.minters['oaiid'](item_id, dc)
            oai_value = oaid.pid_value
        # relation_ar = []
        # relation_ar.append(dict(value="", item_links="", item_title=""))
        # jrc.update(dict(relation=dict(relationType=relation_ar)))
        # dc.update(dict(relation=dict(relationType=relation_ar)))
        jrc.update(dict(control_number=pid))
        jrc.update(dict(_oai={"id": oai_value}))
        jrc.update(dict(_item_metadata=dc))
        jrc.update(dict(itemtype=ojson.model.item_type_name.name))
        jrc.update(dict(publish_date=pubdate))

        # save items's creator to check permission
        if current_user:
            current_user_id = current_user.get_id()
        else:
            current_user_id = '1'
        if current_user_id:
            # jrc is saved on elastic
            jrc_weko_shared_id = jrc.get("weko_shared_id", None)
            jrc_weko_creator_id = jrc.get("weko_creator_id", None)
            if not jrc_weko_creator_id:
                # in case first time create record
                jrc.update(dict(weko_creator_id=current_user_id))
                jrc.update(dict(weko_shared_id=data.get('shared_user_id',
                                                        None)))
            else:
                # incase record is end and someone is updating record
                if current_user_id == int(jrc_weko_creator_id):
                    # just allow owner update shared_user_id
                    jrc.update(dict(weko_shared_id=data.get('shared_user_id',
                                                            None)))

            # dc js saved on postgresql
            dc_owner = dc.get("owner", None)
            if not dc_owner:
                dc.update(
                    dict(
                        weko_shared_id=data.get(
                            'shared_user_id',
                            None)))
                dc.update(dict(owner=current_user_id))
            else:
                if current_user_id == int(dc_owner):
                    dc.update(dict(weko_shared_id=data.get('shared_user_id',
                                                           None)))

    del ojson, mjson, item
    return dc, jrc, is_edit


def set_timestamp(jrc, created, updated):
    """Set timestamp."""
    jrc.update(
        {"_created": pytz.utc.localize(created)
            .isoformat() if created else None})

    jrc.update(
        {"_updated": pytz.utc.localize(updated)
            .isoformat() if updated else None})


def make_itemlist_desc(es_record):
    """Make itemlist description."""
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
                val['index'] = index
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


def get_all_items(nlst, klst, is_get_name=False):
    """Convert and sort item list.

    :param nlst:
    :param klst:
    :param is_get_name:
    :return: alst
    """
    def get_name(key):
        for lst in klst:
            key_arr = lst[0].split('.')
            k = key_arr[-1]
            if key != k:
                continue
            item_name = lst[1]
            if len(key_arr) >= 3:
                parent_key = key_arr[-2].replace('[]', '')
                item_name = item_name + '.' + get_name(parent_key)

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
                            d[k + '.name'] = item_name
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
    """
    alst = []

    # def get_name(key):
    #     for lst in klst:
    #         k = lst[0].split('.')[-1]
    #         if key == k:
    #             return lst[1]
    def get_items(nlst):
        if isinstance(nlst, dict):
            for k, v in nlst.items():
                if isinstance(v, str):
                    alst.append({k: v})
                else:
                    get_items(v)
        elif isinstance(nlst, list):
            for lst in nlst:
                get_items(lst)

    to_orderdict(nlst, klst)
    get_items(nlst)
    return alst


def to_orderdict(alst, klst):
    """Sort item list.

    :param alst:
    :param klst:
    """
    if isinstance(alst, list):
        for i in range(len(alst)):
            if isinstance(alst[i], dict):
                alst.insert(i, OrderedDict(alst.pop(i)))
                to_orderdict(alst[i], klst)
    elif isinstance(alst, dict):
        nlst = []
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


def get_options_and_order_list(item_type_id):
    """Get Options by item type id.

    :param item_type_id:
    :return: options dict and sorted list
    """
    ojson = ItemTypes.get_record(item_type_id)
    solst = find_items(ojson.model.form)
    meta_options = ojson.model.render.pop('meta_fix')
    meta_options.update(ojson.model.render.pop('meta_list'))
    return solst, meta_options


def sort_meta_data_by_options(record_hit):
    """Reset metadata by '_options'.

    :param record_hit:
    """
    try:

        src = record_hit['_source'].pop('_item_metadata')
        item_type_id = record_hit['_source'].get('item_type_id') \
            or src.get('item_type_id')
        if not item_type_id:
            return

        items = []
        solst, meta_options = get_options_and_order_list(item_type_id)

        newline = True
        for lst in solst:
            key = lst[0]

            val = src.get(key)
            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                continue

            hidden = option.get("hidden")
            multiple = option.get('multiple')
            crtf = option.get("crtf")
            showlist = option.get("showlist")
            is_show = False if hidden else showlist

            if not is_show:
                continue

            mlt = val.get('attribute_value_mlt')
            if mlt:
                data = list(map(lambda x: ''.join(x.values()),
                                get_all_items(mlt, solst)))
            else:
                data = val.get('attribute_value')

            if data:
                if isinstance(data, list):
                    data = ",".join(data) if multiple else \
                        (data[0] if len(data) > 0 else "")

                if newline:
                    items.append(data)
                else:
                    items[-1] += "," + data

            newline = crtf

        if items:
            record_hit['_source']['_comment'] = items
    except Exception:
        current_app.logger.exception(
            u'Record serialization failed {}.'.format(
                str(record_hit['_source'].get('control_number'))))
    return


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
    if 'openaire_subtype' not in resource_type:
        return True
    oa_subtype = resource_type['openaire_subtype']
    prefix = oa_subtype.split(':')[0] if ':' in oa_subtype else ''

    cfg = current_openaire.openaire_communities
    defined_comms = [c for c in cfg.get(prefix, {}).get('communities', [])]
    type_ = resource_type['type']
    subtypes = cfg.get(prefix, {}).get('types', {}).get(type_, [])
    # Check if the OA subtype is defined in config and at least one of its
    # corresponding communities is present
    is_defined = any(t['id'] == oa_subtype for t in subtypes)
    comms_match = len(set(communities) & set(defined_comms))
    return is_defined and comms_match
