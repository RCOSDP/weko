
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
    template = 'invenio_records_ui/detail.html'
    with app.test_request_context('/record/1/file_preview/hello.txt?allow_aggs=True'):
        assert preview(record.pid,record,template)


# def children_to_list(node):
# def zip_preview(file):
# def decode_name(k):
