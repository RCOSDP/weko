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

生成物 ``fixtures.json`` に秘密は入らない。パスワードは本スクリプトの
定数（既に公開）で、アクセストークンも固定のダミー値にしてある。
*測定対象の記録として台帳リポジトリで追跡する。*
測定条件(measure_profile.json)だけ残っていても、その条件を
どの recid / バケット / インデックスに当てたかが分からないと
結果を読み解けないため。
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snapshot import resolve_container, sh  # noqa: E402  同ディレクトリのヘルパを再利用

PASSWORD = 'Passw0rd!123'
DUMMY_TOKEN = 'apiinv-probe-token-0000000000000000000000000000'
"""固定のダミー。生成値だと実行のたびに fixtures.json が変わってしまう。"""

PAYLOAD = r'''
# -*- coding: utf-8 -*-
import base64, json, io, traceback, uuid as _uuid
from flask import current_app
from invenio_db import db

PASSWORD = "%(password)s"
SCALE = %(scale)d
DUMMY_TOKEN = "%(token)s"
OUT = {"password": PASSWORD, "users": {}, "records": {}, "file": {},
       "index": None, "index_child": None, "index_health": None,
       "token": None, "community": None, "group": None,
       "activity": None, "activity_other": None, "ids": {}, "errors": []}

# 1x1 透明PNG(75B)。ファイル露出検証はバイト列が取れれば十分
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


# アイテムタイプは「デフォルトアイテムタイプ（フル）」に統一する。
# 1〜14 は harvesting_type=t のハーベスト用で、登録アイテムには使わない。
ITEM_TYPE_ID = 30002

_SCHEMA_CACHE = {}


def _item_schema():
    """アイテムタイプ 30002 のスキーマ。項目は手書きせずここから引く。"""
    if "props" not in _SCHEMA_CACHE:
        from weko_records.models import ItemType
        it = ItemType.query.get(ITEM_TYPE_ID)
        if it is None:
            raise RuntimeError(
                "アイテムタイプ %%d が無い。install.sh を先に流すこと" %% ITEM_TYPE_ID)
        _SCHEMA_CACHE["props"] = (it.schema or {}).get("properties", {})
    return _SCHEMA_CACHE["props"]


def _sample(key, node):
    """文字列項目のダミー値。キー名と format から見当を付ける。"""
    fmt = node.get("format", "")
    k = key.lower()
    if "date" in k or fmt in ("date", "datetime"):
        return "2026-01-01"
    if "uri" in k or "url" in k or "identifier" in k and "reg" not in k:
        return "https://example.org/demo"
    if "mail" in k:
        return "demo@example.org"
    if "lang" in k:
        return "ja"
    if fmt in ("integer", "number"):
        return "1"
    ttl = node.get("title_i18n", {}).get("ja") or node.get("title") or key
    return "デモ値(%%s)" %% ttl


def _gen(node, key=""):
    """スキーマの1ノードから、形の合ったダミー値を作る。"""
    if "enum" in node:
        vals = [v for v in node["enum"] if v is not None]
        return vals[0] if vals else None
    t = node.get("type")
    if t == "array":
        return [_gen(node.get("items", {}), key)]
    if t == "object":
        return {k: _gen(v, k) for k, v in (node.get("properties") or {}).items()}
    if t in ("number", "integer"):
        return 1
    if t == "boolean":
        return True
    return _sample(key, node)


def build_metadata(title, ja, en, rtype, ruri, pub, full=False):
    """アイテムタイプ 30002 の項目を組み立てる。

    ``full=True`` でスキーマ上の全項目を埋める。項目を手書きすると
    アイテムタイプの変更に追随できないので、スキーマから生成する。

    records_metadata 側は attribute_name / attribute_value_mlt で包む形、
    item_metadata 側は登録フォームの生の形。両方を返す。
    """
    props = _item_schema()
    raw = {
        "item_30002_title0": [
            {"subitem_title": title, "subitem_title_language": "ja"}],
        "item_30002_creator2": [{"creatorNames": [
            {"creatorName": ja, "creatorNameLang": "ja"},
            {"creatorName": en, "creatorNameLang": "en"}]}],
        "item_30002_resource_type13": {"resourcetype": rtype,
                                       "resourceuri": ruri},
        "item_30002_language12": [{"subitem_language": "jpn"}],
        "item_30002_publisher10": [
            {"subitem_publisher": "テスト大学",
             "subitem_publisher_language": "ja"}],
    }
    if full:
        for k, node in props.items():
            # system_* はシステムが埋める項目。pubdate は別途入れている
            if k.startswith("system_") or k == "pubdate" or k in raw:
                continue
            raw[k] = _gen(node, k)
    raw["pubdate"] = pub
    raw["$schema"] = "/items/jsonschema/%%d" %% ITEM_TYPE_ID

    wrapped = {}
    for k, v in raw.items():
        if not k.startswith("item_%%d_" %% ITEM_TYPE_ID):
            continue
        name = (props.get(k, {}).get("title")
                or props.get(k, {}).get("title_i18n", {}).get("en") or k)
        wrapped[k] = {"attribute_name": name,
                      "attribute_value_mlt": v if isinstance(v, list) else [v]}
    return wrapped, raw

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
                    index_name="テスト大学 学術情報リポジトリ",
                    index_name_english="APIInventory Public",
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

    # 子インデックス。機関リポジトリらしい資料種別で分ける。
    # コミュニティ配下の判定は「ルートと一致するか」ではなく
    # 「部分木に含まれるか」なので、深さ1では再帰の検証にならない。
    # 非公開インデックスを1つ混ぜてあるのは、公開状態で結果が変わる
    # エンドポイント(検索・インデックスツリー系)を測れるようにするため。
    children = [
        (900011, "紀要論文",     "Departmental Bulletin Paper", True),
        (900012, "学位論文",     "Thesis",                      True),
        (900013, "研究報告書",   "Research Report",             True),
        (900014, "会議発表資料", "Conference Paper",            True),
        (900015, "非公開資料",   "Restricted",                  False),
    ]
    OUT["indexes"] = {}
    for cid, ja, en, public in children:
        c = Index.query.filter_by(id=cid).one_or_none()
        if c is None:
            used = [i.position for i in Index.query.filter_by(parent=idx.id).all()]
            pos = (max(used) + 1) if used else 0
            c = Index(id=cid, parent=idx.id, position=pos,
                      index_name=ja, index_name_english=en,
                      public_state=public, harvest_public_state=public,
                      browsing_role="3,-98,-99",
                      contribute_role="1,2,3,4,-98,-99",
                      public_date=None, owner_user_id=1)
            db.session.add(c)
            db.session.flush()
        c.is_deleted = False
        c.parent = idx.id
        c.index_name = ja
        c.index_name_english = en
        c.public_state = public
        c.harvest_public_state = public
        db.session.add(c)
        OUT["indexes"][en] = int(c.id)
    db.session.flush()
    # 従来のキー。他人所有レコードの置き場所として probe が参照する
    OUT["index_child"] = OUT["indexes"]["Departmental Bulletin Paper"]


# ---------------------------------------------------------------- レコード
def _make_record(recid, owner_id, publish_status, title, with_file,
                 index_key="index", item_type_id=None,
                 rtype="journal article",
                 ruri="http://purl.org/coar/resource_type/c_6501",
                 full=False):
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
        js.setdefault("relation_version_is_last", True)
        js.setdefault("owners", [owner_id])
        js.setdefault("author_link", [])
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

    item_type_id = item_type_id or ITEM_TYPE_ID
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
        "item_type_id": str(item_type_id or ITEM_TYPE_ID),
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2026-01-01"},
        "publish_date": "2026-01-01",
        "publish_status": publish_status,
        "weko_shared_ids": [],
        # 詳細画面はこの3つを見る。無いと権限を通っても 404 になる
        # (既存の実レコードと突き合わせて判明)
        "relation_version_is_last": True,
        "owners": [owner_id],
        "author_link": [],
        "_buckets": {"deposit": str(bucket.id)},
        "_deposit": {
            "id": str(recid),
            "pid": {"type": "depid", "value": str(recid), "revision_id": 0},
            "owner": str(owner_id), "owners": [owner_id],
            "created_by": owner_id, "status": "published",
        },
    }
    wrapped, raw = build_metadata(title, "山田 太郎", "Yamada, Taro",
                                  rtype, ruri, "2026-01-01", full=full)
    js.update(wrapped)
    rm = RecordMetadata(id=uid, json=js, version_id=1)
    db.session.add(rm)
    db.session.flush()
    RecordsBuckets.create(record=rm, bucket=bucket)
    _item_metadata(uid, item_type_id, title, owner_id, raw)

    db.session.flush()
    # PID とバージョン構造。呼び出し順に依存しないようここで作る
    _link_version(recid, uid)

    finfo = None
    if with_file:
        ov = ObjectVersion.create(bucket, "secret.png", stream=io.BytesIO(PNG),
                                  size=len(PNG))
        db.session.flush()
        finfo = _file_info(bucket.id, ov)
    return rm, str(bucket.id), finfo


def _link_version(recid, uid):
    """実レコードと同じ PID 構造を作る。

    詳細画面は次の判定で 404 にする(weko_records_ui/views.py)::

        pid_ver = PIDVersioning(child=pid)
        if not pid_ver.exists or pid_ver.is_last_child:
            abort(404)

    つまり *base の recid が最後の子であってはいけない*。実データは
    parent:<n> の下に <n> / <n>.0 / <n>.1 をぶら下げており、base は
    最後ではないので通る。ここでも <n> と <n>.1 の2つをぶら下げる。

    リレーション種別は実データに合わせる(2=バージョン、3=recid->depid)。
    PIDVersioning.insert_child は親を REDIRECTED にしてしまうが、
    実データの親は R のままなので使わない。
    """
    from invenio_pidstore.models import PersistentIdentifier, PIDStatus
    from invenio_pidrelations.models import PIDRelation

    def pid(t, v):
        p = PersistentIdentifier.query.filter_by(
            pid_type=t, pid_value=v).one_or_none()
        if p is None:
            p = PersistentIdentifier.create(
                t, v, object_type="rec", object_uuid=uid,
                status=PIDStatus.REGISTERED)
        return p

    def relate(parent, child, rtype, index=None):
        if PIDRelation.query.filter_by(parent_id=parent.id,
                                       child_id=child.id).one_or_none() is None:
            db.session.add(PIDRelation(parent_id=parent.id, child_id=child.id,
                                       relation_type=rtype, index=index))

    parent = pid("parent", "parent:%%s" %% recid)
    db.session.flush()
    for i, v in enumerate((str(recid), "%%s.1" %% recid)):
        child = pid("recid", v)
        dep = pid("depid", v)
        db.session.flush()
        relate(parent, child, 2, i)   # バージョン
        relate(child, dep, 3)         # recid -> depid
    db.session.flush()


def _item_metadata(uid, item_type_id, title, owner_id, raw=None):
    """item_metadata を作る。

    無いと ES への反映が落ちる。invenio-indexer の before_record_index が
    weko_deposit.receivers.append_file_content -> WekoDeposit.item_metadata
    -> ItemsMetadata.get_record(...).one() を通るため、行が無いと
    NoResultFound になり *検索に出ない*。
    合成レコードでも検索・一覧を確認したいので作っておく。
    """
    from weko_records.models import ItemMetadata
    if ItemMetadata.query.get(uid) is not None:
        return
    js = dict(raw or {})
    js.setdefault("$schema", "/items/jsonschema/%%s" %% item_type_id)
    js.setdefault("pubdate", "2026-01-01")
    js["title"] = title
    js["owner"] = str(owner_id)
    db.session.add(ItemMetadata(
        id=uid, item_type_id=int(item_type_id), json=js, version_id=1))
    db.session.flush()


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


# --------------------------------------------- リソースタイプ別 / 全項目アイテム
# resourcetype と COAR URI の対応は、推測せずリポジトリ内の既存データから
# 抽出したものを使っている(modules/ 配下の JSON / テストデータ)。
RESOURCE_TYPES = [
    ("journal article",             "c_6501"),
    ("departmental bulletin paper", "c_6501"),
    ("doctoral thesis",             "c_db06"),
    ("conference paper",            "c_5794"),
    ("research report",             "c_18ws"),
    ("technical report",            "c_18gh"),
    ("dataset",                     "c_ddb1"),
    ("software",                    "c_5ce6"),
    ("book",                        "c_2f33"),
    ("still image",                 "c_ecc8"),
    ("sound",                       "c_18cc"),
    ("learning object",             "c_e059"),
    ("other",                       "c_1843"),
]
COAR = "http://purl.org/coar/resource_type/%%s"


@step("pattern_items")
def _pattern_items():
    """リソースタイプ別のアイテムと、全項目を埋めたアイテム。

    アイテムタイプは *デフォルトアイテムタイプ（フル）*(30002) に統一する。
    1〜14 は harvesting_type=t のハーベスト用で、登録アイテムには使わない。

    - 900100 … スキーマ上の*全項目*を埋めた1件。項目ごとの表示・出力を
      1件で確認できるようにするため
    - 900101〜 … リソースタイプ別。種別で分岐する処理(OAI/JPCoAR 出力、
      検索ファセット、詳細画面)を種別ごとに確かめられるようにする

    測定に必要な最低限の一部なので --scale とは無関係に常に作る。
    """
    owner = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    idxs = list((OUT.get("indexes") or {}).values()) or [OUT.get("index")]
    OUT["pattern_items"] = {"full": None, "by_resource_type": {}}

    rm, _, _ = _make_record(
        900100, owner, "0", "全項目入力アイテム（検証用）", False,
        index_key="index", rtype="journal article", ruri=COAR %% "c_6501",
        full=True)
    OUT["pattern_items"]["full"] = {"recid": 900100, "uuid": str(rm.id)}

    for i, (rtype, code) in enumerate(RESOURCE_TYPES):
        recid = 900101 + i
        # 子インデックスに散らす。インデックス側の条件と組み合わせて測れる
        key = "index" if not idxs else None
        rm, _, _ = _make_record(
            recid, owner, "0", "%%s のサンプル" %% rtype, False,
            index_key="index", rtype=rtype, ruri=COAR %% code)
        if idxs:
            # index_key は既存3件と同じ経路なので、path だけ差し替える
            from sqlalchemy.orm.attributes import flag_modified
            j = dict(rm.json or {})
            j["path"] = [str(idxs[i %% len(idxs)])]
            rm.json = j
            flag_modified(rm, "json")
            db.session.add(rm)
        OUT["pattern_items"]["by_resource_type"][rtype] = recid
    db.session.flush()


# ---------------------------------------------------------------- PIDVersioning
@step("pid_versioning")
def _versioning():
    """既にあるレコードの取りこぼしを埋める。

    新規作成時は _make_record が張るので、ここは前回までに作られた分の
    補完用。
    """
    for r in OUT["records"].values():
        _link_version(r["recid"], _uuid.UUID(r["uuid"]))


# ---------------------------------------------------------------- OAuthトークン
@step("oauth_token")
def _token():
    """検証用の個人アクセストークン。

    値は*固定のダミー*にする。生成値のままだと fixtures.json が
    実行のたびに変わるうえ、記録として残せなくなるため。
    この環境でしか通らない値で、秘密として扱う必要はない。

    以前は毎回 create_personal していて、実行のたびにトークン行が増えていた。
    """
    from invenio_oauth2server.models import Token
    uid = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    scopes = list(current_app.extensions["invenio-oauth2server"].scopes.keys())
    # 既にダミー値を持つ行があればそれを使う。別の行に同じ値を入れると
    # ix_oauth2server_token_access_token の一意制約に当たる。
    t = Token.query.filter_by(access_token=DUMMY_TOKEN).first()
    if t is None:
        t = Token.create_personal("api-inventory-probe", uid, scopes=scopes,
                                  is_internal=True)
        t.access_token = DUMMY_TOKEN
    t.user_id = uid
    t.scopes = scopes
    t.expires = None
    db.session.add(t)
    db.session.flush()
    # 旧実装は実行のたびに新しいトークンを作っていた。溜まった分を片付ける。
    for old in Token.query.filter_by(user_id=uid, is_personal=True,
                                     is_internal=True).all():
        if old.id != t.id:
            db.session.delete(old)
    db.session.flush()
    OUT["token"] = {"access_token": DUMMY_TOKEN, "user_id": uid,
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


# ------------------------------------------- インデックスのアクセス制御パターン
@step("index_acl")
def _index_acl():
    """閲覧・投稿の制御パターンを一通り作る。

    weko_index_tree.utils.check_roles / check_groups の仕様に合わせている。
      * browsing_role に "-99" があれば*未ログインでも閲覧可*。無ければ遮断
      * "-98" はロールを持たない認証済ユーザの扱い
      * 認証済ユーザは*自分の全ロールがリストに含まれる*必要がある(AND判定)。
        "1,2" は System/Repository 管理者だけが通り、Contributor は通らない
      * browsing_group は所属していれば通る

    group を使うのでグループ作成の後に置く。
    """
    import datetime
    from weko_index_tree.models import Index

    root = OUT.get("index")
    if not root:
        raise RuntimeError("親インデックスが無い")
    gid = (OUT.get("group") or {}).get("id")
    future = datetime.datetime(2099, 1, 1)
    private_id = (OUT.get("indexes") or {}).get("Restricted")

    specs = [
        (900016, "公開前資料", "Embargoed", root,
         {"public_state": True, "public_date": future}),
        (900017, "ログイン限定", "LoginOnly", root,
         {"browsing_role": "1,2,3,4,-98"}),        # -99 が無い = ゲスト遮断
        (900018, "管理者限定", "AdminOnly", root,
         {"browsing_role": "1,2"}),
        (900019, "グループ限定", "GroupOnly", root,
         {"browsing_group": str(gid) if gid else ""}),
        (900020, "投稿制限", "ContributeRestricted", root,
         {"contribute_role": "1,2"}),              # 閲覧は自由、投稿だけ制限
        (900021, "ハーベスト非公開", "HarvestPrivate", root,
         {"harvest_public_state": False}),
    ]
    # 親が非公開のときに子がどう見えるか(継承の確認)
    if private_id:
        specs.append((900022, "非公開の親の子", "ChildOfPrivate", private_id, {}))

    acl = {}
    for iid, ja, en, parent, extra in specs:
        idx = Index.query.filter_by(id=iid).one_or_none()
        if idx is None:
            used = [i.position for i in Index.query.filter_by(parent=parent).all()]
            pos = (max(used) + 1) if used else 0
            idx = Index(id=iid, parent=parent, position=pos,
                        index_name=ja, index_name_english=en,
                        public_state=True, harvest_public_state=True,
                        browsing_role="3,-98,-99",
                        contribute_role="1,2,3,4,-98,-99",
                        public_date=None, owner_user_id=1)
            db.session.add(idx)
            db.session.flush()
        # 冪等: 毎回この形に戻したうえで、そのパターンの設定だけ上書きする
        idx.is_deleted = False
        idx.parent = parent
        idx.index_name = ja
        idx.index_name_english = en
        idx.public_state = True
        idx.harvest_public_state = True
        idx.browsing_role = "3,-98,-99"
        idx.contribute_role = "1,2,3,4,-98,-99"
        idx.browsing_group = None
        idx.contribute_group = None
        idx.public_date = None
        for k, v in extra.items():
            setattr(idx, k, v)
        db.session.add(idx)
        acl[en] = iid
    db.session.flush()
    OUT["indexes_acl"] = acl

    # 各パターンにアイテムを1件ずつ置く。インデックス側の設定だけでは
    # 到達可否を測れないため
    owner = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    from sqlalchemy.orm.attributes import flag_modified
    items = {}
    for i, (en, iid) in enumerate(sorted(acl.items())):
        recid = 900201 + i
        rm, _, _ = _make_record(recid, owner, "0", "%%s のアイテム" %% en, False)
        j = dict(rm.json or {})
        j["path"] = [str(iid)]
        rm.json = j
        flag_modified(rm, "json")
        db.session.add(rm)
        items[en] = recid
    db.session.flush()
    OUT["indexes_acl_items"] = items


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


# ------------------------------------------------------ デモ用アイテム(規模)
DEMO_SUBJECTS = [
    "地方都市における公共交通網の再編", "近世日本の農村社会と土地制度",
    "深層学習を用いた医用画像の分類", "沿岸域の生態系サービス評価",
    "高齢化社会における地域医療連携", "気候変動が水稲収量に与える影響",
    "オープンサイエンスと研究データ管理", "触媒表面での水素吸着機構",
    "第二言語習得における語彙獲得過程", "大規模災害時の避難行動モデル",
    "量子ドットを用いた太陽電池の高効率化", "中山間地域の集落機能の変容",
    "機械学習による地震動予測の試み", "近代日本文学における都市表象",
    "微生物叢が宿主代謝に及ぼす影響",
]
DEMO_FORMS = ["に関する研究", "の実証的分析", "についての一考察",
              "の基礎的検討", "に関する事例研究"]
DEMO_AUTHORS = [
    ("山田 太郎", "Yamada, Taro"), ("佐藤 花子", "Sato, Hanako"),
    ("鈴木 一郎", "Suzuki, Ichiro"), ("高橋 美咲", "Takahashi, Misaki"),
    ("田中 健二", "Tanaka, Kenji"), ("伊藤 直樹", "Ito, Naoki"),
    ("渡辺 由美", "Watanabe, Yumi"), ("中村 大輔", "Nakamura, Daisuke"),
]
# 子インデックスごとの資料種別。index_name_english -> (resourcetype, uri)
DEMO_KINDS = [
    ("Departmental Bulletin Paper", "departmental bulletin paper",
     "http://purl.org/coar/resource_type/c_6501"),
    ("Thesis", "thesis", "http://purl.org/coar/resource_type/c_46ec"),
    ("Research Report", "research report",
     "http://purl.org/coar/resource_type/c_18ws"),
    ("Conference Paper", "conference paper",
     "http://purl.org/coar/resource_type/c_5794"),
]




@step("demo_items")
def _demo_items():
    """リポジトリの規模感を再現するデモ用アイテム。

    ``--scale`` で件数を選ぶ。*既定は 0 で、何も作らない。*
    測定は3件のフィクスチャで足りるうえ、measure.sh は測定中に
    このスクリプトを何度も流し直すため、既定で件数を積むと無駄が大きい。
    デモや一覧の見え方を確認したいときだけ 100 / 1000 / 10000 /
    100000 / 1000000 を明示する。

    ページングや並び替えを確認するには一覧に十分な件数が要る。台帳では
    ``page`` を取る行が51、``limit`` が31、``offset`` が30、``sort`` が41 ある。
    3件のフィクスチャではどれも確かめられない。

    ORM で1件ずつ作ると1万件でも現実的な時間に収まらないので core insert で
    まとめて流す。*ファイル実体とバケットは作らない* — ここでの目的は一覧の
    見え方であって、ダウンロードや IIIF は既存の3件で測るため。

    冪等: ``_demo`` 印の付いたレコード数を数え、不足分だけ足す。
    """
    import datetime
    from invenio_records.models import RecordMetadata as RM
    from invenio_pidstore.models import PersistentIdentifier as PID
    from weko_records.models import ItemMetadata as IM

    have = db.session.execute(
        "SELECT count(*) FROM records_metadata WHERE json->>'_demo' = '1'"
    ).scalar() or 0
    want = SCALE
    OUT["demo"] = {"scale": want, "existing": int(have), "created": 0}
    if have >= want:
        return

    idxs = OUT.get("indexes") or {}
    kinds = [(idxs.get(en), rt, uri) for en, rt, uri in DEMO_KINDS
             if idxs.get(en)]
    if not kinds:
        raise RuntimeError("子インデックスが無いためデモデータを作れない")
    owner = OUT["users"].get("contributor@example.org", {}).get("id", 3)
    now = datetime.datetime.utcnow()
    base = 1000000
    chunk, rows_rm, rows_pid, rows_im = 2000, [], [], []
    created = 0

    def flush_rows():
        if rows_rm:
            db.session.execute(RM.__table__.insert(), rows_rm)
            db.session.execute(IM.__table__.insert(), rows_im)
            db.session.execute(PID.__table__.insert(), rows_pid)
            db.session.commit()
        del rows_rm[:]
        del rows_pid[:]
        del rows_im[:]

    for k in range(int(have) + 1, want + 1):
        recid = base + k
        idx_id, rtype, ruri = kinds[k %% len(kinds)]
        itype = ITEM_TYPE_ID
        subj = DEMO_SUBJECTS[k %% len(DEMO_SUBJECTS)]
        form = DEMO_FORMS[k %% len(DEMO_FORMS)]
        ja, en = DEMO_AUTHORS[k %% len(DEMO_AUTHORS)]
        year = 2015 + (k %% 12)
        month = 1 + (k %% 12)
        pub = "%%04d-%%02d-01" %% (year, month)
        title = "%%s%%s (%%d)" %% (subj, form, k)
        # 1割を非公開にして、公開状態で結果が変わる経路も測れるようにする
        status = "1" if k %% 10 == 0 else "0"
        uid = _uuid.uuid4()
        js = {
            "_oai": {"id": "oai:weko3.example.org:%%08d" %% recid},
            "_demo": "1",
            "path": [str(idx_id)],
            "owner": str(owner),
            "recid": str(recid),
            "title": [title],
            "item_title": title,
            "item_type_id": itype,
            "pubdate": {"attribute_name": "PubDate", "attribute_value": pub},
            "publish_date": pub,
            "publish_status": status,
            "weko_shared_ids": [],
            "relation_version_is_last": True,
            "owners": [owner],
            "author_link": [],
            "_buckets": {"deposit": ""},
            "_deposit": {
                "id": str(recid),
                "pid": {"type": "depid", "value": str(recid), "revision_id": 0},
                "owner": str(owner), "owners": [owner],
                "created_by": owner, "status": "published",
            },
            "item_1617186331708": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                    {"subitem_1551255647225": title,
                     "subitem_1551255648112": "ja"}]},
            "item_1617186419668": {
                "attribute_name": "Creator",
                "attribute_value_mlt": [
                    {"creatorNames": [
                        {"creatorName": ja, "creatorNameLang": "ja"},
                        {"creatorName": en, "creatorNameLang": "en"}]}]},
            "item_1617258105262": {
                "attribute_name": "Resource Type",
                "attribute_value_mlt": [
                    {"resourcetype": rtype, "resourceuri": ruri}]},
        }
        rows_rm.append({"id": uid, "json": js, "version_id": 1,
                        "created": now, "updated": now})
        rows_im.append({"id": uid, "item_type_id": int(itype),
                        "json": {"title": title, "owner": str(owner),
                                 "$schema": "/items/jsonschema/%%s" %% itype,
                                 "pubdate": pub},
                        "version_id": 1, "created": now, "updated": now})
        # 実レコードと同じ PID 構成。base が最後の子にならないよう
        # <n> と <n>.1 を作る(詳細画面の is_last_child 判定のため)。
        # 5本とも同じ object_uuid を指す。デモ用途では版ごとに別レコードを
        # 作るまでの必要はなく、行数を5倍に増やさずに済む。
        for t, v in (("recid", str(recid)), ("depid", str(recid)),
                     ("recid", "%%s.1" %% recid), ("depid", "%%s.1" %% recid),
                     ("parent", "parent:%%s" %% recid)):
            rows_pid.append({"pid_type": t, "pid_value": v,
                             "status": "R", "object_type": "rec",
                             "object_uuid": uid,
                             "created": now, "updated": now})
        created += 1
        if len(rows_rm) >= chunk:
            flush_rows()
            print("  demo_items: %%d / %%d" %% (int(have) + created, want),
                  flush=True)
    flush_rows()

    # PID リレーションは件数が多いので INSERT ... SELECT で一括生成する。
    # 5本の PID は同じ object_uuid を指すので、そこで結合できる。
    demo_uuid = ("SELECT id FROM records_metadata WHERE json->>'_demo' = '1'")
    db.session.execute("""
        INSERT INTO pidrelations_pidrelation (parent_id, child_id,
                                              relation_type, "index",
                                              created, updated)
        SELECT p.id, c.id, 2,
               CASE WHEN c.pid_value LIKE '%%%%.1' THEN 1 ELSE 0 END,
               now(), now()
        FROM pidstore_pid p
        JOIN pidstore_pid c
          ON c.object_uuid = p.object_uuid AND c.pid_type = 'recid'
        WHERE p.pid_type = 'parent' AND p.object_uuid IN (%%s)
          AND NOT EXISTS (SELECT 1 FROM pidrelations_pidrelation x
                          WHERE x.parent_id = p.id AND x.child_id = c.id)
    """ %% demo_uuid)
    db.session.execute("""
        INSERT INTO pidrelations_pidrelation (parent_id, child_id,
                                              relation_type, created, updated)
        SELECT r.id, d.id, 3, now(), now()
        FROM pidstore_pid r
        JOIN pidstore_pid d
          ON d.object_uuid = r.object_uuid AND d.pid_type = 'depid'
         AND d.pid_value = r.pid_value
        WHERE r.pid_type = 'recid' AND r.object_uuid IN (%%s)
          AND NOT EXISTS (SELECT 1 FROM pidrelations_pidrelation x
                          WHERE x.parent_id = r.id AND x.child_id = d.id)
    """ %% demo_uuid)
    db.session.commit()
    OUT["demo"]["created"] = created


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


CLEAN_PAYLOAD = r'''
# -*- coding: utf-8 -*-
"""fixtures.py が投入したものを消す。ユーザとロールには触らない。"""
import traceback
from invenio_db import db

