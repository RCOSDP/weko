
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
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
#     def _init_hash(self):
    def test__init_hash(self,wekofs):
        type, hash = wekofs._init_hash()
        assert type=='sha256'
        assert len(hash.hexdigest())==64

#     def upload_file(self, fjson):
    def test_upload_file(self,app,wekofs,wekofs_testpath):
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
            wekofs.upload_file(fjson)
            assert fjson['file'] == base64.b64encode(data).decode("utf-8")
        
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
            wekofs.upload_file(fjson)
            assert fjson['file'] == base64.b64encode(data).decode("utf-8")

# def make_path(base_uri, path, filename, path_dimensions, split_length):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::test_make_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_make_path():
    myid = 'deadbeef-dead-dead-dead-deaddeafbeef'
    base = '/base'
    f = 'data'
    assert make_path(base, myid, f, 1, 1) == '/base/d/eadbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 3, 1) == '/base/d/e/a/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 1, 3) == '/base/dea/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 2, 2) == '/base/de/ad/beef-dead-dead-dead-deaddeafbeef/data'
    pytest.raises(AssertionError, make_path, base, myid, f, 1, 50)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 1)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 50)



# def pyfs_storage_factory(fileinstance=None, default_location=None,
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_storage.py::test_pyfs_storage_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_pyfs_storage_factory(app,wekofs,wekofs_testpath,location):
    bucket = Bucket.create()
    key = 'hello2.txt'
    data = b'helloworld!'
    stream = BytesIO(data)
    obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
    with app.test_request_context():
        file = WekoFileObject(obj,{})
        factory = pyfs_storage_factory(fileinstance=file.obj.file)
        assert isinstance(factory,WekoFileStorage) == True
    
    with app.test_request_context():
        file = WekoFileObject(obj,{})
        file.obj.file.uri = ''
        with pytest.raises(AssertionError):
            factory = pyfs_storage_factory(fileinstance=file.obj.file)
        factory = pyfs_storage_factory(fileinstance=file.obj.file,default_location=location.uri)
        assert isinstance(factory,WekoFileStorage) == True
    

    with app.test_request_context():
        file = WekoFileObject(obj,{})
        fileurl = make_path(
                location.uri,
                str(file.obj.file.id),
                'data',
                app.config['FILES_REST_STORAGE_PATH_DIMENSIONS'],
                app.config['FILES_REST_STORAGE_PATH_SPLIT_LENGTH'],
            )
        factory = pyfs_storage_factory(fileurl=fileurl,size=file.obj.file.size,default_location=location.uri)
        assert isinstance(factory,WekoFileStorage) == True

    