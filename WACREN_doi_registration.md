# DOI 登録共通基盤 — 設計仕様

Crossref / DataCite（将来的に JaLC / NDL JaLC）への DOI 登録を、
単一の抽象の上に載せるための共通基盤の設計仕様。

- 対象ブランチ: `feature/nii_WACREN_crossref_doi`（設計時: `feature/nii_WACREN_pre`）
- 作成日: 2026-08-04 / 最終更新: 2026-09-01
- ステータス: **Phase A（共通基盤）実装済み**
- 実装コミット: `23af9ad4` *feat(workflow): register Crossref DOIs through a shared deposit foundation*
- 関連文書:
  - [`WACREN_crossref.md`](./WACREN_crossref.md) — Crossref 固有の仕様（XML マッピング、非同期デポジット）**実装済み**
  - [`WACREN_datacite.md`](./WACREN_datacite.md) — DataCite 固有の仕様（JSON マッピング、同期 REST）**未実装**

---

## 0. 実装状況（2026-09-01 時点）

| Phase | 内容 | 状況 |
| --- | --- | --- |
| A. 基盤 | `base` / `errors` / `registry` / `metadata` / `orchestrator` / `tasks` / `DoiDepositLog` + alembic / フック | ✅ 実装済み |
| B. DataCite | `DataCiteAgency` | ❌ 未着手 |
| C. Crossref | `CrossrefAgency` | ✅ 実装済み（`test.crossref.org` で検証済み） |
| D. 管理 UI | 設定画面・一覧・再送・CLI・通知 | ⚠️ CLI（`weko workflow doi list` / `resend`）と失敗通知メールのみ。管理画面は未実装（§13） |
| E. 将来 | `JalcAgency` / `NdlJalcAgency`、ARK 統合 | ❌ 未着手 |

**実装順序は §15-2 の推奨（B → C）とは逆になり、A と C を同時に実装した。**
非同期・ポーリング側で基盤を先に検証したかたちで、同期エージェンシー用の
`DepositStatus.SUCCEEDED` 経路はまだ実コードでは使われていない（DataCite 実装時に初めて通る）。

**設計との主な差分** — 詳細は各節の「実装結果」を参照。

- 全体マスタースイッチ `WEKO_DOI_ALLOW_REGISTER` は**実装していない**。可否はエージェンシー単位
  （`WEKO_CROSSREF_ALLOW_REGISTER_DOI`）のみで判定する（§9）
- `doi_identifier.jalc_*_flag` によるリポジトリ単位のスイッチは**参照していない**（§9-3）
- `skipped` 状態は持たない。送らない場合はログ行自体を作らない（§7-1）
- `WEKO_DOI_AGENCY_REGISTRY` → **`WEKO_DOI_AGENCIES`**（§5）
- `FakeAgency` は用意せず、`CrossrefAgency` + `requests` のパッチで状態遷移を検証している（§12）

**テスト**: `modules/weko-workflow/tests/test_doi.py`（533 行 / 24 ケース）。

---

## 1. 目的とスコープ

### 1-1. 解決したい課題

WEKO3 は現在、DOI をメタデータと PID ストアに書き込むだけで、
**登録機関の API を一切呼んでいない**（[`WACREN_crossref.md` §1-1](./WACREN_crossref.md)）。
Crossref と DataCite の両方に対応するにあたり、以下を独立に実装すると重複と手戻りが発生する。

- 登録処理のフック位置とトランザクション整合
- 登録結果のステータス管理テーブル
- Celery による非同期化とリトライ
- 設定の可否判定パターン
- 管理 UI（設定・一覧・再送）
- 失敗通知

**これらを共通化し、登録機関ごとの差分だけを実装すれば済む構造にする。**

### 1-2. スコープ

| 含む | 含まない |
| --- | --- |
| 共通インターフェース `DoiRegistrationAgency` | 各エージェンシーの具体実装（別文書） |
| 登録オーケストレータと Celery タスク | JPCOAR → 各スキーマのメタデータ変換ロジック |
| `doi_deposit_log` テーブルと状態遷移 | ワークフロー UI の変更 |
| 設定の階層構造と可否判定 | DOI 付与時のメタデータ検証強化（§10-3） |
| 管理 UI | ARK / Handle の統合（§10-5） |
| 新エージェンシー追加手順 | |

### 1-3. 対象エージェンシー

`IDENTIFIER_GRANT_LIST`（`weko_workflow/config.py:54`）の選択肢に対応する。

| `doi_select` | 表示名 | エージェンシー | 本基盤での扱い |
| --- | --- | --- | --- |
| `0` | Not Grant | — | 対象外 |
| `1` | JaLC DOI | JaLC | **将来対応**（インターフェースのみ用意） |
| `2` | JaLC CrossRef DOI | Crossref | **対応** |
| `3` | JaLC DataCite DOI | DataCite | **対応** |
| `4` | NDL JaLC DOI | NDL 経由 JaLC | **将来対応** |

> ⚠️ **重要**: `saving_doi_pidstore()` は `doi_select=1`（JaLC）と `doi_select=4`（NDL JaLC）の
> **どちらでも `doi_register_typ = 'JaLC'` を設定する**（`weko_workflow/utils.py:154`）。
> したがって**エージェンシーの判別は `doi_register_typ` ではなく `doi_select`（1〜4）で行う。**

---

## 2. 設計原則

1. **外部サービスの障害がアイテム登録を止めない。**
   ARK 実装（`register_ark_by_item_id`）で確立した方針を全エージェンシーで踏襲する。
   登録失敗はログとステータス表に残し、ワークフローは正常終了させる。
2. **「未設定」を「無効」と取り違えない。**
   有効化フラグが立っているのに必須設定が欠けている場合は、
   `ERROR` ログを出したうえで無効扱いにする（`is_ark_registration_allowed()` と同じ）。
