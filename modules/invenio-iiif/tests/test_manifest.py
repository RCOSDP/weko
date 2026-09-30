
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp

from mock import MagicMock

from invenio_iiif.manifest import IIIFMetadata,IIIFManifest,Image

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

# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest::test_dumps_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_dumps_permission(self,app,records,mocker):
        record = records[0][2]
        allowed = MagicMock(key="allowed.png")
        denied = MagicMock(key="denied.png")
        mock_query = MagicMock()
        mock_query.all.return_value = [allowed, denied]
        mocker.patch("invenio_iiif.manifest.ObjectVersion.get_by_bucket",
                     return_value=mock_query)
        mocker.patch("invenio_iiif.manifest.can_preview", return_value=True)
        mocker.patch("invenio_iiif.manifest.PreviewFile")
        mock_permission = mocker.patch(
            "invenio_iiif.manifest.iiif_object_permission_factory",
            side_effect=lambda obj, record=None: MagicMock(
                can=MagicMock(return_value=obj is allowed)))
        mock_key = mocker.patch("invenio_iiif.manifest.iiif_image_key",
                                side_effect=lambda obj: "bucket:version:" + obj.key)

        def set_hw(image):
            image.height = 10
            image.width = 10
        mocker.patch.object(Image, "set_hw_from_iiif", autospec=True,
                            side_effect=set_hw)
        with app.test_request_context("/test"):
            obj = IIIFManifest(record)
            obj.manifest.toJSON = MagicMock(return_value={"test": "value"})
            result = obj.dumps()
            assert result == {"test": "value"}
            mock_key.assert_called_once_with(allowed)
            assert mock_permission.call_args[1]["record"] == record

            # no permitted image
            mocker.patch(
                "invenio_iiif.manifest.iiif_object_permission_factory",
                return_value=MagicMock(can=MagicMock(return_value=False)))
            obj = IIIFManifest(record)
            assert obj.dumps() == {}

# class ManifestFactory(PrezyManifestFactory):
#     def image(self, ident, label="", iiif=False, region='full', size='full'):
# class Image(PreziImage):
#     def set_hw_from_iiif(self):
