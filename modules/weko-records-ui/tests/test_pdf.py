import pytest
from six import BytesIO
from weko_records_ui.pdf import get_east_asian_width_count,make_combined_pdf
from invenio_files_rest.models import Bucket, Location, ObjectVersion

# def get_east_asian_width_count(text):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_pdf.py::test_get_east_asian_width_count -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_east_asian_width_count():
    assert get_east_asian_width_count("日本語")==6
    assert get_east_asian_width_count("english")==7
    

# def make_combined_pdf(pid, fileobj, obj, lang_user):
#     def pixels_to_mm(val):
#     def resize_to_fit(imgFilename):
#     def get_center_position(imgFilename):
#     def get_right_position(imgFilename):
#     def get_pid_object(pid_value):
#     def get_current_activity_id(pid_object):
#     def get_url(pid_value):
#     def get_oa_policy(activity_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_pdf.py::test_make_combined_pdf -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_make_combined_pdf(app,records,itemtypes,pdfcoverpagesetting):
    indexer, results = records
    record = results[0]["record"]
    obj = results[0]['obj']
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        res = make_combined_pdf(record.pid,record['item_1617605131499'],obj,None)
        assert res.status_code==200
