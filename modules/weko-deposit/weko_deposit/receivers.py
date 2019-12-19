# -*- coding: utf-8 -*-
#
# """Deposit module receivers."""

from __future__ import absolute_import, print_function
from flask import current_app
from .api import WekoDeposit
from .pidstore import get_record_without_version
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from weko_records.api import ItemsMetadata

def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    dep = WekoDeposit.get_record(record.id)
    pid = get_record_without_version(dep.pid)
    json['_item_metadata'] = ItemsMetadata.get_record(record.id)
    json['_item_metadata']['pubdate'] = dep['pubdate']
    json['relation_version_is_last'] = True \
        if pid == get_record_without_version(pid) else False
    json['control_number'] = dep.pid.pid_value
    files = [f for f in dep.files]
    contents = []
    for f in files:
        content = f.obj.file.json
        content.update({"file": f.obj.file.read_file(content)})
        contents.append(content)
    json['content'] = contents
    if contents:
        kwargs['arguments']['pipeline'] = 'item-file-pipeline'

