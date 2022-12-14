
from flask import current_app
from datetime import datetime
from celery.worker.request import Request
from weko_sitemap.tasks import link_success_handler,link_error_handler,update_sitemap


# def link_success_handler(retval):
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_tasks.py::test_link_success_handler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_link_success_handler(app,mocker):
    with app.test_request_context():
        mock_send = mocker.patch("weko_sitemap.tasks.sitemap_finished.send")
        data = [
            {"task_id":"test_task_id","total":1},
            "user_data"
        ]
        link_success_handler(data)
        mock_send.assert_called_with(
            current_app._get_current_object(),
            exec_data={"task_id":"test_task_id","total_records":1},
            user_data="user_data"
        )
    
# def link_error_handler(request, exc, traceback):
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_tasks.py::test_link_error_handler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_link_error_handler(app,mocker):
    mocker.patch("datetime.datetime",**{"now.return_value":datetime(2022,10,2,1,2,3)})
    #datetime_mock = mocker.patch("weko_sitemap.tasks.datetime")
    #datetime_mock.now.side_effect=[datetime(2022,10,2,1,2,3)]
    headers = {
        "id":"test_id",
        "task":"test_task",
        "argsrepr":'["2022-10-01T12:01:22","user_data"]'
    }
    class Message:
        body=("test_args","test_kwargs","")
        decoded=True
        payload="test_payload"
        delivery_info=None
        properties=None
    req = Request(Message,headers=headers,task="test_task",decoded=True)
    mock_send=mocker.patch("weko_sitemap.tasks.sitemap_finished.send")
    link_error_handler(req,"","")
    now=datetime.now()
    exe = str(now -datetime(2022,10,1,12,1,22))
    args, kwargs = mock_send.call_args
    assert kwargs["exec_data"]["task_state"] == "FAILURE"
    assert kwargs["exec_data"]["start_time"] == "2022-10-01T12:01:22"
    assert kwargs["exec_data"]["end_time"] == now.strftime('%Y-%m-%dT%H:%M:%S%z')
    assert kwargs["exec_data"]["total_records"] == 0
    assert kwargs["exec_data"]["task_name"] == "sitemap"
    assert kwargs["exec_data"]["repository_name"] == "weko"
    assert kwargs["exec_data"]["task_id"] == "test_id"
    assert kwargs["user_data"] == "user_data"


# def update_sitemap(start_time=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_tasks.py::test_update_sitemap -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_update_sitemap(app,db,mocker):
    def mock_gen_urls():
        for i in range(10):
            yield "http://test{}.com".format(i)
    mocker.patch("weko_sitemap.ext.WekoSitemap._generate_all_item_urls",side_effect=mock_gen_urls)

    current_app.config.update(
        SITEMAP_MAX_URL_COUNT=11
    )
    start = datetime(2022,10,1,1,2,3).strftime('%Y-%m-%dT%H:%M:%S')
    with app.test_request_context():
        mock_send = mocker.patch("weko_sitemap.tasks.sitemap_page_needed.send")
        result,user_data = update_sitemap(start_time=start)
        mock_send.assert_called_with(
            current_app._get_current_object(),
            page=1,
            urlset=["http://test0.com","http://test1.com","http://test2.com","http://test3.com","http://test4.com","http://test5.com","http://test6.com","http://test7.com","http://test8.com","http://test9.com"]
        )
        assert result["start_time"] == "2022-10-01T01:02:03"
        assert result["task_name"] == "sitemap"
        assert user_data == {"user_id":"System"}

        
        current_app.config.update(
            SITEMAP_MAX_URL_COUNT=10
        )
        mock_send = mocker.patch("weko_sitemap.tasks.sitemap_page_needed.send")
        result,user_data = update_sitemap(start_time=start)
        mock_send.assert_called_with(
            current_app._get_current_object(),
            page=1,
            urlset=["http://test0.com","http://test1.com","http://test2.com","http://test3.com","http://test4.com","http://test5.com","http://test6.com","http://test7.com","http://test8.com","http://test9.com"]
        )
        assert result["total"] == 10
        assert result["start_time"] == "2022-10-01T01:02:03"
        assert user_data == {"user_id":"System"}