3. **同期 API と非同期 API を同じインターフェースで扱う。**
   呼び出し側が「今どちらの機関か」を意識しない（§4）。
4. **既定値は安全側に倒す。**
   マスタースイッチは `False`、接続先の既定はテスト系。
5. **監査可能にする。**
   送信ペイロードと応答を必ず保存し、後から検証・再送できるようにする。
6. **エージェンシーの追加はプラグイン的に行える。**
   共通基盤に手を入れずに、クラスを 1 つ足して設定に登録するだけで済む（§11）。

---

## 3. 全体構成

```
weko_workflow/utils.py
  saving_doi_pidstore()                       ← 既存。全 5 呼び出し箇所の合流点
        │ 既存: PID 登録 + メタデータ書き込み
        └─ 追加: request_doi_deposit(item_uuid, doi_select, doi, ...)
                    │
                    ▼
        weko_workflow/doi/orchestrator.py     ← 共通オーケストレータ
                    │ ① レジストリから Agency を解決（§5）
                    │ ② agency.is_allowed() で可否判定
                    │ ③ DoiDepositLog を status='pending' で作成
                    │ ④ Celery タスクを投入（コミット競合対策込み・§7-3）
                    ▼
        weko_workflow/doi/tasks.py
          deposit_doi(log_id)
                    │ ① agency.build_payload(source)      ← エージェンシー固有
                    │ ② agency.register(request)          ← エージェンシー固有
                    │ ③ DepositResult の status で分岐（§4-3）
                    │      SUCCEEDED  → success で確定
                    │      ACCEPTED   → poll_doi_deposit を予約
                    │      RETRIABLE  → 指数バックオフで再投入
                    │      FAILED     → failure で確定 + 通知
                    ▼
          poll_doi_deposit(log_id)             ← requires_polling のときだけ動く
                    └─ agency.poll(tracking_id) → success / failure / 継続

        weko_workflow/doi/agencies/
          ├─ crossref.py   CrossrefAgency   （XML / 非同期 / ポーリングあり）
          ├─ datacite.py   DataCiteAgency   （JSON / 同期）
          ├─ jalc.py       JalcAgency       （将来）
          └─ ndl_jalc.py   NdlJalcAgency    （将来）
```

---

## 4. コアインターフェース

配置: `modules/weko-workflow/weko_workflow/doi/base.py`

### 4-1. 値オブジェクト

```python
"""DOI 登録共通基盤のコア型定義."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class DepositStatus(Enum):
    """デポジット 1 回分の結果種別."""

    SUCCEEDED = 'succeeded'
    """登録が確定した。これ以上の操作は不要."""

    ACCEPTED = 'accepted'
    """受付のみ完了。確定には poll() が必要（Crossref の servlet/deposit）."""

    RETRIABLE = 'retriable'
    """一時的な失敗。時間をおいて再試行する（タイムアウト・5xx・429）."""

    FAILED = 'failed'
    """恒久的な失敗。再試行しても解消しない（メタデータ不備・認証エラー）."""

    SKIPPED = 'skipped'
    """設定が無効、または必須設定が欠けているため実行しなかった."""


@dataclass(frozen=True)
class AgencyCapabilities:
    """エージェンシーが何をできるかの宣言.

    オーケストレータはこの値だけを見て処理を分岐する。
    エージェンシー名で分岐してはならない。
    """

    requires_polling: bool
    """register() が ACCEPTED を返しうるか（＝結果取得が別呼び出しか）."""

    supports_update: bool
    """登録済み DOI のメタデータ更新ができるか."""

    supports_hide: bool
    """公開済み DOI を非公開に戻せるか（DataCite の event=hide）."""

    supports_delete: bool
    """登録済み DOI を削除できるか（Crossref / DataCite とも通常 False）."""

    payload_content_type: str
    """送信ペイロードの MIME type。ログ表示と監査に使う."""


@dataclass
class DepositRequest:
    """登録 1 件分の入力."""

    item_uuid: str
    doi: str
    resource_url: str
    metadata: Dict[str, Any]
    """JPCOAR ベースのアイテムメタデータ（§8 の MetadataSource が供給）."""

    extra: Dict[str, Any] = field(default_factory=dict)
    """エージェンシー固有の追加情報（Crossref の record_type など）."""


@dataclass
class DepositResult:
    """登録 1 回分の結果."""

    status: DepositStatus
    tracking_id: Optional[str] = None
    """poll() に渡す追跡キー。Crossref は file_name、DataCite は不要（None）."""

    message: str = ''
    """人間が読むための要約。管理画面とログに出す."""

    raw_request: Optional[str] = None
    """送信したペイロード（監査・再送用）."""

    raw_response: Optional[str] = None
    """受信した応答そのまま."""

    http_status: Optional[int] = None
```

### 4-2. 抽象基底クラス

