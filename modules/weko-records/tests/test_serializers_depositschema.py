import pytest
from mock import patch, MagicMock

from weko_records.serializers.depositschema import DepositSchemaV1


# class DepositSchemaV1(JSONSerializer): 
# def dump_links
def test_dump_links(app):
    test = DepositSchemaV1()
    obj = {
        "links": {
            "bucket": "bucket"
        },
        "metadata": {
            "_buckets": {
                "deposit": "deposit"
            }
        }
    }

    with patch("weko_records.serializers.depositschema.external_url_for", return_value="test"):
        assert test.dump_links(
            obj=obj
        ) != None


# def remove_envelope
def test_remove_envelope(app):
    test = DepositSchemaV1()
    data = {
        "metadata": {
            "_buckets": {
                "deposit": "deposit"
            }
        }
    }

    assert test.remove_envelope(
        data=data
    ) != None