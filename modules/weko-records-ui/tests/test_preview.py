import pytest
from mock import patch, MagicMock

from weko_records_ui.preview import preview, decode_name, zip_preview, children_to_list

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_preview.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
# def preview(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_preview.py::test_preview -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_preview(app,records):
    @app.route('/record/<pid_value>/file_preview/<path:filename>')
    def view1(parameter0):
        return ''

    indexer, results = records
    record = results[0]['record']
    filename = results[0]['filename']
    recid = results[0]['recid']
    template = 'invenio_records_ui/detail.html'

    with app.test_request_context('/record/{}/file_preview/{}?allow_aggs=True'.format(recid.pid_value,filename)):
        assert "<title>Preview</title>" in preview(record.pid,record,template)
    
    with app.test_request_context('/record/{}/file_preview/{}?allow_aggs=False'.format(recid.pid_value,filename)):
        assert "<title>Preview</title>" in preview(record.pid,record,template)
    
    with app.test_request_context('/record/{}/file_preview/{}'.format(recid.pid_value,filename)):
        assert "<title>Preview</title>" in preview(record.pid,record,template)
    
    with app.test_request_context('/record/{}/file_preview/'.format(recid.pid_value)):
        with pytest.raises(AttributeError):
            assert preview(record.pid,record,template)==""

    with app.test_request_context():
        assert "<title>Preview</title>" in preview(record.pid,record,template)
    
    indexer, results = records
    record = results[1]['record']
    filename = results[1]['filename']
    recid = results[1]['recid']
    template = 'invenio_records_ui/detail.html'

    with app.test_request_context('/record/{}/file_preview/{}?allow_aggs=True'.format(recid.pid_value,filename)):
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    with app.test_request_context('/record/{}/file_preview/{}?allow_aggs=False'.format(recid.pid_value,filename)):
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    with app.test_request_context('/record/{}/file_preview/{}'.format(recid.pid_value,filename)):
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    with app.test_request_context('/record/{}/file_preview/'.format(recid.pid_value)):
        with pytest.raises(AttributeError):
            assert preview(record.pid,record,template)==""

    with app.test_request_context():
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    indexer, results = records
    record = results[2]['record']
    filename = results[2]['filename']
    recid = results[2]['recid']
    template = 'invenio_records_ui/detail.html'

    with app.test_request_context('/record/{}/file_preview/{}?allow_aggs=True'.format(recid.pid_value,filename)):
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    with app.test_request_context('/record/{}/file_preview/{}?allow_aggs=False'.format(recid.pid_value,filename)):
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    with app.test_request_context('/record/{}/file_preview/{}'.format(recid.pid_value,filename)):
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    
    with app.test_request_context('/record/{}/file_preview/'.format(recid.pid_value)):
        with pytest.raises(AttributeError):
            assert preview(record.pid,record,template)==""

    with app.test_request_context():
        with patch("flask.templating._render", return_value=""):
            assert preview(record.pid,record,template)==""
    

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_preview.py::test_preview_file_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_preview_file_permission(app, db, records, users):
    @app.route('/record/<pid_value>/preview_permission_test/<path:filename>')
    def view_preview_permission_test(pid_value, filename):
        return ''

    from werkzeug.exceptions import Forbidden

    indexer, results = records
    # record 5 has a single file whose accessrole is open_no
    record = results[4]['record']
    recid = results[4]['recid']
    filename = 'helloworld.pdf'
    # アイテム登録時と同じく、ファイルのメタデータ(accessrole など)を
    # ファイル実体の JSON に書き込んでおく。権限判定はこの値を見る
    file_md = [f for f in record.get_file_data() if f.get('filename') == filename][0]
    for f in record.files:
        if f.obj.key == filename:
            f.obj.file.update_json(file_md)
    db.session.commit()
    template = 'invenio_records_ui/detail.html'
    url = '/record/{}/preview_permission_test/{}'.format(recid.pid_value, filename)

    # guest user: redirected to login
    with app.test_request_context(url):
        with patch('weko_accounts.views._redirect_method', return_value='redirect') as mock_redirect:
            assert preview(record.pid, record, template) == 'redirect'
            mock_redirect.assert_called_once_with(has_next=True)

    # logged in user without file permission
    with app.test_request_context(url):
        with patch('flask_login.utils._get_user', return_value=users[4]['obj']):
            with pytest.raises(Forbidden):
                preview(record.pid, record, template)

    # owner and sysadmin can preview
    for user in (users[7], users[2]):
        with app.test_request_context(url):
            with patch('flask_login.utils._get_user', return_value=user['obj']):
                assert "<title>Preview</title>" in preview(record.pid, record, template)

    # file permission is checked with the requested file
    with app.test_request_context(url):
        checker = MagicMock()
        checker.can.return_value = False
        with patch('flask_login.utils._get_user', return_value=users[2]['obj']):
            with patch('weko_records_ui.permissions.file_permission_factory', return_value=checker) as mock_factory:
                with pytest.raises(Forbidden):
                    preview(record.pid, record, template)
                args, kwargs = mock_factory.call_args
                assert args[0] == record
                assert kwargs['fjson'].get('filename') == filename


# def children_to_list(node):
def test_children_to_list(app):
    obj1 = MagicMock()
    obj2 = {
        'type': 'item',
        'children': []
    }

    assert children_to_list(obj1) == obj1

    assert children_to_list(obj2) == obj2


# def zip_preview(file):
def test_zip_preview(app):
    obj1 = MagicMock()
    obj2 = MagicMock()
    obj3 = MagicMock()

    with patch("weko_records_ui.preview.make_tree", return_value=(obj1, obj2, obj3)):
        with patch("weko_records_ui.preview.children_to_list", return_value={"children": [1,2,3]}):
            # Error
            try:
                zip_preview(obj1)
            except:
                pass

# def decode_name(k):
def test_decode_name(app):
    obj1 = MagicMock()
    obj2 = {"encoding": "test"}

    assert decode_name(obj1) == obj1

    def detect(a):
        return obj2

    obj1.detect = detect
    with patch("weko_records_ui.preview.chardet", return_value=obj1):
        assert decode_name(obj1) != obj1
    
    with patch("weko_records_ui.preview.chardet.detect", return_value={"encoding": False}):
        assert decode_name(obj1) == obj1

    obj2['encoding'] = 'WINDOWS-1252'
    with patch("weko_records_ui.preview.chardet.detect", return_value=obj2):
        assert decode_name(obj1) != obj1