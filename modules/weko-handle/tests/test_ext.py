import pytest
import json
from mock import patch, MagicMock
from flask import Flask

from weko_handle.ext import WekoHandle


# class WekoHandle(object): 
# def init_config(self, app): 
def test_init_config(app):
    sample = WekoHandle()
    app.config['BASE_EDIT_TEMPLATE'] = "test/test"
    sample.init_config(app)
