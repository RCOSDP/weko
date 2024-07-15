
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp

from invenio_iiif.manifest import IIIFMetadata,IIIFManifest

# class IIIFMetadata(dict):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFMetadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
class TestIIIFMetadata:
#     def __init__(self, record, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFMetadata::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_init(self,app,records):
        record = records[0][2]
        obj = IIIFMetadata(record,test1="test1_value",test2="test2_value")
        assert obj._record == record
        assert obj["test1"] == "test1_value"
        assert obj["test2"] == "test2_value"

#     def extract_metadata(self):


# class IIIFManifest(object):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
class TestIIIFManifest:
#     def __init__(self, record, metadata_class=None, extra_meatadata=None):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_init(self,app,records):
        record = records[0][2]
        with app.test_request_context("/test"):
            obj = IIIFManifest(record)
            manifest = obj.manifest
            assert obj.record == record
            assert obj.manifest.description == "conference paper"
            assert manifest.license == ""
            assert manifest.viewingDirection == "left-to-right"


#     def dumps(self):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest::test_dumps -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_dumps(self,app,records):
        record = records[0][2]
        with app.test_request_context("/test"):
            obj = IIIFManifest(record)
            result = obj.dumps()
            assert result == {}

# class ManifestFactory(PrezyManifestFactory):
#     def image(self, ident, label="", iiif=False, region='full', size='full'):
# class Image(PreziImage):
#     def set_hw_from_iiif(self):