```python
class DoiRegistrationAgency(ABC):
    """DOI 登録機関の共通インターフェース.

    実装クラスは weko_workflow/doi/agencies/ に置き、
    WEKO_DOI_AGENCY_REGISTRY（§5）から解決される。
    """

    key: str
    """レジストリ上のキー。IDENTIFIER_GRANT_LIST の doi_select と対応させる."""

    name: str
    """表示名（管理画面・ログ用）."""

    capabilities: AgencyCapabilities

    # ------------------------------------------------------------------
    # 可否判定
    # ------------------------------------------------------------------
    @abstractmethod
    def is_allowed(self) -> bool:
        """このエージェンシーへの API 登録が有効かつ設定済みかを返す.

        有効化フラグが False なら静かに False を返す。
        フラグは True だが必須設定が欠けている場合は ERROR ログを出して False を返す
        （「未設定」を「無効」と取り違えないため）。
        """

    # ------------------------------------------------------------------
    # ペイロード生成
    # ------------------------------------------------------------------
    @abstractmethod
    def build_payload(self, request: DepositRequest) -> str:
        """JPCOAR メタデータから送信ペイロードを生成する.

        Raises:
            DoiPayloadError: 必須メタデータが欠けており生成できない場合。
                オーケストレータはこれを FAILED（恒久的失敗）として扱う。
        """

    # ------------------------------------------------------------------
    # 登録・更新
    # ------------------------------------------------------------------
    @abstractmethod
    def register(self, request: DepositRequest, payload: str) -> DepositResult:
        """DOI を登録する.

        同期エージェンシー（DataCite）は SUCCEEDED / FAILED / RETRIABLE を返す。
        非同期エージェンシー（Crossref）は ACCEPTED を返し、tracking_id を設定する。
        """

    def poll(self, tracking_id: str) -> DepositResult:
        """登録結果を取得する.

        capabilities.requires_polling が True のエージェンシーのみ実装する。
        まだ処理中の場合は ACCEPTED を返す（オーケストレータが再予約する）。
        """
        raise NotImplementedError

    def update(self, doi: str, request: DepositRequest, payload: str) -> DepositResult:
        """登録済み DOI のメタデータを更新する."""
        raise NotImplementedError

    def hide(self, doi: str) -> DepositResult:
        """公開済み DOI を非公開に戻す."""
        raise NotImplementedError
```

### 4-3. 同期／非同期の吸収 ← **本設計の核心**

Crossref（非同期）と DataCite（同期）の差は、
**`DepositStatus` と `AgencyCapabilities.requires_polling` の 2 つだけで吸収する。**

| | Crossref | DataCite |
| --- | --- | --- |
| `capabilities.requires_polling` | `True` | `False` |
| `register()` の戻り | `ACCEPTED` + `tracking_id`（= 投入ファイル名） | `SUCCEEDED`（HTTP 201） |
| `poll()` | `submissionDownload` を解析 | 実装しない |

オーケストレータ側の分岐は 1 か所に閉じる。

```python
result = agency.register(request, payload)

if result.status is DepositStatus.SUCCEEDED:
    log.mark_success(result)
elif result.status is DepositStatus.ACCEPTED:
    log.mark_submitted(result)
    poll_doi_deposit.apply_async(
        args=[log.id], countdown=cfg('POLL_DELAY'))
elif result.status is DepositStatus.RETRIABLE:
    log.mark_retry(result)
    _reschedule(log)          # 指数バックオフ。上限超過で failure に落とす
else:
    log.mark_failure(result)
    _notify(log)
```

**`if agency.key == 'crossref'` のような分岐を書いてはならない。**
新しいエージェンシーを足したときにオーケストレータを触ることになり、抽象化の意味が失われる。

---

## 5. エージェンシーレジストリ

配置: `weko_workflow/doi/registry.py`

`doi_select`（1〜4）からエージェンシー実装を解決する。
解決には invenio 慣習の import string 方式を使う
（WEKO 内でも `import_string('weko_deposit.api:WekoDeposit')` の形で既に使われている）。

```python
# weko_workflow/config.py
WEKO_DOI_AGENCY_REGISTRY = {
    '1': None,  # JaLC        — 将来対応
    '2': 'weko_workflow.doi.agencies.crossref:CrossrefAgency',
    '3': 'weko_workflow.doi.agencies.datacite:DataCiteAgency',
    '4': None,  # NDL JaLC    — 将来対応
}
"""doi_select（IDENTIFIER_GRANT_LIST の値）→ エージェンシー実装."""
```

```python
# weko_workflow/doi/registry.py
from werkzeug.utils import import_string
from flask import current_app


def get_agency(doi_select):
    """doi_select からエージェンシー実装を解決する.

    Args:
        doi_select: IDENTIFIER_GRANT_LIST の値（int または str）

    Returns:
        DoiRegistrationAgency のインスタンス。未対応・未設定なら None。
    """
    registry = current_app.config.get('WEKO_DOI_AGENCY_REGISTRY', {})
    path = registry.get(str(doi_select))
    if not path:
        return None
    try:
        return import_string(path)()
    except Exception as ex:
        current_app.logger.error(
            'Failed to load DOI agency for doi_select={0}: {1}'.format(
                doi_select, ex))
        return None
```

> **未対応のエージェンシー（JaLC / NDL JaLC）は `None`** とし、
> オーケストレータは「API 登録なし」として静かにスキップする（`skipped`）。
> 従来どおりメタデータ書き込みのみが行われるため、既存挙動は変わらない。

---

## 6. データモデル

配置: `weko_workflow/models.py`（追記）+ alembic リビジョン

**エージェンシーごとにテーブルを分けない。** 1 テーブルに `agency` カラムで持つ。

```
doi_deposit_log
├─ id                BigInteger    PK
├─ item_uuid         UUID          対象アイテム（PersistentIdentifier.object_uuid）
├─ agency            String(32)    'crossref' / 'datacite' / …
├─ doi_select        SmallInteger  IDENTIFIER_GRANT_LIST の値（1〜4）
├─ doi               String(255)   登録対象 DOI
├─ resource_url      Text          ランディングページ URL
├─ operation         String(16)    'register' / 'update' / 'hide'
├─ status            String(16)    §7-1 の状態
├─ tracking_id       String(255)   poll() 用の追跡キー（Crossref の file_name）
├─ attempt           SmallInteger  試行回数
├─ is_test           Boolean       テスト系宛か
├─ payload           Text          送信ペイロード（監査・再送用）
├─ response          Text          応答そのまま
├─ http_status       SmallInteger
├─ message           Text          要約メッセージ・エラー内容
├─ created_at        DateTime
└─ updated_at        DateTime

INDEX: (item_uuid), (agency, status), (doi), (status, updated_at)
```