SCOPE = "%(scope)s"
DEMO_IDS = ([900001, 900002, 900003, 900100]   # probe 用 + 全項目アイテム
            + list(range(900101, 900101 + 13))   # リソースタイプ別
            + list(range(900201, 900201 + 7)))   # アクセス制御パターン
INDEX_IDS = ([900016, 900017, 900018, 900019, 900020, 900021, 900022]
             + [900011, 900012, 900013, 900014, 900015, 900001])
OUT = {"deleted": {}, "errors": []}


def step(name):
    def deco(fn):
        try:
            OUT["deleted"][name] = fn() or 0
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            OUT["errors"].append("%%s: %%s: %%s" %% (name, type(exc).__name__, exc))
            traceback.print_exc()
        return fn
    return deco


@step("demo_items")
def _demo():
    """--scale で作ったデモ用アイテム。件数が多いので SQL でまとめて消す。"""
    n = db.session.execute(
        "SELECT count(*) FROM records_metadata WHERE json->>'_demo' = '1'"
    ).scalar() or 0
    if not n:
        return 0
    sel = "SELECT id FROM records_metadata WHERE json->>'_demo' = '1'"
    sel_pid = "SELECT id FROM pidstore_pid WHERE object_uuid IN (%%s)" %% sel
    # PID を参照している行を先に落とす
    db.session.execute(
        "DELETE FROM pidrelations_pidrelation WHERE parent_id IN (%%s) "
        "OR child_id IN (%%s)" %% (sel_pid, sel_pid))
    db.session.execute(
        "DELETE FROM pidstore_redirect WHERE pid_id IN (%%s)" %% sel_pid)
    db.session.execute(
        "DELETE FROM pidstore_pid WHERE object_uuid IN (%%s)" %% sel)
    db.session.execute(
        "DELETE FROM item_metadata WHERE id IN "
        "(SELECT id FROM records_metadata WHERE json->>'_demo' = '1')")
    db.session.execute(
        "DELETE FROM records_metadata_version WHERE id IN "
        "(SELECT id FROM records_metadata WHERE json->>'_demo' = '1')")
    db.session.execute(
        "DELETE FROM records_metadata WHERE json->>'_demo' = '1'")
    return int(n)


