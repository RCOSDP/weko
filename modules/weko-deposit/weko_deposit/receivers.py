# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Deposit module receivers."""

from .api import WekoDeposit
from .pidstore import get_record_without_version
from weko_records.models import ItemType

def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    dep = WekoDeposit.get_record(record.id)
    pid = get_record_without_version(dep.pid)
    im = dep.copy()
    im.pop('_deposit')
    im.pop('_buckets')
    holds = ['_created', '_updated', '_deposit', '_buckets']
    pops = []
    for key in json:
        if key not in holds:
            pops.append(key)
    for key in pops:
        json.pop(key)
    json['_item_metadata'] = im
    json['_oai'] = im.get('_oai')
    json['control_number'] = im.get('control_number')
    json['relation_version_is_last'] = True \
        if pid == get_record_without_version(pid) else False
    itemtype = ItemType.query.filter(ItemType.id==im.get('item_type_id')).first()
    if itemtype:
        json['itemtype'] = itemtype.item_type_name.name
    json['path'] = im.get('path')
    json['publish_date'] = im.get('publish_date')
    json['publish_status'] = im.get('publish_status')
    json['title'] = im.get('title')
    json['weko_shared_id'] = im.get('weko_shared_id')
    json['weko_creator_id'] = im.get('owner')
    files = [f for f in dep.files]
    contents = []
    for f in files:
        content = f.obj.file.json
        content.update({"file": f.obj.file.read_file(content)})
        if content['file']:
            contents.append(content)
    json['content'] = contents
    if contents:
        kwargs['arguments']['pipeline'] = 'item-file-pipeline'
    for val im.values():
        if isinstance(i, dict):
            if i.get('attribute_type') == 'creator':
                pass
            elif i.get('attribute_name') == 'Language':
                json['language'] = [list(it.values())[0] for it in i.get('attribute_value_mlt')]
            elif i.get('attribute_name') == 'Keyword':
                pass
            elif i.get('attribute_name') == 'Resource Type':
                json['type'] = [it.get('resourcetype') for it in i.get('attribute_value_mlt')]
            
