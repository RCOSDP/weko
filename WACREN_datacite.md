# DataCite DOI の API 登録対応 — 仕様検討

WEKO3 で DataCite DOI が付与された際に、DataCite REST API を叩いて実際に DOI を登録する機能の設計案。

- 対象ブランチ: `feature/nii_WACREN_crossref_doi`（設計時: `feature/nii_WACREN_pre`）
- 作成日: 2026-08-04 / 最終更新: 2026-09-01
- ステータス: **未実装（共通基盤と Crossref は実装済み。残るのは `DataCiteAgency` のみ）**
- 関連文書: [`WACREN_crossref.md`](./WACREN_crossref.md) — **共通アーキテクチャ（フック位置・非同期化・ステータス管理・エラー方針）は同文書 §4 を参照**。本書は DataCite 固有の差分を扱う。

---

## 0-0. 実装状況（2026-09-01 時点）

**DataCite 対応そのものは未着手。** ただし前提が変わっている。

- 共通基盤（`weko_workflow/doi/`）と Crossref アダプタは実装・テスト系検証まで完了
  （`23af9ad4`、[`WACREN_doi_registration.md` §0](./WACREN_doi_registration.md)）
- したがって**残る作業は `doi/agencies/datacite.py` の追加と
  `WEKO_DOI_AGENCIES` への `'3'` の登録、`WEKO_DATACITE_*` 設定の追加のみ**。
  フック・状態管理テーブル・Celery タスク・リトライ・CLI・失敗通知はそのまま流用できる
  （[`WACREN_doi_registration.md` §11](./WACREN_doi_registration.md) の手順）
- 見積は §8 の「Crossref を先に実装済みの場合」の **5〜8 人日**が該当する
- **§9 の「DataCite を先に」という推奨は実現しなかった**（Crossref のテストアカウントが
  先に取れたため A + C から着手した）。その結果、共通基盤の**同期経路
  （`register()` が `DepositStatus.SUCCEEDED` を直接返す流れ）はまだ一度も通っていない**。
  DataCite 実装時に最初に検証すべき箇所。
- DataCite のテストアカウントは未取得（§2-2 の申請は未実施）

---

## 0. 結論（先に要点）

1. **DataCite は Crossref より圧倒的に実装が容易。** 同期 REST API + JSON で、必須項目は 5 つだけ。
   Crossref のような XML スキーマ・レコードタイプ別マッピング・結果ポーリングが不要。
2. **テストアカウントが即座に取れる。** 非会員でも `support@datacite.org` に依頼すれば発行される。
   Crossref のような会員資格の前提がない。
3. **したがって、DataCite を先に実装することを推奨する。**
   共通アーキテクチャ（フック位置・ステータス管理・設定パターン・管理 UI）を安いコストで検証でき、
   その上に Crossref を載せる方が全体の手戻りが少ない（§9）。
4. 既存資産として `datacite==1.0.1` が依存に入っているが、**REST クライアントは含まれない**（§2-1）。

---

## 1. 現状の整理

DOI 処理フロー自体は Crossref と共通。`saving_doi_pidstore()` が
`doi_register_typ = 'DataCite'` としてメタデータと PID ストアに書き込むのみで、
**DataCite の API は一切呼んでいない**（[`WACREN_crossref.md` §1-1](./WACREN_crossref.md)）。

### 1-1. 既存の DataCite 関連実装