if SCOPE == "all":

    @step("probe_records")
    def _records():
        """probe 用の3件。ファイル実体・バケット・PID関連まで落とす。

        ORM で消すと autoflush が途中で走り、まだ参照が残っている段階で
        NOT NULL 制約に当たる(pidrelations が PID を参照している)。
        依存の順番を自分で決めたいので SQL で消す。
        """
        # pid_value は varchar。数値のまま渡すと型比較で落ちる
        ids = ",".join("'%%s'" %% i for i in DEMO_IDS)
        # uuid は先に確定させる。pidstore_pid を消したあとに引き直すと
        # 対象が取れなくなり、records_metadata が消し残る。
        # PID 経由と recid 直引きの両方。過去の削除が途中で失敗すると
        # PID だけ消えて records_metadata が孤児として残ることがある。
        uuids = [str(r[0]) for r in db.session.execute(
            "SELECT object_uuid FROM pidstore_pid "
            "WHERE pid_type='recid' AND pid_value IN (%%s) "
            "UNION "
            "SELECT id FROM records_metadata WHERE json->>'recid' IN (%%s)"
            %% (ids, ids))]
        if not uuids:
            return 0
        u_in = ",".join("'%%s'" %% u for u in uuids)
        # PID は object_uuid だけでは拾えない。insert_child が親PIDを
        # REDIRECTED にして object_uuid を Redirect 行の id に書き換えるため、
        # 親PIDはレコードを指さなくなる。pid_value でも引く。
        vals = ",".join(
            "'%%s'" %% v for i in DEMO_IDS
            for v in (str(i), "parent:%%s" %% i))
        sel_pid = ("SELECT id FROM pidstore_pid WHERE object_uuid IN (%%s) "
                   "OR pid_value IN (%%s)" %% (u_in, vals))
        # リダイレクト先の行。親PIDの object_uuid が指している
        sel_redirect = ("SELECT object_uuid FROM pidstore_pid "
                        "WHERE pid_value IN (%%s) AND status='M'" %% vals)
        # バケットIDも先に確定させる。records_buckets を消すと引けなくなる。
        buckets = [str(r[0]) for r in db.session.execute(
            "SELECT bucket_id FROM records_buckets WHERE record_id IN (%%s)"
            %% u_in)]
        b_in = ",".join("'%%s'" %% b for b in buckets) or "'00000000-0000-0000-0000-000000000000'"
        for sql in (
            # PID の被参照を先に落とす
            "DELETE FROM pidrelations_pidrelation WHERE parent_id IN (%%s) "
            "OR child_id IN (%%s)" %% (sel_pid, sel_pid),
            "DELETE FROM pidstore_redirect WHERE pid_id IN (%%s)" %% sel_pid,
            "DELETE FROM pidstore_redirect WHERE id IN (%%s)" %% sel_redirect,
            # ファイル側は オブジェクト -> 紐づけ -> バケット の順
            "DELETE FROM files_objecttags WHERE version_id IN "
            "(SELECT version_id FROM files_object WHERE bucket_id IN (%%s))"
            %% b_in,
            "DELETE FROM files_object WHERE bucket_id IN (%%s)" %% b_in,
            "DELETE FROM files_buckettags WHERE bucket_id IN (%%s)" %% b_in,
            "DELETE FROM records_buckets WHERE record_id IN (%%s)" %% u_in,
            "DELETE FROM files_bucket WHERE id IN (%%s)" %% b_in,
            # 最後にレコードと PID
            "DELETE FROM item_metadata_version WHERE id IN (%%s)" %% u_in,
            "DELETE FROM item_metadata WHERE id IN (%%s)" %% u_in,
            "DELETE FROM records_metadata_version WHERE id IN (%%s)" %% u_in,
            "DELETE FROM pidstore_pid WHERE object_uuid IN (%%s) "
            "OR pid_value IN (%%s)" %% (u_in, vals),
            "DELETE FROM records_metadata WHERE id IN (%%s)" %% u_in,
        ):
            db.session.execute(sql)
        return len(uuids)

    @step("community")
    def _community():
        from invenio_communities.models import Community
        c = Community.query.get("apiinv")
        if c is None:
            return 0
        db.session.delete(c)
        return 1

    @step("indexes")
    def _indexes():
        """コミュニティより後に消す(root_node_id に参照されているため)。"""
        from weko_index_tree.models import Index
        n = 0
        for i in INDEX_IDS:
            idx = Index.query.filter_by(id=i).one_or_none()
            if idx is not None:
                db.session.delete(idx)
                n += 1
        return n

    @step("token")
    def _token():
        from invenio_oauth2server.models import Token
        n = 0
        for t in Token.query.filter_by(is_personal=True, is_internal=True).all():
            if t.access_token == "%(token)s":
                db.session.delete(t)
                n += 1
        return n

