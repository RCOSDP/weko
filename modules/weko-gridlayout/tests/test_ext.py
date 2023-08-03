import json
import pytest
from mock import patch, Mock, MagicMock

from weko_gridlayout.ext import WekoGridLayout


test = WekoGridLayout()


# class WekoGridLayout(object): 
# def init_config(self, app): 
def test_init_config(i18n_app):
    i18n_app.config['BASE_TEMPLATE'] = "test.html"
    
    test.init_config(i18n_app)