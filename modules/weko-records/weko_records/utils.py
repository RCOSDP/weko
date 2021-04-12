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
import re
from collections import OrderedDict

import pytz
from flask import current_app
from flask_security import current_user
from invenio_i18n.ext import current_i18n
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.ext import pid_exists
from invenio_pidstore.models import PersistentIdentifier
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

    if not (ojson and mjson):
        raise RuntimeError('Item Type {} does not exist.'.format(item_type_id))

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

        if 'control_number' in dc:
            del dc['control_number']

        dc.update(dict(item_title=title))
        dc.update(dict(item_type_id=item_type_id))
        dc.update(dict(control_number=pid))

        # check oai id value
        is_edit = False
        try:
            oai_value = PersistentIdentifier.get_by_object(
                pid_type='oai',
                object_type='rec',
                object_uuid=PersistentIdentifier.get('recid', pid).object_uuid
            ).pid_value
            is_edit = pid_exists(oai_value, 'oai')
        except PIDDoesNotExistError:
            pass

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
            title = node.get('title', '')
            try:
                # Try catch for case this function is called from celery app
                current_lang = current_i18n.language
            except Exception:
                current_lang = 'en'
            title_i18n = node.get('title_i18n', {}) \
                .get(current_lang, title)
            option = {
                'required': node.get('required', False),
                'show_list': node.get('isShowList', False),
                'specify_newline': node.get('isSpecifyNewline', False),
                'hide': node.get('isHide', False),
            }
            val = ''
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
            key_arr = lst[0].split('.')
            k = key_arr[-1]
            if key != k:
                continue
            item_name = lst[1]
            if len(key_arr) >= 3:
                parent_key = key_arr[-2].replace('[]', '')
                parent_key_name = get_name(parent_key)
                if item_name and parent_key_name:
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
                    nlst.append({lst[0]: val})
                if not alst:
                    break

            while len(nlst) > 0:
                alst.update(nlst.pop(0))

            for k, v in alst.items():
                if not isinstance(v, str):
                    to_orderdict(v, klst)


def get_options_and_order_list(item_type_id, ojson=None):
    """Get Options by item type id.

    :param item_type_id:
    :param ojson:
    :return: options dict and sorted list
    """
    if ojson is None:
        ojson = ItemTypes.get_record(item_type_id)
    solst = find_items(ojson.model.form)
    meta_options = ojson.model.render.get('meta_fix')
    meta_options.update(ojson.model.render.get('meta_list'))
    return solst, meta_options


