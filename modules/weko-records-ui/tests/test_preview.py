
import pytest
from mock import patch

from weko_records_ui.preview import preview

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
# def zip_preview(file):
# def decode_name(k):
