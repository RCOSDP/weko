
import pytest
from mock import MagicMock
from werkzeug.exceptions import HTTPException

from invenio_files_rest.models import Bucket, ObjectVersion,FileInstance

from invenio_iiif.handlers import protect_api, image_opener


def _patch_permission(mocker, can):
    return mocker.patch(
        "invenio_iiif.handlers.iiif_object_permission_factory",
        return_value=MagicMock(can=MagicMock(return_value=can)))


# def protect_api(uuid=None, **kwargs)
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_handlers.py::test_protect_api -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_protect_api(db,location,mocker):
    bucket = Bucket.create()
    obj = ObjectVersion.create(bucket,"test.txt")
    db.session.commit()
    version_id = obj.version_id
    key = obj.key

    id = "{}:{}:{}".format(bucket.id,version_id,key)
    mock_permission = _patch_permission(mocker, True)
    result = protect_api(id)
    assert result == obj
    mock_permission.assert_called_with(obj)


# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_handlers.py::test_protect_api_no_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_protect_api_no_permission(db,location,mocker):
    bucket = Bucket.create()
    obj = ObjectVersion.create(bucket,"test.txt")
    db.session.commit()

    id = "{}:{}:{}".format(bucket.id,obj.version_id,obj.key)
    _patch_permission(mocker, False)
    with pytest.raises(HTTPException) as httperror:
        protect_api(id)
    assert httperror.value.code == 404


# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_handlers.py::test_protect_api_not_found -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_protect_api_not_found(db,location,mocker):
    bucket = Bucket.create()
    obj = ObjectVersion.create(bucket,"test.txt")
    db.session.commit()

    id = "{}:{}:{}".format(bucket.id,obj.version_id,"not_exist.txt")
    mock_permission = _patch_permission(mocker, True)
    with pytest.raises(HTTPException) as httperror:
        protect_api(id)
    assert httperror.value.code == 404
    mock_permission.assert_not_called()


# def image_opener(key):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_handlers.py::test_image_opener -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_image_opener(db, location, mocker):
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
    _patch_permission(mocker, True)
    result = image_opener(id)
    assert result.read() == b""