async def sort_meta_data_by_options(
    record_hit, settings, item_type_mapping, item_type_data,
):
    """Reset metadata by '_options'.

    :param record_hit:
    :param settings:
    :param item_type_mapping:
    :param item_type_data:
    """
    from weko_deposit.api import _FormatSysBibliographicInformation
    from weko_records_ui.permissions import check_file_download_permission
    from weko_records_ui.utils import hide_item_metadata
    from weko_search_ui.utils import get_data_by_propertys

    from weko_records.serializers.utils import get_mapping

    web_screen_lang = current_i18n.language

    def convert_data_to_dict(solst):
        """Convert solst to dict."""
        solst_dict_array = []
        for lst in solst:
            key = lst[0]
            option = meta_options.get(key, {}).get('option')
            temp = {
                'key': key,
                'title': lst[1],
                'title_ja': lst[2],
                'option': lst[3],
                'parent_option': option,
                'value': ''
            }
            solst_dict_array.append(temp)
        return solst_dict_array

    def get_author_comment(data_result, key, result, is_specify_newline_array):
        value = data_result[key].get(key, {}).get('value', [])
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
        list_author_key = current_app.config['WEKO_RECORDS_AUTHOR_KEYS']
        for idx, key in enumerate(stt_key):
            lang_id = ''
            if key in data_result and data_result[key] is not None:
                if key in list_author_key:
                    result = get_author_comment(data_result, key, result,
                                                is_specify_newline_array)
                else:
                    if 'lang_id' in data_result[key]:
                        lang_id = data_result[key].get('lang_id') \
                            if "[]" not in data_result[key].get('lang_id') \
                            else data_result[key].get('lang_id').replace("[]", '')
                    data = ''
                    if "stt" in data_result[key] and data_result[key].get(
                            "stt") is not None:
                        data = data_result[key].get("stt")
                    else:
                        data = data_result.get(key)
                    for idx2, d in enumerate(data):
                        if d not in "lang" and d not in "lang_id":
                            lang_arr = []
                            if 'lang' in data_result[key]:
                                lang_arr = data_result[key].get('lang')
                            if (key in data_result) and (
                                d in data_result[key]) and (
                                    'value' in data_result[key][d]):
                                value_arr = data_result[key][d]['value']
                                value = selected_value_by_language(
                                    lang_arr, value_arr, lang_id,
                                    d.replace("[]", ''), web_screen_lang,
                                    _item_metadata
                                )
                                if value is not None and len(value) > 0:
                                    for index, n in enumerate(
                                            is_specify_newline_array):
                                        if d in n:
                                            if n[d] or len(result) == 0:
                                                result.append(value)
                                            else:
                                                result[-1] += "," + value
                                            break
        return result

    def get_comment(solst_dict_array, hide_email_flag, _item_metadata, src,
                    solst):
        """Check and get info."""
        result = []
        data_result = {}
        stt_key = []
        _ignore_items = list()
        _license_dict = current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
        is_specify_newline_array = []
        bibliographic_key = None
        author_key = None
        author_data = {}
        if _license_dict:
            _ignore_items.append(_license_dict[0].get('value'))
        for i, s in enumerate(solst_dict_array):
            value = s['value']
            option = s['option']
            parent_option = s['parent_option']
            # Get show list flag.
            is_show_list = parent_option.get(
                'show_list') if parent_option and parent_option.get(
                'show_list') else option.get('show_list')
            # Get specify newline flag.
            is_specify_newline = parent_option.get(
                'specify_newline') if parent_option and parent_option.get(
                'specify_newline') else option.get('specify_newline')
            # Get hide flag.
            is_hide = parent_option.get('hide') if parent_option and \
                parent_option.get('hide') else option.get('hide')
            # Get hide email flag
            if 'creatorMails[].creatorMail' in s['key'] \
                or 'contributorMails[].contributorMail' in s['key'] \
                    or 'mails[].mail' in s['key']:
                is_hide = is_hide | hide_email_flag
            # Get creator flag.
            is_author = src.get(s['key'], {}).get('attribute_type',
                                                  {}) == 'creator'

            if author_key and author_key in s['key']:
                stt_key, data_result, is_specify_newline_array = add_author(
                    author_data, stt_key, is_specify_newline_array, s, value,
                    data_result, is_specify_newline, is_hide, is_show_list)
            elif is_author:
                # Format creator data to display on item list
                author_key = s['key']
                attr_mlt = src.get(s['key'], {}).get('attribute_value_mlt', {})
                author_data = get_show_list_author(
                    solst_dict_array, hide_email_flag, author_key, attr_mlt
                )
            elif bibliographic_key is None and is_show_list and \
                    'bibliographic_titles' in s['key']:
                # Format bibliographic data to display on item list
                bibliographic_key = s['key'].split(".")[0].replace('[]', '')
                mlt_bibliographic = src.get(bibliographic_key, {}).get(
                    'attribute_value_mlt')
                if mlt_bibliographic:
                    sys_bibliographic = _FormatSysBibliographicInformation(
                        copy.deepcopy(mlt_bibliographic),
                        copy.deepcopy(solst)
                    )
                    stt_key, data_result, is_specify_newline_array = \
                        add_biographic(sys_bibliographic, bibliographic_key,
                                       s, stt_key,
                                       data_result, is_specify_newline_array
                                       )
            elif not (bibliographic_key and bibliographic_key in s['key']) and \
                    value and value not in _ignore_items and \
                    not is_hide and is_show_list and s['key']:
                data_result, stt_key = get_value_and_lang_by_key(
                    s['key'], solst_dict_array, data_result, stt_key)
                is_specify_newline_array.append(
                    {s['key']: is_specify_newline})

        if len(data_result) > 0:
            result = data_comment(result, data_result, stt_key,
                                  is_specify_newline_array)
        return result

    def get_file_comments(record, files):
        """Check and get file info."""
        def __get_label_extension():
            _label = f.get('url', {}).get('label')
            _filename = f.get('filename', '')
            _extension = ''
            if not _label and not f.get('version_id'):
                _label = f.get('url', {}).get('url', '')
            elif not _label:
                _label = _filename
            if f.get('version_id'):
                _idx = _filename.find('.') + 1
                _extension = _filename[_idx:] if _idx > 0 else 'unknown'
            return _label, _extension
        result = []
        for f in files:
            label, extension = __get_label_extension()
            if 'open_restricted' == f.get('accessrole', ''):
                if label:
                    result.append({
                        'label': label,
                        'extention': extension,
                        'url': ""
                    })
            elif label and (
                not extension
                    or check_file_download_permission(record, f, False)):
                result.append({
                    'label': label,
                    'extention': extension,
                    'url': f.get('url', {}).get('url', '')
                })
        return result

    def get_file_thumbnail(thumbnails):
        """Get file thumbnail."""
        thumbnail = {}
        if thumbnails and len(thumbnails) > 0:
            subitem_thumbnails = thumbnails[0].get('subitem_thumbnail')
            if subitem_thumbnails and len(subitem_thumbnails) > 0:
                thumbnail = {
                    'thumbnail_label': subitem_thumbnails[0].get(
                        'thumbnail_label', ''),
                    'thumbnail_width': current_app.config[
                        'WEKO_RECORDS_UI_DEFAULT_MAX_WIDTH_THUMBNAIL']
                }
        return thumbnail

    try:
        src_default = copy.deepcopy(record_hit['_source'].get('_item_metadata'))
        _item_metadata = copy.deepcopy(record_hit['_source'])
        src = record_hit['_source']['_item_metadata']
        item_type_id = record_hit['_source'].get('item_type_id') or \
            src.get('item_type_id')
        item_map = get_mapping(item_type_mapping, 'jpcoar_mapping')
        language_dict = {}
        suffixes = '.@attributes.xml:lang'
        for key in item_map:
            if key.find(suffixes) != -1:
                # get language
                title_languages, _title_key = get_data_by_propertys(
                    _item_metadata, item_map, key)
                # get value
                prefix = key.replace(suffixes, '')
                title_values, _title_key1 = get_data_by_propertys(
                    _item_metadata, item_map, prefix + '.@value')
                language_dict.update({
                    prefix: {'lang': title_languages, 'lang-id': _title_key,
                             'val': title_values, 'val-id': _title_key1}})
        # selected title
        title_obj = language_dict.get("title")
        if title_obj is not None:
            lang_arr = title_obj.get("lang")
            val_arr = title_obj.get("val")
            lang_id = title_obj.get("lang-id")
            val_id = title_obj.get("val-id")
            if lang_arr and len(lang_arr) > 0 and lang_arr != "null":
                result = selected_value_by_language(
                    lang_arr, val_arr, lang_id, val_id,
                    web_screen_lang, _item_metadata
                )
                if result is not None:
                    for idx, val in enumerate(record_hit['_source']['title']):
                        if val == result:
                            arr = []
                            record_hit['_source']['title'][idx] = \
                                record_hit['_source']['title'][0]
                            record_hit['_source']['title'][0] = result
                            arr.append(result)
                            record_hit['_source']['_comment'] = arr
                            break

        if not item_type_id:
            return
        solst, meta_options = get_options_and_order_list(item_type_id,
                                                         item_type_data)
        solst_dict_array = convert_data_to_dict(solst)
        files_info = []
        thumbnail = None
        hide_item_metadata(src, settings, item_type_mapping, item_type_data)
        # Set value and parent option
        for lst in solst:
            key = lst[0]
            val = src.get(key)
            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                continue
            mlt = val.get('attribute_value_mlt', [])
            if mlt:
                if val.get('attribute_type', '') == 'file' \
                    and not option.get("hidden") \
                        and option.get("showlist"):
                    files_info = get_file_comments(src, mlt)
                    continue
                is_thumbnail = any('subitem_thumbnail' in data for data in mlt)
                if is_thumbnail and not option.get("hidden") \
                        and option.get("showlist"):
                    thumbnail = get_file_thumbnail(mlt)
                    continue
                meta_data = get_all_items2(mlt, solst)
                for m in meta_data:
                    for s in solst_dict_array:
                        s_key = s.get('key')
                        if m.get(s_key):
                            s['value'] = m.get(s_key) if not s['value'] else \
                                '{}, {}'.format(s['value'], m.get(s_key))
                            s['parent_option'] = {
                                'required': option.get("required"),
                                'show_list': option.get("showlist"),
                                'specify_newline': option.get("crtf"),
                                'hide': option.get("hidden")
                            }
                            break
        # Format data to display on item list
        items = get_comment(
            solst_dict_array, not settings.items_display_email,
            _item_metadata, src_default, solst)

        if 'file' in record_hit['_source']:
            record_hit['_source'].pop('file')
        if items:
            if record_hit['_source'].get('_comment'):
                record_hit['_source']['_comment'].extend(items)
            else:
                record_hit['_source']['_comment'] = items
        if files_info:
            record_hit['_source']['_files_info'] = files_info
        if thumbnail:
            record_hit['_source']['_thumbnail'] = thumbnail
    except Exception:
        current_app.logger.exception(
            u'Record serialization failed {}.'.format(
                str(record_hit['_source'].get('control_number'))))


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
        current_app.logger.error(
            'Function check_has_attribute_value error:', e)
        return False


