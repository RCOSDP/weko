from flask_login.utils import login_user

from weko_workflow.api import Flow, WorkActivity,UpdateItem, PublishStatus
import unittest
from unittest.mock import MagicMock, patch
from weko_deposit.api import WekoIndexer
from weko_records_ui.models import FileSecretDownload
from weko_schema_ui.models import PublishStatus

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_action(app, client, users, db, action_data):
    with app.test_request_context():
        login_user(users[2]["obj"])
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'create_flow_test'})
        assert flow.flow_name == 'create_flow_test'

        _flow_data = [
            {
                "id":"2",
                "name":"End",
                "date":"2022-12-09",
                "version":"1.0.0",
                "user":"2",
                "user_deny": False,
                "role":"0",
                "role_deny": False,
                "workflow_flow_action_id":8,
                "send_mail_setting": {
                    "request_approval": False,
                    "inform_approval": False,
                    "inform_reject": False},
                "action":"ADD"
            },
            {
                "id":"1",
                "name":"Start",
                "date":"2022-12-09",
                "version":"1.0.0",
                "user":"2",
                "user_deny": False,
                "role":"0",
                "role_deny": False,
                "workflow_flow_action_id":7,
                "send_mail_setting": {
                    "request_approval": False,
                    "inform_approval": False,
                    "inform_reject": False
                },
                "action":"ADD"
            },
            {
                "id":"3",
                "name":"Item Registration",
                "date":"2022-12-9",
                "version":"1.0.1",
                "user":"2",
                "user_deny": False,
                "role":"0",
                "role_deny": False,
                "workflow_flow_action_id":-1,
                "send_mail_setting": {
                    "request_approval": False,
                    "inform_approval": False,
                    "inform_reject": False
                },
            "action":"ADD"
            }
        ]
        _flow.upt_flow_action(flow.flow_id, _flow_data)

        flow_id = flow.flow_id
        flow = _flow.get_flow_detail(flow_id)
        assert flow.flow_name == 'create_flow_test'

        res = _flow.del_flow(flow_id)
        assert res['code'] == 500

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_get_flow_action_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_get_flow_action_list(db,workflow):
    res = Flow().get_flow_action_list(workflow["flow"].id)
    assert len(res) == 7
    assert res[0].action_order == 1
    assert res[1].action_order == 2
    assert res[2].action_order == 3
    assert res[3].action_order == 4
    assert res[4].action_order == 5
    assert res[5].action_order == 6
    assert res[6].action_order == 7

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_filter_by_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_filter_by_date(app, db):
    query = db.session.query()
    activity = WorkActivity()
    assert activity.filter_by_date('2022-01-01', '2022-01-02', query)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_all_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_all_activity_list(app, client, users, db_register):
    with app.test_request_context():
        login_user(users[2]["obj"])
        activity = WorkActivity()
        activities = activity.get_all_activity_list()
        assert len(activities) == 13


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_activity_index_search(app, db_register):
    activity = WorkActivity()
    with app.test_request_context():
        activity_detail, item, steps, action_id, cur_step, \
            temporary_comment, approval_record, step_item_login_url,\
            histories, res_check, pid, community_id, ctx = activity.get_activity_index_search('1')
        assert activity_detail.id == 1
        assert activity_detail.action_id == 1
        assert activity_detail.title == 'test'
        assert activity_detail.activity_id == '1'
        assert activity_detail.flow_id == 1
        assert activity_detail.workflow_id == 1
        assert activity_detail.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_upt_activity_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_upt_activity_detail(app, db_register, db_records):
    activity = WorkActivity()
    db_activity = activity.upt_activity_detail(db_records[2][2].id)
    assert db_activity.id == 4
    assert db_activity.action_id == 2
    assert db_activity.title == 'test item1'
    assert db_activity.activity_id == '2'
    assert db_activity.flow_id == 1
    assert db_activity.workflow_id == 1
    assert db_activity.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_corresponding_usage_activities(app, db_register):
    activity = WorkActivity()
    usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
    assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
    assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

from unittest.mock import call, patch, MagicMock

