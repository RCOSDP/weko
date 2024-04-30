import pytest
import json
from mock import patch, MagicMock
from flask import Flask
from b2handle.handleexceptions import HandleAlreadyExistsException

from weko_handle.api import Handle


# class Handle(object):
# def register_handle(self, location, hdl="", overwrite=False):
def test_register_handle(app):
    sample = Handle()
    
    # Exception coveraga ~ Line 86 - 89
    try:
        location = 1
        sample.register_handle(
            location=location
        )
    except:
        pass
    
    try:
        sample.register_handle(
            location=None,hdl=1
        )
    except:
        pass
    
    # Exception coveraga
    with patch("weko_handle.api.PIDClientCredentials.load_from_JSON", side_effect=HandleAlreadyExistsException()):
        try:
            location = 1
            sample.register_handle(
                location=location
            )
        except:
            pass


def test_handle_get_ark_identifier_from_ark_server(app):
    handleObject = Handle()

    location = "http://test-location/test-item"

    ark_id_prefix = "id/ark:/99999/"

    result_1 = handleObject.get_ark_identifier_from_ark_server(
        location=location
    )

    assert result_1 is None

    recordData = {
        "owner": "test_owner",
        "item_title": "test_item_title",
        "publish_date": "test_publish_date",
            "item_1617186819068": {
                "attribute_name": "Identifier Registration",
                "attribute_value_mlt": [
                    {
                        "subitem_identifier_reg_text" :"test/0000000001",
                        "subitem_identifier_reg_type": "JaLC"
                    }
                ]
        },
    }

    result_2 = handleObject.get_ark_identifier_from_ark_server(
        location=location,
        record=recordData,
        useArkIdentifier=True
    )

    assert ark_id_prefix in result_2

    indexData = {
        "ezid_who": "test_ezid_who",
        "ezid_what": "test_ezid_what",
        "ezid_when": "test_ezid_when",
    }

    result_3 = handleObject.get_ark_identifier_from_ark_server(
        location=location,
        index=indexData,
        useArkIdentifier=True
    )
    assert ark_id_prefix in result_3

    with pytest.raises(Exception):
        result_4 = handleObject.get_ark_identifier_from_ark_server(
            location=location,
            record="record"
        )
        assert result_4 is None
        raise

    
# def get_prefix(self): 
def test_get_prefix(app):
    sample = Handle()

    def load_from_JSON(item):

        def get_prefix():
            return "get_prefix"

        load_from_JSON_MagicMock = MagicMock()
        load_from_JSON_MagicMock.get_prefix = get_prefix
        
        return load_from_JSON_MagicMock
    
    data1 = MagicMock()
    data1.load_from_JSON = load_from_JSON

    with app.app_context():
        with patch("weko_handle.api.PIDClientCredentials", return_value=data1):
            assert sample.get_prefix() != None