def get_attribute_value_all_items(root_key, nlst, klst, is_author=False, hide_email_flag=True):
    """Convert and sort item list.

    :param root_key:
    :param nlst:
    :param klst:
    :param is_author:
    :return: alst
    """
    def get_name(key):
        for lst in klst:
            keys = lst[0].replace("[]", "").split('.')
            if keys[0].startswith(root_key) and key == keys[-1]:
                return lst[2] if not is_author else '{}.{}'.format(
                    key, lst[2])

    def to_sort_dict(alst, klst):
        """Sort item list.

        :param alst:
        :param klst:
        """
        if isinstance(klst, list):
            result = []
            try:
                if isinstance(alst, list):
                    for a in alst:
                        result.append(to_sort_dict(a, klst))
                else:
                    temp = []
                    for lst in klst:
                        key = lst[0].split('.')[-1]
                        val = alst.pop(key, {})
                        hide = lst[3].get('hide')
                        if key in ('creatorMail', 'contributorMail', 'mail'):
                            hide = hide | hide_email_flag
                        if val and (isinstance(val, str)
                                    or (key == 'nameIdentifier')):
                            if not hide:
                                temp.append({key: val})
                        elif isinstance(val, list) and len(
                                val) > 0 and isinstance(val[0], str):
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
                current_app.logger.error('Function to_sort_dict error: ', e)
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
                    item_name = get_name(key) or ''
                    if val and (isinstance(val, str)
                                or (key == 'nameIdentifier')):
                        # the last children level
                        d[item_name] = val
                    elif isinstance(val, list) and len(val) > 0 and isinstance(
                            val[0], str):
                        d[item_name] = ', '.join(val)
                    else:
                        # parents level
                        # check if have any child
                        if check_has_attribute_value(val):
                            d[item_name] = set_attribute_value(val)
                _list.append(d)
            return _list
        except BaseException as e:
            current_app.logger.error('Function set_node error: ', e)
            return _list

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
        if old[k]['input_value'] != new[k]['input_value']:
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
    for k in schema['properties'].keys():
        if 'maxItems' and 'minItems' in schema['properties'][k].keys():
            del schema['properties'][k]['maxItems']
            del schema['properties'][k]['minItems']
        if 'items' in schema['properties'][k].keys():
            schema['properties'][k] = schema['properties'][k]['items']


