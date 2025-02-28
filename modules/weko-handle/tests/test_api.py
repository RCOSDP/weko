import pytest
import json
from mock import patch, MagicMock
from flask import Flask
from b2handle.handleexceptions import HandleAlreadyExistsException, HandleNotFoundException

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


def test_delete_handle(app):
    sample = Handle()

    try:
        sample.delete_handle(
            hdl=1
        )
    except:
        pass

    # HandleNotFoundException coveraga
    with patch("weko_handle.api.PIDClientCredentials.load_from_JSON", side_effect=HandleNotFoundException()):
        try:
            sample.delete_handle(
                hdl=1
            )
        except:
            pass

    # AttributeError coveraga
    with patch("weko_handle.api.PIDClientCredentials.load_from_JSON", side_effect=AttributeError()):
        try:
            sample.delete_handle(
                hdl=1
            )
        except:
            pass

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
