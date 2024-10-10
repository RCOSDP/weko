import pytest
from unittest.mock import patch, MagicMock

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
