import pytest
from mock import patch, MagicMock

from weko_records.ext import WekoRecords


# class WekoRecords(object): 
# def init_config(self, app): 
def test_init_config(app):
    test = WekoRecords()
    app.config["BASE_TEMPLATE"] = "BASE_TEMPLATE"

    assert test.init_config(app) == None