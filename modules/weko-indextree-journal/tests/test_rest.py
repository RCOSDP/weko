'''
/admin/indexjournal/<int:journal_id>:get,put,post,delete

'''
import os
import json
import pytest
from flask import make_response,current_app,Flask,url_for
from mock import patch

from invenio_accounts.testutils import login_user_via_session
from invenio_records_rest.utils import obj_or_import_string

from weko_indextree_journal.errors import JournalInvalidDataRESTError
from weko_indextree_journal.models import Journal_export_processing,Journal
from weko_indextree_journal.rest import need_record_permission, create_blueprint, JournalActionResource


# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_need_record_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_need_record_permission(client_rest,app, db, users):
    class MockSelf:
        def __init__(self):
            self.read_permission_factory = obj_or_import_string('weko_indextree_journal.permissions:indextree_journal_permission')
            self.create_permission_factory = None

    with app.test_request_context():
        # permission is None
        result = need_record_permission("create_permission_factory")(lambda self:True)(self = MockSelf())
        assert result == True

        # permission is not None
        # permission_factory.can is True
        with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
            app.preprocess_request()
            result = need_record_permission("read_permission_factory")(lambda self:True)(self = MockSelf())
            assert result == True

        # permission_factory.can is False with login
        with patch("flask_login.utils._get_user", return_value=users[6]['obj']):
            app.preprocess_request()
            with patch("weko_indextree_journal.rest.abort",reutrn_value=make_response()) as mock_abort:
                need_record_permission("read_permission_factory")(lambda self:True)(self = MockSelf())
                result = [args[0] for args, kwargs in mock_abort.call_args_list]
                assert 403 in result
                assert 401 not in result

        # permission_factory.can is False without login
        with patch("weko_indextree_journal.rest.abort",reutrn_value=make_response()) as mock_abort:
            app.preprocess_request()
            need_record_permission("read_permission_factory")(lambda self:True)(self = MockSelf())
            result = [args[0] for args, kwargs in mock_abort.call_args_list]
            assert 403 in result
            assert 401 in result

def json_record(*args, **kwargs):
    """Test serializer."""
    return current_app.response_class(
        json.dumps({'json_record': 'json_record'}),
        content_type='application/json')

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
@pytest.mark.skip(reason="Negatively impacting other tests")
def test_create_blueprint(instance_path):
    app = Flask("testapp",
        instance_path=instance_path)
    app.config.update(
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        TESTING=True,
        SERVER_NAME="TEST_SERVER",
    )
    endpoints = dict(
        tid=dict(
            record_serializers={'application/json': 'test_rest.json_record'},
            record_class='weko_indextree_journal.api:Journals',
            admin_indexjournal_route='/admin/indexjournal/<int:journal_id>',
            journal_route='/admin/indexjournal',
            default_media_type='application/json',
            create_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            read_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            update_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            delete_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
        )
    )
    from invenio_db import db
    from invenio_db import InvenioDB
    from sqlalchemy_utils.functions import create_database, database_exists
    InvenioDB(app)
    # test dbsession_clean
    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()
        blueprint = create_blueprint(app,endpoints=endpoints)
        app.register_blueprint(blueprint)

        url = url_for("weko_indextree_journal_rest.tid_journal_action",journal_id=1)
        # sucess commit
        with app.test_request_context(url):
            processing1 = Journal_export_processing(id=1,status=False)
            db.session.add(processing1)
        assert Journal_export_processing.query.filter_by(id=1).first() is not None

        # failed commit
        with patch("weko_indextree_journal.rest.db.session.commit", side_effect=Exception("test_error")):
            with app.test_request_context(url):
                processing2 = Journal_export_processing(id=2,status=False)
                db.session.add(processing2)
            assert Journal_export_processing.query.filter_by(id=2).first() is None

        # exist exception
        with patch("weko_indextree_journal.rest.make_response",side_effect=Exception("test_error")):
            try:
                with app.test_client() as client:
                    processing3 = Journal_export_processing(id=3,status=False)
                    db.session.add(processing3)
                    res = client.get(url)
            except Exception as e:
                assert Journal_export_processing.query.filter_by(id=3).first() is None

        db.session.remove()
        db.drop_all()