| 箇所 | 内容 | 現在の利用状況 |
| --- | --- | --- |
| `packages.txt:28` / `requirements-devel.txt:45` | `datacite==1.0.1`（Python ライブラリ） | **依存には入っているが、WEKO 本体からは未使用** |
| `modules/invenio-records-rest/invenio_records_rest/serializers/datacite.py` | `DataCite31Serializer` / `DataCite40Serializer` / `DataCite41Serializer` / `OAIDataCiteSerializer` | **invenio-records-rest 自身のテストからのみ参照**。WEKO の本番パスでは未使用 |
| `weko-admin` `Identifier` モデル | `jalc_datacite_doi`（プレフィックス）、`jalc_datacite_flag`（有効/無効） | 管理画面から設定可 |
| `weko-workflow/config.py` | `IDENTIFIER_GRANT_SELECT_DICT` の `'DataCite': '3'` | 使用中 |
| `weko-workflow/config.py` | `DOI_VALIDATION_INFO_DATACITE` | DOI 付与時のメタデータ検証で使用中 |
| `weko-workflow/utils.py` `item_metadata_validation()` | DataCite は **`dataset_type` のみ**を対象とし、必須は `title` / `type` / `fileURI` | 使用中 |
| `weko-workspace/config.py:315` | `WEKO_WORKSPACE_DATACITE_API_URL = 'https://api.datacite.org/dois/'` | **メタデータ取得（参照系）のみ** |

> WEKO の既存フィールド名も `jalc_datacite_doi`＝「JaLC 経由の DataCite DOI」を意味する。
> Crossref と同じく、直接会員として登録する場合は前提が異なる（§10-1）。

### 1-2. `datacite==1.0.1` の中身 ← **注意**

このライブラリは名前に反して **MDS API 専用**で、REST クライアントを含まない。

| 含まれるもの | 含まれないもの |
| --- | --- |
| `DataCiteMDSClient`（`doi_get` / `doi_post` / `metadata_get` / `metadata_post` / `metadata_delete` / `media_get` / `media_post`） | **`DataCiteRESTClient`**（ライブラリ 1.1.0 以降で追加） |
| `schema31` / `schema40` / `schema41`（`validate()` / `tostring()` / `dump_etree()`） | `schema42` 以降 |

**選択肢**

| 案 | 内容 | 評価 |
| --- | --- | --- |
| **A. `requests` で直接実装** | REST API は Basic 認証 + JSON POST/PUT のみ。クライアントは 50〜80 行程度 | **◎ 推奨**。依存を増やさず、WEKO の脆いバージョン固定を触らずに済む |
| B. `datacite` を 1.1.0+ に更新 | `DataCiteRESTClient` が使える | △ WEKO は Python 3.6 固定（`Dockerfile` の `python:3.6-slim-buster`）。依存解決のリスクあり |
| C. 既存 1.0.1 の MDS クライアントを使う | 追加依存ゼロ | △ MDS API は保守のみで新規開発は停止（§4-2） |

---

## 2. DataCite のテスト環境

### 2-1. 概要

DataCite のテスト環境は本番と**完全に分離された sandbox**。

| 項目 | 内容 |
| --- | --- |
| Fabrica（管理 UI） | `https://doi.test.datacite.org` |
| REST API | `https://api.test.datacite.org` |
| MDS API | `https://mds.test.datacite.org` |
| DOI 解決 | `https://handle.test.datacite.org/<doi>` |
| 認証情報 | **本番とは別**。Repository ID / パスワード / プレフィックスすべて別系統 |
| DOI の解決 | **テスト用 handle サーバで実際に解決する**（メタデータ内のランディングページへ） |
| データの保全 | **保証されない。** 本番ワークフローに組み込んではいけない |
| 削除 | 本番では Registered / Findable の DOI は削除不可。テスト環境は制約が緩い |

### 2-2. テストアカウントの取得方法 ← **Crossref より容易**

| 立場 | 取得方法 |
| --- | --- |
| Direct Member / Consortium Lead | オンボーディング時に DataCite スタッフが作成 |
| Direct Member 配下の Repository | **Direct Member 自身が Fabrica から作成可能** |
| **未加入（加盟検討中）** | **`support@datacite.org` に依頼すれば DataCite スタッフが作成する** |

