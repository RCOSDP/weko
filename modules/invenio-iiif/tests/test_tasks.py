
import uuid

from invenio_iiif.tasks import create_thumbnail

# def create_thumbnail(uuid, thumbnail_width):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_tasks.py::test_create_thumbnail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_create_thumbnail():
    id = uuid.uuid4()
    create_thumbnail(id,"40")
    