def check_to_upgrade_version(old_render, new_render):
    """Check upgrade or keep version by checking different renders data.

    @param old_render:
    @param new_render:
    @return:
    """
    if old_render.get('meta_list').keys() != \
            new_render.get('meta_list').keys():
        return True
    # Check diff input value:
    if check_input_value(old_render.get('meta_list'),
                         new_render.get('meta_list')):
        return True
    # Check diff schema
    old_schema = old_render.get('table_row_map').get('schema')
    new_schema = new_render.get('table_row_map').get('schema')

    excluded_keys = \
        current_app.config['WEKO_ITEMTYPE_EXCLUDED_KEYS']
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
        _s_str = re.sub(pattern, '', _s_str)
        if _s_str == ',':
            return ''
        return _s_str.strip() if _s_str != ',' else ''

    s = s.strip()
    esc_str = ""
    for i in s:
        if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
            esc_str += i
    esc_str = __remove_special_character(esc_str)
    return esc_str


def selected_value_by_language(lang_array, value_array, lang_id, val_id,
                               lang_selected, _item_metadata):
    """Select value by language.

    @param lang_array:
    @param value_array:
    @param lang_selected:
    @param lang_id:
    @param val_id:
    @param _item_metadata:
    @return:
    """
    if (lang_array is not None) and (value_array is not None) \
            and isinstance(lang_selected, str):
        if len(value_array) < 1:
            return None
        else:
            if len(lang_array) > 0:
                for idx, lang in enumerate(lang_array):
                    lang_array[idx] = lang.strip()
            if lang_selected in lang_array:  # Web screen display language
                value = check_info_in_metadata(lang_id, val_id, lang_selected,
                                               _item_metadata)
                if value is not None:
                    return value
            if "en" in lang_array:  # English
                value = check_info_in_metadata(lang_id, val_id, "en",
                                               _item_metadata)
                if value is not None:
                    return value
            # 1st language when registering items
            if len(lang_array) > 0:
                for idx, lg in enumerate(lang_array):
                    if len(lg) > 0:
                        value = check_info_in_metadata(lang_id, val_id, lg,
                                                       _item_metadata)
                        if value is not None:
                            return value
            # 1st value when registering without language
            if len(value_array) > 0:
                return value_array[0]
    else:
        return None


