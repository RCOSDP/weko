import pytest
import json
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session
from flask import current_app
from invenio_records_rest.errors import InvalidDataRESTError

from weko_schema_ui import WekoSchemaREST

# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_ext -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_ext(app):
    WekoSchemaREST(app)
    WekoSchemaREST()


# POST/PUT now need schema-access (weko_schema_ui.permissions), which the
# users fixture grants to Repository Administrator only; System Administrator
# passes through superuser-access.
user_post_results1 = [
    (0, 403),  # contributor
    (1, 201),  # repoadmin
    (2, 201),  # sysadmin
    (3, 403),  # comadmin
    (4, 403),  # generaluser
]
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_schemas_post_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_post_results1)
def test_SchemaFilesResource_schemas_post_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    res = client_rest.post('/schemas/',
                           data=json.dumps({}),
                           content_type='application/json')
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_schemas_post_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_schemas_post_guest(client_rest, users):
    res = client_rest.post('/schemas/',
                           data=json.dumps({}),
                           content_type='application/json')
    assert res.status_code == 401


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_schemas_post_unsupported_media_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_schemas_post_unsupported_media_type(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])
    res = client_rest.post('/schemas/',
                           data=json.dumps({}),
                           content_type='application/xml')
    assert res.status_code == 415


def create_dirs(xsd_location_folder, pid):
    from pathlib import Path
    path = Path(xsd_location_folder)
    furl = path.joinpath('tmp',pid)
    furl.mkdir(exist_ok=True, parents=True)
    dst = path.joinpath(pid)
    dst.mkdir(exist_ok=True, parents=True)


class MockSchemaConverter():
    def __init__(self, fn, root_name):
        self.namespaces={'test_name':'test_namespace'}
        self.target_namespace='test_targetnamespace'

    def to_dict(self):
        return dict()

user_post_results2 = [
    (0, 403),  # contributor
    (1, 200),  # repoadmin
    (2, 200),  # sysadmin
    (3, 403),  # comadmin
    (4, 403),  # generaluser
]
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_shcemaspid_post_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_post_results2)
def test_SchemaFilesResource_shcemaspid_post_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
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
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == status_code



# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_get_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_get_guest(client_rest, users):
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.get('/schemas/111',
                                       content_type='application/json')
                assert res.status_code == 405


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_fail1_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_fail1_post(client_rest2, users):
    login_user_via_session(client=client_rest2, email=users[1]['email'])  # repoadmin
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
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest2.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='test')
                assert res.status_code == 400


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_post_test1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_post_test1(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])  # repoadmin
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'name':'test_name',
        'file_name':'test_file',
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 400


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_post_test2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_post_test2(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])  # repoadmin
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'root_name':'test_rootname',
        'file_name':'test_file',
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_post_test3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_post_test3(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])  # repoadmin
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'name':'test_name_mapping',
        'root_name':'test_rootname',
        'file_name':'test_file',
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_post_test4 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_post_test4(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])  # repoadmin
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'name':'test_name',
        'root_name':'test_rootname',
        'file_name': None,
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 400


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_post_test5 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_post_test5(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])  # repoadmin
    xsd_location_folder=current_app.config[
        'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
        format(current_app.instance_path)
    create_dirs(xsd_location_folder, '111')
    data = {
        '$schema':'test schema',
        'name':'test_name',
        'root_name':'test_rootname',
        'file_name':'test_file',
        'zip_name': 'test_file.zip'
    }
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                with pytest.raises(FileNotFoundError):
                    res = client_rest.post('/schemas/111',
                                           data=json.dumps(data),
                                           content_type='application/json')


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_shcemaspid_post_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_shcemaspid_post_guest(client_rest, users):
    res = client_rest.post('/schemas/111',
                           data=json.dumps({}),
                           content_type='application/json')
    assert res.status_code == 401


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_shcemaspid_post_twice -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_shcemaspid_post_twice(client_rest, users):
    login_user_via_session(client=client_rest, email=users[1]['email'])  # repoadmin
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
    test_aoi_metadata_formats = {'key1':{'serializer':[1]}}
    
    mock_SchemaConverter = MagicMock(side_effect=MockSchemaConverter)
    with patch('weko_schema_ui.rest.SchemaConverter', mock_SchemaConverter):
        with patch('weko_schema_ui.rest.get_oai_metadata_formats', return_value=test_aoi_metadata_formats):
            with patch('weko_schema_ui.api.WekoSchema.create'):
                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 200

                res = client_rest.post('/schemas/111',
                                       data=json.dumps(data),
                                       content_type='application/json')
                assert res.status_code == 400


class MockPyFSFileStorage:
    def __init__(self, furl):
        pass
    
    def save(self, request_stream):
        return 'test_fileurl', 'test_bytes_written', 'test_checksum'


user_put_results = [
    (0, 403),  # contributor
    (1, 200),  # repoadmin
    (2, 200),  # sysadmin
    (3, 403),  # comadmin
    (4, 403),  # generaluser
]
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_put_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_put_results)
def test_SchemaFilesResource_put_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    mock_PyFSFileStorage = MagicMock(side_effect=MockPyFSFileStorage)
    with patch('weko_schema_ui.rest.PyFSFileStorage',mock_PyFSFileStorage):
        res = client_rest.put('/schemas/put/111/test.zip',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == status_code

user_put_results = [
    (1, 400),  # repoadmin: the only role in this fixture with schema-access
]
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_put_login_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
@pytest.mark.parametrize('id, status_code', user_put_results)
def test_SchemaFilesResource_put_login_error(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    m = MagicMock()
    m.save.side_effect=Exception("mock exception")
    with patch('weko_schema_ui.rest.PyFSFileStorage',m):
        res = client_rest.put('/schemas/put/111/test.zip',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == 400


# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_rest.py::test_SchemaFilesResource_put_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_SchemaFilesResource_put_guest(client_rest, users):
    mock_PyFSFileStorage = MagicMock(side_effect=MockPyFSFileStorage)
    with patch('weko_schema_ui.rest.PyFSFileStorage',mock_PyFSFileStorage):
        res = client_rest.put('/schemas/put/111/test.zip',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == 401
