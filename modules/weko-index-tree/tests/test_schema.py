import pytest

from marshmallow import ValidationError

from weko_index_tree.schema import IndexesSchemaBase, validate_public_date, validate_role_or_group


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_schema.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp --full-trace

# def validate_role_or_group(value):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_schema.py::test_validate_role_or_group -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp --full-trace
def test_validate_role_or_group():
    valid_role = "3,4,-98,-99"
    invalid_role = "3.4.-98.-99"

    # Valid role should pass
    try:
        validate_role_or_group(valid_role)
    except ValidationError as e:
        assert False, f"Validation failed for valid role: {e}"

    # Invalid role should raise ValidationError
    with pytest.raises(ValidationError) as excinfo:
        validate_role_or_group(invalid_role)
    assert "Not a valid role or group format." in str(excinfo.value)


# def validate_public_date(value):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_schema.py::test_validate_public_date -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp --full-trace
def test_validate_public_date():
    valid_date = "20230101"
    invalid_date = "2023-01-01"

    # Valid date should pass
    try:
        validate_public_date(None)
        validate_public_date(valid_date)
    except ValidationError as e:
        assert False, f"Validation failed for valid date: {e}"

    # Invalid date should raise ValidationError
    with pytest.raises(ValidationError) as excinfo:
        validate_public_date(invalid_date)
    assert "Not a valid date format. Use YYYYMMDD." in str(excinfo.value)


# class IndexesSchemaBase:
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_schema.py::TestIndexesSchemaBase -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp --full-trace
class TestIndexesSchemaBase:
    def test_valid_index(self):
        index = {
            "parent": 1,
            "index_name": "Index Name",
            "index_name_english": "Index Name English",
            "index_link_name": "Index Link Name",
            "index_link_name_english": "Index Link Name English",
            "index_link_enabled": True,
            "comment": "Comment",
            "more_check": False,
            "display_no": 1,
            "harvest_public_state": True,
            "display_format": "Format",
            "public_state": True,
            "public_date": "20230101",
            "rss_status": True,
            "browsing_role": "3,4,-98,-99",
            "contribute_role": "3,4,-98,-99",
            "browsing_group": "",
            "contribute_group": "",
            "online_issn": "1234-5678",
        }

        schema = IndexesSchemaBase()
        result = schema.load(index).data
        assert result == index

        index_s = {
            "parent": "2",                  # String instead of integer
            "index_name": "Index Name",
            "index_name_english": "Index Name English",
            "index_link_name": "Index Link Name",
            "index_link_name_english": "Index Link Name English",
            "index_link_enabled": "True",   # String instead of boolean
            "comment": "Comment",
            "more_check": "False",          # String instead of boolean
            "display_no": "1",              # String instead of integer
            "harvest_public_state": "true", # String instead of boolean
            "display_format": "Format",
            "public_state": "false",        # String instead of boolean
            "public_date": "20230101",
            "rss_status": 1,           # String instead of boolean
            "browsing_role": "3,4,-98,-99",
            "contribute_role": "3,4,-98,-99",
            "browsing_group": "",
            "contribute_group": "",
            "online_issn": "1234-5678",
            "invalid_field": "Invalid"      # Extra field not in schema
        }
        # Test with string values for boolean fields
        schema = IndexesSchemaBase()
        result = schema.load(index_s).data

        assert result["parent"] == 2
        assert result["index_link_enabled"] is True
        assert result["more_check"] is False
        assert result["display_no"] == 1
        assert result["harvest_public_state"] is True
        assert result["public_state"] is False
        assert result["rss_status"] is True
        assert "invalid_field" not in result  # Extra field should be ignored

    def test_invalid_index(self):
        index = {
            "parent": "X",                      # Invalid type, should be integer
            "index_name": 123,                  # Invalid type, should be string
            "index_name_english": "",           # Invalid type, should not be empty
            "index_link_name": "Index Link Name",
            "index_link_name_english": "Index Link Name English",
            "index_link_enabled": True,
            "comment": "Comment",
            "more_check": False,
            "display_no": 1,
            "harvest_public_state": True,
            "display_format": "Format",
            "public_state": True,
            "public_date": "2023-01-01",        # Invalid format, should be YYYYMMDD
            "rss_status": True,
            "browsing_role": [3,4,-98,-99],     # Invalid type, should be string
            "contribute_role": "3.4.-98.-99",   # Invalid type, should be separated by commas
            "browsing_group": "",
            "contribute_group": "",
            "online_issn": "1234-5678",
        }

        schema = IndexesSchemaBase()
        with pytest.raises(ValidationError) as excinfo:
            schema.load(index)
        assert "parent" in excinfo.value.messages
        assert "index_name" in excinfo.value.messages
        assert "index_name_english" in excinfo.value.messages
        assert "public_date" in excinfo.value.messages
        assert "browsing_role" in excinfo.value.messages
        assert "contribute_role" in excinfo.value.messages