def check_info_in_metadata(str_key_lang, str_key_val, str_lang, metadata):
    """Check language and info corresponding in metadata.

    @param str_key_lang:
    @param str_key_val:
    @param str_lang:
    @param metadata:
    @return
    """
    if len(str_key_lang) > 0 and (
        len(str_lang) > 0 or str_lang is None) and len(
            metadata) > 0 and str_key_val is not None and len(str_key_val) > 0:
        if '.' in str_key_lang:
            str_key_lang = str_key_lang.split('.')
        if '.' in str_key_val:
            str_key_val = str_key_val.split('.')
        metadata = metadata.get("_item_metadata")
        if str_key_lang[0] in metadata:
            obj = metadata.get(str_key_lang[0]).get('attribute_value_mlt')
            save = obj
            for ob in str_key_lang:
                if ob not in str_key_lang[0] and ob not in str_key_lang[
                        len(str_key_lang) - 1]:
                    for x in save:
                        if x.get(ob):
                            save = x.get(ob)
            for s in save:
                if str_lang is None:
                    value = s.get(str_key_val[len(str_key_val) - 1]).strip()
                    if len(value) > 0:
                        return value
                if (s is not None) and (s.get(
                    str_key_lang[len(str_key_lang) - 1]) is not None) and (
                        s.get(str_key_val[len(str_key_val) - 1]) is not None):
                    if (s.get(str_key_lang[len(
                        str_key_lang) - 1]).strip() == str_lang.strip()) and (
                        str_key_val[len(str_key_val) - 1] in s) and len(
                            s.get(str_key_val[len(str_key_val) - 1]).strip()) > 0:
                        return s.get(str_key_val[len(str_key_val) - 1])
    return None


