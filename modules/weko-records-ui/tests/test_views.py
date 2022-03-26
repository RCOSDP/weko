import pytest
from weko_records_ui.views import json_string_escape,xml_string_escape
# def record_from_pid(pid_value):
# def url_to_link(field):
# def pid_value_version(pid_value):
# def publish(pid, record, template=None, **kwargs):
# def export(pid, record, template=None, **kwargs):
# def get_image_src(mimetype):
# def get_license_icon(license_type):
#     # In case of current lang is not JA, set to default.
#     current_lang = 'default' if current_i18n.language != 'ja' \
# def check_permission(record):
# def check_file_permission(record, fjson):
# def check_file_permission_period(record, fjson):
# def get_file_permission(record, fjson):
# def check_content_file_clickable(record, fjson):
# def get_usage_workflow(file_json):
# def get_workflow_detail(workflow_id):
# def default_view_method(pid, record, filename=None, template=None, **kwargs):
#     """Display default view.
#     def _get_rights_title(result, rights_key, rights_values, current_lang, meta_options):
# def doi_ish_view_method(parent_pid_value=0, version=0):
# def parent_view_method(pid_value=0):
# def set_pdfcoverpage_header():
#     def handle_over_max_file_size(error):
# def file_version_update():
# def citation(record, pid, style=None, ln=None):
# def soft_delete(recid):
# def restore(recid):
# def init_permission(recid):
# def escape_str(s):
# def escape_newline(s):
# def json_string_escape(s):

def test_json_string_escape():
    assert json_string_escape('\x5c')=='\\\\'
    assert json_string_escape('\x08')=='\\b'
    assert json_string_escape('\x0a')=='\\n'
    assert json_string_escape('\x0d')=='\\r'
    assert json_string_escape('\x09')=='\\t'
    assert json_string_escape('\x0c')=='\\f'

# def xml_string_escape(s):
def test_xml_string_escape():
    assert xml_string_escape('&<>')=='&amp;&lt;&gt;'

# def preview_able(file_json):