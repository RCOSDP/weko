
from invenio_files_rest.models import Bucket, ObjectVersion,FileInstance

from invenio_iiif.handlers import protect_api, image_opener

# def protect_api(uuid=None, **kwargs)
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_handlers.py::test_protect_api -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_protect_api(db,location):
    bucket = Bucket.create()
    obj = ObjectVersion.create(bucket,"test.txt")
    db.session.commit()
    version_id = obj.version_id
    key = obj.key
    
    id = "{}:{}:{}".format(bucket.id,version_id,key)
    result = protect_api(id)
    assert result == obj


# def image_opener(key):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_handlers.py::test_image_opener -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_image_opener(db, location):
    bucket = Bucket.create()
    obj = ObjectVersion.create(bucket,"test.txt")
    db.session.commit()

    import uuid
    fi = FileInstance(id=str(uuid.uuid4()),uri="tests/data/test.txt",storage_class="S",size=18,checksum="test_checksum",readable=True,writable=True,last_check_at=None,last_check=True,json={})
    db.session.add(fi)
    obj.file_id = fi.id
    db.session.merge(obj)
    db.session.commit()

    version_id = obj.version_id
    key = obj.key

    id = "{}:{}:{}".format(bucket.id,version_id,key)
    result = image_opener(id)
    assert result.read() == b""