> "DataCite staff can also create test accounts for potential Members who have not yet joined.
> If you are considering membership and would like a test account, please contact DataCite support
> at support@datacite.org."
> — [Get a test account](https://support.datacite.org/docs/getting-a-test-account)

**必要なのは Repository アカウント**（DOI の作成・更新権限を持つのはこの種別のみ）。

**手順**

1. `support@datacite.org` にメールを送る（文面は §2-3）。
2. パスワード設定リンク付きの自動メールが届く。
3. Fabrica Test (`https://doi.test.datacite.org`) でパスワードを設定。
4. Account ID（Repository ID）とパスワードでサインインして疎通確認。

### 2-3. 申請メール文面

**To:** support@datacite.org
**Subject:** `Request for a test Repository account — WEKO3 repository software`

```
Dear DataCite Support,

We are the development team of WEKO3, an open-source institutional repository
software developed and maintained by the National Institute of Informatics
(NII) in Japan. WEKO3 is the platform behind JAIRO Cloud, a hosted repository
service used by several hundred Japanese institutions, and it is also deployed
by institutions outside Japan.

We are implementing an automated DOI registration feature in WEKO3 using the
DataCite REST API, so that repositories running our software can register DOIs
directly with DataCite. We would like to verify this integration against your
test environment.

Could you please create a test Repository account for us?

  Software / service    : WEKO3 (https://github.com/RCOSDP/weko)
  Operating organisation: National Institute of Informatics (NII), Japan
  Hosted service        : JAIRO Cloud (https://jpcoar.repo.nii.ac.jp/)
  Contact name          : <担当者名>
  Contact email         : <担当者メール>
  Role                  : <役職・立場>

We plan to use:

  - POST https://api.test.datacite.org/dois  (Content-Type: application/vnd.api+json)
  - PUT  https://api.test.datacite.org/dois/{doi}
  - DataCite Metadata Schema 4.x

We are not currently a DataCite member; we are evaluating the integration on
behalf of the institutions that run our software.

Thank you very much for your help.

Best regards,
<氏名>
<所属・役職>
National Institute of Informatics
```

> Crossref の申請（[`WACREN_crossref.md` §2-5](./WACREN_crossref.md)）と**同時に出してよい**。
> DataCite の方が早く返ってくる見込みが高く、先に着手できる。

---

## 3. DataCite REST API

### 3-1. DOI の作成

```
POST https://api.test.datacite.org/dois
Content-Type: application/vnd.api+json
Authorization: Basic <base64(REPOSITORY_ID:PASSWORD)>
```

```json
{
  "data": {
    "type": "dois",
    "attributes": {
      "event": "publish",
      "doi": "10.xxxxx/weko.123",
      "url": "https://research.ren.ng/records/123",
      "titles": [{ "title": "An example item" }],
      "creators": [{ "name": "Yamada, Taro" }],
      "publisher": "Example University",
      "publicationYear": 2026,
      "types": { "resourceTypeGeneral": "Text" }
    }
  }
}
```

- 成功時は **`201 Created`** と登録後のメタデータ全体が返る。**同期処理でその場で完結する。**
- `doi` を省略して `prefix` のみ指定すると、**サフィックスが自動採番**される。
  WEKO は自前でサフィックスを組み立てるので、通常は `doi` を明示する。

### 3-2. Findable DOI の必須メタデータ — **5 項目のみ**

| 属性 | 内容 |
| --- | --- |
| `creators` | 作成者 |
| `titles` | タイトル |
| `publisher` | 公開者 |
| `publicationYear` | 公開年 |
| `types.resourceTypeGeneral` | 資源タイプ |
| （`url`） | ランディングページ URL |

Crossref のようなレコードタイプ別の必須要素は無い。**この差が実装コストを大きく分ける。**

### 3-3. DOI の状態と `event`

| 状態 | 意味 | 遷移方法 |
| --- | --- | --- |
| **Draft** | 非公開・未登録。`event` を付けずに作成 | 作成時に `event` 省略 |
| **Registered** | handle サーバに登録済みだが検索には出ない | `"event": "register"` |
| **Findable** | 公開・検索可能 | `"event": "publish"` |

- `"event": "hide"` で Findable → Registered に戻せる。
- **Crossref と違い、DOI を「隠す」手段がある**ため、
  WEKO のアイテム非公開・削除への対応が Crossref よりきれいに書ける（[`WACREN_crossref.md` §9-3](./WACREN_crossref.md) の課題が緩和される）。

> WEKO のワークフローとの対応づけ案:
> 一時保存 → **Draft**、承認・公開 → **`publish`（Findable）**、アイテム非公開 → **`hide`**

### 3-4. DOI の更新

```
PUT https://api.test.datacite.org/dois/{doi}
Content-Type: application/vnd.api+json
```

```json
{ "data": { "type": "dois", "attributes": { "event": "publish" } } }
```

- **ペイロードに含めた属性だけが更新される**（部分更新可）。全メタデータの再送信は不要。
- Crossref のような「`timestamp` を大きくして全体を再デポジット」という方式より扱いやすい。

### 3-5. MDS API（旧方式）

`https://mds.test.datacite.org` / `https://mds.datacite.org`。
`datacite==1.0.1` の `DataCiteMDSClient` が対応しているのはこちら。

**保守はされているが新規開発は停止している**ため、新規実装では REST API を選ぶ。
既存依存を使い回せる利点はあるが、XML（DataCite Metadata Schema）の生成が必要になり、
REST + JSON より手間が増える。

---

## 4. Crossref との比較

| 観点 | Crossref | DataCite |
| --- | --- | --- |
| プロトコル | XML を multipart/form-data で POST | **REST（JSON:API）** |
| 認証 | フォームパラメータ `login_id` / `login_passwd` | **HTTP Basic 認証** |
| 同期性 | **非同期**（受付のみ。`submissionDownload` をポーリング） | **同期**（`201` で完了） |
| ペイロード | Crossref schema 5.4.0 XML。レコードタイプ別（`journal_article` / `dissertation` / `posted_content` / `book` …） | JSON。**レコードタイプ別の分岐なし** |
| 必須メタデータ | レコードタイプごとに多数 | **5 項目のみ**（§3-2） |
| 状態管理 | サブミッションログを解析して成否判定 | `draft` / `registered` / `findable` を `event` で制御 |
| 更新 | 全体を再デポジット（`timestamp` で上書き） | **部分更新（PUT）** |
| 非公開化・削除 | **削除不可。** 解決先 URL 変更のみ | **`hide` で Registered に戻せる** |
| テストアカウント | `support@crossref.org` へ依頼。サービスプロバイダ経路なら会員資格不要 | **`support@datacite.org` へ依頼。非会員でも発行される** |
| 既存資産 | なし | `datacite` ライブラリ（MDS のみ）、DataCite シリアライザ（未使用） |
| **実装工数（MVP）** | **20〜30 人日** | **8〜13 人日**（§8） |

---

## 5. 実装方針

**共通アーキテクチャ（フック位置・Celery 非同期化・ステータス管理テーブル・エラー方針）は
[`WACREN_crossref.md` §4](./WACREN_crossref.md) と同一。** ここでは差分のみ記す。

### 5-1. 追加ファイル

| ファイル | 役割 |
| --- | --- |
| `modules/weko-workflow/weko_workflow/datacite_client.py` | DataCite REST API クライアント（`requests` で直接実装、§1-2 案 A） |
| `modules/weko-workflow/weko_workflow/datacite_mapper.py` | JPCOAR メタデータ → DataCite JSON 変換 |
| `modules/weko-workflow/weko_workflow/datacite.py` | 登録の入口・可否判定 |
| `models.py` / `tasks.py` / `config.py`（追記） | Crossref と**共通のテーブル・タスク基盤を流用**（§9） |

### 5-2. Crossref との差分

| 項目 | 差分 |
| --- | --- |
| 結果ポーリング | **不要**。`201` のレスポンスで確定するため `poll_*` タスクを作らない |
| ステータス | `pending` → `success` / `failure` の 2 段階で済む（`submitted` 中間状態が不要） |
| XML 生成 | 不要。`orjson` で JSON を組むだけ |
| レコードタイプ分岐 | 不要。`resourceTypeGeneral` を 1 つ決めるだけ |
| 非同期化 | 同期 API なので Celery は必須ではないが、**外部 API 呼び出しをリクエストスレッドから外す目的で使う**（タイムアウト時にワークフローを止めないため） |

---

## 6. 設定項目

Crossref（[`WACREN_crossref.md` §5](./WACREN_crossref.md)）と同じ命名パターンに揃える。

| 設定キー | 既定値 | 説明 |
| --- | --- | --- |
| **`WEKO_DATACITE_ALLOW_REGISTER_DOI`** | **`False`** | **API 経由の DOI 登録のマスタースイッチ** |
| `WEKO_DATACITE_API_URL` | `'https://api.test.datacite.org'` | **既定をテスト系にして事故を防ぐ** |
| `WEKO_DATACITE_REPOSITORY_ID` | `None` | Repository アカウント ID |
| `WEKO_DATACITE_PASSWORD` | `None` | パスワード |
| `WEKO_DATACITE_PREFIX` | `None` | DOI プレフィックス |
| `WEKO_DATACITE_EVENT` | `'publish'` | `publish` / `register` / （空で Draft） |
| `WEKO_DATACITE_SCHEMA_VERSION` | `'4.4'` | 生成するメタデータのスキーマ版 |
| `WEKO_DATACITE_TIMEOUT` | `30` | HTTP タイムアウト（秒） |
| `WEKO_DATACITE_ASYNC` | `True` | Celery 経由で送信 |
| `WEKO_DATACITE_MAX_RETRY` | `3` | リトライ上限 |
| `WEKO_DATACITE_RETRY_DELAY` | `300` | リトライ間隔（秒） |
| `WEKO_DATACITE_RESOURCE_URL_PATTERN` | `'{root_url}records/{recid}'` | `url` 属性 |
| `WEKO_DATACITE_DEFAULT_RESOURCE_TYPE` | `'Text'` | 判定できない場合の `resourceTypeGeneral` |
| `WEKO_DATACITE_RESOURCE_TYPE_MAP` | §7-1 の dict | WEKO 資源タイプ → `resourceTypeGeneral` |
| `WEKO_DATACITE_HIDE_ON_UNPUBLISH` | `False` | アイテム非公開時に `event: hide` を送るか |
| `WEKO_DATACITE_UPDATE_ON_EDIT` | `False` | メタデータ更新時に PUT で同期するか |
| `WEKO_DATACITE_DRY_RUN` | `False` | JSON 生成とログ記録のみ行い送信しない |
| `WEKO_DATACITE_NOTIFY_EMAIL` | `None` | 失敗時の通知先 |

可否判定は ARK / Crossref と同じパターン。

```python
def is_datacite_registration_allowed():
    if not current_app.config.get('WEKO_DATACITE_ALLOW_REGISTER_DOI'):
        return False
    required = ('WEKO_DATACITE_API_URL', 'WEKO_DATACITE_REPOSITORY_ID',
                'WEKO_DATACITE_PASSWORD', 'WEKO_DATACITE_PREFIX')
    missing = [k for k in required if not current_app.config.get(k)]
    if missing:
        current_app.logger.error(
            'DataCite DOI registration is enabled but not configured: {0}'
            .format(', '.join(missing)))
        return False
    return True
```

---

## 7. メタデータマッピング（JPCOAR → DataCite JSON）

### 7-1. 資源タイプ → `resourceTypeGeneral`

WEKO の `item_metadata_validation()` は現在 **DataCite を `dataset_type` にのみ許可**しているが、
DataCite 自体は幅広い資源タイプを扱える。対応範囲を広げるかは §10-2 で決める。

| WEKO 資源タイプ | `resourceTypeGeneral`（DataCite 4.4） |
| --- | --- |
| dataset, aggregated data, experimental data, observational data ほか | `Dataset` |
| software, source code | `Software` |
| journal article, article | `JournalArticle` |
| conference paper | `ConferencePaper` |
| thesis, doctoral thesis, master thesis, bachelor thesis | `Dissertation` |
| book | `Book` |
| book part | `BookChapter` |
| technical report, research report, report, working paper | `Report` |
| data paper | `DataPaper` |
| peer review | `PeerReview` |
| image, still image | `Image` |
| moving image, video | `Audiovisual` |
| sound | `Sound` |
| interactive resource | `InteractiveResource` |
| data management plan | `OutputManagementPlan` |
| workflow | `Workflow` |
| その他 | `Text` または `Other` |

> `resourceTypeGeneral` の許容値は DataCite Metadata Schema のバージョンで増減する。
> 実装時に採用するスキーマ版（既定 4.4）の正式な語彙リストで検証すること。

### 7-2. 要素マッピング

| DataCite 属性 | JPCOAR / WEKO 側 | 必須 | 備考 |
| --- | --- | --- | --- |
| `doi` | `identifierRegistration.@value` | ✔ | プレフィックス込み |
| `url` | `WEKO_DATACITE_RESOURCE_URL_PATTERN` から生成 | ✔ | アイテム詳細画面 |
| `titles[].title` | `title.@value` | ✔ | `title.@attributes.xml:lang` を `lang` へ |
| `creators[].name` | `creator.creatorName.@value` | ✔ | |
| `creators[].givenName` / `familyName` | `creator.givenName.@value` / `creator.familyName.@value` | | `nameType: "Personal"` を付与 |
| `creators[].nameIdentifiers` | `creator.nameIdentifier`（`nameIdentifierScheme=ORCID`） | | `nameIdentifierScheme` / `schemeUri` |
| `creators[].affiliation` | `creator.affiliation.affiliationName.@value` | | |
| `publisher` | `publisher.@value` / `publisher_jpcoar.publisherName.@value` | ✔ | |
| `publicationYear` | `date.@value`（`dateType=Issued`）の年 | ✔ | |
| `types.resourceTypeGeneral` | `type.@value` → §7-1 の対応表 | ✔ | |
| `types.resourceType` | `type.@value` | | 元の値をそのまま入れる |
| `contributors[]` | `contributor.*` | | `contributorType` の対応づけが必要 |
| `dates[]` | `date.@value` + `date.@attributes.dateType` | | JPCOAR の dateType を DataCite の語彙へ |
| `descriptions[]` | `description.@value` + `descriptionType` | | `Abstract` / `Methods` など |
| `subjects[]` | `subject.@value` + `subjectScheme` | | |
| `language` | `language.@value` | | ISO 639 |
| `rightsList[]` | `rights.@value` / `rights.@attributes.rdf:resource` | | `rightsUri` |
| `sizes[]` / `formats[]` | `file.filesize` / `file.mimeType` | | |
| `relatedIdentifiers[]` | `relation.relatedIdentifier` + `relationType` | | |
| `fundingReferences[]` | `fundingReference.funderName` / `awardNumber` | | |
| `geoLocations[]` | `geoLocation.*` | | 研究データで有用 |
| `version` | `version.@value` | | |

**Crossref との決定的な違い**: 必須の 6 項目（§3-2）さえ埋まれば登録できる。
残りは**段階的に足していける**ため、初期実装のスコープを小さく切れる。

---

## 8. 工数見積

| 作業 | 内容 | 人日 |
| --- | --- | --- |
| **Phase 1: JSON マッパー** | 資源タイプ判定 + 必須 6 項目 + 主要な任意項目 | **3〜5** |
| **Phase 2: クライアント** | `requests` で POST / PUT、Basic 認証、エラー分類 | **1〜2** |
| **Phase 3: 登録フロー・状態管理** | フック、Celery タスク、`DepositLog` への記録、リトライ | **2〜3** |
| **Phase 4: 管理 UI** | 設定画面・一覧・再送（Crossref と共通化する場合は大幅減） | **1〜2** |
| **テスト** | | **5〜8** |
| **結合検証** | `api.test.datacite.org` との往復、エラーケース | **2〜3** |

- **MVP（Phase 1〜3、テスト最小、管理 UI なし）: 8〜13 人日**
- **フル（Phase 1〜4 + WEKO 相当のテスト）: 14〜23 人日**

Crossref（MVP 20〜30 人日 / フル 35〜56 人日）の **概ね 1/2〜1/3**。
差の主因は「XML → JSON」「レコードタイプ別分岐の不要」「結果ポーリングの不要」の 3 点。

**Crossref を先に実装済みの場合**、共通基盤（フック・テーブル・タスク・管理 UI）を流用できるため
DataCite の追加は **5〜8 人日**まで下がる。逆も同様（§9）。

---

## 9. 共通抽象化の設計判断 ← **決定済み: 案 1 を採用**

> **本節の検討結果を受けて、共通基盤を独立した設計仕様として起こした。**
> **→ [`WACREN_doi_registration.md`](./WACREN_doi_registration.md)**
>
> インターフェース定義・状態遷移・データモデル・オーケストレーション・設定構造・
> テスト戦略・段階導入計画は同文書を参照。本節は判断の経緯として残す。

Crossref と DataCite の両方を実装するなら、
[`WACREN_crossref.md` §9-7](./WACREN_crossref.md) で挙げた共通インターフェースを
**最初から切るべきか、後から切り出すか**を決める必要がある。

> **2026-09-01 追記**: 案 1 で共通基盤が実装済み
> （[`WACREN_doi_registration.md`](./WACREN_doi_registration.md)）。
> ただし下記「推奨する進め方」の順序（DataCite 先行）は採らず、Crossref から実装した。

### 案 1: 最初から共通インターフェースを設計する ← **推奨**

```
DoiRegistrationAgency（抽象）
  ├─ register(item_uuid, doi, resource_url) -> DepositResult
  ├─ update(doi, attributes)  -> DepositResult
  ├─ hide(doi)                -> DepositResult   （DataCite のみ実装、Crossref は未対応を返す）
  └─ is_allowed()             -> bool
      ├─ CrossrefAgency   （XML / 非同期 / ポーリングあり）
      └─ DataCiteAgency   （JSON / 同期）

共通: doi_deposit_log テーブル、Celery タスク、管理 UI、saving_doi_pidstore からのフック
```

- **長所**: テーブル・タスク・管理 UI・設定パターンが 1 つで済む。
  JaLC を将来足すときも同じ形に載る。2 つ目の実装が 5〜8 人日で済む。
- **短所**: 初回の設計コストが +2〜3 人日。同期/非同期の差を抽象化で吸収する必要がある
  （`register()` が「確定」を返す場合と「受付」を返す場合がある）。

### 案 2: それぞれ独立に実装し、後で共通化する

- **長所**: 初回の見通しが良い。
- **短所**: `crossref_deposit_log` と `datacite_deposit_log` が別テーブルになるなど、
  後からの統合コストが高い。管理 UI も 2 つ作ることになる。

### 推奨する進め方

**DataCite を先に、共通インターフェース（案 1）の形で実装する。**

理由:

1. **テストアカウントが先に手に入る**（§2-2）。Crossref は往復待ちが発生する。
2. **同期 API + JSON で最も単純**なため、共通基盤（フック位置・ステータス管理・
   コミット競合対策・管理 UI）の検証を安いコストで済ませられる。
3. その上に Crossref を載せる際は、**非同期・ポーリングという「難しい側」だけに集中できる**。
4. 逆順（Crossref 先）だと、非同期前提で作った抽象に同期 API を後付けすることになり、
   インターフェースが歪みやすい。

> **実際は逆順（Crossref 先）になった。** 4 の懸念に対しては、共通基盤の設計時点で
> `DepositStatus.ACCEPTED` と `AgencyCapabilities.requires_polling` を先に用意することで
> 対処してある（[`WACREN_doi_registration.md` §4-3](./WACREN_doi_registration.md)）。
> 同期エージェンシーは `register()` から `SUCCEEDED` を返し、`poll()` を実装しなければよい。

---

## 10. 未決事項・要確認事項

### 10-1. DataCite 会員資格

> **2026-09-01 時点: 未解決。** テストアカウントの申請（§2-2）も未実施。

Crossref（[`WACREN_crossref.md` §9-1](./WACREN_crossref.md)）と同じ論点。

- WACREN 側機関が DataCite 会員か（Direct Member / Consortium 経由 / 未加入）
- 割り当てられる DOI プレフィックス
- 既存の `jalc_datacite_doi` フィールドを流用するか、新たに `datacite_doi` を設けるか
- **DataCite には Crossref の GEM に相当する減免制度があるか**（要確認）

ただし §2-2 のとおり **テスト環境は非会員でも使える**ため、
**Phase 1〜3 は会員資格の確定を待たずに着手できる**。

### 10-2. 対象資源タイプの拡大

現在 `item_metadata_validation()` は DataCite DOI を `dataset_type` にのみ許可している。
DataCite 自体は §7-1 のとおり幅広い資源タイプを扱えるため、
**この制限を緩めるかどうか**を決める必要がある。緩める場合は既存の検証ロジックの変更を伴う。

### 10-3. `datacite` ライブラリの扱い

§1-2 のとおり、依存には入っているが未使用で、REST クライアントも含まれない。

- 案 A（`requests` 直接実装）を採るなら、`datacite==1.0.1` は**依存から外せる可能性**がある。
  ただし `invenio-records-rest/serializers/datacite.py` が `schema31` / `schema40` / `schema41` を
  import しているため、**シリアライザを使っていなくても import 時に必要**。削除は要調査。

### 10-4. アイテム非公開・削除時の挙動

DataCite は `event: hide` で Findable → Registered に戻せる（§3-3）。

- WEKO のアイテム非公開時に `hide` を送るか（`WEKO_DATACITE_HIDE_ON_UNPUBLISH`）
- `delete_pidstore_doi()` が呼ばれたときの挙動
- Crossref とは挙動が異なるため、**両方を使うインスタンスでは運用ルールの統一が必要**

### 10-5. メタデータ更新の同期

`PUT /dois/{doi}` で部分更新できる（§3-4）ため、Crossref より安価に実装できる。
アイテム編集時に自動同期するか（`WEKO_DATACITE_UPDATE_ON_EDIT`）を決める。

### 10-6. 既存メタデータ検証との整合

`DOI_VALIDATION_INFO_DATACITE` の必須項目（`title` / `type` / `fileURI`）は
DataCite Findable DOI の必須 6 項目（§3-2）と一致していない。
特に **`publisher` と `publicationYear` が WEKO 側で必須になっていない**ため、
「承認は通るが DataCite 登録だけ失敗する」アイテムが発生しうる。
[`WACREN_crossref.md` §9-5](./WACREN_crossref.md) と同じ論点。

---

## 11. 参考リンク

- [Introduction to the DataCite REST API](https://support.datacite.org/docs/api)
- [Creating DOIs with the REST API](https://support.datacite.org/docs/api-create-dois)
- [Updating metadata with the REST API](https://support.datacite.org/docs/updating-metadata-with-the-rest-api)
- [Get a test account](https://support.datacite.org/docs/getting-a-test-account)
- [Test Accounts Policy](https://support.datacite.org/docs/test-accounts-policy)
- [Differences Between Test and Production Environments](https://support.datacite.org/docs/what-is-the-difference-between-the-datacite-test-and-production-environments)
- [Testing Guide](https://support.datacite.org/docs/testing-guide)
- [Best Practices for Integrators](https://support.datacite.org/docs/best-practices-for-integrators)
- [DataCite MDS API Guide](https://support.datacite.org/docs/mds-api-guide)
- [datacite — Python library documentation](https://datacite.readthedocs.io/)
- [`WACREN_crossref.md`](./WACREN_crossref.md) — Crossref 版の検討結果（共通アーキテクチャ）
