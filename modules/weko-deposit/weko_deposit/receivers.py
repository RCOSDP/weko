# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Deposit module receivers."""

from flask import current_app
from weko_records.models import ItemType

from .api import WekoDeposit
from .pidstore import get_record_without_version

ATTR_MLT = 'attribute_value_mlt'


def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    dep = WekoDeposit.get_record(record.id)
    pid = get_record_without_version(dep.pid)
    im = dep.copy()
    im.pop('_deposit')
    im.pop('_buckets')
    holds = ['_created', '_updated']
    pops = []
    for key in json:
        if key not in holds:
            pops.append(key)
    for key in pops:
        json.pop(key)
    json['_item_metadata'] = im
    json['_oai'] = im.get('_oai')
    json['control_number'] = im.get('recid')
    json['relation_version_is_last'] = True \
        if pid == get_record_without_version(pid) else False
    itemtype = ItemType.query.filter(ItemType.id == im.get(
        'item_type_id')).first()
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
    file_size_max = current_app.config[
        'WEKO_MAX_FILE_SIZE_FOR_ES']
    mimetypes = current_app.config[
        'WEKO_MIMETYPE_WHITELIST_FOR_ES']
    for f in files:
        if f.obj.file.size <= file_size_max and \
                f.obj.mimetype in mimetypes:
            content = f.obj.file.json
            content.update({"file": f.obj.file.read_file(content)})
            if content['file']:
                contents.append(content)
    json['content'] = []
    if contents:
        kwargs['arguments']['pipeline'] = 'item-file-pipeline'
    for i in im.values():
        if isinstance(i, dict):
            if i.get('attribute_type') == 'creator':
                values = i.get(ATTR_MLT)[0]
                creator = {}
                if 'creatorNames' in values:
                    creator['creatorName'] = \
                        [n['creatorName'] for n in values['creatorNames']]
                if 'familyNames' in values:
                    creator['familyName'] = \
                        [n['familyName'] for n in values['familyNames']]
                if 'givenNames' in values:
                    creator['givenName'] = \
                        [n['givenName'] for n in values['givenNames']]
                if 'creatorAlternatives' in values:
                    creator['creatorAlternative'] = \
                        [n['creatorAlternative'] for n in values[
                            'creatorAlternatives']]
                if 'affiliation' in values:
                    affiliation = dict()
                    affiliation['affiliationName'] = \
                        [n['affiliationName'] for n in values['affiliation']]
                    affiliation['nameIdentifier'] = \
                        [n['affiliationNameIdentifier'] for n in values[
                            'affiliation']]
                    creator['affiliation'] = affiliation
                if 'affiliation' in values:
                    creator['nameIdentifier'] = \
                        [n['nameIdentifier'] for n in values['nameIdentifiers']]
                json['creator'] = creator
            elif i.get('attribute_type') == 'file':
                values = i.get(ATTR_MLT)
                files = {}
                dates, extent, mimetype = [], [], []
                for v in values:
                    dates.append(v.get('date')) if 'date' in v else None
                    extent.append(v.get('filesize')[0]['value']) if \
                        'filesize' in v else None
                    mimetype.append(v.get('format')) if 'format' in v else None
                if dates:
                    files['date'] = []
                    for date in dates:
                        files['date'] += [dict(
                            dateType=n.get('dateType'),
                            value=n.get('dateValue')) for n in date]
                else:
                    files['date'] = None
                files['extent'] = extent if extent else None
                files['mimeType'] = mimetype if mimetype else None
                files['URI'] = []
                files['version'] = []
                json['file'] = files
            elif i.get('attribute_name') == 'Language':
                json['language'] = [list(it.values())[0] for it in i.get(
                    ATTR_MLT)]
            elif i.get('attribute_name') == 'Resource Type':
                json['type'] = [it.get('resourcetype') for it in i.get(
                    ATTR_MLT)]
