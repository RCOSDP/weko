import json
import pytest
from mock import patch, MagicMock

from weko_theme.ext import WekoTheme


# class WekoTheme(object):
def test_WekoTheme(i18n_app):
    i18n_app.config['ADMIN_UI_SKIN'] = 'skin_red'
    test = WekoTheme()
    test.init_config(i18n_app)