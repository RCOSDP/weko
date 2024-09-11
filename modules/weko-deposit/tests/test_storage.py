
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
from io import TextIOWrapper
import logging
from unittest import mock
from unittest.mock import MagicMock, patch
from invenio_files_rest.errors import StorageError
from weko_deposit.errors import WekoDepositError, WekoDepositStorageError
from weko_deposit.storage import WekoFileStorage,make_path,pyfs_storage_factory
from weko_deposit.api import WekoFileObject
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records_files.api import FileObject
import hashlib
import base64
import pytest
from six import BytesIO
# class WekoFileStorage(PyFSFileStorage):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

class TestWekoFileStorage:
    # def _init_hash(self):
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test__init_hash -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test__init_hash(self,wekofs):
        # Test initialization of hash
        with patch('weko_deposit.storage.weko_logger') as mock_logger:
            type, hash = wekofs._init_hash()
            assert type=='sha256'
            assert len(hash.hexdigest())==64
            mock_logger.assert_called_with(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def upload_file(self, fjson):
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test_upload_file(self, app, wekofs, wekofs_testpath):
        # test upload_file with valid data
        bucket = Bucket.create()
        key = 'hello.txt'
        data = b'somedata'
        stream = BytesIO(data)
        obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
        with app.test_request_context():
            file = WekoFileObject(obj,{})
            uri, size, checksum = wekofs.save(BytesIO(data))
            assert uri == wekofs_testpath
            assert size == len(data)
            m = hashlib.sha256()
            m.update(data)
            assert checksum == "sha256:{}".format(m.hexdigest())
            fjson = file.info()
            with patch('weko_deposit.storage.weko_logger') as mock_logger:
                wekofs.upload_file(fjson)
                assert fjson['file'] == base64.b64encode(data).decode("utf-8")
                mock_logger.assert_called_with(key='WEKO_DEPOSIT_UPLOAD_FILE', file_id=mock.ANY)
                mock_logger.reset_mock()

        # test upload_file with valid data and mimetype
        bucket = Bucket.create()
        key = 'hello2.txt'
        data = b'helloworld!'
        stream = BytesIO(data)
        obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
        with app.test_request_context():
            file = WekoFileObject(obj,{})
            uri, size, checksum = wekofs.save(BytesIO(data))
            assert uri == wekofs_testpath
            assert size == len(data)
            m = hashlib.sha256()
            m.update(data)
            assert checksum == "sha256:{}".format(m.hexdigest())
            fjson = file.info()
            fjson['mimetype'] = "plain/text"
            with patch('weko_deposit.storage.weko_logger') as mock_logger:
                wekofs.upload_file(fjson)
                # logger.debug(fjson)
                assert 'file' in fjson, "fjson does not contain 'file' key"
                assert fjson['file'] == base64.b64encode(data).decode("utf-8")
                mock_logger.assert_called_with(key='WEKO_DEPOSIT_UPLOAD_FILE', file_id=mock.ANY)
                mock_logger.reset_mock()

    # fjson is not None and len(fjson) > 0
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file_with_valid_fjson -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test_upload_file_with_valid_fjson(self, app, wekofs, wekofs_testpath):
        # test upload_file with valid fjson
        bucket = Bucket.create()
        key = 'hello.txt'
        data = b'somedata'
        stream = BytesIO(data)
        obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
        with app.test_request_context():
            file = WekoFileObject(obj, {})
            uri, size, checksum = wekofs.save(BytesIO(data))
            assert uri == wekofs_testpath
            assert size == len(data)
            m = hashlib.sha256()
            m.update(data)
            assert checksum == "sha256:{}".format(m.hexdigest())
            fjson = file.info()
            fjson['mimetype'] = "plain/text"
            with patch('weko_deposit.storage.weko_logger') as mock_logger:
                wekofs.upload_file(fjson)
                assert 'file' in fjson, "fjson does not contain 'file' key"
                assert fjson['file'] == base64.b64encode(data).decode("utf-8")
                mock_logger.assert_called_with(key='WEKO_DEPOSIT_UPLOAD_FILE', file_id=mock.ANY)
                mock_logger.reset_mock()

    # fjson is None
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file_with_none_fjson -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test_upload_file_with_none_fjson(self, wekofs):
        with patch('weko_deposit.storage.weko_logger') as mock_logger:
            wekofs.upload_file(None)
            mock_logger.assert_not_called()

    # environment error
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file_with_environment_error -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test_upload_file_with_environment_error(self, app, wekofs, wekofs_testpath):
        fjson = {'mimetype': 'plain/text'}
        with patch.object(wekofs, 'open', side_effect=EnvironmentError()):
            with patch('weko_deposit.storage.weko_logger') as mock_logger:
                with pytest.raises(StorageError, match="Could not upload file"):
                    wekofs.upload_file(fjson)
                mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_FILE_UPLOAD', file_name="", ex=mock.ANY)
                mock_logger.reset_mock()

    # unexpected error
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file_with_unexpected_error -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test_upload_file_with_unexpected_error(self, wekofs):
        fjson = {'mimetype': 'plain/text'}
        with patch.object(wekofs, 'open', side_effect=Exception()):
            with patch('weko_deposit.storage.weko_logger') as mock_logger:
                with pytest.raises(StorageError, match="Could not upload file"):
                    wekofs.upload_file(fjson)
                mock_logger.assert_called_with(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
                mock_logger.reset_mock()

    # # 'UTF-8' in ecd
    # #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file_with_utf8_encoding -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    # def test_upload_file_with_utf8_encoding(self, wekofs):
    #     fjson = {'mimetype': 'plain/text'}
    #     data = b'somedata'
    #     with patch.object(wekofs, 'open', return_value=BytesIO(data)):
    #         with patch('chardet.detect', return_value={'encoding': 'UTF-8'}):
    #             with patch('weko_deposit.storage.weko_logger') as mock_logger:
    #                 wekofs.upload_file(fjson)
    #                 mock_logger.assert_called_with(key='WEKO_DEPOSIT_UPLOAD_FILE', file_id=mock.ANY)
    #                 assert fjson['file'] == base64.b64encode(data).decode("utf-8")
    #                 mock_logger.reset_mock()

    # UnicodeError
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::TestWekoFileStorage::test_upload_file_with_unicode_error -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
    def test_upload_file_with_unicode_error(self, app, wekofs):
        bucket = Bucket.create()
        key = 'hello.txt'
        data = b'somedata'
        stream = BytesIO(data)
        obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
        s = b'\xff\xfe\xfa'
        with app.test_request_context():
            file = WekoFileObject(obj,{})
            wekofs.save(BytesIO(data))
            fjson = file.info()
            fjson['mimetype'] = 'plain/text'
            with patch('weko_deposit.storage.weko_logger') as mock_logger:
                with patch.object(stream, 'read', return_value=s):
                    with patch.object(wekofs, 'open', return_value=stream):
                        with patch('chardet.detect', return_value={'encoding': 'ISO-8859-1'}):
                            with pytest.raises(WekoDepositError, match="Could not encoding/decoding file"):
                                wekofs.upload_file(fjson)
                mock_logger.assert_called_with(key="WEKO_DEPOSIT_FAILED_ENCODING_DECODING_FILE", file_name="", ex=mock.ANY)
                mock_logger.reset_mock()

# def make_path(base_uri, path, filename, path_dimensions, split_length):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::test_make_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_make_path():
    # Test make path with various parameters
    myid = 'deadbeef-dead-dead-dead-deaddeafbeef'
    base = '/base'
    f = 'data'
    assert make_path(base, myid, f, 1, 1) == '/base/d/eadbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 3, 1) == '/base/d/e/a/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 1, 3) == '/base/dea/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 2, 2) == '/base/de/ad/beef-dead-dead-dead-deaddeafbeef/data'
    with patch('weko_deposit.storage.weko_logger') as mock_logger:
        pytest.raises(WekoDepositError, make_path, base, myid, f, 1, 50)
        mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_MAKE_PATH', path=myid, length=50)
        pytest.raises(WekoDepositError, make_path, base, myid, f, 50, 1)
        mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_MAKE_PATH', path=myid, length=50)
        pytest.raises(WekoDepositError, make_path, base, myid, f, 50, 50)
        mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_MAKE_PATH', path=myid, length=2500)
        mock_logger.reset_mock()


# def pyfs_storage_factory(fileinstance=None, default_location=None,
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::test_pyfs_storage_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_pyfs_storage_factory(app,wekofs,wekofs_testpath,location):
    bucket = Bucket.create()
    key = 'hello2.txt'
    data = b'helloworld!'
    stream = BytesIO(data)
    obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)

    # fileinstance is not None
    with app.test_request_context():
        file = WekoFileObject(obj,{})
        with patch('weko_deposit.storage.weko_logger') as mock_logger:
            factory = pyfs_storage_factory(fileinstance=file.obj.file)
            assert isinstance(factory,WekoFileStorage) == True
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=factory)
            mock_logger.reset_mock()

    # fileinstance is not None and default_location is not None
    with app.test_request_context():
        file = WekoFileObject(obj,{})
        file.obj.file.uri = ''
        with patch('weko_deposit.storage.weko_logger') as mock_logger:
            with pytest.raises(WekoDepositStorageError):
                factory = pyfs_storage_factory(fileinstance=file.obj.file)
            factory = pyfs_storage_factory(fileinstance=file.obj.file,default_location=location.uri)
            assert isinstance(factory,WekoFileStorage) == True
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=factory)
            mock_logger.reset_mock()

    # fileinstance is None and fileurl and size are not None
    with app.test_request_context():
        file = WekoFileObject(obj,{})
        fileurl = make_path(
                location.uri,
                str(file.obj.file.id),
                'data',
                app.config['FILES_REST_STORAGE_PATH_DIMENSIONS'],
                app.config['FILES_REST_STORAGE_PATH_SPLIT_LENGTH'],
            )
        with patch('weko_deposit.storage.weko_logger') as mock_logger:
            factory = pyfs_storage_factory(fileurl=fileurl,size=file.obj.file.size,default_location=location.uri)
            assert isinstance(factory,WekoFileStorage) == True
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=factory)
            mock_logger.reset_mock()

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::test_pyfs_storage_factory_with_invalid_parameters -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_pyfs_storage_factory_with_invalid_parameters():
    #fileinstance is None and both fileurl and size are None
    with patch('weko_deposit.storage.weko_logger') as mock_logger:
        with pytest.raises(WekoDepositStorageError, match="Either fileinstance or both fileurl and size must be specified."):
            pyfs_storage_factory(fileinstance=None, fileurl=None, size=None)
        mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_STORAGE_FACTORY')
        mock_logger.reset_mock()

    # fileinstance is None and fileurl is None
    with patch('weko_deposit.storage.weko_logger') as mock_logger:
        with pytest.raises(WekoDepositStorageError, match="Either fileinstance or both fileurl and size must be specified."):
            pyfs_storage_factory(fileinstance=None, fileurl=None, size=100)
        mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_STORAGE_FACTORY')
        mock_logger.reset_mock()

    # fileinstance is None and size is None
    with patch('weko_deposit.storage.weko_logger') as mock_logger:
        with pytest.raises(WekoDepositStorageError, match="Either fileinstance or both fileurl and size must be specified."):
            pyfs_storage_factory(fileinstance=None, fileurl='some_url', size=None)
        mock_logger.assert_called_with(key='WEKO_DEPOSIT_FAILED_STORAGE_FACTORY')
        mock_logger.reset_mock()