**設計判断**

| 判断 | 理由 |
| --- | --- |
| 単一テーブル + `agency` カラム | 管理 UI・再送処理・集計を 1 つで書ける。エージェンシー追加時に DDL 変更が不要 |
| `payload` / `response` を保存 | 監査要件。失敗原因の調査と再送に必須 |
| `doi_select` も保持 | JaLC(1) と NDL JaLC(4) は `agency` 名が同じになりうるため、元の選択値を残す |
| `operation` カラム | 登録・更新・非公開化を同じテーブルで追跡する |

> `payload` / `response` はサイズが大きくなる（Crossref XML は最大 10MB）。
> **保持期間の方針**（例: 成功分は 90 日で `payload` を NULL 化）を運用設計で決めること（§10-4）。

---

## 7. 状態遷移とオーケストレーション

### 7-1. 状態

| 状態 | 意味 | 次の遷移 |
| --- | --- | --- |
| `pending` | ログ作成済み、未送信 | → `submitted` / `success` / `retrying` / `failure` |
| `submitted` | 受付済み、結果待ち（非同期エージェンシーのみ） | → `success` / `failure` |
| `retrying` | 一時的失敗。再試行待ち | → `pending` 相当の再実行 → 各状態 |
| `success` | 登録確定 | 終端（`update` / `hide` で新しいログが起きる） |
| `failure` | 恒久的失敗、またはリトライ上限超過 | 手動再送で `pending` に戻せる |
| `skipped` | 設定無効・未対応エージェンシー | 終端 |

```
pending ──register: SUCCEEDED──────────────> success
   │
   ├────register: ACCEPTED───> submitted ──poll: SUCCEEDED──> success
   │                              │        └─poll: ACCEPTED──> （再予約）
   │                              └─poll: FAILED────────────> failure
   │
   ├────register: RETRIABLE──> retrying ──(バックオフ後)──> pending
   │                              └──(上限超過)───────────> failure
   │
   └────register: FAILED─────────────────────────────────> failure
                                                              │
                                        failure ──手動/一括再送──> pending
```

### 7-2. フック位置

[`WACREN_crossref.md` §4-3](./WACREN_crossref.md) の検討どおり **`saving_doi_pidstore()` の末尾**。
ワークフロー経由（`views.py:2089, 2272`）とインポート経由
（`weko_search_ui/utils.py:3671, 3683, 3707`）の**全 5 箇所を 1 箇所でカバーできる**。

```python
# weko_workflow/utils.py の saving_doi_pidstore() 末尾（temporal_saving=False の分岐内）
from .doi.orchestrator import request_doi_deposit

request_doi_deposit(
    item_uuid=record_without_version,
    doi_select=doi_select,
    doi=doi_register_val,
    identifier_url=identifier_val,
)
```

`request_doi_deposit()` は**例外を外に出さない**。内部で捕捉してログに残す。

> **実装結果**: 実装済み（`weko_workflow/utils.py`）。引数は
> `request_doi_deposit(record_without_version, doi_select, doi_register_val)` の 3 つで、
> `identifier_url` は渡していない（解決先 URL はオーケストレータ側で
> `build_resource_url()` が親 recid から組み立てる）。

### 7-3. コミット競合への対策 ← **実装時の注意点**

`saving_doi_pidstore()` は呼び出し側で `db.session.commit()` される**前**に実行される。
Celery ワーカーが「まだコミットされていない PID / レコード」を読みに行くと失敗する。

**三段構えで対処する。**

1. **タスク投入に遅延を入れる** — `countdown=WEKO_DOI_SUBMIT_COUNTDOWN`（既定 10 秒）。
2. **タスク側で存在チェックとリトライ** — 対象レコードが取得できなければ
   `RETRIABLE` として短い間隔で再試行する（最大 `WEKO_DOI_NOT_FOUND_MAX_RETRY` 回）。
3. **より厳密にするなら** SQLAlchemy の `after_commit` イベントでタスクを投入する。
   ただし WEKO のセッション管理（`db.session.begin_nested()` の多用）との相性検証が必要。

初期実装は 1 + 2 で進め、問題が出たら 3 に切り替える。

> **実装結果**: 1 + 2 で実装。2 はレコード有無ではなく **`DoiDepositLog` 行の可視性**で判定し、
> 見えなければ `DepositLogNotReadyError` を投げて `WEKO_DOI_SUBMIT_COUNTDOWN` 秒後に
> Celery の `self.retry()`（最大 `WEKO_DOI_MAX_RETRY` 回）で再試行する。
> 3（`after_commit`）は採用していない。

---

## 8. メタデータ供給層

各エージェンシーの `build_payload()` が同じ入力を受け取れるよう、
JPCOAR メタデータの取得を 1 か所にまとめる。

配置: `weko_workflow/doi/metadata.py`

```python
class DoiMetadataSource:
    """JPCOAR マッピングを解決してエージェンシーに渡す共通レイヤー.

    既存の MappingData（weko_workflow/utils.py）と
    get_mapping()（weko_records）をラップする。
    """

    def __init__(self, item_uuid):
        ...

    def get(self, mapping_path, default=None):
        """'title.@value' のようなマッピングパスで値を引く."""

    def get_all(self, mapping_path):
        """多値プロパティをリストで引く."""

    def get_localized(self, mapping_path, lang=None):
        """xml:lang 付きの多言語プロパティを引く."""

    @property
    def resource_type(self):
        """dc:type の値（エージェンシー側のレコードタイプ判定に使う）."""
```

