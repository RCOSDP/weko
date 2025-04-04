import pytest
import json
from mock import patch
from flask import Flask, json, url_for, make_response
from invenio_accounts.testutils import login_user_via_session

from weko_records.models import ItemType, ItemTypeName

from weko_indextree_journal.admin import IndexJournalSettingView

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
class TestIndexJournalSettingView:
    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    user_results = [
        (0, True),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    ]
    @pytest.mark.parametrize('id, is_permission', user_results)
    def test_index_acl(self, app, db, client_rest, users, test_indices, test_journals,mocker, id, is_permission):
        mocker.patch("weko_indextree_journal.admin.IndexJournalSettingView.render",return_value=make_response())
        login_user_via_session(client=client_rest, email=users[id]["email"])
        url = url_for("indexjournal.index", index_id=1)
        res = client_rest.get(url)
        if is_permission:
            assert res.status_code == 200
        else:
            assert res.status_code != 200

    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_index(self, app, db,client_rest, users,test_indices, test_journals,mocker):
        login_user_via_session(client=client_rest, email=users[0]["email"])
        from weko_indextree_journal.models import Journal
        template = 'weko_indextree_journal/admin/index.html'

        url = url_for("indexjournal.index")
        # not lists
        mock_render = mocker.patch("weko_indextree_journal.admin.IndexJournalSettingView.render",return_value=make_response())
        res = client_rest.get(url)
        assert res.status_code == 200
        args, _ = mock_render.call_args
        assert args[0] == "weko_items_ui/error.html"

        itemtype_name = ItemTypeName(id=1,name="test_itemtype")
        itemtype = ItemType(
            id=1, name_id=1,tag=1
        )
        with db.session.begin_nested():
            db.session.add(itemtype_name)
            db.session.add(itemtype)
        db.session.commit()

        # index_id <= 0
        mock_render = mocker.patch("weko_indextree_journal.admin.IndexJournalSettingView.render",return_value=make_response())
        res = client_rest.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == template
        assert kwargs["get_tree_json"] == "/api/tree"
        assert kwargs["upt_tree_json"] == ""
        assert kwargs["mod_tree_detail"] == "/api/tree/index/"
        assert kwargs["mod_journal_detail"] == "/api/indextree/journal"
        assert kwargs["record"] == []
        assert kwargs["jsonschema"] == "/admin/indexjournal/jsonschema"
        assert kwargs["schemaform"] == "/admin/indexjournal/schemaform"
        assert kwargs["lists"][0].id == 1
        assert kwargs["links"] == None
        assert kwargs["pid"] == None
        assert kwargs["index_id"] == 0
        assert kwargs["journal_id"] == None
        assert kwargs["lang_code"] == "en"

        # journal is not None
        url = url_for("indexjournal.index",index_id="1")
        mock_render = mocker.patch("weko_indextree_journal.admin.IndexJournalSettingView.render",return_value=make_response())
        res = client_rest.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs['record']["id"] == 1
        assert kwargs['lists'][0].id == 1
        assert kwargs['index_id'] == 1
        assert kwargs['journal_id'] == 1

        # journal is None(raise error in get_journal_by_index_id)
        with patch("weko_indextree_journal.admin.Journals.get_journal_by_index_id",return_value=None):
            url = url_for("indexjournal.index",index_id="1000")
            mock_render = mocker.patch("weko_indextree_journal.admin.IndexJournalSettingView.render",return_value=make_response())
            res = client_rest.get(url)
            args, kwargs = mock_render.call_args
            assert res.status_code == 200
            args, kwargs = mock_render.call_args
            assert kwargs['record'] == None
            assert kwargs['lists'][0].id == 1
            assert kwargs['index_id'] == 1000
            assert kwargs['journal_id'] == None

        # WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API != "/admin/indexjournal/jsonschema",WEKO_INDEXTREE_JOURNAL_FORM_JSON_API != "/admin/indexjournal/schemaform"
        url = url_for("indexjournal.index")
        app.config.update(
            WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API = "/xxx/xxx/xxx",
            WEKO_INDEXTREE_JOURNAL_FORM_JSON_API = "/yyy/yyy/yyy"
        )
        mock_render = mocker.patch("weko_indextree_journal.admin.IndexJournalSettingView.render",return_value=make_response())
        res = client_rest.get(url)
        args, kwargs = mock_render.call_args
        assert kwargs['record'] == []
        assert kwargs['jsonschema'] == '/xxx/xxx/xxx'
        assert kwargs['schemaform'] == '/yyy/yyy/yyy'
        assert kwargs['lists'][0].id == 1
        assert kwargs['index_id'] == 0
        assert kwargs['journal_id'] == None

    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_get_journal_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    user_results = [
        (0, True),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    ]
    @pytest.mark.parametrize('id, is_permission', user_results)
    def test_get_journal_by_index_id_acl(self, app, db, client_rest, users, test_indices, id, is_permission):
        login_user_via_session(client=client_rest, email=users[id]["email"])
        res = client_rest.get(url_for("indexjournal.get_journal_by_index_id", index_id=1))

        if is_permission:
            assert res.status_code == 200
        else:
            assert res.status_code != 200

    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_get_journal_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get_journal_by_index_id(self,app,db,client_rest,users, test_indices, test_journals):
        login_user_via_session(client=client_rest, email=users[0]["email"])

        url = url_for("indexjournal.get_journal_by_index_id",index_id = 0)
        res = client_rest.get(url)
        assert json.loads(res.data) == '{}'

        url = url_for("indexjournal.get_journal_by_index_id",index_id = 1)
        res = client_rest.get(url)
        assert json.loads(res.data) == {'access_type': 'F', 'coverage_depth': 'abstract', 'coverage_notes': '', 'date_first_issue_online': '2022-01-01', 'date_last_issue_online': '2022-01-01', 'date_monograph_published_online': '', 'date_monograph_published_print': '', 'deleted': '', 'embargo_info': '', 'first_author': '', 'first_editor': '', 'ichushi_code': '', 'id': 1, 'index_id': 1, 'is_output': True, 'jstage_code': '', 'language': 'en', 'monograph_edition': '', 'monograph_volume': '', 'ncid': '', 'ndl_bibid': '', 'ndl_callno': '', 'num_first_issue_online': '', 'num_first_vol_online': '', 'num_last_issue_online': '', 'num_last_vol_online': '', 'online_identifier': '', 'owner_user_id': 0, 'parent_publication_title_id': '', 'preceding_publication_title_id': '', 'print_identifier': '', 'publication_title': 'test journal 1', 'publication_type': 'serial', 'publisher_name': '', 'title_alternative': '', 'title_id': 1, 'title_transcription': '', 'title_url': 'search?search_type=2&q=1', 'abstract':'', 'code_issnl':''}

        with patch("weko_indextree_journal.admin.Journals.get_journal_by_index_id",side_effect=BaseException("test_error")):
            res = client_rest.get(url)
            assert res.status_code == 400


    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_get_json_schema_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    user_results = [
        (0, True),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    ]
    @pytest.mark.parametrize('id, is_permission', user_results)
    def test_get_json_schema_acl(self,i18n_app, db, users, test_indices, id, is_permission):
        with i18n_app.test_client() as client:
            login_user_via_session(client=client, email=users[id]["email"])
            res = client.get(url_for("indexjournal.get_json_schema"))
            if is_permission:
                assert res.status_code == 200
            else:
                assert res.status_code != 200

    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_get_json_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get_json_schema(self, i18n_app, db, users,test_indices):
        with i18n_app.test_client() as client:
            url = url_for("indexjournal.get_json_schema")
            login_user_via_session(client=client, email=users[0]["email"])
            res = client.get(url)
            assert res.status_code == 200
            assert json.loads(res.data)["title"] == "OutputItemList"
            # json_schema is {}
            i18n_app.config.update(
                WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE="../tests/data/schemas/jsonschema_empty.json"
            )
            res = client.get(url)
            assert res.status_code == 200
            assert json.loads(res.data) == {}
            # raise Exception,
            i18n_app.config.update(
                WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE="../tests/data/schemas/not_exist_file.json",
            )
            res = client.get(url)
            assert res.status_code == 500

    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_get_schema_form_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    user_results = [
        (0, True),
        (1, False),
        (2, True),
        (3, True),
        (4, False),
    ]
    @pytest.mark.parametrize('id, is_permission', user_results)
    def test_get_schema_form_acl(self,i18n_app, db, users, test_indices, id, is_permission):

        with i18n_app.test_client() as client:
            login_user_via_session(client=client, email=users[id]["email"])
            res = client.get(url_for("indexjournal.get_schema_form"))
            if is_permission:
                assert res.status_code == 200
            else:
                assert res.status_code != 200
    # .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::TestIndexJournalSettingView::test_get_schema_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get_schema_form(self,app,client_rest,db,users,test_indices):
        url = url_for("indexjournal.get_schema_form")
        login_user_via_session(client=client_rest, email=users[0]["email"])
        test = [{'key': 'is_output', 'titleMap': [{'name': 'Output', 'value': True}, {'name': 'Do Not Output', 'value': False}], 'type': 'radios'}, {'condition': 'model.is_output', 'key': 'publication_title', 'title': 'Title', 'title_i18n': {'en': 'Title', 'ja': 'タイトル'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'print_identifier', 'title': 'Print-format identifier', 'title_i18n': {'en': 'Print-format identifier', 'ja': 'プリント版ISSN/プリント版ISBN'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'online_identifier', 'title': 'Online-format identifier', 'title_i18n': {'en': 'Online-format identifier', 'ja': 'eISSN/eISBN'}, 'type': 'text'}, {'condition': "model.is_output && model.publication_type == 'serial'", 'format': 'yyyy-MM-dd', 'key': 'date_first_issue_online', 'required': True, 'templateUrl': '/static/templates/weko_deposit/datepicker_multi_format.html', 'title': 'Date of first issue available online', 'title_i18n': {'en': 'Date of first issue available online', 'ja': '最古オンライン巻号の出版年月日'}, 'type': 'template'}, {'condition': "model.is_output && model.publication_type != 'serial'", 'format': 'yyyy-MM-dd', 'key': 'date_first_issue_online', 'templateUrl': '/static/templates/weko_deposit/datepicker_multi_format.html', 'title': 'Date of first issue available online', 'title_i18n': {'en': 'Date of first issue available online', 'ja': '最古オンライン巻号の出版年月日'}, 'type': 'template'}, {'condition': 'model.is_output', 'key': 'num_first_vol_online', 'title': 'Number of first volume available online', 'title_i18n': {'en': 'Number of first volume available online', 'ja': '提供最古巻'}, 'type': 'text'}, {'condition': "model.is_output && model.num_first_vol_online != ''", 'key': 'num_first_issue_online', 'title': 'Number of first issue available online', 'title_i18n': {'en': 'Number of first issue available online', 'ja': '提供最古号'}, 'type': 'text'}, {'condition': "model.is_output && model.num_first_vol_online == ''", 'key': 'num_first_issue_online', 'readonly': True, 'title': 'Number of first issue available online', 'title_i18n': {'en': 'Number of first issue available online', 'ja': '提供最古号'}, 'type': 'text'}, {'condition': 'model.is_output', 'format': 'yyyy-MM-dd', 'key': 'date_last_issue_online', 'templateUrl': '/static/templates/weko_deposit/datepicker_multi_format.html', 'title': 'Date of last issue available online', 'title_i18n': {'en': 'Date of last issue available online', 'ja': '最新オンライン巻号の出版年月日'}, 'type': 'template'}, {'condition': 'model.is_output', 'key': 'num_last_vol_online', 'title': 'Number of last volume available online', 'title_i18n': {'en': 'Number of last volume available online', 'ja': '提供最新巻'}, 'type': 'text'}, {'condition': "model.is_output && model.num_last_vol_online != ''", 'key': 'num_last_issue_online', 'title': 'Number of last issue available online', 'title_i18n': {'en': 'Number of last issue available online', 'ja': '提供最新号'}, 'type': 'text'}, {'condition': "model.is_output && model.num_last_vol_online == ''", 'key': 'num_last_issue_online', 'readonly': True, 'title': 'Number of last issue available online', 'title_i18n': {'en': 'Number of last issue available online', 'ja': '提供最新号'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'embargo_info', 'title': 'Embargo information', 'title_i18n': {'en': 'Embargo information', 'ja': 'エンバーゴ情報'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'coverage_depth', 'title': 'Coverage depth', 'titleMap': [{'name': 'Abstract', 'value': 'abstract'}, {'name': 'Fulltext', 'value': 'fulltext'}, {'name': 'Selected Articles', 'value': 'selectedArticles'}], 'title_i18n': {'en': 'Coverage depth', 'ja': 'カバー範囲'}, 'type': 'select'}, {'condition': 'model.is_output', 'key': 'coverage_notes', 'title': 'Coverage notes', 'title_i18n': {'en': 'Coverage notes', 'ja': 'カバー範囲に関する注記'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'publisher_name', 'title': 'Publisher name', 'title_i18n': {'en': 'Publisher name', 'ja': '出版者'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'publication_type', 'title': 'Publication type', 'titleMap': [{'name': 'Serial', 'value': 'serial'}], 'title_i18n': {'en': 'Publication type', 'ja': '資料種別'}, 'type': 'select'}, {'condition': 'model.is_output', 'key': 'parent_publication_title_id', 'title': 'Parent publication identifier', 'title_i18n': {'en': 'Parent publication identifier', 'ja': 'シリーズのタイトルID'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'preceding_publication_title_id', 'title': 'Preceding publication identifier', 'title_i18n': {'en': 'Preceding publication identifier', 'ja': '変遷前誌のタイトルID'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'access_type', 'title': 'Access type', 'titleMap': [{'name': 'Free（無料・オープンアクセス）', 'value': 'F'}, {'name': 'Paid（有料）', 'value': 'P'}], 'title_i18n': {'en': 'Access type', 'ja': 'アクセスモデル'}, 'type': 'select'}, {'condition': 'model.is_output', 'key': 'language', 'title': 'Language', 'titleMap': [{'name': 'jpn', 'value': 'jpn'}, {'name': 'eng', 'value': 'eng'}, {'name': 'chi', 'value': 'chi'}, {'name': 'kor', 'value': 'kor'}, {'name': 'aar', 'value': 'aar'}, {'name': 'abk', 'value': 'abk'}, {'name': 'afr', 'value': 'afr'}, {'name': 'aka', 'value': 'aka'}, {'name': 'alb', 'value': 'alb'}, {'name': 'amh', 'value': 'amh'}, {'name': 'ara', 'value': 'ara'}, {'name': 'arg', 'value': 'arg'}, {'name': 'arm', 'value': 'arm'}, {'name': 'asm', 'value': 'asm'}, {'name': 'ava', 'value': 'ava'}, {'name': 'ave', 'value': 'ave'}, {'name': 'aym', 'value': 'aym'}, {'name': 'aze', 'value': 'aze'}, {'name': 'bak', 'value': 'bak'}, {'name': 'bam', 'value': 'bam'}, {'name': 'bel', 'value': 'bel'}, {'name': 'baq', 'value': 'baq'}, {'name': 'ben', 'value': 'ben'}, {'name': 'bih', 'value': 'bih'}, {'name': 'bis', 'value': 'bis'}, {'name': 'bos', 'value': 'bos'}, {'name': 'bre', 'value': 'bre'}, {'name': 'bul', 'value': 'bul'}, {'name': 'bur', 'value': 'bur'}, {'name': 'cat', 'value': 'cat'}, {'name': 'cha', 'value': 'cha'}, {'name': 'che', 'value': 'che'}, {'name': 'chu', 'value': 'chu'}, {'name': 'chv', 'value': 'chv'}, {'name': 'cor', 'value': 'cor'}, {'name': 'cos', 'value': 'cos'}, {'name': 'cre', 'value': 'cre'}, {'name': 'cze', 'value': 'cze'}, {'name': 'dan', 'value': 'dan'}, {'name': 'div', 'value': 'div'}, {'name': 'dut', 'value': 'dut'}, {'name': 'dzo', 'value': 'dzo'}, {'name': 'epo', 'value': 'epo'}, {'name': 'est', 'value': 'est'}, {'name': 'ewe', 'value': 'ewe'}, {'name': 'fao', 'value': 'fao'}, {'name': 'fij', 'value': 'fij'}, {'name': 'fin', 'value': 'fin'}, {'name': 'fre', 'value': 'fre'}, {'name': 'fry', 'value': 'fry'}, {'name': 'ful', 'value': 'ful'}, {'name': 'geo', 'value': 'geo'}, {'name': 'ger', 'value': 'ger'}, {'name': 'gla', 'value': 'gla'}, {'name': 'gle', 'value': 'gle'}, {'name': 'glg', 'value': 'glg'}, {'name': 'glv', 'value': 'glv'}, {'name': 'gre', 'value': 'gre'}, {'name': 'grn', 'value': 'grn'}, {'name': 'guj', 'value': 'guj'}, {'name': 'hat', 'value': 'hat'}, {'name': 'hau', 'value': 'hau'}, {'name': 'heb', 'value': 'heb'}, {'name': 'her', 'value': 'her'}, {'name': 'hin', 'value': 'hin'}, {'name': 'hmo', 'value': 'hmo'}, {'name': 'hrv', 'value': 'hrv'}, {'name': 'hun', 'value': 'hun'}, {'name': 'ibo', 'value': 'ibo'}, {'name': 'ice', 'value': 'ice'}, {'name': 'ido', 'value': 'ido'}, {'name': 'iii', 'value': 'iii'}, {'name': 'iku', 'value': 'iku'}, {'name': 'ile', 'value': 'ile'}, {'name': 'ina', 'value': 'ina'}, {'name': 'ind', 'value': 'ind'}, {'name': 'ipk', 'value': 'ipk'}, {'name': 'ita', 'value': 'ita'}, {'name': 'jav', 'value': 'jav'}, {'name': 'kal', 'value': 'kal'}, {'name': 'kan', 'value': 'kan'}, {'name': 'kas', 'value': 'kas'}, {'name': 'kau', 'value': 'kau'}, {'name': 'kaz', 'value': 'kaz'}, {'name': 'khm', 'value': 'khm'}, {'name': 'kik', 'value': 'kik'}, {'name': 'kin', 'value': 'kin'}, {'name': 'kir', 'value': 'kir'}, {'name': 'kom', 'value': 'kom'}, {'name': 'kon', 'value': 'kon'}, {'name': 'kua', 'value': 'kua'}, {'name': 'kur', 'value': 'kur'}, {'name': 'lao', 'value': 'lao'}, {'name': 'lat', 'value': 'lat'}, {'name': 'lav', 'value': 'lav'}, {'name': 'lim', 'value': 'lim'}, {'name': 'lin', 'value': 'lin'}, {'name': 'lit', 'value': 'lit'}, {'name': 'ltz', 'value': 'ltz'}, {'name': 'lub', 'value': 'lub'}, {'name': 'lug', 'value': 'lug'}, {'name': 'mac', 'value': 'mac'}, {'name': 'mah', 'value': 'mah'}, {'name': 'mal', 'value': 'mal'}, {'name': 'mao', 'value': 'mao'}, {'name': 'mar', 'value': 'mar'}, {'name': 'may', 'value': 'may'}, {'name': 'mlg', 'value': 'mlg'}, {'name': 'mlt', 'value': 'mlt'}, {'name': 'mon', 'value': 'mon'}, {'name': 'nau', 'value': 'nau'}, {'name': 'nav', 'value': 'nav'}, {'name': 'nbl', 'value': 'nbl'}, {'name': 'nde', 'value': 'nde'}, {'name': 'ndo', 'value': 'ndo'}, {'name': 'nep', 'value': 'nep'}, {'name': 'nno', 'value': 'nno'}, {'name': 'nob', 'value': 'nob'}, {'name': 'nor', 'value': 'nor'}, {'name': 'nya', 'value': 'nya'}, {'name': 'oci', 'value': 'oci'}, {'name': 'oji', 'value': 'oji'}, {'name': 'ori', 'value': 'ori'}, {'name': 'orm', 'value': 'orm'}, {'name': 'oss', 'value': 'oss'}, {'name': 'pan', 'value': 'pan'}, {'name': 'per', 'value': 'per'}, {'name': 'pli', 'value': 'pli'}, {'name': 'pol', 'value': 'pol'}, {'name': 'por', 'value': 'por'}, {'name': 'pus', 'value': 'pus'}, {'name': 'que', 'value': 'que'}, {'name': 'roh', 'value': 'roh'}, {'name': 'rum', 'value': 'rum'}, {'name': 'run', 'value': 'run'}, {'name': 'rus', 'value': 'rus'}, {'name': 'sag', 'value': 'sag'}, {'name': 'san', 'value': 'san'}, {'name': 'sin', 'value': 'sin'}, {'name': 'slo', 'value': 'slo'}, {'name': 'slv', 'value': 'slv'}, {'name': 'sme', 'value': 'sme'}, {'name': 'smo', 'value': 'smo'}, {'name': 'sna', 'value': 'sna'}, {'name': 'snd', 'value': 'snd'}, {'name': 'som', 'value': 'som'}, {'name': 'sot', 'value': 'sot'}, {'name': 'spa', 'value': 'spa'}, {'name': 'srd', 'value': 'srd'}, {'name': 'srp', 'value': 'srp'}, {'name': 'ssw', 'value': 'ssw'}, {'name': 'sun', 'value': 'sun'}, {'name': 'swa', 'value': 'swa'}, {'name': 'swe', 'value': 'swe'}, {'name': 'tah', 'value': 'tah'}, {'name': 'tam', 'value': 'tam'}, {'name': 'tat', 'value': 'tat'}, {'name': 'tel', 'value': 'tel'}, {'name': 'tgk', 'value': 'tgk'}, {'name': 'tgl', 'value': 'tgl'}, {'name': 'tha', 'value': 'tha'}, {'name': 'tib', 'value': 'tib'}, {'name': 'tir', 'value': 'tir'}, {'name': 'ton', 'value': 'ton'}, {'name': 'tsn', 'value': 'tsn'}, {'name': 'tso', 'value': 'tso'}, {'name': 'tuk', 'value': 'tuk'}, {'name': 'tur', 'value': 'tur'}, {'name': 'twi', 'value': 'twi'}, {'name': 'uig', 'value': 'uig'}, {'name': 'ukr', 'value': 'ukr'}, {'name': 'urd', 'value': 'urd'}, {'name': 'uzb', 'value': 'uzb'}, {'name': 'ven', 'value': 'ven'}, {'name': 'vie', 'value': 'vie'}, {'name': 'vol', 'value': 'vol'}, {'name': 'wel', 'value': 'wel'}, {'name': 'wln', 'value': 'wln'}, {'name': 'wol', 'value': 'wol'}, {'name': 'xho', 'value': 'xho'}, {'name': 'yid', 'value': 'yid'}, {'name': 'yor', 'value': 'yor'}, {'name': 'zha', 'value': 'zha'}, {'name': 'zul', 'value': 'zul'}], 'title_i18n': {'en': 'Language', 'ja': '言語'}, 'type': 'select'}, {'condition': 'model.is_output', 'key': 'title_alternative', 'title': 'Title alternative', 'title_i18n': {'en': 'Title alternative', 'ja': 'その他のタイトル（他の言語でのタイトルなど）'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'title_transcription', 'title': 'Title transcription', 'title_i18n': {'en': 'Title transcription', 'ja': 'タイトルヨミ'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'ncid', 'title': 'NCID', 'title_i18n': {'en': 'NCID', 'ja': 'NCID'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'ndl_callno', 'title': 'NDL Call No.', 'title_i18n': {'en': 'NDL Call No.', 'ja': 'NDL請求記号'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'ndl_bibid', 'title': 'NDL Bibliographic ID', 'title_i18n': {'en': 'NDL Bibliographic ID', 'ja': 'NDL書誌ID'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'jstage_code', 'title': 'J-STAGE CDJOURNAL', 'title_i18n': {'en': 'J-STAGE CDJOURNAL', 'ja': 'J-STAGE資料コード（雑誌名の略称）'}, 'type': 'text'}, {'condition': 'model.is_output', 'key': 'ichushi_code', 'title': 'Ichushi Code', 'title_i18n': {'en': 'Ichushi Code', 'ja': '医中誌ジャーナルコード'}, 'type': 'text'}]
        res = client_rest.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == test

        app.config.update(
            WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE="../tests/data/schemas/schemaform.json"
        )
        test = [{"condition": "model.is_output", "key": "publication_title", "title": "タイトル", "title_i18n": {"en": "Title", "ja": "タイトル"}, "type": "text"}, {"condition": "model.is_output", "key": "publisher_name", "title_i18n": {"en": "Publisher name", "ja": ""}, "type": "text"}, {"condition": "model.is_output", "key": "title_alternative", "title_i18n": {"en": "Title alternative"}, "type": "text"}, {"condition": "model.is_output", "items": [{"condition": "model.is_output", "key": "creator_name", "title": "作成者", "title_i18n": {"en": "creator name", "ja": "作成者"}, "type": "text"}, {"condition": "model.is_output", "key": "creator_name", "title_i18n": {"en": "age", "ja": ""}, "type": "text"}, {"condition": "model.is_output", "key": "creator_name", "title_i18n": {"en": "creator affiliation"}, "type": "text"}, {"condition": "model.is_output", "key": "creator_name", "type": "text"}], "key": "creator_info", "type": "obj"}]
        res = client_rest.get(url,headers={"Accept-Language":"ja"})
        assert res.status_code == 200
        assert json.loads(res.data) == test

        app.config.update(
            WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE="../tests/data/schemas/schemaform_empty.json"
        )
        res = client_rest.get(url,headers={"Accept-Language":"ja"})
        assert res.status_code == 200
        assert json.loads(res.data) == ["*"]

        # raise Exception
        app.config.update(
            WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE="../tests/data/schemas/not_exist_file.json"
        )
        res = client_rest.get(url,headers={"Accept-Language":"ja"})
        assert res.status_code == 500


    def test_get_journal_by_index_id_IndexJournalSettingView(self,i18n_app, indices):
        test = IndexJournalSettingView()
        index_id = 33

        assert "Response" in str(type(test.get_journal_by_index_id(index_id=index_id)))

        with patch("weko_indextree_journal.api.Journals.get_journal_by_index_id", return_value=None):
            assert "Response" in str(type(test.get_journal_by_index_id(index_id=1)))

        # Exception coverage
        try:
            assert "Response" in str(type(test.get_journal_by_index_id(index_id="a")))
        except:
            pass


    def test_get_schema_form_IndexJournalSettingView(self,i18n_app):
        test = IndexJournalSettingView()

        assert "Response" in str(type(test.get_schema_form()))

        # Exception coverage
        try:
            i18n_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'] = ""
            test.get_schema_form()
        except:
            pass
