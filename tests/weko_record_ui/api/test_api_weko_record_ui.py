from weko_records_ui.permissions import check_created_id
from pytest_invenio.fixtures import app,es_clear
from mock import mock, patch

class User:
    name=''

def test_check_created_id(app,es_clear):
    record = {"_deposit": {
        "id": "55.1",
        "pid": {
            "type": "recid",
            "value": "55.1",
            "revision_id": 0
        },
        "owners": [
            1
        ],
        "status": "published",
        "created_by": 1
    }, "item_type_id": "6", }

    with app.app_context(),mock.patch('weko_records.serializers.utils.get_item_type_name',return_value="ライフ利用申請"):
        mock_user = mock.MagicMock()
        mock_user.get_id.return_value = '1'
        mock_user.is_authenticated = True
        admin = User
        admin.name = 'Administrator'
        mock_user.roles = [admin]
        # User is admin,,should have permission
        with mock.patch('weko_records_ui.permissions.current_user',mock_user):
            assert check_created_id(record) == True
        non_admin = User
        non_admin.name = 'General'
        mock_user.roles = [non_admin]
        # User is not admin but author,should have permission
        with mock.patch('weko_records_ui.permissions.current_user',mock_user):
            assert check_created_id(record) == True
        # User is not admin nor author,should not have permission
        mock_user.get_id.return_value = '2'
        with mock.patch('weko_records_ui.permissions.current_user',mock_user):
            assert check_created_id(record) == False