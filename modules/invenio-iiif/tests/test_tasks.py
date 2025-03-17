
import uuid

from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_iiif.tasks import create_thumbnail

# def create_thumbnail(uuid, thumbnail_width):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_tasks.py::test_create_thumbnail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_create_thumbnail(app, db, location):
    with app.test_request_context("/test"):
        bucket = Bucket.create()
        obj = ObjectVersion.create(bucket,"image-public-domain.jpg")

        fi = FileInstance(id=str(uuid.uuid4()),uri="tests/data/image-public-domain.jpg",storage_class="S",size=18,checksum="test_checksum",readable=True,writable=True,last_check_at=None,last_check=True,json={})
        db.session.add(fi)
        obj.file_id = fi.id
        db.session.merge(obj)
        db.session.commit()

        version_id = obj.version_id
        key = obj.key

        id = "{}:{}:{}".format(bucket.id,version_id,key)
        create_thumbnail(id,"40")
