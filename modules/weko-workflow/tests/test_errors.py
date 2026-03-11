from weko_workflow.errors import MetadataFormatError

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_errors.py::TestMetadataFormatError -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
class TestMetadataFormatError:
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_errors.py::TestMetadataFormatError::test_metadata_format_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_metadata_format_error(self):
        # Test with a single cause
        cause = "Invalid metadata format"
        error = MetadataFormatError(cause)
        assert error.description == 'Metadata format Error.\n  - Invalid metadata format'

        # Test with multiple causes
        causes = ["Invalid metadata format", "Another error"]
        error = MetadataFormatError(causes)
        assert error.description == 'Metadata format Error.\n  - Invalid metadata format\n  - Another error'