# -*- coding: utf-8 -*-
"""End-to-end: real HTTP POST to SWORD deposit (paper + evidence data).

conftest の `item_type` フィクスチャは 親(item_type) より先に 子(item_type_mapping)
を INSERT して FK 違反になるため、正しい順序（親を flush してから子）に直した
`item_type` をこのモジュールでオーバーライドする。以降の
sword_mapping / workflow / sword_client は自動的にこの item_type を使う。

POST /sword/service-document をモックなしで実行し、実レスポンスをダンプする。
"""
import hashlib
import io
import json
import os
import zipfile

import pytest
from flask import url_for
from werkzeug.datastructures import FileStorage
from weko_records.models import ItemTypeName, ItemType, ItemTypeMapping
from invenio_accounts.testutils import login_user_via_session

from .helpers import json_data


@pytest.fixture()
def item_type(app, db):
    """conftest 版と同じ内容を、親→flush→子 の順序で作り直したもの。"""
    name1 = ItemTypeName(id=1, name="デフォルトアイテムタイプ（フル）",
                         has_site_license=True, is_active=True)
    name2 = ItemTypeName(id=2, name="デフォルトアイテムタイプ（SWORD）",
                         has_site_license=True, is_active=True)
    it1 = ItemType(id=1, name_id=1, harvesting_type=True,
                   schema=json_data("data/item_type/schema_1.json"),
                   form=json_data("data/item_type/form_1.json"),
                   render=json_data("data/item_type/render_1.json"),
                   tag=1, version_id=1, is_deleted=False)
    it2 = ItemType(id=2, name_id=2, harvesting_type=True,
                   schema=json_data("data/item_type/schema_2.json"),
                   form=json_data("data/item_type/form_2.json"),
                   render=json_data("data/item_type/render_2.json"),
                   tag=2, version_id=1, is_deleted=False)
    for o in (name1, name2, it1, it2):
        db.session.add(o)
    db.session.flush()  # 親を確定してから子(FK)を入れる
    m1 = ItemTypeMapping(id=1, item_type_id=1,
                         mapping=json_data("data/item_type/mapping_1.json"))
    m2 = ItemTypeMapping(id=2, item_type_id=2,
                         mapping=json_data("data/item_type/mapping_2.json"))
    db.session.add(m1)
    db.session.add(m2)
    db.session.commit()
    return [
        {"item_type_name": name1, "item_type": it1, "item_type_mapping": m1},
        {"item_type_name": name2, "item_type": it2, "item_type_mapping": None},
    ]


def _build_simplezip():
    """論文＋根拠データの2アイテム crate（ファイル参照のみ除去・分割フラグ補正）。"""
    base = "tests/data/zip_crate2"
    crate = json.load(open(os.path.join(base, "ro-crate-metadata.json")))
    file_ids = {
        e["@id"] for e in crate["@graph"]
        if e.get("@type") == "File"
        or (isinstance(e.get("@type"), list) and "File" in e["@type"])
    }
    # itemLink のうち、バッチ外(既存システム/外部URL)を指すものは除去。
    # バッチ内リンク(identifier が "_:" のblank node)だけ残す。
    bad_links = {
        e["@id"] for e in crate["@graph"]
        if e.get("@type") == "PropertyValue"
        and isinstance(e.get("identifier"), str)
        and not e["identifier"].startswith("_:")
    }
    drop_ids = file_ids | bad_links
    graph = []
    for e in crate["@graph"]:
        if e.get("@id") in drop_ids:
            continue  # File / 外部itemLink エンティティを除去
        if "wk:itemLinks" in e:
            kept = [p for p in e["wk:itemLinks"] if p.get("@id") not in bad_links]
            if kept:
                e["wk:itemLinks"] = kept
            else:
                e.pop("wk:itemLinks", None)
        # 分割フラグをマッパが見るキー名に補正
        if e.get("@id") == "./":
            e.pop("wk:is_splited", None)
            e["wk:isSplited"] = True
        # hasPart から File 参照だけ除去（サブアイテム参照は残す）
        if "hasPart" in e:
            kept = [p for p in e["hasPart"] if p.get("@id") not in file_ids]
            if kept:
                e["hasPart"] = kept
            else:
                e.pop("hasPart", None)
        # サブアイテム: 新規登録として扱わせるため既存参照/DOI/更新モードを除去
        if e.get("@id") in ("_:JournalPaper1", "_:EvidenceData1"):
            for k in ("identifier", "wk:grant", "wk:editMode"):
                e.pop(k, None)
        graph.append(e)
    crate["@graph"] = graph

    fp = io.BytesIO()
    with zipfile.ZipFile(fp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data/ro-crate-metadata.json",
                   json.dumps(crate, ensure_ascii=False).encode("utf-8"))
    fp.seek(0)
    return fp


def _post(client, token):
    zip_bytes = _build_simplezip().read()
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Disposition": "attachment; filename=crate.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest": "SHA-256=" + hashlib.sha256(zip_bytes).hexdigest(),
    }
    storage = FileStorage(filename="crate.zip", stream=io.BytesIO(zip_bytes),
                          content_type="application/zip")
    url = url_for("weko_swordserver.post_service_document")
    return client.post(url, data={"file": storage},
                       content_type="multipart/form-data", headers=headers)


