# -*- coding: utf-8 -*-
"""Phase 7-a: 動的検証(probe)に必要な最小テストコーパスを実機に投入する。

    python3 fixtures.py --out fixtures.json

`install.sh` は `populate-instance.sh:179` の `demo init` がコメントアウトされているため、
ロール・ユーザ・アイテムタイプ・インデックスツリーは入るが **レコードが0件**になる。
このままでは到達可否(dynamic_verified)を測れない。本スクリプトが最小限を補う。

投入するもの:
  - 既知パスワードのユーザ(既存アカウントのパスワードを揃える)
  - 公開インデックス
  - 公開アイテム / 非公開アイテム / 他人所有の非公開アイテム(いずれもファイル実体付き)
  - 全スコープの個人アクセストークン
  - Community / Group(担当外リソースの越境検証用)

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
       "index": None, "token": None, "community": None, "group": None,
       "errors": []}

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
    OUT["index"] = int(idx.id)


# ---------------------------------------------------------------- レコード
def _make_record(recid, owner_id, publish_status, title, with_file):
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
        js["path"] = [str(OUT["index"])] if OUT["index"] else js.get("path", [])
        js["owner"] = str(owner_id)
        js["publish_status"] = publish_status
        js.setdefault("pubdate", {"attribute_name": "PubDate",
                                  "attribute_value": "2026-01-01"})
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
        "path": [str(OUT["index"])] if OUT["index"] else [],
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
        ("public",       900001, owner_c, "0", "APIInventory 公開アイテム",   False),
        ("private",      900002, owner_c, "1", "APIInventory 非公開アイテム", True),
        ("other_owner",  900003, owner_u, "1", "APIInventory 他人所有",       True),
    ]
    for name, recid, owner, pub, title, with_file in specs:
        rm, bucket, finfo = _make_record(recid, owner, pub, title, with_file)
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
    OUT["community"] = {"id": cid, "owner": c.id_user}


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
          f"index={data['index']} file={'あり' if data['file'] else 'なし'} "
          f"token={'あり' if data['token'] else 'なし'} "
          f"community={'あり' if data['community'] else 'なし'} "
          f"group={'あり' if data['group'] else 'なし'} "
          f"errors={len(data['errors'])}")
    if data['errors']:
        print('  ※ 失敗した投入があります。probe の測定範囲が狭まります。')


if __name__ == '__main__':
    main()
