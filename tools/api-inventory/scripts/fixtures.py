# -*- coding: utf-8 -*-
"""Phase 7-a: 動的検証(probe)に必要な最小テストコーパスを実機に投入する。

    python3 fixtures.py --out fixtures.json

`install.sh` は `populate-instance.sh:179` の `demo init` がコメントアウトされているため、
ロール・ユーザ・アイテムタイプ・インデックスツリーは入るが **レコードが0件**になる。
このままでは到達可否(dynamic_verified)を測れない。本スクリプトが最小限を補う。

投入するもの:
  - 既知パスワードのユーザ(既存アカウントのパスワードを揃える)
  - 公開インデックスとその配下の子インデックス
  - 公開アイテム / 非公開アイテム / 他人所有の非公開アイテム(いずれもファイル実体付き)
  - 全スコープの個人アクセストークン
  - Community / Group(担当外リソースの越境検証用)
  - 上記の健全性の回復(削除済みになったインデックスを戻す)

生成したIDは fixtures.json に書き出し、probe.py がプレースホルダ解決に使う。

冪等: 既存の値があれば再利用し、無ければ作る。CI で毎回流してよい。
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snapshot import resolve_container, sh  # noqa: E402  同ディレクトリのヘルパを再利用

PASSWORD = 'Passw0rd!123'

PAYLOAD = r'''
# -*- coding: utf-8 -*-
import base64, json, io, traceback, uuid as _uuid
from flask import current_app
from invenio_db import db

PASSWORD = "%(password)s"
OUT = {"password": PASSWORD, "users": {}, "records": {}, "file": {},
       "index": None, "index_child": None, "index_health": None,
       "token": None, "community": None, "group": None,
       "activity": None, "activity_other": None, "ids": {}, "errors": []}

# 1x1 透明PNG(75B)。ファイル露出検証はバイト列が取れれば十分
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def step(name):
    """各投入を独立させる。1つ失敗しても残りは進める。"""
    def deco(fn):
        try:
            fn()
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            OUT["errors"].append("%%s: %%s: %%s" %% (name, type(exc).__name__, exc))
            traceback.print_exc()
        return fn
    return deco


# ---------------------------------------------------------------- ユーザ
@step("users")
def _users():
    from invenio_accounts.models import User
    from flask_security.utils import hash_password
    for email in ["wekosoftware@nii.ac.jp", "repoadmin@example.org",
                  "contributor@example.org", "user@example.org",
                  "comadmin@example.org"]:
        u = User.query.filter_by(email=email).one_or_none()
        if u is None:
            continue
        u.password = hash_password(PASSWORD)
        u.active = True
        db.session.add(u)
        roles = [r.name for r in u.roles]
        OUT["users"][email] = {"id": u.id, "roles": roles}


# ---------------------------------------------------------------- インデックス
@step("index")
def _index():
    from weko_index_tree.models import Index
    idx = Index.query.filter_by(index_name_english="APIInventory Public").one_or_none()
    if idx is None:
        # (parent, position) に一意制約(uix_position)があるため空き position を取る
        used = [i.position for i in Index.query.filter_by(parent=0).all()]
        pos = (max(used) + 1) if used else 0
        idx = Index(id=900001, parent=0, position=pos,
                    index_name="APIインベントリ検証用", index_name_english="APIInventory Public",
                    public_state=True, harvest_public_state=True,
                    browsing_role="3,-98,-99", contribute_role="1,2,3,4,-98,-99",
                    public_date=None, owner_user_id=1)
        db.session.add(idx)
        db.session.flush()
    # 冪等かつ自己修復。--allow-writes の probe はインデックス削除系も叩くため、
    # 測定のたびに is_deleted が立ちうる。放置すると次回以降の測定が壊れる:
    # get_child_list_recursive は is_deleted を除外したうえで .one() するので、
    # コミュニティのルートが削除済みだと NoResultFound になり、
    # has_comadmin_permission -> check_created_id が例外を投げて 500 になる。
    idx.is_deleted = False
    idx.parent = 0
    idx.public_state = True
    idx.harvest_public_state = True
    db.session.add(idx)
    db.session.flush()
    OUT["index"] = int(idx.id)

    # 子インデックス。コミュニティ配下の判定は「ルートと一致するか」ではなく
    # 「部分木に含まれるか」なので、深さ1では再帰の検証にならない。
    child = Index.query.filter_by(
        index_name_english="APIInventory Child").one_or_none()
    if child is None:
        used = [i.position for i in Index.query.filter_by(parent=idx.id).all()]
        pos = (max(used) + 1) if used else 0
        child = Index(id=900011, parent=idx.id, position=pos,
                      index_name="APIインベントリ検証用(子)",
                      index_name_english="APIInventory Child",
                      public_state=True, harvest_public_state=True,
                      browsing_role="3,-98,-99", contribute_role="1,2,3,4,-98,-99",
                      public_date=None, owner_user_id=1)
        db.session.add(child)
        db.session.flush()
    child.is_deleted = False
    child.parent = idx.id
    child.public_state = True
    child.harvest_public_state = True
    db.session.add(child)
    db.session.flush()
    OUT["index_child"] = int(child.id)


# ---------------------------------------------------------------- レコード
def _make_record(recid, owner_id, publish_status, title, with_file,
                 index_key="index"):
    """PID(recid/depid/parent)+RecordMetadata+バケットを作る。

    合成レコードなのでアイテムタイプ固有フィールドは入れていない。
    詳細画面のレンダリングは 500 になりうるが、認可を通過したか(到達したか)の
    判定はできる。
    """
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus
    from invenio_records.models import RecordMetadata
    from invenio_files_rest.models import Location, Bucket, ObjectVersion
    from invenio_records_files.models import RecordsBuckets

    existing = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value=str(recid)).one_or_none()
    if existing is not None:
        # 冪等かつ自己修復: 既存を再利用しつつ、重要フィールドは毎回入れ直す。
        # 先行するステップ(インデックス作成など)が失敗した回に作られたレコードは
        # path が空のままになり、check_index_permissions が通らず公開アイテムでも
        # 未認証で読めない。再実行で直るようにする。
        from sqlalchemy.orm.attributes import flag_modified
        rm = RecordMetadata.query.get(existing.object_uuid)
        js = dict(rm.json or {})
        idx = OUT.get(index_key)
        js["path"] = [str(idx)] if idx else js.get("path", [])
        js["owner"] = str(owner_id)
        js["publish_status"] = publish_status
        js.setdefault("pubdate", {"attribute_name": "PubDate",
                                  "attribute_value": "2026-01-01"})
        # weko_shared_ids が無いと weko_records_ui.permissions.check_created_id が
        # len(None) で TypeError になり、詳細画面が 500 になる(v2.0.3/v2.1.0 とも)。
        # 新規作成側では入れているが、この自己修復パスで入れ忘れていた。
        js.setdefault("weko_shared_ids", [])
        rm.json = js
        flag_modified(rm, "json")
        db.session.add(rm)
        rb = RecordsBuckets.query.filter_by(record_id=rm.id).first()
        bucket_id = str(rb.bucket_id) if rb else None
        finfo = None
        if rb is not None:
            ov = ObjectVersion.query.filter_by(
                bucket_id=rb.bucket_id, key="secret.png", is_head=True).first()
            if ov is not None:
                finfo = _file_info(rb.bucket_id, ov)
        return rm, bucket_id, finfo

    uid = _uuid.uuid4()
    loc = Location.get_default() or Location.query.first()
    bucket = Bucket.create(loc)
    db.session.flush()

    js = {
        "_oai": {"id": "oai:weko3.example.org:%%08d" %% recid},
        "path": [str(OUT.get(index_key))] if OUT.get(index_key) else [],
        "owner": str(owner_id),
        "recid": str(recid),
        "title": [title],
        "item_title": title,
        "item_type_id": "1",
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2026-01-01"},
        "publish_date": "2026-01-01",
        "publish_status": publish_status,
        "weko_shared_ids": [],
        "_buckets": {"deposit": str(bucket.id)},
        "_deposit": {
            "id": str(recid),
            "pid": {"type": "depid", "value": str(recid), "revision_id": 0},
            "owner": str(owner_id), "owners": [owner_id],
            "created_by": owner_id, "status": "published",
        },
    }
    rm = RecordMetadata(id=uid, json=js, version_id=1)
    db.session.add(rm)
    db.session.flush()
    RecordsBuckets.create(record=rm, bucket=bucket)

    for t, v in (("recid", str(recid)), ("depid", str(recid)),
                 ("parent", "parent:%%s" %% recid)):
        if PersistentIdentifier.query.filter_by(pid_type=t, pid_value=v).one_or_none() is None:
            PersistentIdentifier.create(t, v, object_type="rec", object_uuid=uid,
                                        status=PIDStatus.REGISTERED)

    finfo = None
    if with_file:
        ov = ObjectVersion.create(bucket, "secret.png", stream=io.BytesIO(PNG),
                                  size=len(PNG))
        db.session.flush()
        finfo = _file_info(bucket.id, ov)
    return rm, str(bucket.id), finfo


def _file_info(bucket_id, ov):
    """IIIF は bucket:version:key の三つ組を要求するのでそれも組み立てる。"""
    return {"key": ov.key,
            "bucket": str(bucket_id),
            "version_id": str(ov.version_id),
            "uuid_triplet": "%%s:%%s:%%s" %% (bucket_id, ov.version_id, ov.key),
            "size": ov.file.size if ov.file else None}


@step("records")
def _records():
    owner_c = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    owner_u = OUT["users"].get("user@example.org", {}).get("id", 4)
    specs = [
        ("public",       900001, owner_c, "0", "APIInventory 公開アイテム",   False,
         "index"),
        ("private",      900002, owner_c, "1", "APIInventory 非公開アイテム", True,
         "index"),
        # 他人所有だけ子インデックス配下に置く。コミュニティ管理者は
        # 「自分の担当インデックスの部分木にある他人のアイテム」を扱えるので、
        # 深さ1のままだとその判定を測れない。
        ("other_owner",  900003, owner_u, "1", "APIInventory 他人所有",       True,
         "index_child"),
    ]
    for name, recid, owner, pub, title, with_file, index_key in specs:
        rm, bucket, finfo = _make_record(recid, owner, pub, title, with_file,
                                         index_key)
        OUT["records"][name] = {"recid": recid, "uuid": str(rm.id),
                                "owner": owner, "publish_status": pub,
                                "bucket": bucket, "file": finfo}
        # 非公開アイテムのファイルが露出検証(IIIF/files-rest)の主対象
        if finfo and name == "private":
            OUT["file"] = finfo


# ---------------------------------------------------------------- PIDVersioning
@step("pid_versioning")
def _versioning():
    """親PIDから last_child が解決する状態にする(records系の到達に必要)。"""
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_pidrelations.contrib.versioning import PIDVersioning
    for r in OUT["records"].values():
        child = PersistentIdentifier.query.filter_by(
            pid_type="recid", pid_value=str(r["recid"])).one()
        parent = PersistentIdentifier.query.filter_by(
            pid_type="parent", pid_value="parent:%%s" %% r["recid"]).one()
        pv = PIDVersioning(parent=parent)
        if pv.last_child is None:
            pv.insert_child(child)


# ---------------------------------------------------------------- OAuthトークン
@step("oauth_token")
def _token():
    from invenio_oauth2server.models import Token
    uid = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    scopes = list(current_app.extensions["invenio-oauth2server"].scopes.keys())
    t = Token.create_personal("api-inventory-probe", uid, scopes=scopes,
                              is_internal=True)
    OUT["token"] = {"access_token": t.access_token, "user_id": uid,
                    "scopes": scopes}


# ---------------------------------------------------------------- Community
@step("community")
def _community():
    from invenio_communities.models import Community
    from invenio_accounts.models import Role
    from weko_index_tree.models import Index
    cid = "apiinv"
    c = Community.query.get(cid)
    if c is None:
        role = Role.query.filter_by(name="Community Administrator").first()
        owner = OUT["users"].get("comadmin@example.org", {}).get("id", 5)
        # root_node_id は NOT NULL。専用インデックスが作れていなければ既存を使う
        root = OUT["index"]
        if root is None:
            any_idx = Index.query.first()
            root = int(any_idx.id) if any_idx else None
        if root is None:
            raise RuntimeError("インデックスが1件も無いため Community を作れない")
        c = Community(id=cid, id_role=(role.id if role else None), id_user=owner,
                      title="APIInventory Community", description="probe用",
                      root_node_id=root)
        db.session.add(c)
        db.session.flush()
    # 自己修復: ルートに指しているインデックスが消えていたら差し替える。
    # root_node_id は NOT NULL だが、参照先の存在は保証されていない。
    if OUT["index"] is not None:
        root_idx = Index.query.filter_by(id=c.root_node_id).one_or_none()
        if root_idx is None:
            c.root_node_id = OUT["index"]
            db.session.add(c)
            db.session.flush()
    OUT["community"] = {"id": cid, "owner": c.id_user,
                        "root_node_id": int(c.root_node_id)}


# ------------------------------------------------ インデックスの健全性
@step("index_health")
def _index_health():
    """コミュニティのルートから部分木を辿れる状態かを確かめ、壊れていれば直す。

    コミュニティ管理者の認可判定はここを通る。辿れない状態のまま測ると、
    その識別子の結果が 500 や 403 に化けて台帳の roles 列が実態とずれる。
    """
    from invenio_communities.models import Community
    from weko_index_tree.models import Index
    from weko_index_tree.api import Indexes

    repaired, broken = [], []
    for c in Community.query.all():
        idx = Index.query.filter_by(id=c.root_node_id).one_or_none()
        if idx is None:
            if OUT["index"] is None:
                broken.append("%%s: root_node_id=%%s が存在しない" %% (c.id, c.root_node_id))
                continue
            c.root_node_id = OUT["index"]
            db.session.add(c)
            repaired.append("%%s: ルートを %%s に差し替え" %% (c.id, OUT["index"]))
        elif idx.is_deleted:
            idx.is_deleted = False
            db.session.add(idx)
            repaired.append("%%s: ルート %%s の削除フラグを戻した" %% (c.id, idx.id))
    db.session.flush()

    # 直したうえで、実際に辿れることを確認する
    for c in Community.query.all():
        try:
            Indexes.get_child_list_recursive(c.root_node_id)
        except Exception as exc:
            broken.append("%%s: root=%%s %%s: %%s"
                          %% (c.id, c.root_node_id, type(exc).__name__, exc))
    OUT["index_health"] = {"repaired": repaired, "broken": broken}
    for m in repaired:
        OUT["errors"].append("index_health 修復(非致命): %%s" %% m)
    for m in broken:
        OUT["errors"].append("index_health 未解決: %%s" %% m)


# ---------------------------------------------------------------- Group
@step("group")
def _group():
    from weko_groups.models import Group
    from invenio_accounts.models import User
    name = "APIInventory Group"
    g = Group.query.filter_by(name=name).one_or_none()
    if g is None:
        admin = User.query.filter_by(email="contributor@example.org").one_or_none()
        g = Group.create(name=name, description="probe用",
                         admins=[admin] if admin else [])
    OUT["group"] = {"id": g.id, "name": name}


# ---------------------------------------------------------------- ワークフロー
@step("activity")
def _activity():
    """ワークフローの activity を2件作る。

    no.601-636 のワークフロー系は `<activity_id>` を要求するため、これが無いと
    probe が「未解決プレースホルダ」で skip する。所有者チェック欠落の検証には
    **他人所有の activity** が要るので2件作る。
    """
    from weko_workflow.api import WorkActivity
    from weko_workflow.models import Activity as _Act, WorkFlow

    wf = WorkFlow.query.first()
    if wf is None:
        raise RuntimeError("ワークフロー定義が無い(install.sh の defaultworkflow.sql 未投入)")

    def ensure(title, uid, key):
        act = _Act.query.filter_by(title=title).first()
        if act is None:
            act = WorkActivity().init_activity({
                "workflow_id": wf.id,
                "flow_id": wf.flow_id,
                "itemtype_id": wf.itemtype_id,
                "activity_login_user": uid,
                "activity_update_user": uid,
                "title": title,
            })
            db.session.flush()
        OUT[key] = {"activity_id": act.activity_id,
                    "owner": uid,
                    "action_id": act.action_id,
                    "workflow_id": wf.id,
                    "flow_id": str(wf.flow_id)}

    own = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    other = OUT["users"].get("user@example.org", {}).get("id", 4)
    ensure("APIInventory 検証用(自分)", own, "activity")
    ensure("APIInventory 検証用(他人所有)", other, "activity_other")


# ---------------------------------------------------------------- 著者
@step("author")
def _author():
    """著者を1件作る(no.243-267 の <identifier> 用)。authors は初期状態で0件。"""
    from weko_authors.models import Authors
    a = Authors.query.filter_by(gather_flg=0).first()
    if a is None:
        a = Authors(gather_flg=0, is_deleted=False)
        db.session.add(a)
        db.session.flush()
    OUT["ids"]["author_id"] = int(a.id)


# ---------------------------------------------- ウィジェット/ページ/ジャーナル
@step("gridlayout")
def _gridlayout():
    """widget_items / widget_design_page / journal を1件ずつ作る。

    install.sh はこれらを投入しないため空で、<widget_id> / <page_id> /
    <journal_id> を含む行(no.281/282/295/297/298/359)が測れなかった。
    repository_id は Root Index を使う(WEKO ではリポジトリ識別子に
    インデックスIDを充てている)。
    """
    from sqlalchemy import text
    ins = lambda sql, **kw: db.session.execute(text(sql), kw)   # noqa: E731
    repo = "Root Index"

    if db.session.execute(text("SELECT count(*) FROM widget_items")).scalar() == 0:
        wtype = db.session.execute(
            text("SELECT type_id FROM widget_type LIMIT 1")).scalar() or "Free description"
        ins("""INSERT INTO widget_items
               (created, updated, widget_id, repository_id, widget_type,
                settings, is_enabled, is_deleted, locked)
               VALUES (now(), now(), 900001, :r, :t, '{}', true, false, false)""",
            r=repo, t=wtype)

    if db.session.execute(text("SELECT count(*) FROM widget_design_page")).scalar() == 0:
        ins("""INSERT INTO widget_design_page
               (id, title, repository_id, url, template_name, settings, is_main_layout)
               VALUES (900001, 'APIInventory 検証用', :r, '/apiinv', NULL, '{}', false)""",
            r=repo)

    if db.session.execute(text("SELECT count(*) FROM journal")).scalar() == 0:
        idx = OUT.get("index") or db.session.execute(
            text("SELECT id FROM index LIMIT 1")).scalar()
        ins("""INSERT INTO journal
               (created, updated, id, index_id, publication_title, is_output)
               VALUES (now(), now(), 900001, :i, 'APIInventory 検証用ジャーナル', true)""",
            i=idx)


# ------------------------------------------------- 既存データのID参照(作成しない)
@step("lookups")
def _lookups():
    """probe のプレースホルダ解決に使う既存レコードのIDを拾う。

    install.sh が投入する初期データ(アイテムタイプ・プロパティ・メールテンプレート・
    著者プレフィクス/所属・ファセット検索・OAuthクライアント)は作らずに参照する。
    作ってしまうと実環境の初期データと二重になるため。
    """
    from sqlalchemy import text
    q = lambda sql: db.session.execute(text(sql)).first()   # noqa: E731
    for key, sql in (
        ("item_type_id",     "SELECT id FROM item_type WHERE is_deleted=false ORDER BY id LIMIT 1"),
        ("property_id",      "SELECT id FROM item_type_property ORDER BY id LIMIT 1"),
        ("prefix_id",        "SELECT id FROM authors_prefix_settings ORDER BY id LIMIT 1"),
        ("affiliation_id",   "SELECT id FROM authors_affiliation_settings ORDER BY id LIMIT 1"),
        ("mail_template_id", "SELECT id FROM mail_templates ORDER BY id LIMIT 1"),
        ("facet_search_id",  "SELECT id FROM facet_search_setting ORDER BY id LIMIT 1"),
        ("oauth_client_id",  "SELECT client_id FROM oauth2server_client LIMIT 1"),
        ("oauth_token_id",   "SELECT id FROM oauth2server_token LIMIT 1"),
        ("schema_name",      "SELECT schema_name FROM oaiserver_schema ORDER BY schema_name LIMIT 1"),
        ("widget_id",        "SELECT widget_id FROM widget_items ORDER BY widget_id LIMIT 1"),
        ("widget_page_id",   "SELECT id FROM widget_design_page ORDER BY id LIMIT 1"),
        ("journal_id",       "SELECT id FROM journal ORDER BY id LIMIT 1"),
    ):
        try:
            r = q(sql)
            if r is not None and r[0] is not None:
                OUT["ids"][key] = str(r[0])
        except Exception as exc:
            OUT["errors"].append("lookup %%s: %%s" %% (key, exc))


# ---------------------------------------------------------------- ES反映
@step("reindex")
def _reindex():
    from invenio_indexer.api import RecordIndexer
    from invenio_records.api import Record
    import uuid as _u
    idx = RecordIndexer()
    for r in OUT["records"].values():
        try:
            idx.index(Record.get_record(_u.UUID(r["uuid"])))
        except Exception as exc:
            # ES反映は検索系エンドポイントの hits にしか効かない。
            # 到達可否(dynamic_verified)の判定には不要なので失敗しても続行する。
            OUT["errors"].append("reindex %%s(非致命): %%s" %% (r["recid"], exc))


json.dump(OUT, open("/tmp/_fixtures.json", "w"), ensure_ascii=False, indent=1)
print("FIXTURES_OK errors=%%d" %% len(OUT["errors"]))
for e in OUT["errors"]:
    print("  ERR", e)
'''


def main():
    p = argparse.ArgumentParser(description='動的検証用フィクスチャを投入する')
    p.add_argument('--out', default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures.json'))
    p.add_argument('--container', default='',
                   help='投入先コンテナ(省略時は compose ラベルから自動検出)')
    p.add_argument('--password', default=PASSWORD)
    a = p.parse_args()

    container = resolve_container(a.container)
    import tempfile
    work = tempfile.mkdtemp(prefix='api-fixtures-')
    local = os.path.join(work, '_fixtures_payload.py')
    with open(local, 'w', encoding='utf-8') as f:
        f.write(PAYLOAD % {'password': a.password})

    r = sh(['docker', 'cp', local, f'{container}:/tmp/_fixtures_payload.py'])
    if r.returncode:
        sys.exit(f'docker cp 失敗: {r.stderr.strip()}')
    r = sh([
        'docker', 'exec', container, 'bash', '-lc',
        'source ~/.virtualenvs/invenio/bin/activate; cd /code; '
        'invenio shell -c "exec(open(\'/tmp/_fixtures_payload.py\').read())"',
    ])
    if 'FIXTURES_OK' not in r.stdout:
        sys.exit(f'フィクスチャ投入に失敗:\n{r.stdout[-3000:]}\n{r.stderr[-2000:]}')
    for line in r.stdout.splitlines():
        if line.startswith('FIXTURES_OK') or line.strip().startswith('ERR'):
            print('  ' + line.strip())

    r = sh(['docker', 'cp', f'{container}:/tmp/_fixtures.json', a.out])
    if r.returncode:
        sys.exit(f'fixtures.json の取得に失敗: {r.stderr.strip()}')
    data = json.load(open(a.out, encoding='utf-8'))
    print(f"\n{a.out}")
    print(f"  users={len(data['users'])} records={len(data['records'])} "
          f"index={data['index']}/{data.get('index_child')} "
          f"file={'あり' if data['file'] else 'なし'} "
          f"token={'あり' if data['token'] else 'なし'} "
          f"community={'あり' if data['community'] else 'なし'} "
          f"group={'あり' if data['group'] else 'なし'} "
          f"activity={'あり' if data.get('activity') else 'なし'} "
          f"ids={len(data.get('ids') or {})} "
          f"errors={len(data['errors'])}")
    health = data.get('index_health') or {}
    if health.get('repaired'):
        print('  ※ インデックスを修復しました(前回の測定で壊れた分):')
        for m in health['repaired']:
            print(f'      {m}')
    if health.get('broken'):
        print('  ※ コミュニティのルートから部分木を辿れません。'
              'コミュニティ管理者の測定値は信用できません:')
        for m in health['broken']:
            print(f'      {m}')
    if data['errors']:
        print('  ※ 失敗した投入があります。probe の測定範囲が狭まります。')


if __name__ == '__main__':
    main()
