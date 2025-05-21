# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

import json
import uuid
from mock import patch
from flask import Blueprint, Response

from invenio_deposit.utils import check_oauth2_scope_write, \
    check_oauth2_scope_write_elasticsearch
from invenio_records_rest.utils import check_elasticsearch
from weko_authors.rest import (
    create_blueprint,
)

import urllib.parse
from flask_oauthlib.provider import OAuth2Provider
from invenio_oauth2server.views.server import login_oauth2_user
from mock import MagicMock
from weko_index_tree.api import Indexes
import pytest
from sqlalchemy.exc import SQLAlchemyError

blueprint = Blueprint(
    'invenio_records_rest',
    __name__,
    url_prefix='',
)

_PID = 'pid(depid,record_class="invenio_deposit.api:Deposit")'

endpoints = {
    'depid': {
        'pid_type': 'depid',
        'pid_minter': 'deposit',
        'pid_fetcher': 'deposit',
        'record_class': 'invenio_deposit.api:Deposit',
        'files_serializers': {
            'application/json': ('invenio_deposit.serializers:json_v1_files_response'),
        },
        'search_class': 'invenio_deposit.search:DepositSearch',
        'search_serializers': {
            'application/json': ('invenio_records_rest.serializers:json_v1_search'),
        },
        'list_route': '/deposits/',
        'indexer_class': None,
        'item_route': '/deposits/<{0}:pid_value>'.format(_PID),
        'route': '/deposits/<{0}:pid_value>/authors/count'.format(_PID),
        'default_media_type': 'application/json',
        'links_factory_imp': 'invenio_deposit.links:deposit_links_factory',
        'create_permission_factory_imp': check_oauth2_scope_write,
        'read_permission_factory_imp': check_elasticsearch,
        'update_permission_factory_imp':
            check_oauth2_scope_write_elasticsearch,
        'delete_permission_factory_imp':
            check_oauth2_scope_write_elasticsearch,
        'max_result_window': 10000,
        'cites_route': 1,
    },
}


# def create_blueprint(endpoints):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_blueprint(app):
    assert create_blueprint(endpoints) != None


# def Authors(ContentNegotiatedMethodView):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::test_Authors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_Authors(app):
    app.register_blueprint(create_blueprint(app.config['WEKO_AUTHORS_REST_ENDPOINTS']))
    with \
        app.test_client() as client, \
        patch('weko_authors.utils.count_authors', return_value=Response(status=200)), \
        patch('json.dumps', return_value={}):

        # 1 GET reqest
        res = client.get('/v1/authors/count')
        assert res.status_code == 200

        # 2 Invalid version
        res = client.get('/v0/authors/count')
        assert res.status_code == 400




# .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorDBManagementAPI -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace -p no:warnings

