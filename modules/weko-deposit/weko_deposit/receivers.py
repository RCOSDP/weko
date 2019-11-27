# -*- coding: utf-8 -*-
#
# """Deposit module receivers."""

from __future__ import absolute_import, print_function
from .api import WekoDeposit
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from weko_records.api import ItemsMetadata

def append_file_content(sender, json=None, record=None, index=None, **kwargs):
    """Append file content to ES record."""
    json['_item_metadata'] = ItemsMetadata.get_record(record.id)
    dep = WekoDeposit.get_record(record.id)
    files = [f for f in dep.files]
    contents = []
    for f in files:
        content = f.obj.file.json
        content.update({"file": f.obj.file.read_file(content)})
        contents.append(content)
    json['content'] = contents
    if contents:
        kwargs['arguments']['pipeline'] = 'item-file-pipeline'