**この層を切る理由**: JPCOAR の多値・多言語・欠損の扱いは
Crossref 版・DataCite 版で共通して面倒な部分であり
（[`WACREN_crossref.md` §8-3](./WACREN_crossref.md)、[`WACREN_datacite.md` §8](./WACREN_datacite.md) の
最大のリスク要因）、ここを共通化できれば両方の工数が下がる。

---

## 9. 設定の構造

**共通設定 + エージェンシー固有設定**の 2 階層にする。

### 9-1. 共通設定

| 設定キー | 既定値 | 説明 |
| --- | --- | --- |
| **`WEKO_DOI_ALLOW_REGISTER`** | **`False`** | **API 登録機能全体のマスタースイッチ。これが False なら全エージェンシーが無効** |
| `WEKO_DOI_AGENCY_REGISTRY` | §5 の dict | `doi_select` → エージェンシー実装 |
| `WEKO_DOI_ASYNC` | `True` | Celery 経由で送信（`False` は デバッグ用） |
| `WEKO_DOI_SUBMIT_COUNTDOWN` | `10` | タスク投入の遅延（秒）。§7-3 |
| `WEKO_DOI_NOT_FOUND_MAX_RETRY` | `5` | レコード未検出時のリトライ上限 |
| `WEKO_DOI_MAX_RETRY` | `3` | 送信リトライ上限 |
| `WEKO_DOI_RETRY_DELAY` | `300` | リトライ間隔（秒、指数バックオフの基準） |
| `WEKO_DOI_POLL_DELAY` | `60` | 結果ポーリングの初回待ち（秒） |
| `WEKO_DOI_POLL_MAX_ATTEMPTS` | `20` | ポーリング上限回数 |
| `WEKO_DOI_RESOURCE_URL_PATTERN` | `'{root_url}records/{recid}'` | ランディングページ URL |
| `WEKO_DOI_DRY_RUN` | `False` | ペイロード生成とログ記録のみ行い送信しない |
| `WEKO_DOI_NOTIFY_EMAIL` | `None` | 失敗時の通知先 |
| `WEKO_DOI_PAYLOAD_RETENTION_DAYS` | `90` | 成功ログの `payload` を保持する日数（§10-4） |

> **実装結果**（`weko_workflow/config.py`）: 実装されたのは次の 8 キー。
>
> | 実装された設定キー | 既定値 | 上表との対応 |
> | --- | --- | --- |
> | `WEKO_DOI_AGENCIES` | `{'2': '…CrossrefAgency'}` | `WEKO_DOI_AGENCY_REGISTRY` を改名 |
> | `WEKO_DOI_SUBMIT_COUNTDOWN` | `10` | 同名 |
> | `WEKO_DOI_MAX_RETRY` | `3` | 同名。`WEKO_DOI_NOT_FOUND_MAX_RETRY` も兼ねる |
> | `WEKO_DOI_RETRY_COUNTDOWN` | `60` | `WEKO_DOI_RETRY_DELAY` を改名・既定値変更 |
> | `WEKO_DOI_FIRST_POLL_DELAY` | `60` | `WEKO_DOI_POLL_DELAY` を改名 |
> | `WEKO_DOI_POLL_INTERVAL` | `300` | **新設**（2 回目以降のポーリング間隔） |
> | `WEKO_DOI_MAX_POLL_ATTEMPTS` | `20` | `WEKO_DOI_POLL_MAX_ATTEMPTS` を改名 |
> | `WEKO_DOI_NOTIFY_EMAIL` | `None` | 同名 |
>
> **未実装**: `WEKO_DOI_ALLOW_REGISTER`（全体マスタースイッチ。エージェンシー単位の
> スイッチで足りると判断）、`WEKO_DOI_ASYNC`、`WEKO_DOI_DRY_RUN`、
> `WEKO_DOI_RESOURCE_URL_PATTERN`（`orchestrator.build_resource_url()` で
> `{root_url}records/{親 recid}` 固定）、`WEKO_DOI_PAYLOAD_RETENTION_DAYS`（§16-4 は未決のまま）。
>
> これらのキーは `weko_workflow/ext.py` で `WEKO_DOI_` / `WEKO_CROSSREF_` プレフィックスごと
> app.config へ流し込まれる。

### 9-2. エージェンシー固有設定

各エージェンシーの文書で定義する。命名は `WEKO_<AGENCY>_*` に揃える。

- Crossref: [`WACREN_crossref.md` §5](./WACREN_crossref.md) の `WEKO_CROSSREF_*`
- DataCite: [`WACREN_datacite.md` §6](./WACREN_datacite.md) の `WEKO_DATACITE_*`

### 9-3. 有効性の判定順序

```
WEKO_DOI_ALLOW_REGISTER が False              → 全体オフ（skipped）
  ↓ True
WEKO_DOI_AGENCY_REGISTRY に実装が無い          → 未対応（skipped）
  ↓ あり
agency.is_allowed() が False
  ├─ WEKO_<AGENCY>_ALLOW_REGISTER_DOI が False → そのエージェンシーのみオフ（skipped）
  └─ 必須設定が欠けている                       → ERROR ログ + skipped
  ↓ True
doi_identifier.jalc_<agency>_flag が False     → リポジトリ単位でオフ（skipped）
  ↓ True
実行
```

既存の `doi_identifier` テーブル（`jalc_crossref_flag` / `jalc_datacite_flag`）を
**リポジトリ単位のスイッチとしてそのまま流用する**。新しいカラムは追加しない。