def _dump(title, resp):
    print("\n\n########## {} ##########".format(title))
    print("HTTP/1.1 {}".format(resp.status))
    for k, v in resp.headers.items():
        print("{}: {}".format(k, v))
    print("")
    body = resp.get_data(as_text=True)
    try:
        print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
    except Exception:
        print(body)
    import sys as _s
    _s.stdout.flush()


def test_diag(app, db, users, esindex, location, index, item_type,
              doi_identifier, sword_mapping, sword_client, workflow):
    """マッパ出力を直接ダンプ（何がマップされ、何が欠落するか）。"""
    from weko_search_ui.utils import check_jsonld_import_items
    app.config["WEKO_RECORDS_REFERENCE_SUPPLEMENT"] = ["isSupplementTo", "isSupplementedBy"]
    mapping_id = sword_mapping[0]["id"]
    from flask import request as _req
    with app.test_request_context("/sword/service-document", method="POST",
                                  base_url="https://repository.example.org"):
        _req.view_args = {}
        storage = FileStorage(filename="crate.zip", stream=_build_simplezip(),
                              content_type="application/zip")
        res = check_jsonld_import_items(
            storage, "http://purl.org/net/sword/3.0/package/SimpleZip",
            mapping_id, validate_bagit=False)
    print("\n\n===== MAPPER DIAG =====")
    print("item_type_id:", res.get("item_type_id"), "| top-error:", res.get("error"))
    for i, r in enumerate(res.get("list_record", [])):
        md = r.get("metadata", {}) or {}
        print("\n-- item[{}] errors: {}".format(i, r.get("errors")))
        print("   all metadata keys:", sorted(md.keys()))
        for k in sorted(md.keys()):
            print("     {} = {}".format(k, str(md[k])[:90]))


def test_e2e(app, client, db, users, esindex, location, index, tokens,
             item_type, doi_identifier, sword_mapping, sword_client, workflow,
             monkeypatch):
    app.config["WEKO_SWORDSERVER_BAGIT_VERIFICATION"] = False
    # テストアプリに欠けている実アプリ側の設定を補う
    app.config["WEKO_RECORDS_REFERENCE_SUPPLEMENT"] = ["isSupplementTo", "isSupplementedBy"]
    app.config["ACCOUNTS_SESSION_REDIS_DB_NO"] = 1
    app.config["WEKO_PERMISSION_SUPER_ROLE_USER"] = [
        "System Administrator", "Repository Administrator"]
    app.config["WEKO_PERMISSION_ROLE_COMMUNITY"] = ["Community Administrator"]
    app.config["WEKO_NOTIFICATIONS"] = False
    # 外部副作用（メール送信/通知/DOI/handle 登録）は無効化。
    # 中核（認証・パッケージ解析・マッピング・アイテム登録・関連付け・Status Document）は実処理のまま。
    # user_activity_logs は日付パーティション表。テストDB(create_all)には当日パーティションが
    # 無く INSERT が失敗するため、全期間をカバーする DEFAULT パーティションを用意する。
    try:
        db.session.execute(
            "CREATE TABLE IF NOT EXISTS user_activity_logs_default "
            "PARTITION OF user_activity_logs DEFAULT")
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Workflowクライアントのフローを、headless自動実行が完結できるクリーンなフロー
    # (begin -> item_login -> item_link -> end。oa_policy等の未実装アクションを含まない)へ付替。
    from weko_workflow.models import WorkFlow as _WorkFlow, FlowDefine as _FlowDefine
    _clean_flow = _FlowDefine.query.filter_by(
        flow_name="Registration Flow").first()
    _wf = _WorkFlow.query.get(sword_client[1]["sword_client"].workflow_id)
    if _wf and _clean_flow:
        _wf.flow_id = _clean_flow.id
        db.session.commit()

    _noop = lambda *a, **k: None
    monkeypatch.setattr("weko_swordserver.views.notify_about_item", _noop)
    monkeypatch.setattr("weko_search_ui.utils.register_item_doi", _noop)
    monkeypatch.setattr("weko_search_ui.utils.register_item_handle", _noop)
    # commit() が投げる非同期タスク(Celery/RabbitMQ)はテストのbroker未到達で固まるため無効化。
    # （ESへのメタデータ登録そのものは実処理のまま）
    monkeypatch.setattr(
        "weko_deposit.tasks.extract_pdf_and_update_file_contents.apply_async", _noop)
    monkeypatch.setattr("invenio_oaiserver.tasks.update_records_sets.delay", _noop)
    # トークン文字列は POST 前に取り出す（POST後は ORM オブジェクトが detach する）
    tok_direct = tokens[0]["token"].access_token
    tok_workflow = tokens[1]["token"].access_token
    email_direct = users[0]["email"]
    email_workflow = users[1]["email"]

    login_user_via_session(client=client, email=email_direct)  # sysadmin
    resp_direct = _post(client, tok_direct)
    _dump("DIRECT (workflow disabled)", resp_direct)

    login_user_via_session(client=client, email=email_workflow)  # repoadmin
    resp_wf = _post(client, tok_workflow)
    _dump("WORKFLOW (workflow enabled)", resp_wf)