def get_value_and_lang_by_key(key, data_json, data_result, stt_key):
    """Get value and lang in json by key.

    @param key:
    @param data_json:
    @param data_result:
    @param stt_key:
    @return:
    """
    if (key is not None) and isinstance(key, str) and (data_json is not None) \
            and (data_result is not None):
        save_key = ""
        key_split = key.split(".")
        if len(key_split) > 1:
            for i, k in enumerate(key_split):
                if k == key_split[len(key_split) - 1] and i == (
                        len(key_split) - 1):
                    break
                save_key += str(k + ".") if i < len(key_split) - 2 else str(k)
        for j in data_json:
            if key == j["key"]:
                flag = False
                if save_key not in data_result.keys():
                    stt_key.append(save_key)
                    data_result = {**data_result, **{save_key: {}}}
                if save_key in data_result.keys() and (
                    j["title"].strip() in "Language") or (
                    j["title_ja"].strip() in "Language") \
                    or (j["title_ja"].strip() in "言語") or (
                        j["title"].strip() in "言語"):
                    data_result[save_key] = {**data_result[save_key],
                                             **{'lang': j["value"].split(","),
                                                "lang_id": key}}
                    flag = True
                if key not in data_result[save_key] and not flag:
                    if "stt" not in data_result[save_key]:
                        data_result[save_key] = {**data_result[save_key],
                                                 **{'stt': []}}
                    if "stt" in data_result[save_key]:
                        data_result[save_key]["stt"].append(key)
                    data_result[save_key] = {**data_result[save_key], **{
                        key: {'value': j["value"].split(",")}}}
        return data_result, stt_key
    else:
        return None


def result_rule_create_show_list(source_title, current_lang):
    """Result rules create show list.

    @param source_title:
    @param current_lang:
    @return:
    """
    title_data_langs = []
    title_data_langs_none = []
    for key, value in source_title.items():
        title = {}
        if not value:
            continue
        elif current_lang == key:
            return value
        else:
            if key == 'None Language':
                title[key] = value
                title_data_langs_none.append(title)
            elif key:
                title[key] = value
                title_data_langs.append(title)

    for title_data_lang in title_data_langs:
        if title_data_lang.get('en'):
            return title_data_lang.get('en')

    if len(title_data_langs) > 0:
        return list(title_data_langs[0].values())[0]

    if len(title_data_langs_none) > 0:
        return list(title_data_langs_none[0].values())[0]


def get_show_list_author(solst_dict_array, hide_email_flag, author_key,
                         creates):
    """Get show list author.

    @param solst_dict_array:
    @param hide_email_flag:
    @param author_key:
    @param creates:
    @return:
    """
    remove_show_list_create = []
    for s in solst_dict_array:
        option = s['option']
        parent_option = s['parent_option']
        is_show_list = parent_option.get(
            'show_list') if parent_option and parent_option.get(
            'show_list') else option.get('show_list')
        is_hide = parent_option.get(
            'hide') if parent_option and parent_option.get(
            'hide') else option.get('hide')
        if 'creatorMails[].creatorMail' in s['key'] \
            or 'contributorMails[].contributorMail' in s['key'] \
                or 'mails[].mail' in s['key']:
            is_hide = is_hide | hide_email_flag

        if author_key != s['key'] and author_key in s['key']:
            sub_author_key = s['key'].split('.')[-1]
            key_creator = ['creatorName', 'familyName', 'givenName']
            if sub_author_key in key_creator and (is_hide or not is_show_list):
                remove_show_list_create.append(sub_author_key + 's')

    return format_creates(creates, remove_show_list_create)


