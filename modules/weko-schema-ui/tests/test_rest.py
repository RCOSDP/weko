import pytest
import json
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session


user_results = [
    (0, 403),
    (1, 403),
    (2, 403),
    (3, 200),
    (4, 200),
]


@pytest.mark.parametrize('id, status_code', user_results)
def test_SchemaFilesResource_schemas_post_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    res = client_rest.post('/schemas/',
                           data=json.dumps({}),
                           content_type='application/json')
    assert res.status_code == status_code


def test_SchemaFilesResource_schemas_post_guest(client_rest, users, create_schema):
    res = client_rest.post('/schemas/',
                       data=json.dumps({}),
                       content_type='application/json')
    assert res.status_code == 302


def create_dirs(xsd_location_folder, pid):
    from pathlib import Path
    path = Path(xsd_location_folder)
    furl = path.joinpath('tmp',pid)
    furl.mkdir(exist_ok=True, parents=True)
    dst = path.joinpath(pid)
    dst.mkdir(exist_ok=True, parents=True)


class MockSchemaConverter():
    def __init__(self, current_app):
        self.namespaces={'test_name':'test_namespace'}
        self.target_namespace='test_targetnamespace'

    def to_dict(self):
        return dict()


@pytest.mark.parametrize('id, status_code', user_results)
def test_SchemaFilesResource_shcemaspid_post_login(client_rest, users, id, status_code):
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'name':'test_name',
        'root_name':'test_rootname',
        'file_name':'test_file',
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.rest.WekoSchema.create'):
                res = client_rest.post('/schema/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == status_code


def test_SchemaFilesResource_shcemaspid_post_guest(client_rest, users):
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'name':'test_name',
        'root_name':'test_rootname',
        'file_name':'test_file',
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.rest.WekoSchema.create'):
                res = client_rest.post('/schema/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 403


class MockPyFSFileStorage:
    def __init__(self, furl):
        pass
    
    def save(self, request_stream):
        return 'test_fileurl', 'test_bytes_written', 'test_checksum'


@pytest.mark.parametrize('id, status_code', user_results)
def test_SchemaFilesResource_put_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    mock_PyFSFileStorage = MagicMock(side_effect=MockPyFSFileStorage)
    with patch('weko_schema_ui.rest.PyFSFileStorage',mock_PyFSFileStorage):
        res = client_rest.put('/schemas/put/111/test.zip',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == status_code


def test_SchemaFilesResource_put_guest(client_rest, users):
    mock_PyFSFileStorage = MagicMock(side_effect=MockPyFSFileStorage)
    with patch('weko_schema_ui.rest.PyFSFileStorage',mock_PyFSFileStorage):
        res = client_rest.put('/schemas/put/111/test.zip',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == status_code
