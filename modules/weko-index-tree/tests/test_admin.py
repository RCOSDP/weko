import base64
import pytest
import werkzeug
from io import BytesIO
from mock import patch, MagicMock

from jinja2.exceptions import TemplateNotFound
from flask import current_app, url_for
from werkzeug.local import LocalProxy
from invenio_accounts.testutils import login_user_via_session


SMALLEST_JPEG_B64 = """\
/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8Q
EBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k=
"""

class MockSyncFunc:
    def __init__(self, form):
        pass

    def validate(self):
        return True


# class IndexLinkSettingView(BaseView):
# def index(self):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_admin.py::test_IndexLinkSettingView -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 403),
        (2, 400),
        (3, 400),
        (4, 400)
    ],
)
def test_IndexLinkSettingView(app, users, id, status_code):
    app.config['WEKO_INDEX_TREE_LINK_ADMIN_TEMPLATE'] = 'weko_index_tree/admin/index_link_setting.html'
    with app.test_client() as client:
        login_user_via_session(client=client, email=users[id]["email"])
        res = client.get(url_for('indexlink.index'))
        assert res.status_code==status_code

        mock_sync_func = MagicMock(side_effect=MockSyncFunc)
        with patch("weko_index_tree.admin.FlaskForm", mock_sync_func):
            _form = {'indexlink': 'enable'}
            res = client.post(url_for('indexlink.index'), data=_form)
            assert res.status_code==status_code

            _form = {'indexlink': 'disable'}
            res = client.post(url_for('indexlink.index'), data=_form)
            assert res.status_code==status_code


# class IndexEditSettingView(BaseView):
# def index(self, index_id=0):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_admin.py::test_IndexEditSettingView -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (2, 400),
        (3, 400),
        (4, 400)
    ],
)
def test_IndexEditSettingView(app, db, location, users, id, status_code):
    app.config['WEKO_INDEX_TREE_INDEX_ADMIN_TEMPLATE'] = 'weko_index_tree/admin/index_edit_setting.html'
    app.config['WEKO_THEME_INSTANCE_DATA_DIR'] = 'data'
    _file1 = werkzeug.datastructures.FileStorage(
                stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="example image.jpg",
                content_type="image/jpg",
            )
    _file2 = werkzeug.datastructures.FileStorage(
                stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="",
                content_type="image/jpg",
            )
    _file3 = werkzeug.datastructures.FileStorage(
                stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="example image.jpg",
                content_type="image/jpg",
            )
    with app.test_client() as client:
        login_user_via_session(client=client, email=users[id]["email"])
        # need to fix
        with pytest.raises(Exception) as e:
            res = client.get(url_for('indexedit.index'))
        assert e.type==TemplateNotFound

        with pytest.raises(Exception) as e:
            res = client.post(url_for('indexedit.upload_image'), data=dict(uploadFile=_file1))
        assert e.type==FileNotFoundError

        res = client.post(url_for('indexedit.upload_image'), data=dict(uploadFile=_file2))
        assert res.status_code==status_code

        res = client.post(url_for('indexedit.upload_image'), data=dict(data=_file3))
        assert res.status_code==status_code