class MockRecord(dict):
    def commit(self):
        pass

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_publish -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@patch('weko_records_ui.models.FileSecretDownload')
@patch('weko_deposit.api.WekoIndexer')
@patch('weko_workflow.api.db.session.commit')
def test_publish(mock_db_commit, mock_WekoIndexer, mock_FileSecretDownload):
    def create_mock_record(publish_status, accessroles, filenames, recid='12345'):
        attribute_value_mlt = [{'accessrole': role, 'filename': filename} for role, filename in zip(accessroles, filenames)]
        record = MockRecord({
            'publish_status': publish_status,
            'recid': recid,
            'some_field': {
                'attribute_value_mlt': attribute_value_mlt
            }
        })
        record.commit = MagicMock()
        return record

    def assert_publish(record, reset_mock=True):
        update_item.publish(record)
        assert record['publish_status'] == PublishStatus.PUBLIC.value
        record.commit.assert_called_once()
        mock_db_commit.assert_called()
        mock_WekoIndexer.return_value.update_es_data.assert_called_with(record, update_revision=False, field='publish_status')
        if reset_mock:
            mock_FileSecretDownload.query.filter_by.return_value.all.reset_mock()

    # Mock record objects
    record1 = create_mock_record(None, [None], ['testfile.txt'])
    record2 = create_mock_record(PublishStatus.PRIVATE.value, ['open_date'], ['testfile.txt'])
    record3 = create_mock_record(PublishStatus.NEW.value, ['open_no'], ['testfile.txt'])
    record4 = create_mock_record(PublishStatus.DELETE.value, ['other_date'], ['testfile.txt'])
    record5 = create_mock_record(PublishStatus.PUBLIC.value, ['other_date'], ['testfile.txt'], None)
    record_multiple_files = create_mock_record(PublishStatus.PUBLIC.value, ['open_no', 'open_date', 'other_date'], ['testfile1.txt', 'testfile2.txt', 'testfile3.txt'])

    # Mock secret URLs
    mock_secret_url = MagicMock()
    mock_secret_url.delete_logically = MagicMock()
    mock_FileSecretDownload.query.filter_by.return_value.all.return_value = [mock_secret_url]

    # Create instance of UpdateItem
    update_item = UpdateItem()

    # record1のテスト
    assert_publish(record1)

    # record2のテスト
    assert_publish(record2)

    # record3のテスト
    assert_publish(record3)

    # record4のテスト
    assert_publish(record4, reset_mock=False)
    # record4のシークレットURL削除確認
    mock_FileSecretDownload.query.filter_by.assert_called_with(record_id='12345', is_deleted=False, file_name='testfile.txt')
    assert mock_secret_url.delete_logically.call_count == 1

    # モックの呼び出し履歴をリセット
    mock_FileSecretDownload.query.filter_by.reset_mock()
    mock_secret_url.delete_logically.reset_mock()

    # record5のテスト (recidがNoneの場合)
    assert_publish(record5, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_not_called()
    mock_secret_url.delete_logically.assert_not_called()

    
    # 複数のファイルが含まれている場合のテスト
    record_multiple_files = create_mock_record(PublishStatus.DELETE.value, ['other_date', 'other_date'], ['testfile1.txt', 'testfile2.txt'])
    assert_publish(record_multiple_files, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    assert mock_secret_url.delete_logically.call_count == 2

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # 片方のファイルが更新され、片方が更新されない場合のテスト
    record_partial_update = create_mock_record(PublishStatus.DELETE.value, ['other_date', 'open_no'], ['testfile1.txt', 'testfile2.txt'])
    assert_publish(record_partial_update, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    assert mock_secret_url.delete_logically.call_count == 1

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # どちらのファイルも論理削除が行われない場合のテスト
    record_partial_update = create_mock_record(PublishStatus.DELETE.value, ['open_no', 'open_no'], ['testfile1.txt', 'testfile2.txt'])
    assert_publish(record_partial_update, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    mock_secret_url.delete_logically.assert_not_called()

    # モックの呼び出し履歴をリセット
    mock_secret_url.delete_logically.reset_mock()

    # 2つ以上のファイルすべてが更新され、論理削除が行われる場合のテスト
    record_partial_update = create_mock_record(PublishStatus.DELETE.value, ['other_date', 'other_date','other_date'], ['testfile1.txt', 'testfile2.txt', 'testfile3.txt'])
    assert_publish(record_partial_update, reset_mock=False)
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile1.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile2.txt')
    mock_FileSecretDownload.query.filter_by.assert_any_call(record_id='12345', is_deleted=False, file_name='testfile3.txt')
    assert mock_secret_url.delete_logically.call_count == 3

    # attribute_value_mltが空のリストの場合のテスト
    record_empty_role = MockRecord({
        'publish_status': PublishStatus.PRIVATE.value,
        'recid': '12345',
        'some_field': {
            'attribute_value_mlt': []
        }
    })
    update_item.publish(record_empty_role)
    assert record_empty_role['publish_status'] == PublishStatus.PUBLIC.value

    # "accessrole"が欠落しているケースのテスト
    record_no_role = MockRecord({
        'publish_status': PublishStatus.PRIVATE.value,
        'recid': '12345',
        'some_field': {
            'attribute_value_mlt': [{'filename': 'testfile.txt'}]
        }
    })
    update_item.publish(record_no_role)
    assert record_no_role['publish_status'] == PublishStatus.PUBLIC.value

    # "attribute_value_mlt"が辞書ではない場合のテスト
    record_non_dict_attribute_value_mlt = MockRecord({
        'publish_status': PublishStatus.PRIVATE.value,
        'recid': '12345',
        'some_field': {
            'attribute_value_mlt': ['not_dict']
        }
    })
    update_item.publish(record_non_dict_attribute_value_mlt)
    assert record_non_dict_attribute_value_mlt['publish_status'] == PublishStatus.PUBLIC.value