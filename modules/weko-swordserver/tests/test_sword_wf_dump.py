# -*- coding: utf-8 -*-
"""Ad-hoc dump: ワークフロー（承認あり）経由での実レスポンスをダンプする。

以下を実HTTPリクエストで実行し、レスポンスをそのまま出力する。

1. POST /sword/service-document  (単一アイテム / 承認ありワークフロー)  -> 202
2. GET  /sword/deposit/<recid>   (承認待ちの状態)                       -> 200
3. 承認（POST /workflow/activity/action/<activity_id>/<approval>）
4. GET  /sword/deposit/<recid>   (承認後の状態)                        -> 200
5. DELETE /sword/deposit/<recid> (削除フロー = 承認あり)                -> 202

実行環境（postgres / elasticsearch / redis と実行用コンテナ）:
  docker network create swordtest
  docker run -d --name postgresql --network swordtest \
    -e POSTGRES_USER=invenio -e POSTGRES_PASSWORD=dbpass123 \
    -e POSTGRES_DB=wekotest postgres:12
  docker run -d --name redis --network swordtest redis:7.4.1
  docker run -d --name elasticsearch --network swordtest \
    -e discovery.type=single-node weko-elasticsearch:latest
  docker run -d --name swordtest-web --network swordtest \
    -v /home/mhaya/weko:/code -w /code wekotest-ready:latest -lc 'sleep infinity'
  # 初回のみ: egg-info の再生成
  docker exec swordtest-web bash -lc 'cd /code/modules && for d in */setup.py; do \
    (cd $(dirname $d) && /home/invenio/.virtualenvs/invenio/bin/python setup.py -q egg_info); done'

実行:
  docker exec swordtest-web bash -lc '\
    cd /code/modules/weko-swordserver && \
    /home/invenio/.virtualenvs/invenio/bin/python -m pytest \
    tests/test_sword_wf_dump.py -s -q -p no:warnings'

途中で失敗した場合はテストDBが残るため、下記で作り直してから再実行する。
  docker exec postgresql psql -U invenio -d postgres \
    -c 'DROP DATABASE IF EXISTS wekotest;' -c 'CREATE DATABASE wekotest OWNER invenio;'

不要になったらこのファイルは削除してよい（gitには含めない）。
"""
import hashlib
import io
import json
import os
import uuid
import zipfile
from datetime import datetime

import pytest
from flask import url_for
from werkzeug.datastructures import FileStorage
from invenio_accounts.testutils import login_user_via_session
from weko_records.models import ItemTypeName, ItemType, ItemTypeMapping

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
    db.session.flush()
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
    """単一アイテムの crate（tests/data/zip_crate）を SimpleZip 化する。

    既存アイテム参照(identifier)・DOI付与(wk:grant)・更新モード(wk:editMode)は
    新規登録として扱わせるため除去する。
    """
    base = "tests/data/zip_crate"
    crate = json.load(open(os.path.join(base, "ro-crate-metadata.json")))
    for e in crate["@graph"]:
        if e.get("@id") == "./":
            for k in ("identifier", "wk:grant", "wk:editMode"):
                e.pop(k, None)

    fp = io.BytesIO()
    with zipfile.ZipFile(fp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data/ro-crate-metadata.json",
                   json.dumps(crate, ensure_ascii=False).encode("utf-8"))
        # hasPart の @id は "data/xxx"（バグ内の相対パス）であり、
        # 実体はペイロード(data/)配下の data/xxx に配置される。
        for name in os.listdir(os.path.join(base, "data")):
            with open(os.path.join(base, "data", name), "rb") as f:
                z.writestr("data/data/{}".format(name), f.read())
    fp.seek(0)
    return fp


def _dump(title, resp):
    print("\n\n########## {} ##########".format(title))
    print("HTTP/1.1 {}".format(resp.status))
    for k, v in resp.headers.items():
        if k in ("Set-Cookie", "Content-Length", "Vary"):
            continue
        print("{}: {}".format(k, v))
    print("")
    body = resp.get_data(as_text=True)
    if body:
        try:
            print(json.dumps(json.loads(body), indent=2, ensure_ascii=False))
        except Exception:
            print(body)
    else:
        print("(no body)")
    import sys as _s
    _s.stdout.flush()


