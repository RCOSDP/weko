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


def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    dep = WekoDeposit.get_record(record.id)
    pid = get_record_without_version(dep.pid)
    im = dep.copy()
    im.pop('_deposit')
    im.pop('_buckets')
    json['_item_metadata'] = im
    json['_oai'] = im['_oai']
    json['control_number'] = dep.pid.pid_value
    json['relation_version_is_last'] = True \
        if pid == get_record_without_version(pid) else False
    files = [f for f in dep.files]
    contents = []
    for f in files:
        content = f.obj.file.json
        content.update({"file": f.obj.file.read_file(content)})
        contents.append(content)
    json['content'] = contents
    if contents:
        kwargs['arguments']['pipeline'] = 'item-file-pipeline'
