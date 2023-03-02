import csv
from io import StringIO
from os.path import dirname, join
import json
import pytest

from weko_admin.utils import (
    make_stats_file, write_report_file_rows
)


# .tox/c1/bin/pytest -vv -s --basetemp=/code/modules/weko-admin/.tox/c1/tmp --full-trace tests/test_utils.py --cov=weko_admin --cov-branch --cov-report=term

# .tox/c1/bin/pytest -vv -s --basetemp=/code/modules/weko-admin/.tox/c1/tmp --full-trace tests/test_utils.py::test_write_report_file_rows --cov=weko_admin --cov-branch --cov-report=term
# def write_report_file_rows(writer, records, file_type=None, other_info=None):
@pytest.mark.parametrize(
    'raw_stats_file,file_type,expected_file',
    [
        ('data/raw_stats_data/billing_file_download.json', 'billing_file_download', 'data/expected_data/billing_file_download_stats_only.tsv')
    ],
)
def test_write_report_file_rows(app, roles, raw_stats_file, file_type, expected_file):
    with open(join(dirname(__file__), raw_stats_file), 'r') as json_file:
        records = json.load(json_file)

    dummy_file = StringIO()
    writer = csv.writer(dummy_file, delimiter='\t', lineterminator="\n")

    write_report_file_rows(writer, records['all'], file_type=file_type)

    with open(join(dirname(__file__), expected_file), 'r') as tsv_file:
        assert dummy_file.getvalue() == tsv_file.read()

# .tox/c1/bin/pytest -vv -s --basetemp=/code/modules/weko-admin/.tox/c1/tmp --full-trace tests/test_utils.py::test_make_stats_file --cov=weko_admin --cov-branch --cov-report=term
# def make_stats_file(raw_stats, file_type, year, month):
#   def write_report_file_rows(writer, records, file_type=None, other_info=None):
@pytest.mark.parametrize(
    'raw_stats_file,file_type,expected_file_en,expected_file_ja',
    [
        ('data/raw_stats_data/billing_file_download.json', 'billing_file_download',
         'data/expected_data/billing_file_download_en.tsv', 'data/expected_data/billing_file_download_ja.tsv'),
    ],
)
def test_make_stats_file(i18n_app, roles, raw_stats_file, file_type, expected_file_en, expected_file_ja):
    with open(join(dirname(__file__), raw_stats_file), 'r') as json_file:
        raw_stats = json.load(json_file)

    # assert file content (en)
    i18n_app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    with i18n_app.test_request_context():
        file_content = make_stats_file(raw_stats, file_type, '2023', '01')
        with open(join(dirname(__file__), expected_file_en), 'r') as tsv_file:
            assert file_content.getvalue() == tsv_file.read()

    # assert file content (ja)
    i18n_app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
    with i18n_app.test_request_context():
        file_content = make_stats_file(raw_stats, file_type, '2023', '01')
        with open(join(dirname(__file__), expected_file_ja), 'r') as tsv_file:
            assert file_content.getvalue() == tsv_file.read()