def _make_flow(db, users, name, action_ids, flow_pk, flow_type=1):
    """action_ids の順にアクションを持つフローを作成し、FlowDefine を返す。

    flow_type: 1=登録フロー, 2=削除フロー(WEKO_WORKFLOW_DELETION_FLOW_TYPE)
    """
    from weko_workflow.models import FlowDefine, FlowAction
    flow = FlowDefine(id=flow_pk, flow_id=uuid.uuid4(), flow_name=name,
                      flow_user=users[0]["obj"].id, flow_status="A",
                      flow_type=flow_type)
    db.session.add(flow)
    db.session.commit()
    for order, action_id in enumerate(action_ids, start=1):
        db.session.add(FlowAction(
            status="N", flow_id=flow.flow_id, action_id=action_id,
            action_version="1.0.0", action_order=order, action_condition="",
            action_status="A",
            action_date=datetime.strptime("2018/07/28 0:00:00",
                                          "%Y/%m/%d %H:%M:%S"),
            send_mail_setting={}))
    db.session.commit()
    return flow


def test_workflow_dump(app, client, db, users, esindex, location, index, tokens,
                       item_type, doi_identifier, sword_mapping, sword_client,
                       workflow, monkeypatch):
    app.config["WEKO_SWORDSERVER_BAGIT_VERIFICATION"] = False
    app.config["WEKO_RECORDS_REFERENCE_SUPPLEMENT"] = [
        "isSupplementTo", "isSupplementedBy"]
    app.config["ACCOUNTS_SESSION_REDIS_DB_NO"] = 1
    app.config["WEKO_PERMISSION_SUPER_ROLE_USER"] = [
        "System Administrator", "Repository Administrator"]
    app.config["WEKO_PERMISSION_ROLE_COMMUNITY"] = ["Community Administrator"]
    app.config["WEKO_NOTIFICATIONS"] = False

    try:
        db.session.execute(
            "CREATE TABLE IF NOT EXISTS user_activity_logs_default "
            "PARTITION OF user_activity_logs DEFAULT")
        db.session.commit()
    except Exception:
        db.session.rollback()

    _noop = lambda *a, **k: None
    monkeypatch.setattr("weko_swordserver.views.notify_about_item", _noop)
    monkeypatch.setattr("weko_search_ui.utils.register_item_doi", _noop)
    monkeypatch.setattr("weko_search_ui.utils.register_item_handle", _noop)
    monkeypatch.setattr(
        "weko_deposit.tasks.extract_pdf_and_update_file_contents.apply_async",
        _noop)
    monkeypatch.setattr("invenio_oaiserver.tasks.update_records_sets.delay",
                        _noop)
    # celery inspect() はブローカー未起動だと長時間ブロックするため無効化
    monkeypatch.setattr("weko_items_ui.views.check_an_item_is_locked",
                        lambda *a, **k: False)
    monkeypatch.setattr("weko_workflow.views.check_an_item_is_locked",
                        lambda *a, **k: False)

    # action id: 1=begin, 2=end, 3=item_login(item register), 4=approval,
    #            5=item_link
    from weko_workflow.models import WorkFlow as _WorkFlow, Activity as _Activity
    register_flow = _make_flow(db, users, "Registration Flow with approval(dump)",
                              [1, 3, 5, 4, 2], 3)
    delete_flow = _make_flow(db, users, "Delete Flow with approval(dump)",
                             [1, 4, 2], 4, flow_type=2)

    wf = _WorkFlow.query.get(sword_client[1]["sword_client"].workflow_id)
    wf.flow_id = register_flow.id
    wf.delete_flow_id = delete_flow.id
    db.session.commit()

    # DELETE 用に item:delete スコープを追加
    tok = tokens[1]["token"]
    tok._scopes = "deposit:write deposit:actions item:create item:delete user:activity"
    db.session.commit()

    token = tok.access_token
    email = users[1]["email"]  # repoadmin
    login_user_via_session(client=client, email=email)

    # ---- 1. POST (workflow, 承認あり) ----
    zip_bytes = _build_simplezip().read()
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Disposition": "attachment; filename=crate.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest": "SHA-256=" + hashlib.sha256(zip_bytes).hexdigest(),
    }
    storage = FileStorage(filename="crate.zip", stream=io.BytesIO(zip_bytes),
                          content_type="application/zip")
    resp = client.post(url_for("weko_swordserver.post_service_document"),
                       data={"file": storage},
                       content_type="multipart/form-data", headers=headers)
    _dump("1. POST /sword/service-document (Workflow, 承認待ち)", resp)

    body = json.loads(resp.get_data(as_text=True))
    recid = body["@id"].rstrip("/").split("/")[-1]
    activity_id = None
    for link in body.get("links", []):
        if "/workflow/activity/detail/" in link.get("@id", ""):
            activity_id = link["@id"].split("/workflow/activity/detail/")[1]
            if "?" in activity_id:
                activity_id = activity_id.split("?")[0]
            break
    print("\n[info] recid={} activity_id={}".format(recid, activity_id))

    get_headers = {"Authorization": "Bearer {}".format(token)}

    # ---- 2. GET (承認待ち) ----
    resp = client.get(
        url_for("weko_swordserver.get_status_document", recid=recid),
        headers=get_headers)
    _dump("2. GET /sword/deposit/{} (承認待ち)".format(recid), resp)

    # ---- 3. 承認 ----
    activity = _Activity.query.filter_by(activity_id=activity_id).first()
    print("\n[info] current action_id before approval = {}".format(
        activity.action_id if activity else None))
    login_user_via_session(client=client, email=users[0]["email"])  # sysadmin
    approve = client.post(
        "/workflow/activity/action/{}/{}".format(activity_id, activity.action_id),
        data=json.dumps({"action_version": "1.0.0", "commond": "approved"}),
        content_type="application/json")
    print("[info] approval response: {} {}".format(
        approve.status, approve.get_data(as_text=True)[:300]))
    activity = _Activity.query.filter_by(activity_id=activity_id).first()
    print("[info] current action_id after approval = {}".format(
        activity.action_id if activity else None))

    # ---- 4. GET (承認後) ----
    # 以降は OAuth トークンで認証されるため再ログインは不要
    resp = client.get(
        url_for("weko_swordserver.get_status_document", recid=recid),
        headers=get_headers)
    _dump("4. GET /sword/deposit/{} (承認後)".format(recid), resp)

    # ---- 5. DELETE (削除フロー = 承認あり) ----
    resp = client.delete(
        url_for("weko_swordserver.delete_object", recid=recid),
        headers=get_headers)
    _dump("5. DELETE /sword/deposit/{} (Workflow)".format(recid), resp)

    # ---- 6. 削除アクティビティを承認して GET ----
    del_activity_id = resp.headers.get("Location", "").split(
        "/workflow/activity/detail/")[-1].split("?")[0]
    del_activity = _Activity.query.filter_by(
        activity_id=del_activity_id).first()
    print("\n[info] delete activity={} action_id={}".format(
        del_activity_id, del_activity.action_id if del_activity else None))
    login_user_via_session(client=client, email=users[0]["email"])  # sysadmin
    approve = client.post(
        "/workflow/activity/action/{}/{}".format(
            del_activity_id, del_activity.action_id),
        data=json.dumps({"action_version": "1.0.0", "commond": "approved"}),
        content_type="application/json")
    print("[info] delete approval response: {} {}".format(
        approve.status, approve.get_data(as_text=True)[:300]))
    del_activity = _Activity.query.filter_by(
        activity_id=del_activity_id).first()
    print("[info] delete activity action_id after approval = {} status={}".format(
        del_activity.action_id if del_activity else None,
        del_activity.activity_status if del_activity else None))
    from invenio_pidstore.models import PersistentIdentifier as _PID
    for p in _PID.query.filter_by(pid_value=str(recid)).all():
        print("[info] pid {} type={} status={}".format(
            p.pid_value, p.pid_type, p.status))

    resp = client.get(
        url_for("weko_swordserver.get_status_document", recid=recid),
        headers=get_headers)
    _dump("6. GET /sword/deposit/{} (削除承認後)".format(recid), resp)
