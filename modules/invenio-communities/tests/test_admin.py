# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

from flask import url_for, current_app, make_response
from flask_admin import Admin
import pytest
import werkzeug
import base64
from io import BytesIO
from mock import patch
from invenio_accounts.testutils import login_user_via_session, create_test_user
from invenio_access.models import ActionUsers
from invenio_communities.models import Community
from weko_records.models import ItemTypeProperty
from weko_index_tree.models import IndexStyle,Index
from invenio_accounts.testutils import login_user_via_session
from invenio_communities.admin import community_adminview,request_adminview,featured_adminview, CommunityModelView
from wtforms.validators import ValidationError
from unittest.mock import MagicMock, patch

SMALLEST_JPEG_B64 = """\
/9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8Q
EBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k=
"""

@pytest.fixture()
def setup_view_community(app,db,users):
    sysadmin = users[2]["obj"]
    test_index = Index(
            index_name="testIndexOne",
            browsing_role="Contributor",
            public_state=True,
            id=11,
        )
    db.session.add(test_index)
    db.session.commit()
    comm = Community(
        id="test_comm",
        id_role=1,root_node_id=11,
        page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False, cnri="http://hdl.handle.net/1234567890/1",
        title="Test comm",
        description="this is test comm",
        id_user=1,
        group_id=1
    )
    db.session.add(comm)
    comm2 = Community(
        id="test_comm2",
        id_role=1,root_node_id=11,
        page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=None, login_menu_enabled=False, cnri=None,
        title="Test comm2",
        description="this is test comm2",
        id_user=1
    )
    db.session.add(comm2)
    db.session.commit()

    item_property = ItemTypeProperty(
		id = 1057,
		name = "カタログ",
		schema = {"type": "object", "title": "catalog", "format": "object", "properties": {"catalog_file": {"type": "object", "title": "File", "format": "object", "properties": {"catalog_file_uri": {"type": "string", "title": "File URI", "format": "text", "title_i18n": {"en": "File URI", "ja": "ファイルURI"}}, "catalog_file_object_type": {"enum": ["thumbnail"], "type": "string", "title": "Object Type", "format": "select", "title_i18n": {"en": "Object Type", "ja": "オブジェクトタイプ"}, "currentEnum": ["thumbnail"]}}}, "catalog_rights": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"catalog_rights_right": {"type": "string", "title": "Rights", "format": "text", "title_i18n": {"en": "Rights", "ja": "権利情報"}}, "catalog_right_language": {"enum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"], "type": "string", "title": "Language", "format": "select", "title_i18n": {"en": "Language", "ja": "言語"}, "currentEnum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"]}, "catalog_right_rdf_resource": {"type": "string", "title": "RDF Resource", "format": "text", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}}}, "title": "Rights", "format": "array"}, "catalog_titles": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"catalog_title": {"type": "string", "title": "Title", "format": "text", "title_i18n": {"en": "Title", "ja": "タイトル"}}, "catalog_title_language": {"enum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"], "type": "string", "title": "Language", "format": "select", "title_i18n": {"en": "Language", "ja": "言語"}, "currentEnum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"]}}}, "title": "Title", "format": "array"}, "catalog_licenses": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"catalog_license": {"type": "string", "title": "License", "format": "text", "title_i18n": {"en": "License", "ja": "ライセンス"}}, "catalog_license_type": {"enum": ["file", "metadata", "thumbnail"], "type": "string", "title": "License Type", "format": "select", "title_i18n": {"en": "License Type", "ja": "ライセンスタイプ"}, "currentEnum": ["file", "metadata", "thumbnail"]}, "catalog_license_language": {"enum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"], "type": "string", "title": "Language", "format": "select", "title_i18n": {"en": "Language", "ja": "言語"}, "currentEnum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"]}, "catalog_license_rdf_resource": {"type": "string", "title": "RDF Resource", "format": "text", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}}}, "title": "License", "format": "array"}, "catalog_subjects": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"catalog_subject": {"type": "string", "title": "Subject", "format": "text", "title_i18n": {"en": "Subject", "ja": "主題"}}, "catalog_subject_uri": {"type": "string", "title": "Subject URI", "format": "text", "title_i18n": {"en": "Subject URI", "ja": "主題URI"}}, "catalog_subject_scheme": {"enum": ["BSH", "DDC", "e-Rad", "LCC", "LCSH", "MeSH", "NDC", "NDLC", "NDLSH", "SciVal", "UDC", "Other"], "type": "string", "title": "Subject Scheme", "format": "select", "title_i18n": {"en": "Subject Scheme", "ja": "主題スキーマ"}, "currentEnum": ["BSH", "DDC", "e-Rad", "LCC", "LCSH", "MeSH", "NDC", "NDLC", "NDLSH", "SciVal", "UDC", "Other"]}, "catalog_subject_language": {"enum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"], "type": "string", "title": "Language", "format": "select", "title_i18n": {"en": "Language", "ja": "言語"}, "currentEnum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"]}}}, "title": "Subject", "format": "array"}, "catalog_identifiers": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"catalog_identifier": {"type": "string", "title": "Identifier", "format": "text", "title_i18n": {"en": "Identifier", "ja": "識別子"}}, "catalog_identifier_type": {"enum": ["DOI", "HDL", "URI"], "type": ["null", "string"], "title": "Identifier Type", "format": "select", "title_i18n": {"en": "Identifier Type", "ja": "識別子タイプ"}, "currentEnum": ["DOI", "HDL", "URI"]}}}, "title": "Identifier", "format": "array"}, "catalog_contributors": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"contributor_type": {"enum": ["HostingInstitution"], "type": "string", "title": "Contributor Type", "format": "select", "title_i18n": {"en": "Contributor Type", "ja": "提供機関タイプ"}, "currentEnum": ["HostingInstitution"]}, "contributor_names": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"contributor_name": {"type": "string", "title": "Contributor Name", "format": "text", "title_i18n": {"en": "Contributor Name", "ja": "提供機関名"}}, "contributor_name_language": {"enum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"], "type": ["null", "string"], "title": "Language", "format": "select", "title_i18n": {"en": "Language", "ja": "言語"}, "currentEnum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"]}}}, "title": "Contributor Name", "format": "array"}}}, "title": "Contributor", "format": "array"}, "catalog_descriptions": {"type": "object", "title": "Description", "format": "object", "properties": {"catalog_description": {"type": "string", "title": "Description", "format": "text", "title_i18n": {"en": "Description", "ja": "内容記述"}}, "catalog_description_type": {"enum": ["Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"], "type": "string", "title": "Description Type", "format": "select", "title_i18n": {"en": "Description Type", "ja": "内容記述タイプ"}, "currentEnum": ["Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"]}, "catalog_description_language": {"enum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"], "type": "string", "title": "Language", "format": "select", "title_i18n": {"en": "Language", "ja": "言語"}, "currentEnum": ["null", "ja", "ja-Kana", "ja-Latn", "en", "fr", "it", "de", "es", "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar", "el", "ko"]}}}, "catalog_access_rights": {"type": "array", "items": {"type": "object", "format": "object", "properties": {"catalog_access_right": {"enum": ["embargoed access", "metadata only access", "restricted access", "open access"], "type": "string", "title": "Access Rights", "format": "select", "title_i18n": {"en": "Access Rights", "ja": "アクセス権"}, "currentEnum": ["embargoed access", "metadata only access", "restricted access", "open access"]}, "catalog_access_right_rdf_resource": {"type": "string", "title": "RDF Resource", "format": "text", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}}}, "title": "Access Rights", "format": "array"}}},
		form = {"key": "parentkey", "type": "fieldset", "items": [{"add": "New", "key": "parentkey.catalog_contributors", "items": [{"key": "parentkey.catalog_contributors[].contributor_type", "type": "select", "title": "Contributor Type", "titleMap": [{"name": "HostingInstitution", "value": "HostingInstitution"}], "title_i18n": {"en": "Contributor Type", "ja": "提供機関タイプ"}}, {"add": "New", "key": "parentkey.catalog_contributors[].contributor_names", "items": [{"key": "parentkey.catalog_contributors[].contributor_names[].contributor_name", "type": "text", "title": "Contributor Name", "title_i18n": {"en": "Contributor Name", "ja": "提供機関名"}}, {"key": "parentkey.catalog_contributors[].contributor_names[].contributor_name_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}], "style": {"add": "btn-success"}, "title": "Contributor Name"}], "style": {"add": "btn-success"}, "title": "Contributor"}, {"add": "New", "key": "parentkey.catalog_identifiers", "items": [{"key": "parentkey.catalog_identifiers[].catalog_identifier", "type": "text", "title": "Identifier", "title_i18n": {"en": "Identifier", "ja": "識別子"}}, {"key": "parentkey.catalog_identifiers[].catalog_identifier_type", "type": "select", "title": "Identifier Type", "titleMap": [{"name": "DOI", "value": "DOI"}, {"name": "HDL", "value": "HDL"}, {"name": "URI", "value": "URI"}], "title_i18n": {"en": "Identifier Type", "ja": "識別子タイプ"}}], "style": {"add": "btn-success"}, "title": "Identifier"}, {"add": "New", "key": "parentkey.catalog_titles", "items": [{"key": "parentkey.catalog_titles[].catalog_title", "type": "text", "title": "Title", "title_i18n": {"en": "Title", "ja": "タイトル"}}, {"key": "parentkey.catalog_titles[].catalog_title_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}], "style": {"add": "btn-success"}, "title": "Title"}, {"add": "New", "key": "parentkey.catalog_descriptions", "items": [{"key": "parentkey.catalog_descriptions[].catalog_description", "type": "text", "title": "Description", "title_i18n": {"en": "Description", "ja": "内容記述"}}, {"key": "parentkey.catalog_descriptions[].catalog_description_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey.catalog_descriptions[].catalog_description_type", "type": "select", "title": "Description Type", "titleMap": [{"name": "Abstract", "value": "Abstract"}, {"name": "Methods", "value": "Methods"}, {"name": "TableOfContents", "value": "TableOfContents"}, {"name": "TechnicalInfo", "value": "TechnicalInfo"}, {"name": "Other", "value": "Other"}], "title_i18n": {"en": "Description Type", "ja": "内容記述タイプ"}}], "style": {"add": "btn-success"}, "title": "Description"}, {"add": "New", "key": "parentkey.catalog_subjects", "items": [{"key": "parentkey.catalog_subjects[].catalog_subject", "type": "text", "title": "Subject", "title_i18n": {"en": "Subject", "ja": "主題"}}, {"key": "parentkey.catalog_subjects[].catalog_subject_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey.catalog_subjects[].catalog_subject_uri", "type": "text", "title": "Subject URI", "title_i18n": {"en": "Subject URI", "ja": "主題URI"}}, {"key": "parentkey.catalog_subjects[].catalog_subject_scheme", "type": "select", "title": "Subject Scheme", "titleMap": [{"name": "BSH", "value": "BSH"}, {"name": "DDC", "value": "DDC"}, {"name": "e-Rad", "value": "e-Rad"}, {"name": "LCC", "value": "LCC"}, {"name": "LCSH", "value": "LCSH"}, {"name": "", "value": ""}, {"name": "MeSH", "value": "MeSH"}, {"name": "NDC", "value": "NDC"}, {"name": "NDLC", "value": "NDLC"}, {"name": "NDLSH", "value": "NDLSH"}, {"name": "SciVal", "value": "SciVal"}, {"name": "UDC", "value": "UDC"}, {"name": "Other", "value": "Other"}], "title_i18n": {"en": "Subject Scheme", "ja": "主題スキーマ"}}], "style": {"add": "btn-success"}, "title": "Subject"}, {"add": "New", "key": "parentkey.catalog_licenses", "items": [{"key": "parentkey.catalog_licenses[].catalog_license", "type": "text", "title": "License", "title_i18n": {"en": "License", "ja": "ライセンス"}}, {"key": "parentkey.catalog_license.catalog_license_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey.catalog_license.catalog_license_type", "type": "select", "title": "License Type", "titleMap": [{"name": "file", "value": "file"}, {"name": "metadata", "value": "metadata"}, {"name": "thumbnail", "value": "thumbnail"}], "title_i18n": {"en": "License Type", "ja": "ライセンスタイプ"}}, {"key": "parentkey.catalog_license.catalog_license_rdf_resource", "type": "text", "title": "RDF Resource", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}], "style": {"add": "btn-success"}, "title": "License"}, {"add": "New", "key": "parentkey.catalog_rights", "items": [{"key": "parentkey.catalog_rights[].catalog_right", "type": "text", "title": "Rights", "title_i18n": {"en": "Access Rights", "ja": "アクセス権"}}, {"key": "parentkey.catalog_rights[].catalog_right_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey.catalog_rights[].catalog_right_rdf_resource", "type": "text", "title": "RDF Resource", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}], "style": {"add": "btn-success"}, "title": "Rights"}, {"add": "New", "key": "parentkey.catalog_access_rights", "items": [{"key": "parentkey.catalog_access_rights[].catalog_access_right_access_rights", "type": "select", "title": "Access Rights", "titleMap": [{"name": "embargoed access", "value": "embargoed access"}, {"name": "metadata only access", "value": "metadata only access"}, {"name": "restricted access", "value": "restricted access"}, {"name": "open access", "value": "open access"}], "title_i18n": {"en": "Access Rights", "ja": "アクセス権"}}, {"key": "parentkey.catalog_access_rights[].catalog_access_right_rdf_resource", "type": "text", "title": "RDF Resource", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}], "style": {"add": "btn-success"}, "title": "Access Rights"}, {"key": "parentkey.catalog_file", "type": "fieldset", "items": [{"key": "parentkey.catalog_file.catalog_file_uri", "type": "text", "title": "File URI", "title_i18n": {"en": "File URI", "ja": "ファイルURI"}}, {"key": "parentkey.catalog_file.catalog_file_object_type", "type": "select", "title": "Object Type", "titleMap": [{"name": "thumbnail", "value": "thumbnail"}], "title_i18n": {"en": "Object Type", "ja": "オブジェクトタイプ"}}], "title": "File"}], "title_i18n": {"en": "Catalog", "ja": "カタログ"}},
		forms = {"add": "New", "key": "parentkey", "items": [{"add": "New", "key": "parentkey[].catalog_contributors", "items": [{"key": "parentkey[].catalog_contributors[].contributor_type", "type": "select", "title": "Contributor Type", "titleMap": [{"name": "HostingInstitution", "value": "HostingInstitution"}], "title_i18n": {"en": "Contributor Type", "ja": "提供機関タイプ"}}, {"add": "New", "key": "parentkey[].catalog_contributors[].contributor_names", "items": [{"key": "parentkey[].catalog_contributors[].contributor_names[].contributor_name", "type": "text", "title": "Contributor Name", "title_i18n": {"en": "Contributor Name", "ja": "提供機関名"}}, {"key": "parentkey[].catalog_contributors[].contributor_names[].contributor_name_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}], "style": {"add": "btn-success"}, "title": "Contributor Name"}], "style": {"add": "btn-success"}, "title": "Contributor"}, {"add": "New", "key": "parentkey[].catalog_identifiers", "items": [{"key": "parentkey[].catalog_identifiers[].catalog_identifier", "type": "text", "title": "Identifier", "title_i18n": {"en": "Identifier", "ja": "識別子"}}, {"key": "parentkey[].catalog_identifiers[].catalog_identifier_type", "type": "select", "title": "Identifier Type", "titleMap": [{"name": "DOI", "value": "DOI"}, {"name": "HDL", "value": "HDL"}, {"name": "URI", "value": "URI"}], "title_i18n": {"en": "Identifier Type", "ja": "識別子タイプ"}}], "style": {"add": "btn-success"}, "title": "Identifier"}, {"add": "New", "key": "parentkey[].catalog_titles", "items": [{"key": "parentkey[].catalog_titles[].catalog_title", "type": "text", "title": "Title", "title_i18n": {"en": "Title", "ja": "タイトル"}}, {"key": "parentkey[].catalog_titles[].catalog_title_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}], "style": {"add": "btn-success"}, "title": "Title"}, {"add": "New", "key": "parentkey[].catalog_descriptions", "items": [{"key": "parentkey[].catalog_descriptions[].catalog_description", "type": "text", "title": "Description", "title_i18n": {"en": "Description", "ja": "内容記述"}}, {"key": "parentkey[].catalog_descriptions[].catalog_description_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey[].catalog_descriptions[].catalog_description_type", "type": "select", "title": "Description Type", "titleMap": [{"name": "Abstract", "value": "Abstract"}, {"name": "Methods", "value": "Methods"}, {"name": "TableOfContents", "value": "TableOfContents"}, {"name": "TechnicalInfo", "value": "TechnicalInfo"}, {"name": "Other", "value": "Other"}], "title_i18n": {"en": "Description Type", "ja": "内容記述タイプ"}}], "style": {"add": "btn-success"}, "title": "Description"}, {"add": "New", "key": "parentkey[].catalog_subjects", "items": [{"key": "parentkey[].catalog_subjects[].catalog_subject", "type": "text", "title": "Subject", "title_i18n": {"en": "Subject", "ja": "主題"}}, {"key": "parentkey[].catalog_subjects[].catalog_subject_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey[].catalog_subjects[].catalog_subject_uri", "type": "text", "title": "Subject URI", "title_i18n": {"en": "Subject URI", "ja": "主題URI"}}, {"key": "parentkey[].catalog_subjects[].catalog_subject_scheme", "type": "select", "title": "Subject Scheme", "titleMap": [{"name": "BSH", "value": "BSH"}, {"name": "DDC", "value": "DDC"}, {"name": "e-Rad", "value": "e-Rad"}, {"name": "LCC", "value": "LCC"}, {"name": "LCSH", "value": "LCSH"}, {"name": "", "value": ""}, {"name": "MeSH", "value": "MeSH"}, {"name": "NDC", "value": "NDC"}, {"name": "NDLC", "value": "NDLC"}, {"name": "NDLSH", "value": "NDLSH"}, {"name": "SciVal", "value": "SciVal"}, {"name": "UDC", "value": "UDC"}, {"name": "Other", "value": "Other"}], "title_i18n": {"en": "Subject Scheme", "ja": "主題スキーマ"}}], "style": {"add": "btn-success"}, "title": "Subject"}, {"add": "New", "key": "parentkey[].catalog_licenses", "items": [{"key": "parentkey[].catalog_licenses[].catalog_license", "type": "text", "title": "License", "title_i18n": {"en": "License", "ja": "ライセンス"}}, {"key": "parentkey[].catalog_license.catalog_license_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey[].catalog_license.catalog_license_type", "type": "select", "title": "License Type", "titleMap": [{"name": "file", "value": "file"}, {"name": "metadata", "value": "metadata"}, {"name": "thumbnail", "value": "thumbnail"}], "title_i18n": {"en": "License Type", "ja": "ライセンスタイプ"}}, {"key": "parentkey[].catalog_license.catalog_license_rdf_resource", "type": "text", "title": "RDF Resource", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}], "style": {"add": "btn-success"}, "title": "License"}, {"add": "New", "key": "parentkey[].catalog_rights", "items": [{"key": "parentkey[].catalog_rights[].catalog_right", "type": "text", "title": "Rights", "title_i18n": {"en": "Access Rights", "ja": "アクセス権"}}, {"key": "parentkey[].catalog_rights[].catalog_right_language", "type": "select", "title": "Language", "titleMap": [{"name": "ja", "value": "ja"}, {"name": "ja-Kana", "value": "ja-Kana"}, {"name": "ja-Latn", "value": "ja-Latn"}, {"name": "en", "value": "en"}, {"name": "fr", "value": "fr"}, {"name": "it", "value": "it"}, {"name": "de", "value": "de"}, {"name": "es", "value": "es"}, {"name": "zh-cn", "value": "zh-cn"}, {"name": "zh-tw", "value": "zh-tw"}, {"name": "ru", "value": "ru"}, {"name": "la", "value": "la"}, {"name": "ms", "value": "ms"}, {"name": "eo", "value": "eo"}, {"name": "ar", "value": "ar"}, {"name": "el", "value": "el"}, {"name": "ko", "value": "ko"}], "title_i18n": {"en": "Language", "ja": "言語"}}, {"key": "parentkey[].catalog_rights[].catalog_right_rdf_resource", "type": "text", "title": "RDF Resource", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}], "style": {"add": "btn-success"}, "title": "Rights"}, {"add": "New", "key": "parentkey[].catalog_access_rights", "items": [{"key": "parentkey[].catalog_access_rights[].catalog_access_right_access_rights", "type": "select", "title": "Access Rights", "titleMap": [{"name": "embargoed access", "value": "embargoed access"}, {"name": "metadata only access", "value": "metadata only access"}, {"name": "restricted access", "value": "restricted access"}, {"name": "open access", "value": "open access"}], "title_i18n": {"en": "Access Rights", "ja": "アクセス権"}}, {"key": "parentkey[].catalog_access_rights[].catalog_access_right_rdf_resource", "type": "text", "title": "RDF Resource", "title_i18n": {"en": "RDF Resource", "ja": "RDFリソース"}}], "style": {"add": "btn-success"}, "title": "Access Rights"}, {"key": "parentkey.catalog_file", "type": "fieldset", "items": [{"key": "parentkey.catalog_file.catalog_file_uri", "type": "text", "title": "File URI", "title_i18n": {"en": "File URI", "ja": "ファイルURI"}}, {"key": "parentkey.catalog_file.catalog_file_object_type", "type": "select", "title": "Object Type", "titleMap": [{"name": "thumbnail", "value": "thumbnail"}], "title_i18n": {"en": "Object Type", "ja": "オブジェクトタイプ"}}], "title": "File"}], "title_i18n": {"en": "Catalog", "ja": "カタログ"}},
		delflg =False,
		sort = None
    )
    db.session.add(item_property)
    db.session.commit()


    admin = Admin(app)
    community_adminview_copy = dict(community_adminview)
    community_model = community_adminview_copy.pop("model")
    community_view = community_adminview_copy.pop("modelview")
    view = community_view(community_model,db.session,**community_adminview_copy)
    admin.add_view(view)
    return app, db, admin, sysadmin, view

# def _(x):
# class CommunityModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestCommunityModelView():
    def test_index_view_acl_guest(self,app,setup_view_community,client):
        url = url_for('community.index_view')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_index_view_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_index_view_acl(self,app,client,setup_view_community,users,id,status_code):
        url = url_for('community.index_view')
        with patch("flask_login.utils._get_user", return_value=users[id]["obj"]):
            # login_user_via_session(client,email=users[id]["email"])
            res = client.get(url)
            assert res.status_code == status_code

    # def on_model_change(self, form, model, is_created):
    # def _validate_input_id(self, field):
    # def role_query_cond(self, role_ids):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_role_query_cond -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_role_query_cond(self, setup_view_community, users):
        _, _, _, user, view = setup_view_community
        with patch("flask_login.utils._get_user", return_value=user):
            # role_ids is false
            result = view.role_query_cond([])
            assert result == None

            # role_idss is true
            result = view.role_query_cond([1,2])
            assert str(result) == "communities_community.group_id IN (:group_id_1, :group_id_2)"

    # def get_query(self):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_get_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_query(self,setup_view_community,users):
        _, _, _, user, view = setup_view_community
        # min(role_ids) <= 2
        with patch("flask_login.utils._get_user", return_value=user):
            result = view.get_query()
            assert "WHERE" not in str(result)

        # min(role_ids) > 2
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            result = view.get_query()
            assert "WHERE communities_community.group_id IN " in str(result)

    # def get_count_query(self):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_get_count_query -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_count_query(self,setup_view_community,users):
        app, _, _, user, view = setup_view_community
        # min(role_ids) <= 2
        with patch("flask_login.utils._get_user", return_value=user):
            result = view.get_count_query()
            assert "WHERE" not in str(result)

        # min(role_ids) > 2
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            result = view.get_count_query()
            assert "WHERE communities_community.group_id IN " in str(result)

    # def edit_form(self, obj):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_create(self,setup_view_community,users,mocker,db):
        app, _, _, user, _ = setup_view_community
        app.config['WEKO_THEME_INSTANCE_DATA_DIR'] = 'data'
        app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = False
        app.config['WEKO_HANDLE_CREDS_JSON_PATH'] = '/code/modules/resources/handle_creds.json'
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("community.create_view",url="/admin/community/")
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            # get
            res = client.get(url)
            assert res.status_code == 200
            login_user_via_session(client,email=users[0]["email"])
            res = client.get(url)
            assert res.status_code == 403

            login_user_via_session(client,email=user.email)
            # post
            # first character is not alphabet,"-","_"
            data = {
                "id": "111",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": object(),
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # first character is alphabet,"-","_"  negative number
            data = {
                "id": "-1",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": object(),
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # special character
            data = {
                "id": "a-1^^^",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": object(),
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # over max length (community id max length = 100)
            data = {
                "id": "a-" + "1"*99,
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": object(),
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # over max length (title max length = 255)
            data = {
                "id": "a-123456789",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "T"*256,
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": object(),
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # correct_data
            file1 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.jpg",
                content_type="image/jpg")
            data = {
                "id": "a-123456789",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file1,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 302
            comm = Community.query.filter_by(id="a-123456789").one()
            assert comm
            assert comm.title == "Test comm after"
            assert comm.description == "this is description of community1."

            # catalog_data {}
            file2 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="",
                content_type="image/jpg")
            data = {
                "id": "file2",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{}}",
                "thumbnail": file2,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 302

            # thumbnail_format_error
            file3 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.bmp",
                content_type="image/bmp")
            data = {
                "id": "file3",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{}}",
                "thumbnail": file3,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # add widget page failed
            file4 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.png",
                content_type="image/png")
            data = {
                "id": "file4",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{}}",
                "thumbnail": file4,
                "content_policy":""
            }
            with patch("weko_gridlayout.services.WidgetDesignPageServices.add_or_update_page", return_value={'result': False, 'error': 'error'}):
                res = client.post(url,data=data)
                assert res.status_code == 302

            # CNRI handle register success
            file5 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image5.jpg",
                content_type="image/jpg")
            data = {
                "id": "file5",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file5,
                "content_policy":""
            }
            app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = True
            with patch("weko_handle.api.Handle.register_handle", return_value='1234567890/1'):
                res = client.post(url,data=data)
                assert res.status_code == 302
                comm5 = Community.query.filter_by(id="file5").one()
                assert comm5.cnri == "http://hdl.handle.net/1234567890/1"

            # CNRI handle register failed
            file6 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image6.jpg",
                content_type="image/jpg")
            data = {
                "id": "file6",
                "owner": 1,
                "index": 11,
                "group": 1,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file6,
                "content_policy":""
            }
            app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = True
            with patch("weko_handle.api.Handle.register_handle", return_value=None):
                res = client.post(url,data=data)
                assert res.status_code == 302

    # def _use_append_repository_edit(self, form, index_id: str):
    # def _get_child_index_list(self):

    # def edit_form(self, obj):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_edit(self,setup_view_community,users,mocker,db):
        app, _, _, user, _ = setup_view_community
        app.config['WEKO_THEME_INSTANCE_DATA_DIR'] = 'data'
        app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = False
        app.config['WEKO_HANDLE_CREDS_JSON_PATH'] = '/code/modules/resources/handle_creds.json'
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("community.edit_view",id="test_comm",url="/admin/community/")
            url_comm2 = url_for("community.edit_view",id="test_comm2",url="/admin/community/")
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            # get
            res = client.get(url)
            assert res.status_code == 200
            login_user_via_session(client,email=users[0]["email"])
            res = client.get(url)
            assert res.status_code == 200

            login_user_via_session(client,email=user.email)
            # post
            # first character is not alphabet,"-","_"

            # correct_data
            file1 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_comm",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file1,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 302
            comm = Community.query.filter_by(id="test_comm").one()
            assert comm
            assert comm.title == "Test comm after"
            assert comm.description == "this is description of community1."

            # file remove error
            file6 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image6.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_comm",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file6,
                "content_policy":""
            }
            with patch("invenio_communities.admin.os.remove", side_effect=Exception()):
                res = client.post(url,data=data)
                assert res.status_code == 302

            # CNRI handle register failed
            file7 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image7.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_comm2",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file7,
                "content_policy":""
            }
            app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = True
            with patch("weko_handle.api.Handle.register_handle", return_value=None):
                res = client.post(url_comm2,data=data)
                assert res.status_code == 302
                comm = Community.query.filter_by(id="test_comm2").one()
                assert comm.cnri == None

            # CNRI handle register success
            file8 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image8.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_comm2",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file8,
                "content_policy":""
            }
            app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = True
            with patch("weko_handle.api.Handle.register_handle", return_value='1234567890/1'):
                res = client.post(url_comm2,data=data)
                assert res.status_code == 302
                comm = Community.query.filter_by(id="test_comm2").one()
                assert comm.cnri == "http://hdl.handle.net/1234567890/1"

            # CNRI handle register already exists
            file9 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_comm2",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file9,
                "content_policy":""
            }
            app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = True
            with patch("weko_handle.api.Handle.register_handle", return_value='1234567890/2'):
                res = client.post(url_comm2,data=data)
                assert res.status_code == 302
                comm = Community.query.filter_by(id="test_comm2").one()
                assert comm.cnri == "http://hdl.handle.net/1234567890/1"
            app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = False

            # title over max length (title max length = 255)
            file_dummy = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_comm",
                "owner": 1,
                "index": 11,
                "title": "T"*256,
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file_dummy,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # thumbnail_format_error
            file2 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.bmp",
                content_type="image/bmp")
            data = {
                "id": "test_comm",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file2,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 400

            # current_thumbnail_delete
            file3 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.png",
                content_type="image/png")
            data = {
                "id": "test_comm",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{}}",
                "thumbnail": file3,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 302

            # thumbnail_None
            file4 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="",
                content_type="image/jpg")
            data = {
                "id": "test_comm",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{}}",
                "thumbnail": file4,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 302

            # No community
            url_none = url_for("community.edit_view",id="test_none",url="/admin/community/")
            file5 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image2.jpg",
                content_type="image/jpg")
            data = {
                "id": "test_none",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":False,
                "catalog_data": "{\"metainfo\":{}}",
                "thumbnail": file5,
                "content_policy":""
            }
            res = client.post(url_none,data=data)
            assert res.status_code == 404

    # def on_model_delete(self, model):
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_on_model_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_on_model_delete(self,setup_view_community,users,mocker,db):
        app, _, _, user, _ = setup_view_community
        app.config['WEKO_THEME_INSTANCE_DATA_DIR'] = 'data'
        app.config['WEKO_HANDLE_ALLOW_REGISTER_CNRI'] = False
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("community.create_view",url="/admin/community/")
            mock_render = mocker.patch("weko_admin.admin.FacetSearchSettingView.render", return_value=make_response())
            login_user_via_session(client,email=user.email)
            # post
            # correct_data
            file1 = werkzeug.datastructures.FileStorage(stream=BytesIO(base64.b64decode(SMALLEST_JPEG_B64)),
                filename="image.jpg",
                content_type="image/jpg")
            data = {
                "id": "a-123456789",
                "owner": 1,
                "index": 11,
                "title": "Test comm after",
                "description": "this is description of community1.",
                "page":"",
                "curation_policy":"",
                "ranking":0,
                "fixed_points":0,
                "login_menu_enabled":True,
                "catalog_data": "{\"metainfo\":{\"parentkey\":[{\"catalog_contributors\":[{\"contributor_names\":[{\"contributor_name\":\"提供機関名\",\"contributor_name_language\":\"ja\"}],\"contributor_type\":\"HostingInstitution\"}],\"catalog_identifiers\":[{}],\"catalog_subjects\":[{}],\"catalog_licenses\":[{}],\"catalog_rights\":[{}],\"catalog_access_rights\":[{}]}]}}",
                "thumbnail": file1,
                "content_policy":""
            }
            res = client.post(url,data=data)
            assert res.status_code == 302
        model =  Community.query.filter_by(id="a-123456789").one()
        model.cnri = "http://hdl.handle.net/1234567890/1"

        # cnri delete faile
        with patch("weko_handle.api.Handle.delete_handle", return_value=None):
            CommunityModelView.on_model_delete(self, model)

        # thumbnail delete error
        with patch("weko_handle.api.Handle.delete_handle", return_value="1234567890/1"):
            with patch("invenio_communities.admin.os.remove", side_effect=Exception()):
                CommunityModelView.on_model_delete(self, model)

        # cnri delete success
        # thumbnail delete success
        with patch("weko_handle.api.Handle.delete_handle", return_value="1234567890/1"):
            CommunityModelView.on_model_delete(self, model)

        # skip
        model.cnri = None
        model.thumbnail_path = None
        CommunityModelView.on_model_delete(self, model)
    
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_on_model_change_sets_id_user -vv -s --
    def test_on_model_change_sets_id_user(self, setup_view_community, mocker):
        _, _, _, _, view = setup_view_community

        class DummyForm: pass
        class DummyModel:
            id_user = None

        dummy_form = DummyForm()
        dummy_model = DummyModel()

        dummy_user = mocker.Mock()
        dummy_user.get_id.return_value = "test_user_id"
        mocker.patch("invenio_communities.admin.current_user", dummy_user)

        view.on_model_change(dummy_form, dummy_model, is_created=True)

        assert dummy_model.id_user == "test_user_id"

    def test_get_json_schema(self,setup_view_community,users,mocker,db):
        app, _, _, user, _ = setup_view_community
        app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE']  = 'data'
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("community.get_json_schema")
            res = client.get(url)
            assert res.status_code == 200
            with patch("invenio_communities.admin.json.load", side_effect=BaseException()):
                res = client.get(url)
                assert res.status_code == 500
            app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE']  = None
            with patch("invenio_communities.admin.json.load", return_value={}):
                res = client.get(url)
                assert res.status_code == 200
                
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_get_schema_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_schema_form(self,setup_view_community,users,mocker,db):
        app, _, _, user, _ = setup_view_community
        with app.test_client() as client:
            login_user_via_session(client,email=user.email)
            url = url_for("community.get_schema_form")
            res = client.get(url)
            assert res.status_code == 200
            with patch("invenio_communities.admin.db.session.execute", side_effect=BaseException()):
                res = client.get(url)
                assert res.status_code == 500
    
    @pytest.mark.parametrize("input_id,expected_error", [
        ("1abc", "The first character cannot"),
        ("-123", "Cannot set negative number"), 
        ("abc def", "Don't use space or special"),
    ])
    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_validate_input_id_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_validate_input_id_error(self, setup_view_community, input_id, expected_error):
        _, _, _, _, view = setup_view_community
        class DummyField:
            def __init__(self, data):
                self.data = data
        field = DummyField(input_id)
        with pytest.raises(ValidationError) as e:
            view._validate_input_id(field)
        assert expected_error in str(e.value)

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_validate_input_id_success -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_validate_input_id_success(self, setup_view_community):
        _, _, _, _, view = setup_view_community
        class DummyField:
            def __init__(self, data):
                self.data = data
        field = DummyField("Abc-123_def")
        view._validate_input_id(field)
        assert field.data == "abc-123_def"

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_edit_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_edit_form(self, setup_view_community, mocker):
        _, _, _, _, view = setup_view_community

        class DummyIndex:
            id = 123
        class DummyObj:
            index = DummyIndex()

        # With permission
        mocker.patch("invenio_communities.admin.get_user_role_ids", return_value=[1])
        mocker.patch("invenio_communities.admin.current_app").config = {"COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT": 2}
        # Directly patch the super() call
        mock_super = mocker.patch("flask_admin.contrib.sqla.ModelView.edit_form", return_value="super_form")
        mocker.patch.object(view, "_use_append_repository_edit")
        result = view.edit_form(DummyObj())
        assert result == "super_form"
        assert mock_super.called

        mocker.stopall()

        # Without permission
        mocker.patch("invenio_communities.admin.get_user_role_ids", return_value=[3])
        mocker.patch("invenio_communities.admin.current_app").config = {"COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT": 2}
        mocker.patch.object(view, "_use_append_repository_edit", return_value="custom_form")
        result = view.edit_form(DummyObj())
        assert result == "custom_form"

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_use_append_repository_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_use_append_repository_edit(self, setup_view_community, mocker):
        _, _, _, _, view = setup_view_community
        class DummyIndex:
            query_factory = None
        class DummyForm:
            index = DummyIndex()
            action = None
        form = DummyForm()
        result = view._use_append_repository_edit(form, "123")
        assert getattr(view, "index_id") == "123"
        assert form.index.query_factory == view._get_child_index_list
        assert form.action == "edit"
        assert result is form

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestCommunityModelView::test_get_child_index_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_child_index_list(self, setup_view_community, mocker):
        _, _, _, _, view = setup_view_community
        view.index_id = "42"

        mock_indexes = mocker.patch("weko_index_tree.api.Indexes.get_recursive_tree", return_value=[MagicMock(cid=1), MagicMock(cid=2)])
        mock_query = mocker.patch("invenio_communities.admin.Index.query")
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = ["index1", "index2"]

        result = view._get_child_index_list()

        mock_indexes.assert_called_once_with("42")
        mock_query.filter.assert_called_once()
        mock_order.all.assert_called_once()
        assert result == ["index1", "index2"]