> **実装結果**: 実際の判定は 2 段階のみ。
>
> ```
> WEKO_DOI_AGENCIES に doi_select の登録が無い     → 何もしない（ログ行も作らない）
>   ↓ あり
> agency.is_allowed() が False
>   ├─ WEKO_CROSSREF_ALLOW_REGISTER_DOI が False   → 何もしない
>   └─ 必須設定（7 キー）が欠けている               → ERROR ログを出して何もしない
>   ↓ True
> 実行
> ```
>
> `WEKO_DOI_ALLOW_REGISTER` による全体オフと、`doi_identifier.jalc_*_flag` による
> リポジトリ単位のオフは**実装していない**。後者は「DOI 付与そのものの可否」を既に制御しており、
> 付与された DOI を登録しない用途は現状無いと判断したため。
> `skipped` というログ状態も持たない（送らない場合は行を作らない）。

---

## 10. エラー分類

`DepositStatus` への振り分けを共通の判定関数にまとめ、各エージェンシーから使う。

配置: `weko_workflow/doi/errors.py`

| 事象 | 分類 | 根拠 |
| --- | --- | --- |
| HTTP 5xx | `RETRIABLE` | サーバ側の一時障害 |
| HTTP 429 | `RETRIABLE` | Crossref のキュー上限（保留 10,000 件）。時間をおけば解消 |
| 接続タイムアウト / 名前解決失敗 | `RETRIABLE` | ネットワーク一時障害 |
| HTTP 401 / 403 | `FAILED` | 認証情報の誤り。再試行しても解消しない。**要即時通知** |
| HTTP 400 / 422 | `FAILED` | ペイロード不正 |
| `build_payload()` の `DoiPayloadError` | `FAILED` | 必須メタデータ不足 |
| Crossref `record_diagnostic status="Failure"` | `FAILED` | 登録機関側が明示的に拒否 |
| 対象レコードが未コミット（§7-3） | `RETRIABLE` | 短い間隔で再試行 |

**通知方針**: `FAILED` のうち認証エラーは即時通知（設定ミスは全件失敗に直結するため）。
それ以外の `FAILED` は日次サマリで通知する。

---

## 11. 新しいエージェンシーを追加する手順

**共通基盤に手を入れずに完結すること**が本設計のゴール。

1. `weko_workflow/doi/agencies/<name>.py` に `DoiRegistrationAgency` の実装クラスを書く。
   - `key` / `name` / `capabilities` を定義
   - `is_allowed()` / `build_payload()` / `register()` を実装
   - 非同期なら `poll()`、更新対応なら `update()`、非公開化対応なら `hide()` を追加実装
2. `weko_workflow/config.py` に `WEKO_<AGENCY>_*` の設定キーを追加。
3. `WEKO_DOI_AGENCY_REGISTRY` に `doi_select` → クラスパスを登録。
4. テストを書く（§12）。

**オーケストレータ・テーブル・Celery タスク・管理 UI の変更は不要。**

> **実装結果**: 実際の基底クラス（`doi/base.py`）が持つのは `name` / `capabilities` と
> `is_allowed()` / `validate()` / `build_payload()` / `register()` / `poll()`。
> 設計時の `key` 属性は無く（レジストリのキーは `WEKO_DOI_AGENCIES` の dict のキー）、
> `update()` / `hide()` も未定義（DOI 更新・非公開化が未実装のため）。
> `validate(source) -> List[str]` は設計時になかったが、送信前にメタデータを弾くために追加した。
> 手順 3 の登録先は **`WEKO_DOI_AGENCIES`**。

---

## 12. テスト戦略

| レベル | 対象 | 方針 |
| --- | --- | --- |
| ユニット | `build_payload()` | 実データに近いアイテムメタデータの fixture から生成し、期待ペイロードと突き合わせる。Crossref は XSD 検証、DataCite は必須項目の存在検証 |
| ユニット | `DoiMetadataSource` | 多値・多言語・欠損の各パターン |
| ユニット | エラー分類 | HTTP ステータス → `DepositStatus` の対応表を網羅 |
| 結合（モック） | オーケストレータ | **`FakeAgency` を用意し、`SUCCEEDED` / `ACCEPTED` / `RETRIABLE` / `FAILED` を返させて状態遷移を検証する。実 API を叩かない** |
| 結合（実 API） | 各エージェンシー | テスト系（`test.crossref.org` / `api.test.datacite.org`）へ実際に投入 |
| 回帰 | `saving_doi_pidstore()` | **`WEKO_DOI_ALLOW_REGISTER=False` のとき既存挙動が一切変わらないこと** |

> `FakeAgency` による状態遷移テストが最も費用対効果が高い。
> 同期・非同期の両パターンを実 API なしで検証でき、
> 新エージェンシー追加時の回帰テストにもそのまま使える。

> **実装結果**（`modules/weko-workflow/tests/test_doi.py`、24 ケース）:
>
> - **`FakeAgency` は用意しなかった。** 状態遷移テストは `CrossrefAgency` を通し、
>   `requests.post` / `requests.get` をパッチして `ACCEPTED` / `FAILED` / `unknown` を検証している。
>   そのため**同期エージェンシー（`SUCCEEDED` を直接返す経路）のテストはまだ無い**。
>   DataCite 実装時に `FakeAgency` を入れるのが望ましい。
> - 実 API（`test.crossref.org`）への投入は手動で実施済み。自動テストには含めていない。
> - XSD 検証は自動テストに組み込んでいない（生成 XML の要素・属性を突き合わせるかたち）。
> - `DoiMetadataSource` は `FakeMappingData` 経由で多値・多言語・欠損を検証。
> - 回帰（`saving_doi_pidstore()` の既存挙動）は、エージェンシー未設定・
>   `is_allowed()` が False のとき何も起きないことで担保している。

---

## 13. 管理 UI

