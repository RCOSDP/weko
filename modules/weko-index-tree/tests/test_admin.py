import pytest
from flask import current_app, session, url_for
from flask_admin import menu
from flask_security.utils import hash_password
from invenio_db import db
from werkzeug.local import LocalProxy
from flask_admin import BaseView, expose
from flask_login import current_user
from mock import patch

from invenio_accounts import InvenioAccounts, testutils
from invenio_accounts.cli import users_create
from invenio_accounts.models import SessionActivity
from invenio_accounts.testutils import login_user_via_view
from invenio_accounts.testutils import login_user_via_session

from weko_records.utils import custom_record_medata_for_export, \
    remove_weko2_special_character, selected_value_by_language
from weko_index_tree.admin import IndexLinkSettingView, IndexEditSettingView


_datastore = LocalProxy(
    lambda: current_app.extensions['security'].datastore
)

# class IndexLinkSettingView(BaseView):
# def index(self):
def test_index(app, i18n_app, indices, client_rest, client_api, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        admin_test = IndexLinkSettingView()

        assert not admin_test.index()


# class IndexEditSettingView(BaseView):
# def index(self, index_id=0):
def test_index_2(app, i18n_app, client_rest, client_api, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        admin_test = IndexEditSettingView()
    
        assert not admin_test.index()