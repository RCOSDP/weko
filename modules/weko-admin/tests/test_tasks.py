from mock import patch, MagicMock, Mock
from requests.models import Response
from invenio_oaiserver.models import OAISet
from weko_admin.models import AdminSettings

from weko_admin.tasks import (is_reindex_running,reindex)

INSPECT_RETURN_VALUE={'celery@d852e7dcb4da': [{'id': '0789eb75-2d50-45ba-b132-e85a70e71524', 'name': 'weko_admin.tasks.reindex', 'args': [False], 'kwargs': {}, 'type': 'weko_admin.tasks.reindex', 'hostname': 'celery@d852e7dcb4da', 'time_start': 1671494657.8838153, 'acknowledged': True, 'delivery_info': {'exchange': '', 'routing_key': 'celery', 'priority': 0, 'redelivered': False}, 'worker_pid': 264}]}

def test_is_reindex_running_not_running(i18n_app ,mocker):
    with patch("weko_search_ui.tasks.inspect.ping",return_value=False):
        with patch("weko_admin.tasks.inspect.active",return_value=INSPECT_RETURN_VALUE):
            with patch("weko_admin.tasks.inspect.reserved",return_value=[]):
                assert is_reindex_running()==False
def test_is_reindex_running_active(i18n_app):
    with patch("weko_search_ui.tasks.inspect.ping",return_value=True):
        with patch("weko_admin.tasks.inspect.active",return_value=INSPECT_RETURN_VALUE):
            with patch("weko_admin.tasks.inspect.reserved",return_value=[]):
                assert is_reindex_running()==True
def test_is_reindex_running_reserved(i18n_app):
    with patch("weko_search_ui.tasks.inspect.ping",return_value=True):
        with patch("weko_admin.tasks.inspect.active",return_value=[]):
            with patch("weko_admin.tasks.inspect.reserved",return_value=INSPECT_RETURN_VALUE):
                assert is_reindex_running()==True
def test_is_reindex_running_waiting(i18n_app):
    with patch("weko_search_ui.tasks.inspect.ping",return_value=True):
        with patch("weko_admin.tasks.inspect.active",return_value=MagicMock()):
            with patch("weko_admin.tasks.inspect.reserved",return_value=MagicMock()):
                assert is_reindex_running()==False

def test_reindex_EStoES(i18n_app,mocker,admin_settings):
    
    return_value = Mock(spec=Response)
    return_value.text = "test_mock"
    return_value.status_code = 200

    with mocker.patch("weko_admin.utils.requests.put" , return_value=return_value):
        with mocker.patch("weko_admin.utils.requests.post" , return_value=return_value):
            with mocker.patch("weko_admin.utils.requests.delete" , return_value=return_value):
                with mocker.patch("weko_admin.utils.requests.get" , return_value=return_value):
                    assert 'completed' == reindex(False)


def test_reindex_DBtoES(i18n_app,mocker,admin_settings,reindex_settings):
    
    return_value = Mock(spec=Response)
    return_value.text = "test_mock"
    return_value.status_code = 200

    with mocker.patch("weko_admin.utils.requests.put" , return_value=return_value):
        with mocker.patch("weko_admin.utils.requests.post" , return_value=return_value):
            with mocker.patch("weko_admin.utils.requests.delete" , return_value=return_value):
                with mocker.patch("weko_admin.utils.requests.get" , return_value=return_value):
                    with mocker.patch("invenio_oaiserver.receivers.update_affected_records" , return_value=""):

                        retVal1= OAISet(spec="1669370353014",name="index name" ,search_pattern="path[1669370353014]")
                        retVal2= OAISet(spec="1669959650594",name="index name" ,search_pattern="path[1669959650594]")
                        reindex_settings.session.add(retVal1)
                        reindex_settings.session.add(retVal2)
                        reindex_settings.session.commit()

                        assert 'completed' == reindex(True)

def test_reindex_raise(i18n_app,mocker,admin_settings):
    with mocker.patch("weko_admin.tasks.elasticsearch_reindex" , side_effect=BaseException("test_error")):
        try :
            reindex(True)

            assert False , "expected Exception raised but"
        except BaseException as ex:
            assert "test_error" in ex.args
            admin_setting = AdminSettings.get('elastic_reindex_settings',False)
            assert True == admin_setting.get('has_errored')