> **状況: 未実装。** 現状は CLI（`weko_workflow/cli.py`）のみ。
>
> - `weko workflow doi list [--status <status>] [--limit N]`
> - `weko workflow doi resend <log_id>` — 1 件ずつ再送（`pending` に戻して再投入）
>
> §13-2 にある `--agency` / `--since` での絞り込みや一括再送はまだ無い。
> 失敗通知は `WEKO_DOI_NOTIFY_EMAIL` 宛のメールのみ。

`weko-admin` に「DOI 登録」画面を 1 つ作る。**エージェンシーごとに画面を作らない。**

### 13-1. 設定画面

- 全体の有効/無効（`WEKO_DOI_ALLOW_REGISTER`）
- エージェンシー別の状態一覧（有効/無効、接続先が本番かテストか、必須設定の充足状況）
- 認証情報の表示（パスワードはマスク）
- **疎通テストボタン** — エージェンシーごとに軽量なリクエストで認証を確認

### 13-2. 登録状況の一覧・再送

`doi_deposit_log` の Flask-Admin モデルビュー。

- 絞り込み: `agency` / `status` / `doi` / アイテム / 期間
- 各行: 送信ペイロード・応答の表示、**手動再送**
- 一括操作: 条件に合致する `failure` の一括再送
- CLI: `invenio weko doi resend --agency=crossref --status=failure --since=2026-08-01`

---

## 14. ファイル構成

```
modules/weko-workflow/weko_workflow/
├─ doi/
│  ├─ __init__.py
│  ├─ base.py            DoiRegistrationAgency, DepositRequest/Result, Capabilities
│  ├─ errors.py          例外定義とエラー分類
│  ├─ registry.py        get_agency()
│  ├─ metadata.py        DoiMetadataSource
│  ├─ orchestrator.py    request_doi_deposit() ほか
│  ├─ tasks.py           deposit_doi / poll_doi_deposit / retry_failed_deposits
│  └─ agencies/
│     ├─ __init__.py
│     ├─ crossref.py     CrossrefAgency   （WACREN_crossref.md）
│     └─ datacite.py     DataCiteAgency   （WACREN_datacite.md）
├─ models.py             DoiDepositLog を追記
├─ config.py             WEKO_DOI_* / WEKO_CROSSREF_* / WEKO_DATACITE_* を追記
├─ utils.py              saving_doi_pidstore() にフックを追記
└─ alembic/
   └─ xxxx_add_doi_deposit_log.py
```

> **実装結果**（`23af9ad4`）: 上記のうち `agencies/datacite.py` 以外は実装済み。
>
> ```
> modules/weko-workflow/weko_workflow/
> ├─ doi/
> │  ├─ __init__.py          44 行
> │  ├─ base.py             174 行
> │  ├─ errors.py            71 行
> │  ├─ registry.py          56 行  get_agency() / is_supported()
> │  ├─ metadata.py         396 行  DoiMetadataSource
> │  ├─ orchestrator.py     282 行  request_doi_deposit() / run_deposit() / run_poll() / notify_failure()
> │  ├─ tasks.py            116 行  deposit_doi / poll_doi_deposit / resend_doi_deposit
> │  └─ agencies/
> │     ├─ __init__.py
> │     ├─ crossref.py            346 行
> │     └─ crossref_mapper.py     305 行  ← 設計時に無かった分割
> ├─ models.py             DoiDepositLog（+63 行）
> ├─ config.py             WEKO_DOI_* / WEKO_CROSSREF_*（+75 行）
> ├─ utils.py              saving_doi_pidstore() のフック（+5 行）
> ├─ tasks.py              doi/tasks.py の再エクスポート（+1 行）
> ├─ ext.py                WEKO_DOI_ / WEKO_CROSSREF_ プレフィックスの読み込み
> ├─ cli.py                weko workflow doi list / resend（+39 行）
> └─ alembic/
>    └─ b1c7d3f9a204_add_doi_deposit_log.py   （down_revision: f312b8c2839a）
> ```
>
> 差分: `retry_failed_deposits`（定期リトライ）は実装せず、代わりに手動再送の
> `resend_doi_deposit` を置いた。`agencies/datacite.py` は未作成。

> **配置理由**: `saving_doi_pidstore()` / `IdentifierHandle` / `item_metadata_validation()` が
> すべて `weko-workflow` にあり、ARK 対応も同モジュールに追加した実績がある。
> `doi/` サブパッケージに閉じることで、将来 `weko-doi` として切り出す余地も残す。

---

## 15. 段階導入計画

> **実績は §0 を参照。** A と C が完了、D は CLI と通知のみ、B と E は未着手。
> 以下は当初の計画と見積。

| Phase | 内容 | 前提 | 人日 |
| --- | --- | --- | --- |
| **A. 基盤** | `base.py` / `errors.py` / `registry.py` / `metadata.py` / `orchestrator.py` / `tasks.py` / `DoiDepositLog` + alembic / `saving_doi_pidstore()` フック / `FakeAgency` によるテスト | なし | **6〜9** |
| **B. DataCite** | `DataCiteAgency`（同期・JSON）。基盤の検証を兼ねる | A、DataCite テスト account | **5〜8** |
| **C. Crossref** | `CrossrefAgency`（非同期・XML・ポーリング） | A、Crossref テスト account | **12〜18** |
| **D. 管理 UI** | 設定画面・一覧・再送・CLI・通知 | A | **4〜6** |
| **E. 将来** | `JalcAgency` / `NdlJalcAgency`、ARK の統合（§16-5） | A | — |

**合計: 27〜41 人日**

### 15-1. 独立実装との比較