class TestJournalActionResource:
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get(self, app,client_rest, db, test_journals,users):

        ctx = {
            "record_class":obj_or_import_string('weko_indextree_journal.api:Journals'),
            "read_permission_factory":obj_or_import_string('weko_indextree_journal.permissions:indextree_journal_permission')
        }
        with app.test_request_context():
            with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
                app.preprocess_request()
                test = '{"access_type":"F","coverage_depth":"abstract","coverage_notes":"","date_first_issue_online":"2022-01-01","date_last_issue_online":"2022-01-01","date_monograph_published_online":"","date_monograph_published_print":"","deleted":"","embargo_info":"","first_author":"","first_editor":"","ichushi_code":"","id":1,"index_id":1,"is_output":true,"jstage_code":"","language":"en","monograph_edition":"","monograph_volume":"","ncid":"","ndl_bibid":"","ndl_callno":"","num_first_issue_online":"","num_first_vol_online":"","num_last_issue_online":"","num_last_vol_online":"","online_identifier":"","owner_user_id":0,"parent_publication_title_id":"","preceding_publication_title_id":"","print_identifier":"","publication_title":"test journal 1","publication_type":"serial","publisher_name":"","title_alternative":"","title_id":1,"title_transcription":"","title_url":"search?search_type=2&q=1","abstract":"","code_issnl":""}'
                view = JournalActionResource(ctx)
                res = view.get(1)
                assert '"title_url":"search?search_type=2&q=1"' in str(res.data,"utf-8")

                res = view.get(0)
                assert str(res.data,"utf-8") == "[]\n"

                with patch("weko_indextree_journal.rest.make_response",side_effect=Exception("test_error")):
                    with pytest.raises(JournalInvalidDataRESTError) as e:
                        res = view.get(0)
    user_results1 = [
        (0, True),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    ]
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_post_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    @pytest.mark.parametrize('id, is_permission', user_results1)
    def test_post_acl(self,client_rest, users, test_indices, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]['email'])
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps({}),
                               content_type='application/json')
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_post_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_post_acl_guest(self,client_rest, test_indices):
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps({}),
                               content_type='application/json')
        assert res.status_code == 401

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_post(self,client_rest, users, test_indices):
        _data = dict(
            id=1,
            index_id=1,
            publication_title="test journal {}".format(1),
            date_first_issue_online="2022-01-01",
            date_last_issue_online="2022-01-01",
            title_url="search?search_type=2&q={}".format(1),
            title_id=str(1),
            coverage_depth="abstract",
            publication_type="serial",
            access_type="F",
            language="en",
            is_output=True,
            abstract='',
            code_issnl=''
        )
        login_user_via_session(client=client_rest, email=users[0]['email'])
        # success create
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps(_data),
                               content_type='application/json')
        assert res.status_code == 201
        assert json.loads(str(res.data,"utf-8")) == {"status": 201,"message":"Journal created successfully."}
        assert Journal.query.filter_by(id=1).one().publication_title == "test journal 1"

        # not data
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps({}),
                               content_type='application/json')
        assert res.status_code == 400

        # failed create
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps(_data),
                               content_type='application/json')
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_put_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    user_results2 = [
        (0, True),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    ]
    @pytest.mark.parametrize('id, is_permission', user_results2)
    def test_put_acl(self, client_rest, users, test_indices, test_journals, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]['email'])
        res = client_rest.put('/admin/indexjournal/1',
                              data=json.dumps({}),
                              content_type='application/json')
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_put_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_put_acl_guest(self, client_rest, users, test_indices, test_journals):
        res = client_rest.put('/admin/indexjournal/1',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == 401

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_put -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_put(self, client_rest, users, test_indices, test_journals):
        _data = dict(
            id=1,
            index_id=1,
            publication_title="updated test journal {}".format(1),
            date_first_issue_online="2022-01-01",
            date_last_issue_online="2022-01-01",
            title_url="search?search_type=2&q={}".format(1),
            title_id=str(1),
            coverage_depth="abstract",
            publication_type="serial",
            access_type="F",
            language="en",
            is_output=True,
            abstract='',
            code_issnl=''
        )
        login_user_via_session(client=client_rest, email=users[0]['email'])
        # success update
        res = client_rest.put('/admin/indexjournal/1',
                              data=json.dumps(_data),
                              content_type='application/json')
        assert res.status_code == 200
        assert json.loads(str(res.data,"utf-8")) == {"status":200,"message":'Journal updated successfully.'}
        assert Journal.query.filter_by(id=1).one().publication_title == "updated test journal 1"

        # no data
        res = client_rest.put('/admin/indexjournal/1',
                              data=json.dumps({}),
                              content_type='application/json')
        assert res.status_code == 400

        # failed update
        res = client_rest.put('/admin/indexjournal/2',
                              data=json.dumps(_data),
                              content_type='application/json')
        assert res.status_code == 400

    @pytest.mark.parametrize('id, is_permission', user_results2)
    def test_delete_acl(self, client_rest, users, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]['email'])
        res = client_rest.delete('/admin/indexjournal/0')
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403

    def test_delete_acl_guest(self,client_rest, users):
        res = client_rest.delete('/admin/indexjournal/0')
        assert res.status_code == 401

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::TestJournalActionResource::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_delete(self,app, client_rest, users, test_indices, test_journals):
        login_user_via_session(client=client_rest, email=users[0]['email'])
        # success delete
        res = client_rest.delete("/admin/indexjournal/1")
        assert Journal.query.filter_by(id=1).one_or_none() is None
        assert json.loads(str(res.data,"utf-8")) == {"status": 200, "message": "Journal deleted successfully."}
        assert res.status_code == 200

        # not journal_id
        res = client_rest.delete("/admin/indexjournal/0")
        assert res.status_code == 204

        # failed delete
        res = client_rest.delete("/admin/indexjournal/100")
        assert res.status_code == 204


