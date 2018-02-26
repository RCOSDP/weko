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

import base64

import pytz
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from .api import FilesMetadata, ItemsMetadata, ItemTypes, Mapping


def save_item_metadata(rejson, pid):
    """Save the item.

    :param rejson: json from item form post.
    :param pid: pid value.
    """
    dc = dict()
    ju = dict()
    item = dict()
    ar = []

    if not isinstance(rejson, dict) or rejson.get("$schema") is None:
        return

    item_id = pid.object_uuid
    pid = pid.pid_value

    # find the item type identifier
    index = rejson["$schema"].rfind('/')
    item_type_id = rejson["$schema"][index + 1:len(rejson["$schema"])]

    # get itemtype mapping file json data
    ojson = ItemTypes.get_record(item_type_id)
    mjson = Mapping.get_record(item_type_id)
    # fjson = FilesMetadata.get_records(pid)

    if ojson and mjson:
        mp = mjson.dumps()
        rejson.get("$schema")
        for k, v in rejson.items():
            if k == "$schema" or \
                mp.get(k) is None:
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
                item["attribute_value"] = ar
                ar = []
            else:
                item["attribute_value"] = v

            dc[k] = item.copy()
            item.update(mp.get(k))
            ju[k] = item.copy()

    del ojson, mjson

    if dc:
        # get the tile name to detail page
        title = rejson.get("title_ja") or rejson.get("title_en")

        if 'control_number' in dc:
            del dc['control_number']

        dc.update(dict(item_title=title))
        dc.update(dict(item_type_id=item_type_id))
        dc.update(dict(control_number=pid))

        # convert to junii2 schema for es
        jrc = tojunii2(ju)
        oaid = current_pidstore.minters['oaiid'](item_id, dc)

        jrc.update(dict(control_number=pid))
        jrc.update(dict(_oai={"id": oaid.pid_value}))

        # with db.session.begin_nested():
        #     record = ItemsMetadata.create(rejson, id_=item_id, item_type_id=item_type_id)
        # create Record metadata
        # record = Record.create(dc, id_=item_id)
        # update_file_metadata(rejson, fjson)

        # jrc.update(
        #     {"_created": pytz.utc.localize(record.created)
        #         .isoformat() if record.created else None})
        #
        # jrc.update(
        #     {"_updated": pytz.utc.localize(record.updated)
        #         .isoformat() if record.updated else None})

        # # Upload  item metadata to ElasticSearch
        # upload_metadata(jrc, item_id)
        # # Upload  file metadata to ElasticSearch
        # upload_file(fjson, item_id)

    return dc, jrc


def save_items_data(rejson, item_id, item_type_id):
    """"""
    with db.session.begin_nested():
        ItemsMetadata.create(rejson, id_=item_id, item_type_id=item_type_id)


def upload_metadata(jrc, item_id):
    """
    Upload the item data to ElasticSearch
    :param jrc:
    :param item_id:
    """
    indexer = RecordIndexer()
    indexer.client.index(id=str(item_id),
                         index="weko",
                         doc_type="item",
                         body=jrc,
                         )


def upload_file(fjson, uuid):
    """Upload file  to ElasticSearch.

    :param fjson: file json info
    :param uuid: uuid
    """
    if fjson is None or len(fjson) == 0:
        return

    indexer = RecordIndexer()
    for fj in fjson:
        strb = base64.b64encode(fj.model.contents[:]).decode("utf-8")
        fjs = fj.dumps()
        fjs.update({"file": strb})
        fjs.update(
            {"_created": pytz.utc.localize(fj.created)
                .isoformat() if fj.created else None})

        fjs.update(
            {"_updated": pytz.utc.localize(fj.updated)
                .isoformat() if fj.updated else None})

        indexer.client.index(id=str(fj.id),
                             index="weko",
                             doc_type="content",
                             parent=uuid,
                             body=fjs,
                             )


def update_file_metadata(rejson, fjson):
    """ update FilesMetadata's json
    :param fm: file metadata
    :param fjson: FilesMetadata's json obj
    """
    # get file metadata
    fm = rejson.get("filemeta")
    for lst in fm:
        if isinstance(lst, dict):
            fn = lst.get("filename")
            for fj in fjson:
                for k, v in fj.model.json.items():
                    if fn in str(v):
                        jsn = fj.model.json.copy()
                        jsn.update(lst)
                        FilesMetadata.update_data(fj.id, jsn)
                        break


def tojunii2(records):
    """Convert to junii2 json.

    :param records:
    """
    j = dict()
    for k, y in records.items():
        if isinstance(y, dict):
            if k != "item":
                del_dupl(j, get_value(y))
            else:
                for ke, ve in y.items():
                    if isinstance(ve, dict):
                        del_dupl(j, get_value(ve))

    return j


def get_value(obj):
    """Get value."""
    j = dict()
    if isinstance(obj, dict):
        obj.pop("display_lang_type")
        obj.pop("jpcoar_mapping")
        obj.pop("dublin_core_mapping")
        obj.pop("lido_mapping")
        obj.pop("lom_mapping")
        itn = obj.pop("junii2_mapping")

        if itn != "":
            if obj.get("attribute_value_mlt"):
                s = "attribute_value_mlt"
                if isinstance(obj[s], list):
                    if itn == "jtitle,volume,issue,spage,epage,dateofissued":
                        itnl = itn.split(",")

                        j[itnl[0]] = obj[s][0].get("biblio_name")
                        j[itnl[1]] = obj[s][0].get("volume")
                        j[itnl[2]] = obj[s][0].get("issue")
                        j[itnl[3]] = obj[s][0].get("start_page")
                        j[itnl[4]] = obj[s][0].get("end_page")
                        j[itnl[5]] = obj[s][0].get("date_of_issued")[0:11]
                    else:
                        creator = []
                        for lst in obj[s]:
                            if isinstance(lst, dict):
                                fn1 = lst.get("family")
                                fn2 = lst.get("name")

                                if fn1 and fn2:
                                    fn = fn1 + "," + fn2
                                    creator.append(fn)

                                fn = lst.get("file_name")
                                if fn:
                                    creator.append(fn)

                        j[itn] = creator
            if obj.get("attribute_value"):
                if isinstance(obj["attribute_value"], list):
                    if len(obj["attribute_value"]) > 1:
                        j[itn] = obj["attribute_value"]
                    else:
                        j[itn] = obj["attribute_value"][0]
                elif itn == "title" or itn == "NIItype" or itn == "URI":
                    j[itn] = obj["attribute_value"]
                else:
                    kc = []
                    kc.append(obj["attribute_value"])
                    j[itn] = kc

        else:
            j = None

    return j


def del_dupl(jd, dpd):
    """Merge duble key.

    :param jd:
    :param dpd:
    """
    if dpd:
        if len(jd) == 0:
            jd.update(dpd)
        else:
            kc = dpd.keys()
            for key in dpd.keys():
                pass
            arr = jd.get(key)
            if arr:
                arr.extend(dpd.get(key))
            else:
                jd.update(dpd)
