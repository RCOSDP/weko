import pytest
import json

from mock import patch, MagicMock

from invenio_resourcesyncclient.resync import ResourceSyncClient

# class ResourceSyncClient(Client):
#     def update_resource(self, resource, filename, change=None):
def test_ResourceSyncClient_update_resource():
    resource = MagicMock()
    filename = 'filename'

    client = ResourceSyncClient()
    client.ignore_failures = True
    json_data = {'key': 'value'}
    with patch('invenio_resourcesyncclient.resync.repr', return_value=json.dumps(json_data)):
        ret = client.update_resource(resource, filename)
        assert ret == 0
