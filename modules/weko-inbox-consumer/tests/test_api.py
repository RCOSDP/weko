from flask import Flask
from mock import patch, MagicMock, Mock
import json
import datetime
from invenio_accounts.testutils import \
    login_user_via_view, login_user_via_session
from weko_inbox_consumer.api import \
    check_inbox_publish, get_notification_filter,\
    get_notifications, get_notification, create_push_data, get_oai_format


def mock_datetime(year, month, day, hour, minutes, second, minsecond):
    datetime_mock = MagicMock(wraws=datetime.datetime)
    datetime_mock.now.return_value = \
        datetime.datetime(year, month, day, hour,
                          minutes, second, minsecond
                          )
    datetime_mock.strptime.side_effect = datetime.datetime.strptime
    datetime_mock.strftime.side_effect = datetime.datetime.strftime
    return datetime_mock


@patch('weko_inbox_consumer.api.inbox_url', return_value="http://inbox")
def test_check_inbox_publish1(
    mock_inbox, app, db,
    test_push_data, test_method_result, user, monkeypatch
                              ):
    # cookieあり、ユーザーあり、かつデフォルト範囲内
    monkeypatch.setattr('weko_inbox_consumer.api.datetime',
                        mock_datetime(2022, 2, 2, 12, 0, 0, 0)
                        )
    from weko_inbox_consumer import api
    api.get_notification_filter =\
        Mock(return_value=test_method_result)
    api.create_push_data = Mock(side_effect=test_push_data)
    api.request_signposting = Mock(return_value="xxx")
    result = [
        {
            'title': 'Item release',
            'body': 'Items awaiting approval have been published.',
            'data': test_push_data[i],
            'url': test_method_result[i]['object']['id']
        } for i in range(2)]
    with app.test_client() as client:
        login_user_via_session(client, user=user)
        client.set_cookie("localhost:5000",
                          "LatestGet",
                          "{\"1\":\"2022-02-02 00:00:00\"}"
                          )
        res = client.get('/check_inbox/publish')
        cookie = res.headers['Set-Cookie'].split(';')[0].\
            replace('LatestGet=', '')
        assert json.loads(res.data) == result
        assert json.loads(cookie) == "{\"1\": \"2022-02-02 12:00:00\"}"


@patch('weko_inbox_consumer.api.inbox_url', return_value="http://inbox")
def test_check_inbox_publish2(
    mock_inbox, app, db,
    test_push_data, test_method_result, user, monkeypatch
                              ):
    # cookieなし
    monkeypatch.setattr('weko_inbox_consumer.api.datetime',
                        mock_datetime(2022, 2, 2, 12, 0, 0, 0)
                        )
    from weko_inbox_consumer import api
    api.get_notification_filter =\
        Mock(return_value=test_method_result)
    api.create_push_data = Mock(side_effect=test_push_data)
    api.request_signposting = Mock(return_value="xxx")
    result = [
        {
            'title': 'Item release',
            'body': 'Items awaiting approval have been published.',
            'data': test_push_data[i],
            'url': test_method_result[i]['object']['id']
        } for i in range(2)]
    with app.test_client() as client:
        login_user_via_session(client, user=user)
        res = client.get('/check_inbox/publish')
        cookie = res.headers['Set-Cookie'].split(';')[0].\
            replace('LatestGet=', '')
        assert json.loads(res.data) == result
        assert json.loads(cookie) == "{\"1\": \"2022-02-02 12:00:00\"}"


@patch('weko_inbox_consumer.api.inbox_url', return_value="http://inbox")
def test_check_inbox_publish3(
    mock_inbox, app, db,
    test_push_data, test_method_result, user, monkeypatch
                              ):
    # cookieあり、デフォルトより前
    monkeypatch.setattr('weko_inbox_consumer.api.datetime',
                        mock_datetime(2022, 2, 2, 12, 0, 0, 0)
                        )
    from weko_inbox_consumer import api
    mock_get_notification = MagicMock(return_value=test_method_result)
    api.get_notification_filter =\
        mock_get_notification
    api.create_push_data = MagicMock(side_effect=test_push_data)
    api.request_signposting = MagicMock(return_value="xxx")
    result = [
        {
            'title': 'Item release',
            'body': 'Items awaiting approval have been published.',
            'data': test_push_data[i],
            'url': test_method_result[i]['object']['id']
        } for i in range(2)]
    with app.test_client() as client:
        login_user_via_session(client, user=user)
        client.set_cookie("localhost:5000",
                          "LatestGet",
                          "{\"1\":\"2021-02-02 00:00:00\"}"
                          )
        res = client.get('/check_inbox/publish')
        cookie = res.headers['Set-Cookie'].split(';')[0].\
            replace('LatestGet=', '')
        args, kwargs = mock_get_notification.call_args
        assert json.loads(res.data) == result
        assert json.loads(cookie) == "{\"1\": \"2022-02-02 12:00:00\"}"
        assert args[1] == '2022-01-26 12:00:00'


@patch('weko_inbox_consumer.api.inbox_url', return_value='http://inbox')
def test_get_notificatin_filter(app, db,
                                test_inbox_notifications,
                                test_notification,
                                test_method_result,
                                user
                                ):
    # 正常系
    mock_notifications = MagicMock(return_value=test_inbox_notifications)
    mock_notification = MagicMock(side_effect=test_notification)
    result = test_method_result
    user_id = user.id
    with app.test_client() as client:
        login_user_via_session(client, user=user)
        with patch('weko_inbox_consumer.api.get_notifications',
                   mock_notifications
                   ):
            with patch('weko_inbox_consumer.api.get_notification',
                       mock_notification
                       ):
                test = get_notification_filter(
                    None, None, str(user_id), 'action1', "http://test.com")
                assert test == result


@patch('weko_inbox_consumer.api.inbox_url', return_value="http://xxx/inbox")
def test_get_notifications(inbox_mock, test_inbox_notifications):
    # 正常系
    with patch('weko_inbox_consumer.api.ldnlib.Consumer.notifications',
               return_value=test_inbox_notifications
               ):
        test = get_notifications('http://test/inbox',
                                 '2022-01-01 12:12:12'
                                 )
        assert test == test_inbox_notifications


def test_get_notification(test_notification):
    # 正常系
    with patch('weko_inbox_consumer.api.ldnlib.Consumer.notification',
               return_value=test_notification[0]
               ):
        test = get_notification('http://notification1')
        assert test == test_notification[0]


@patch('weko_inbox_consumer.api.get_oai_format', return_value="oai_server")
def test_create_push_data(mock, app, test_push_data, test_signposting_data):
    # 正常系
    result = test_push_data[0]
    test = create_push_data(test_signposting_data)
    assert test == result


def test_get_oai_format1(app):
    # 正常に取得
    oad = app.config['OAISERVER_METADATA_FORMATS']
    namespace = 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/'
    test = get_oai_format(oad, namespace)
    assert test == 'jpcoar_1.0'


def test_get_oai_format2(app):
    # configからoadの取得失敗。もしくは存在しない
    oad = {}
    namespace = 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/'
    test = get_oai_format(oad, namespace)
    assert test is None


def test_get_oai_format3(app):
    # oadに該当namespaceが存在しない
    oad = app.config['OAISERVER_METADATA_FORMATS']
    namespace = 'https://not_exist_server'
    test = get_oai_format(oad, namespace)
    assert test is None