def format_creates(creates, hide_creator_keys):
    """Format creates.

    @param creates:
    @param hide_creator_keys:
    @return:
    """
    current_lang = current_i18n.language
    result_end = {}
    for create in creates:
        # get creator comments
        result_end = get_creator(create, result_end, hide_creator_keys,
                                 current_lang)
        # get alternatives comments
        if 'creatorAlternatives' in create:
            alternatives_key = current_app.config[
                'WEKO_RECORDS_ALTERNATIVE_NAME_KEYS']
            result_end = get_author_has_language(create['creatorAlternatives'],
                                                 result_end, current_lang,
                                                 alternatives_key)
        # get affiliations comments
        if 'creatorAffiliations' in create:
            affiliation_key = current_app.config[
                'WEKO_RECORDS_AFFILIATION_NAME_KEYS']
            result_end = get_affiliation(create['creatorAffiliations'],
                                         result_end, current_lang,
                                         affiliation_key)
    return result_end


def get_creator(create, result_end, hide_creator_keys, current_lang):
    """Get creator, family name, given name.

    @param create:
    @param result_end:
    @param hide_creator_keys:
    @param current_lang:
    @return:
    """
    creates_key = {
        'creatorNames': ['creatorName', 'creatorNameLang'],
        'familyNames': ['familyName', 'familyNameLang'],
        'givenNames': ['givenName', 'givenNameLang']
    }
    if hide_creator_keys:
        for key in hide_creator_keys:
            if creates_key:
                del creates_key[key]
    result = get_creator_by_languages(creates_key, create)
    creator = result_rule_create_show_list(result, current_lang)
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
                key_data = val.get(value[1], 'None Language')
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
            if key == 'affiliationNames':
                result_end = get_author_has_language(value, result_end,
                                                     current_lang,
                                                     affiliation_key)
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
        key_data = val.get(map_keys[1], 'None Language')
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
    alternative = result_rule_create_show_list(result, current_lang)
    if map_keys[0] not in result_end:
        result_end[map_keys[0]] = []
    if isinstance(alternative, str):
        result_end[map_keys[0]].append(alternative)
    elif isinstance(alternative, list):
        result_end[map_keys[0]] += alternative

    return result_end


def add_author(author_data, stt_key, is_specify_newline_array, s, value,
               data_result, is_specify_newline, is_hide, is_show_list):
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
    list_author_key = current_app.config[
        'WEKO_RECORDS_AUTHOR_KEYS']
    sub_author_key = s['key'].split('.')[-1]
    if sub_author_key in current_app.config[
            'WEKO_RECORDS_AUTHOR_NONE_LANG_KEYS']:
        stt_key.append(sub_author_key)
        is_specify_newline_array.append(
            {sub_author_key: is_specify_newline})
        data_result.update({
            sub_author_key: {sub_author_key: {
                "value": [value]}}})
    elif sub_author_key in list_author_key and sub_author_key in \
            author_data and not is_hide and is_show_list:
        stt_key.append(sub_author_key)
        is_specify_newline_array.append(
            {sub_author_key: is_specify_newline})
        data_result.update({
            sub_author_key: {sub_author_key: {
                "value": author_data[sub_author_key]}}})
    return stt_key, data_result, is_specify_newline_array


def convert_bibliographic(data_sys_bibliographic):
    """Add author in show list result.

    @param data_sys_bibliographic:
    @return:
    """
    list_data = []
    for bibliographic_value in data_sys_bibliographic:
        if bibliographic_value.get('title_attribute_name'):
            list_data.append(
                bibliographic_value.get('title_attribute_name'))
        for magazine in bibliographic_value.get('magazine_attribute_name'):
            for key in magazine:
                list_data.append(key + ' ' + magazine[key])
    return ", ".join(list_data)


def add_biographic(sys_bibliographic, bibliographic_key, s, stt_key,
                   data_result, is_specify_newline_array):
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
        sys_bibliographic.get_bibliographic_list(True))
    stt_key.append(bibliographic_key)
    is_specify_newline_array.append({s['key']: True})
    data_result.update({
        bibliographic_key: {s['key']: {"value": [bibliographic]}}})

    return stt_key, data_result, is_specify_newline_array