| 進め方 | 工数 |
| --- | --- |
| Crossref 単独（[`WACREN_crossref.md` §8-1](./WACREN_crossref.md)） | 35〜56 人日 |
| DataCite 単独（[`WACREN_datacite.md` §8](./WACREN_datacite.md)） | 14〜23 人日 |
| **独立に両方実装（単純合計）** | **49〜79 人日** |
| **共通基盤ありで両方実装（A〜D）** | **27〜41 人日** |

**共通基盤の初期投資 6〜9 人日に対し、2 つ目の実装以降で回収できる。**
3 つ目（JaLC）を足す時点では差がさらに開く。

### 15-2. 実装順序 ← **B（DataCite）を C（Crossref）より先に**

[`WACREN_datacite.md` §9](./WACREN_datacite.md) の判断を踏襲する。

1. **DataCite のテストアカウントが先に手に入る**（非会員でも発行される）。
2. **同期 API + JSON で最も単純**なため、基盤（フック位置・状態遷移・コミット競合対策）の
   検証を安いコストで済ませられる。
3. その上に Crossref を載せる際、**非同期・ポーリングという難しい側だけに集中できる**。
4. 逆順だと非同期前提で作った抽象に同期 API を後付けすることになり、インターフェースが歪む。

ただし **Phase A の設計時点で Crossref の非同期要件を織り込んでおく**こと
（`ACCEPTED` / `poll()` / `requires_polling` は最初から用意する）。
これを後付けにすると §4-3 の分岐がオーケストレータ外に漏れる。

> **実際の経緯（2026-09-01）**: Crossref のテストアカウントが先に取得できたため、
> **推奨と逆の A + C（Crossref）から実装した**。§4-3 の抽象を最初から入れていたので
> インターフェースの歪みは生じていないが、裏返しの副作用として
> **同期経路（`DepositStatus.SUCCEEDED` を `register()` が直接返す流れ）は
> まだ実コードでもテストでも通っていない**。DataCite 実装時にここが最初の検証点になる。

---

## 16. 未決事項

### 16-1. 会員資格・プレフィックス

Crossref・DataCite とも WACREN 側機関の会員資格が未確定
（[`WACREN_crossref.md` §9-1](./WACREN_crossref.md)、[`WACREN_datacite.md` §10-1](./WACREN_datacite.md)）。
**Phase A は会員資格と無関係に着手できる。**

> **2026-09-01 時点**: Crossref はサービスプロバイダ経路でテストアカウントを取得し、
> テスト系での検証まで完了。**会員資格・DOI プレフィックスは依然として未確定**で、
> 本番系への登録はできない。DataCite のテストアカウントは未取得。

### 16-2. 認証情報の格納場所

[`WACREN_crossref.md` §5-2](./WACREN_crossref.md) の案 A（設定ファイル）/ 案 B（DB + 管理画面）。
共通基盤としては**どちらでも動くように、`is_allowed()` と設定読み出しをエージェンシー側に閉じる**。
初期実装は案 A。マルチテナント要件が出た時点で案 B に拡張する。

> **実装結果**: 案 A（設定ファイル）。`CrossrefAgency.is_allowed()` が
> `WEKO_CROSSREF_*` の必須 7 キーの充足を確認し、欠けていれば ERROR ログを出して送信しない。

### 16-3. DOI 付与時の検証と登録要件の不一致

`DOI_VALIDATION_INFO_*` の必須項目は、各登録機関の実際の必須要素と一致していない
（[`WACREN_crossref.md` §9-5](./WACREN_crossref.md)、[`WACREN_datacite.md` §10-6](./WACREN_datacite.md)）。
その結果「ワークフローの承認は通るが API 登録だけ失敗する」アイテムが発生する。

**対応案**: エージェンシーに `validate(source) -> List[str]` を追加し、
DOI 付与アクションの検証時にも同じ関数を呼ぶ。
これにより「登録できないメタデータでは DOI を付与させない」を実現できる。
**ただし既存の検証挙動を変えるため、影響範囲の調査が必要。Phase A のスコープ外とする。**

### 16-4. ログの保持期間

`payload` / `response` は大きい（Crossref XML は最大 10MB）。
成功ログの `payload` を一定期間後に NULL 化するバッチ
（`WEKO_DOI_PAYLOAD_RETENTION_DAYS`）の要否と既定値を決める。

> **2026-09-01 時点: 未解決・未実装。** `payload` / `response` は無期限に残る。

### 16-5. ARK / Handle の統合

ARK（`register_ark_by_item_id`）と Handle（`register_hdl_by_item_id`）も
「外部サービスへの識別子登録」という点では同じ構造を持つ。
将来この基盤に寄せられるが、
**DOI とは付与タイミング・状態モデル・エラー許容度が異なるため、今回のスコープ外とする。**
Phase A の設計時に「DOI 専用」と割り切るか、
より一般的な `IdentifierRegistrationAgency` にするかは判断が必要。

> 現時点の判断: **DOI 専用で切る。** ARK / Handle は失敗しても再送需要が薄く、
> 状態管理テーブルを持つほどの複雑さがない。無理に一般化すると抽象が緩くなる。

### 16-6. 既存 DOI の一括登録

API 登録を有効化する以前に付与済みの DOI を遡って登録するバッチ（CLI）の要否。
共通基盤があれば `agency` を指定して流すだけで済むため、実装は軽い（1〜2 人日）。

> **2026-09-01 時点: 未実装。** CLI にあるのは `list` / `resend` のみ。

---

## 17. 関連文書

- [`WACREN_crossref.md`](./WACREN_crossref.md) — Crossref 固有仕様（テスト環境・XML マッピング・非同期デポジット）
- [`WACREN_datacite.md`](./WACREN_datacite.md) — DataCite 固有仕様（テスト環境・JSON マッピング・同期 REST）
- [`WACREN.md`](./WACREN.md) — 本ブランチと v2.0.3 の差分