print("CLEAN_OK errors=%%d" %% len(OUT["errors"]))
for k, v in OUT["deleted"].items():
    print("  DEL %%s=%%s" %% (k, v))
for e in OUT["errors"]:
    print("  ERR", e)
'''


def run_payload(container, src, label):
    """ペイロードをコンテナの invenio shell で実行する。"""
    import tempfile
    work = tempfile.mkdtemp(prefix='api-fixtures-')
    local = os.path.join(work, '_payload.py')
    with open(local, 'w', encoding='utf-8') as f:
        f.write(src)
    r = sh(['docker', 'cp', local, f'{container}:/tmp/_payload.py'])
    if r.returncode:
        sys.exit(f'docker cp 失敗: {r.stderr.strip()}')
    return sh([
        'docker', 'exec', container, 'bash', '-lc',
        'source ~/.virtualenvs/invenio/bin/activate; cd /code; '
        'invenio shell -c "exec(open(\'/tmp/_payload.py\').read())"',
    ])


def main():
    p = argparse.ArgumentParser(description='動的検証用フィクスチャを投入する')
    p.add_argument('--out', default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fixtures.json'))
    p.add_argument('--container', default=os.environ.get('WEKO_WEB_CONTAINER', ''),
                   help='投入先コンテナ。既定は $WEKO_WEB_CONTAINER、'
                        'それも無ければ compose ラベルから自動検出')
    p.add_argument('--password', default=PASSWORD)
    p.add_argument('--scale', type=int, default=0,
                   help='デモ用アイテムの件数。0(既定)はテストに必要な最低限のみ。'
                        'リポジトリの規模感を再現するには 100 / 1000 / 10000 / '
                        '100000 / 1000000 を指定する')
    p.add_argument('--clean', choices=['demo', 'all'], default='',
                   help='投入したデータを消す。demo: デモ用アイテムのみ / '
                        'all: 本スクリプトが作るもの全部(ユーザは消さない)')
    a = p.parse_args()

    container = resolve_container(a.container)

    if a.clean:
        r = run_payload(container,
                        CLEAN_PAYLOAD % {'scope': a.clean,
                                         'token': DUMMY_TOKEN},
                        'clean')
        if 'CLEAN_OK' not in r.stdout:
            sys.exit(f'削除に失敗:\n{r.stdout[-3000:]}\n{r.stderr[-2000:]}')
        for line in r.stdout.splitlines():
            t = line.strip()
            if t.startswith(('CLEAN_OK', 'DEL ', 'ERR ')):
                print('  ' + t)
        print('\n  投入し直すには --clean を外して実行してください。')
        return

    r = run_payload(container,
                    PAYLOAD % {'password': a.password, 'scale': a.scale,
                               'token': DUMMY_TOKEN},
                    'fixtures')
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
    demo = data.get('demo') or {}
    if demo.get('scale'):
        print(f"  デモ用アイテム: 既存 {demo.get('existing', 0)} 件 + "
              f"新規 {demo.get('created', 0)} 件 = 目標 {demo['scale']} 件")
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