class TestAuthorDBManagementAPI:
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorDBManagementAPI::test_get_v1 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace | tee log.log
    def test_get_v1(self, app, esindex, client_api, auth_headers_noroleuser, auth_headers_sysadmin, auth_headers_sysadmin_without_scope, author_records_for_test, authors_affiliation_settings, authors_prefix_settings):
        """
        著者DB検索API - 著者情報取得
        - 正常系: 検索パラメータごとに正しくデータが取得できるか確認
        - 異常系: 不正なパラメータや認証なしでのアクセス制御確認
        """

        oauth2 = OAuth2Provider()
        oauth2.after_request(login_oauth2_user)

        # 正常系テスト（検索条件ごとの動作確認）
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"fullname": "Test_1 User_1"}, 200, ['1'])  # フルネーム検索で特定の著者ID 1 が返ることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"fullname": "Test_1 "}, 200, ['1','2','3','4'])  # 部分一致検索で該当する複数の著者IDが返ることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"firstname": "Test_2"}, 200, ['2'])  # 名（ファーストネーム）で検索し、著者ID 2 のみが返ることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"familyname": "User_3"}, 200, ['3','4'])  # 姓（ファミリーネーム）で検索し、著者ID 3 のみが返ることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"idtype": "WEKO", "authorid": "1"}, 200, ['1'])  # ID タイプが WEKO で ID が 1 の著者が正しく取得できるか確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"idtype": "ORCID", "authorid": "1"}, 200, [])  # ID タイプが WEKO で ID が 1 の著者が正しく取得できるか確認

        # 異常系テスト（不正なアクセスや無効なパラメータの確認）
        self.run_get_authors_unauthorized(app, client_api)  # 認証なしでのアクセスが 401（Unauthorized） となることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin_without_scope, {"fullname": "Test_1 "}, 403, [])  # スコープ権限のないシステム管理者が検索した場合、403（Forbidden）となることを確認
        self.run_get_authors(app, client_api, auth_headers_noroleuser, {"fullname": "Test_1 "}, 403, [])  # 権限のないユーザーが検索した場合、403（Forbidden）となることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"idtype": "ORCID"}, 400, [])  # Both 'idtype' and 'authorid' must be specified together or omitted.
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"idtype": "ORCID_wrong","authorid": "1"}, 400, [])  # ORCID というIDタイプでの検索が不正な場合、400（Bad Request）となることを確認
        self.run_get_authors(app, client_api, auth_headers_sysadmin, {"authorid": "https://orcid.org/##"}, 400, [])  # 無効な著者IDで検索した場合、400（Bad Request）となることを確認

        with patch("weko_authors.utils.get_author_prefix_obj",side_effect={}):
            self.run_get_authors(app, client_api, auth_headers_sysadmin, {"fullname": "Test_1 User_1"}, 200, ['1'])  # フルネーム検索で特定の著者ID 1 が返ることを確認
        # システムエラーの確認
        with patch("invenio_search.current_search_client.search", side_effect=Exception):
            self.run_get_authors(app, client_api, auth_headers_sysadmin, {"firstname": "Test_2"}, 500, [])  # 検索時にエラーが発生した場合、500（Internal Server Error）となることを確認

    def run_get_authors(self, app, client_api, user_role, query_params, expected_status, expected_ids):
        """
        著者情報取得APIのテスト
        - 検索条件に応じて正しくデータが取得できるか確認
        - 取得した著者IDリストが期待通りか検証
        """
        if query_params:
            url = f"v1/authors?{self.build_query_string(query_params)}"
        else:
            url = f"v1/authors"
        response = client_api.get(url, headers=user_role)
        assert response.status_code == expected_status
        if response.status_code == 200:
            data = response.json
            assert "authors" in data, "レスポンスJSONに 'authors' キーが含まれていない"
            print(data)
            retrieved_ids = [
                authorInfo.get("authorId", None)
                for author in data.get("authors", [])
                for authorInfo in author.get("authorIdInfo", [])
                if authorInfo.get("idType") == "WEKO"
            ]
            assert set(retrieved_ids) == set(expected_ids), f"取得した著者IDが想定外: {retrieved_ids}"

    def run_get_authors_unauthorized(self, app, client_api):
        """
        認証なしで著者情報取得を試みるテスト
        - 認証が必要なAPIにアクセスし、Unauthorized(401)が返ることを確認
        """
        url = "v1/authors"
        response = client_api.get(url, headers={})
        assert response.status_code == 401
        print(f"Unauthorizedアクセスエラー: {response.get_data(as_text=True)}")

    def build_query_string(self, params):
        """
        クエリパラメータをURLエンコードするヘルパー関数
        """
        return "&".join(f"{key}={urllib.parse.quote(str(value))}" for key, value in params.items() if value)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorDBManagementAPI::test_post_v1 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace | tee log.log
    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    def test_post_v1(self, app, client_api, auth_headers_noroleuser, auth_headers_sysadmin, author_records_for_test, authors_affiliation_settings, authors_prefix_settings):
        """
        著者情報登録API - 著者情報の登録テスト
        - 正常系: 正しく登録できるか確認
        - 異常系: 不正なリクエストや認証なしでのアクセス制御確認
        """

        oauth2 = OAuth2Provider()
        oauth2.after_request(login_oauth2_user)

        # 正常系テスト
        # 正しく著者情報を登録できることを確認
        self.run_post_author(app, client_api, auth_headers_sysadmin, self.valid_author_data(), 200, "Author successfully registered.")  # 正常なデータ
        self.run_post_author(app, client_api, auth_headers_sysadmin, self.valid_author_data("ORCID", ""), 200, "Author successfully registered.")  # カーバレジのためのテストケース
        self.run_post_author(app, client_api, auth_headers_sysadmin, self.valid_author_data("ORCID", ""), 200, "Author successfully registered.")  # カーバレジのためのテストケース

        # 認証なしのリクエストが拒否されることを確認
        self.run_post_author_unauthorized(app, client_api)  # 認証なしでリクエストするとエラー

        # 権限のないユーザーのリクエストが拒否されることを確認
        self.run_post_author(app, client_api, auth_headers_noroleuser, self.valid_author_data(), 403, None)  # 権限なしのユーザーでリクエスト

        # 異常系テスト（リクエスト内容のバリデーション）
        # 不正なリクエストが適切に処理されることを確認
        self.run_post_author(app, client_api, auth_headers_sysadmin, {}, 400, "Bad Request: Invalid payload, {'author': ['Missing data for required field.']}")  # 空のリクエスト
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": None}, 400, "Bad Request: Invalid payload, {'author': ['Field may not be null.']}")  # authorがNone
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"authorIdInfo": [{"idType": "ORCID"}]}}, 400, "Both 'idType' and 'authorId' must be provided together.")  # idTypeのみ指定
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"authorIdInfo": [{"idType": "WEKO", "authorId": "A1"}]}}, 400, "The WEKO ID must be numeric characters only.")  # WEKO IDが数字以外
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"authorIdInfo": [{"idType": "WEKO", "authorId": "1"}]}}, 400, "The value is already in use as WEKO ID.")  # 既存のWEKO ID
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"authorNameInfo": [{"firstName": "John", "familyName": "Doe"}]}}, 400, "If 'firstName' or 'familyName' is provided, 'language' must also be specified.")  # language未指定
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"affiliationInfo": "InvalidFormat"}}, 400, "Bad Request: Invalid payload, {'author': {'affiliationInfo': ['Not a valid list.']}}")  # affiliationInfoがリストでない
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"affiliationInfo": ["InvalidFormat"]}}, 400, "Bad Request: Invalid payload, {'author': {'affiliationInfo': {0: {'_schema': ['Invalid input type.']}}}}")  # affiliationInfoのフォーマット不正
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"affiliationInfo": [{"affiliationPeriodInfo": [{"periodStart": "2025-03-21", "periodEnd": "2025-01-27"}]}]}}, 400, 'periodStart must be before periodEnd.')  # 開始日が終了日より後
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"affiliationInfo": [{"identifierInfo": [{"affiliationId": "https://ror.org/##", "identifierShowFlg": "true"}]}]}}, 400, "Both 'affiliationIdType' and 'affiliationId' must be provided together.")  # affiliationIdType未指定
        self.run_post_author(app, client_api, auth_headers_sysadmin, {"author": {"affiliationInfo": [{"affiliationNameInfo": [{"affiliationName": "NII", "identifierShowFlg": "true"}]}]}}, 400, "Both 'affiliationName' and 'affiliationNameLang' must be provided together.")  # affiliationNameLang未指定

        # システムエラーの確認
        # DBエラーや例外発生時の動作を確認
        self.run_post_author_db_error(app, client_api, auth_headers_sysadmin, self.valid_author_data())  # DBエラー発生時
        with patch("invenio_search.current_search_client.search", side_effect=Exception):
            self.run_post_author(app, client_api, auth_headers_sysadmin, self.valid_author_data(), 500)  # 検索時に例外が発生した場合

    def run_post_author(self, app, client_api, user_headers, request_data, expected_status, expected_message=None):
        """
        著者情報登録APIのテスト
        - 指定したリクエストデータでAPIを実行し、期待するレスポンスを検証
        """
        url = "v1/authors"
        response = client_api.post(url, json=request_data, headers=user_headers)
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"

        if expected_message:
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                # print("Response is HTML format.")
                response_text = response.get_data(as_text=True)
                assert expected_message in response_text, f"Expected message '{expected_message}' not found in HTML response, got: \n{response_text}"
            else:
                response_json = json.loads(response.data.decode('utf-8'))
                message = response_json.get("message")
                assert expected_message in message, f"Expected message: {expected_message}, got: {message}"

    def run_post_author_unauthorized(self, app, client_api):
        """
        認証なしで著者情報を登録しようとした場合のテスト
        - 認証が必要なAPIにアクセスし、Unauthorized(401)が返ることを確認
        """
        url = "v1/authors"
        response = client_api.post(url, json=self.valid_author_data(), headers={})

        assert response.status_code == 401

    def run_post_author_db_error(self, app, client_api, user_headers, request_data):
        """
        データベースエラー時のテスト
        - DBエラー発生時に500 (Internal Server Error) が返されることを確認
        """
        url = "v1/authors"

        with patch("weko_authors.models.Authors.get_sequence", side_effect=SQLAlchemyError):
            response = client_api.post(url, json=request_data, headers=user_headers)

        assert response.status_code == 500
        assert "Database error." in response.get_data(as_text=True)

    def valid_author_data(self, idType = "WEKO",nameFormat = "familyNmAndNm"):
        """
        正常な著者データ
        - 正しく登録できるデータを返す
        """
        return {
            "author": {
                "emailInfo": [{"email": "sample@xxx.co.jp"}],
                "authorIdInfo": [{"idType": idType, "authorId": "5", "authorIdShowFlg": "true"}],
                "authorNameInfo": [{"language": "en", "firstName": "John", "familyName": "Doe", "nameFormat": nameFormat, "nameShowFlg": "true"}],
                "affiliationInfo": [{
                    "identifierInfo": [{"affiliationId": "https://ror.org/5678", "affiliationIdType": "ISNI", "identifierShowFlg": "true"}],
                    "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}],
                    "affiliationPeriodInfo": [{"periodStart": "2025-01-27", "periodEnd": "2025-03-21"}]
                }]
            }
        }


    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorDBManagementAPI::test_put_v1 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace | tee log.log
    def test_put_v1(self, app, client_api, auth_headers_noroleuser, auth_headers_sysadmin, author_records_for_test, authors_affiliation_settings, authors_prefix_settings):
        """
        著者情報更新API - 著者情報の更新テスト
        - 正常系: 正しく更新できるか確認
        - 異常系: 不正なリクエストや認証なしでのアクセス制御確認
        """
        with patch("weko_deposit.tasks.update_items_by_authorInfo.delay",side_effect = MagicMock()):
            oauth2 = OAuth2Provider()
            oauth2.after_request(login_oauth2_user)

            # 正常系テスト
            # 正しく著者情報を更新できることを確認
            self.run_put_author(app, client_api, auth_headers_sysadmin, self.valid_update_data(), 1, 200, "Author successfully updated.")
            author_data = self.valid_update_data()
            del author_data["author"]["emailInfo"]
            self.run_put_author(app, client_api, auth_headers_sysadmin, author_data, 1, 200, "Author successfully updated.")
            es_id = author_records_for_test["1"]
            self.run_put_author(app, client_api, auth_headers_sysadmin, {"author": self.valid_update_data().get("author")}, es_id, 200, "Author successfully updated.")
            self.run_put_author(app, client_api, auth_headers_sysadmin, {"force_change": True, "author": self.valid_update_data().get("author")}, es_id, 200, "Author successfully updated.")
            self.run_put_author(app, client_api, auth_headers_sysadmin, {"author": self.valid_update_data().get("author")}, es_id, 200, "Author successfully updated.")

            data_no_weko = {
                "author": {
                    "emailInfo": [{"email": "updated@xxx.co.jp"}],
                    "authorIdInfo": [{"idType": "ORCID", "authorId": "5", "authorIdShowFlg": "true"}],
                    "authorNameInfo": [{"language": "en", "firstName": "Jane", "familyName": "Smith", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}],
                    "affiliationInfo": [{
                        "identifierInfo": [{"affiliationId": "https://ror.org/5678", "affiliationIdType": "ISNI", "identifierShowFlg": "true"}],
                        "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}],
                        "affiliationPeriodInfo": [{"periodStart": "2025-02-01", "periodEnd": "2025-04-01"}]
                    }]
                }
            }
            self.run_put_author(app, client_api, auth_headers_sysadmin, data_no_weko, 1, 400, "At least one WEKO ID must be provided in update.")

            # 認証なしのリクエストが拒否されることを確認
            self.run_put_author_unauthorized(app, client_api)

            # 権限のないユーザーのリクエストが拒否されることを確認
            self.run_put_author(app, client_api, auth_headers_noroleuser, self.valid_update_data(), 403, None)

            # 異常系テスト（リクエスト内容のバリデーション）
            self.run_put_author(app, client_api, auth_headers_sysadmin, {}, 1, 400, "'author': ['Missing data for required field.']")
            author_data = self.valid_update_data()
            author_data["author"]["authorNameInfo"][0]["language"] = "jp"
            self.run_put_author(app, client_api, auth_headers_sysadmin, author_data, 1, 400, "Invalid authorNameInfo_language.")
            author_data = self.valid_update_data()
            author_data["author"]["affiliationInfo"][0]["affiliationNameInfo"][0]["affiliationNameLang"] = "jp"
            self.run_put_author(app, client_api, auth_headers_sysadmin, author_data, 1, 400, "Invalid affiliationInfo_affiliationNameLang.")
            author_data = self.valid_update_data()
            author_data["author"]["authorIdInfo"].append({"idType": "WEKO_WRONG", "authorId": "5"})
            self.run_put_author(app, client_api, auth_headers_sysadmin, author_data, 1, 400, "Invalid authorIdInfo_idType.")
            author_data = self.valid_update_data()
            author_data["author"]["affiliationInfo"][0]["identifierInfo"][0]["affiliationIdType"] = "Ringgold_WRONG"
            self.run_put_author(app, client_api, auth_headers_sysadmin, author_data, 1, 400, "Invalid affiliationInfo_affiliationIdType.")

            self.run_put_author(app, client_api, auth_headers_sysadmin, {}, 123, 400, "'author': ['Missing data for required field.']")
            self.run_put_author(app, client_api, auth_headers_sysadmin, {"author": self.valid_update_data().get("author")}, "invalid", 400,  "Invalid identifier format. Must be an integer ID or UUID.")

            self.run_put_author(app, client_api, auth_headers_sysadmin, {"author": self.valid_update_data().get("author")}, 999, 404, "Specified author does not exist.")
            self.run_put_author(app, client_api, auth_headers_sysadmin, {"author": self.valid_update_data().get("author")}, str(uuid.uuid4()), 404, "Specified author does not exist.")

            # システムエラーの確認
            self.run_put_author_db_error(app, client_api, auth_headers_sysadmin, self.valid_update_data())

    def run_put_author(self, app, client_api, user_headers, request_data, id, expected_status, expected_message=None):
        """
        著者情報更新APIのテスト
        """
        print(1111111111111111111111111111)
        print(request_data)
        print(1111111111111111111111111111)
        url = f"v1/authors/{id}"
        response = client_api.put(url, json=request_data, headers=user_headers)
        # assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"

        if expected_message:
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type:
                response_text = response.get_data(as_text=True)
                assert expected_message in response_text, f"Expected message '{expected_message}' not found in HTML response, got: \n{response_text}"
            else:
                response_json = json.loads(response.data.decode('utf-8'))
                message = response_json.get("message")
                assert expected_message in message, f"Expected message: {expected_message}, got: {message}"

    def run_put_author_unauthorized(self, app, client_api):
        """
        認証なしで著者情報を更新しようとした場合のテスト
        """
        url = "v1/authors/1"
        response = client_api.put(url, json=self.valid_update_data(), headers={})
        assert response.status_code == 401

    def run_put_author_db_error(self, app, client_api, user_headers, request_data):
        """
        データベースエラー時のテスト
        """
        url = "v1/authors/1"
        with patch("weko_authors.models.Authors.query", side_effect=SQLAlchemyError):
            response = client_api.put(url, json=request_data, headers=user_headers)
        assert response.status_code == 500
        assert "Failed to update author." in response.get_data(as_text=True)

        with patch("weko_authors.rest.AuthorDBManagementAPI.get_all_schemes", side_effect=Exception):
            response = client_api.put(url, json=request_data, headers=user_headers)
        assert response.status_code == 500
        assert "Failed to update author." in response.get_data(as_text=True)

    def valid_update_data(self):
        """
        正常な更新データ
        """
        return {
            "author": {
                "emailInfo": [{"email": "updated@xxx.co.jp"}],
                "authorIdInfo": [{"idType": "WEKO", "authorId": "5", "authorIdShowFlg": "true"}],
                "authorNameInfo": [{"language": "en", "firstName": "Jane", "familyName": "Smith", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}],
                "affiliationInfo": [{
                    "identifierInfo": [{"affiliationId": "https://ror.org/5678", "affiliationIdType": "ISNI", "identifierShowFlg": "true"}],
                    "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}],
                    "affiliationPeriodInfo": [{"periodStart": "2025-02-01", "periodEnd": "2025-04-01"}]
                }]
            }
        }

    @pytest.mark.parametrize('base_app',[dict(
        is_es=True
    )],indirect=['base_app'])
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorDBManagementAPI::test_delete_v1 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_index_tree/.tox/c1/tmp --full-trace | tee log.log
    def test_delete_v1(self, app, client_api, auth_headers_sysadmin, auth_headers_noroleuser,author_records_for_test):
        """
        著者削除API - 著者情報の削除テスト
        - 正常系: 正しく削除できるか確認
        - 異常系: 認証なし、権限なし、存在しないデータ削除時の動作確認
        """
        es_ids = author_records_for_test
        self.run_delete_author(app, client_api, auth_headers_sysadmin, 1, 200)
        self.run_delete_author(app, client_api, auth_headers_sysadmin, es_ids["2"], 200)

        self.run_delete_author(app, client_api, auth_headers_sysadmin, "invalid", 400, "Invalid identifier format. Must be an integer ID or UUID.")
        self.run_delete_author(app, client_api, auth_headers_sysadmin, 999, 404, "Specified author does not exist.")
        self.run_delete_author(app, client_api, auth_headers_sysadmin, uuid.uuid4(), 404, "Specified author does not exist.")

        # 認証エラー
        self.run_delete_author_unauthorized(app, client_api)

        # 権限なし
        self.run_delete_author(app, client_api, auth_headers_noroleuser, 1, 403)

        # エラー
        self.run_delete_author_error(app, client_api, auth_headers_sysadmin, 4)

    def run_delete_author(self, app, client_api, user_headers, id, expected_status, expected_message=None):
        """
        著者削除APIのテスト
        - 指定したリクエストデータでAPIを実行し、期待するレスポンスを検証
        """
        url = f"v1/authors/{id}"
        response = client_api.delete(url, headers=user_headers)
        print(response.get_data(as_text=True))
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        if expected_message:
            assert expected_message in response.get_data(as_text=True)

    def run_delete_author_unauthorized(self, app, client_api):
        """
        認証なしで著者情報を削除しようとした場合のテスト
        - 認証が必要なAPIにアクセスし、Unauthorized(401)が返ることを確認
        """
        url = "v1/authors/1"
        response = client_api.delete(url, headers={})

        assert response.status_code == 401
        # assert "OAuth2 authentication failed" in response.get_data(as_text=True)

    def run_delete_author_error(self, app, client_api, user_headers, id):
        """
        データベースエラー時のテスト
        - DBエラー発生時に500 (Internal Server Error) が返されることを確認
        """
        url = f"v1/authors/{id}"

        with patch("weko_authors.models.db.session.commit", side_effect=SQLAlchemyError):
            response = client_api.delete(url, headers=user_headers)

        assert response.status_code == 500
        assert "Failed to delete author." in response.get_data(as_text=True)

        with patch("weko_authors.models.db.session.commit", side_effect=Exception):
            response = client_api.delete(url, headers=user_headers)

        assert response.status_code == 500
        assert "Failed to delete author." in response.get_data(as_text=True)