# class FeaturedCommunityModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestFeaturedCommunityModelView():
    def test_index_view_acl_guest(self,app,db,client):
        admin = Admin(app)
        featured_adminview_copy = dict(featured_adminview)
        featured_model = featured_adminview_copy.pop("model")
        featured_view = featured_adminview_copy.pop("modelview")
        view = featured_view(featured_model,db.session,**featured_adminview_copy)
        admin.add_view(view)

        url = url_for('featuredcommunity.index_view')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionfeaturedModelView::test_index_view_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_index_view_acl(self,app,db,client,users,id,status_code):
        admin = Admin(app)
        featured_adminview_copy = dict(featured_adminview)
        featured_model = featured_adminview_copy.pop("model")
        featured_view = featured_adminview_copy.pop("modelview")
        view = featured_view(featured_model,db.session,**featured_adminview_copy)
        admin.add_view(view)
        url = url_for('featuredcommunity.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code


# class InclusionRequestModelView(ModelView):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
class TestInclusionRequestModelView():
    def test_index_view_acl_guest(self,app,client,db):
        admin = Admin(app)
        request_adminview_copy = dict(request_adminview)
        request_model = request_adminview_copy.pop("model")
        request_view = request_adminview_copy.pop("modelview")
        view = request_view(request_model,db.session,**request_adminview_copy)
        admin.add_view(view)
        url = url_for('inclusionrequest.index_view')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py::TestInclusionRequestModelView::test_index_view_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_index_view_acl(self,app,client,db,users,id,status_code):
        admin = Admin(app)
        request_adminview_copy = dict(request_adminview)
        request_model = request_adminview_copy.pop("model")
        request_view = request_adminview_copy.pop("modelview")
        view = request_view(request_model,db.session,**request_adminview_copy)
        admin.add_view(view)

        url = url_for('inclusionrequest.index_view')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code
