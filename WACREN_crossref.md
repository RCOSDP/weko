# Crossref DOI の API 登録対応 — 仕様検討

WEKO3 で Crossref DOI が付与された際に、Crossref の Content Registration API を叩いて
実際に DOI を登録する機能の設計案。設定でオン/オフを切り替えられることを前提とする。

- 対象ブランチ: `feature/nii_WACREN_pre`
- 作成日: 2026-08-04
- ステータス: **検討段階（未実装）**

---

## 1. 現状の整理

### 1-1. 現在の DOI 処理フロー

WEKO3 は **DOI をメタデータに書き込み、PID ストアに登録するだけ**で、
外部の DOI 登録機関（Crossref / JaLC / DataCite）の API は一切叩いていない。

```
ワークフロー「識別子付与 (identifier_grant)」アクション
   ↓ ユーザが Crossref DOI を選択・入力
「承認 (approval)」アクション完了時
   ↓ weko_workflow/views.py:2089, 2272
saving_doi_pidstore(item_id, record_without_version, data, doi_select)
   ↓  weko_workflow/utils.py:154
   ├─ IdentifierHandle.register_pidstore('doi', identifier_val)
   │     → PersistentIdentifier テーブルに pid_type='doi' で登録（ローカル DB のみ）
   └─ IdentifierHandle.update_idt_registration_metadata(doi_register_val, 'Crossref')
         → アイテムメタデータの jpcoar:identifierRegistration に書き込み
   ↓
（外部への登録処理は無い）
```

インポート経由も同様（`weko_search_ui/utils.py:3671, 3683, 3707` から `saving_doi_pidstore` を呼ぶ）。

### 1-2. 既存の Crossref 連携（登録以外）

| 箇所 | 用途 | エンドポイント |
| --- | --- | --- |
| `weko-admin/utils.py` `validate_certification()` | JaLC/Crossref アカウントの疎通確認 | `https://doi.crossref.org/openurl?pid=...` |
| `weko-items-autofill/utils.py` `get_crossref_record_data()` | DOI からのメタデータ自動入力（**取得のみ**） | `https://doi.crossref.org` |
| `weko-workspace/config.py` | JaLC / DataCite からのメタデータ取得 | `api.japanlinkcenter.org/dois/`, `api.datacite.org/dois/` |

いずれも **参照系**であり、登録（deposit）系の実装は存在しない。

### 1-3. 既存の Crossref 関連設定

| 箇所 | 内容 |
| --- | --- |
| `weko-admin` `Identifier` モデル (`doi_identifier` テーブル) | `jalc_crossref_doi`（プレフィックス）、`jalc_crossref_flag`（有効/無効）、`suffix` |
| `weko-admin/admin.py` `IdentifierSettingView` | 管理画面「DOI 識別子付与」でプレフィックスと有効フラグを設定 |
| `weko-workflow/config.py` `IDENTIFIER_GRANT_SELECT_DICT` | `'Crossref': '2'` |
| `weko-workflow/config.py` `DOI_VALIDATION_INFO_CROSSREF` | Crossref DOI 付与時の必須メタデータ定義 |
| `weko-workflow/utils.py` `item_metadata_validation()` | Crossref 選択時は資源タイプに応じて `journal_article` / `report_types` のマッピングで検証 |

> **重要**: WEKO のフィールド名が `jalc_crossref_doi` であることが示すとおり、
> WEKO の想定は「**JaLC 経由で登録する Crossref DOI**」（日本の JaLC 会員機関のユースケース）。
> WACREN 参加機関が Crossref の**直接会員**として登録する場合は前提が異なるため、
> §9-1 の未決事項を先に確定する必要がある。

---

## 2. Crossref のテストサイト（サンドボックス）

### 2-1. 概要

Crossref は本番と同等に動作する **テストシステム** を提供している。

| 項目 | 内容 |
| --- | --- |
| URL | `https://test.crossref.org` |
| 特徴 | 本番と同じ動作をするが、**テスト用 DB** を使い、**Handle への DOI 登録は行わない**（＝登録した DOI は解決しない） |
| 管理画面 | Test Admin Tool（本番の Admin Tool と同 UI） |
| データ | 本番とは別。定期的にリセットされる場合がある |

### 2-2. テストアカウントの取得方法

テストアカウントの申請窓口は **`support@crossref.org` へのメール依頼のみ**（Web の申込フォームは無い）。
申請には立場によって 2 つの経路がある。

#### 経路 A: サービスプロバイダとして申請 ← **本件で採用**

Crossref の公式ドキュメントに、統合をテストしたいサービスプロバイダ向けの記載がある。

> "If you're a service provider and would like to test your integrations, you may POST submissions
> to our test system using https://test.crossref.org/servlet/deposit."
> "You'll need to email us at support@crossref.org so we can configure an account within the test
> system before you test your integration."
> — [XML deposit using HTTPS POST](https://www.crossref.org/documentation/register-maintain-records/direct-deposit-xml/https-post/)

**この経路では、申請者自身が Crossref 会員である必要は明記されていない。**
WEKO3 / JAIRO Cloud のようなリポジトリソフトウェアの開発者は、
「WEKO3 に Crossref デポジット連携を実装するための検証」という目的でこの経路を使うのが適切。

1. `support@crossref.org` にメールを送る（文面は §2-5）。
   - 開発しているソフトウェア／サービス名（WEKO3 / JAIRO Cloud）とその位置づけ
   - 運営組織（国立情報学研究所）
   - テストシステムを使う目的
   - 実装予定のエンドポイントと operation
2. Crossref 側でテストシステム上にアカウントが構成されるのを待つ。
3. 発行された **テスト用の `login_id` / `login_passwd`** で `https://test.crossref.org` にログインして疎通確認。

> Crossref は 2026 年に **Service Providers Program** を正式に再開しており、
> メタデータ登録ツールを提供する組織からの申請を受け付けている（参加は無料、認定プロセスあり）。
> 参照: [Service providers — Crossref](https://www.crossref.org/community/service-providers/)

#### 経路 B: コンテンツ登録機関（Crossref 会員）として申請

実際に自機関の DOI を登録する立場で申請する場合。

1. **前提: Crossref 会員であり、DOI プレフィックスを保有していること。**
   未加入の場合は先に [メンバーシップ申請](https://www.crossref.org/membership/_apply) が必要（§2-3 参照）。
2. `support@crossref.org` にメールを送る。本文に含める情報:
   - 所属機関名 / Crossref メンバー名、**member ID**、**DOI プレフィックス**
   - 本番の Crossref アカウント（`login_id`、ロール名）
   - テストシステムを使う目的
3. 以降は経路 A と同じ。

> ⚠️ **共通の注意点**
> - **本番の認証情報がそのままテストシステムで使えるとは限らない。**
>   特に新規会員の場合、テストシステムでのログインが拒否されることがある。その場合も `support@crossref.org` に連絡する。
> - Crossref は Admin Tool のフロントエンドを `sandbox.crossref.org` へ移行する計画を持っている。
>   将来的に URL が変わる可能性があるため、実装では **エンドポイントを設定値**にしておく（§5 参照）。

### 2-3. Crossref 会員資格について（経路 B / 本番登録に必要）

WACREN 参加機関側で実際に DOI を登録する段階では、Crossref 会員資格が必要になる。
2026-08 時点の調査結果は以下のとおり。

| 項目 | 内容 |
| --- | --- |
| 申請先 | [Become a member](https://www.crossref.org/membership/_apply) |
| 費用（通常） | 年会費（組織規模に応じた階層制）+ レコード登録料（四半期請求）。メタデータ更新は無料 |
| **GEM プログラム** | [Global Equitable Membership](https://www.crossref.org/gem/) — 対象国の機関は**年会費・登録料ともに無料** |
| GEM 対象国 | World Bank IDA（full/blend）と UN LDC がベース。116 か国以上 |
| **Nigeria** | **2026-01-01 の拡大で GEM 対象に追加**（他に Kenya, Cameroon, Cabo Verde, Angola, Congo 共和国など計 18 か国） |
| 判定基準 | 郵送先住所と請求先住所の**両方**が対象国内にあること |
| Sponsor 経由 | [Sponsors program](https://www.crossref.org/community/sponsors/) — 事務手続きを代行。GEM 対象なら独立会員でも無料のため必須ではない |

> WACREN 参加機関が GEM 対象国に所在する場合、**費用面の障壁なく Crossref 会員になれる**。
> ただし GEM 判定は実際の機関所在国によるため、個別に確認が必要。

**GEM は費用のみの制度であり、技術的な登録方法は通常会員と変わらない。**

| | 内容 |
| --- | --- |
| GEM で変わる | 年会費が無料（組織規模ではなく**国**で判定）。全レコードタイプのコンテンツ登録料が無料 |
| GEM でも変わらない | DOI プレフィックスの割り当て / アカウント認証情報（`login_id`・`login_passwd`）/ デポジットのエンドポイントと `operation` / Admin Tool・テストシステムへのアクセス / メタデータの品質要件・会員義務 |
| GEM でも無料にならない | Similarity Check、Metadata Plus などの有償サービス |

GEM は会員種別ではなく**料金区分**であり、独立会員・Sponsor 経由会員のどちらにも適用される。
したがって **§3〜§7（API 方式・設定項目・メタデータマッピング・実装方針）は GEM の有無で変更不要**。
影響があるのは運用ポリシー側で、登録料が無料になるため
「どのアイテムに DOI を付与するか」の判断がコスト制約から解放される点のみ。

> ⚠️ Crossref の GEM ページは制度を**費用の観点でのみ**説明しており、
> 「技術的な扱いは通常会員と同一」と明示してはいない。上記は
> 「GEM が料金プログラムとして定義されていること」「独立会員・Sponsor 会員の双方に適用されること」
> からの判断。確実にするなら、WACREN 側機関の会員申請が具体化した時点で Crossref に以下を確認する。
>
> ```
> We understand that the GEM program only waives fees and does not change the
> technical registration process. Could you confirm that GEM members use the same
> deposit endpoints, credentials, and prefix assignment as other members?
> ```
>
> なお **§2-5 の申請（JAIRO Cloud 開発者としてのサービスプロバイダ経路）は GEM とは無関係**のため、
> この確認は当面不要。

### 2-4. アカウント取得前にできる検証

テストアカウントが来るまでの間も、生成した XML の妥当性は以下で確認できる。

| 手段 | 内容 |
| --- | --- |
| Crossref XML parser | `https://www.crossref.org/02publishers/parser.html` — 単一ファイルをアップロードして検証のみ行う（アカウント不要） |
| `xmllint` | Crossref スキーマ (XSD) をローカルに置いて `xmllint --schema crossref5.4.0.xsd deposit.xml --noout` |
| XML エディタ | Oxygen、XMLSpy など |
| スキーマ本体 | `https://gitlab.com/crossref/schema` — XSD と best-practice-examples がある |

**実装順序としては、まず「XML を生成して parser で通す」ところまで作り、
テストアカウントが届いた時点で送信部分を繋ぐ**のが効率的（§8 の Phase 1 → 2）。

### 2-5. 申請メール文面（経路 A: サービスプロバイダ）

WEKO3 / JAIRO Cloud の開発者としてテストアカウントを申請する場合の文面。
`<>` の箇所を差し替えて `support@crossref.org` に送る。

**Subject:** `Request for a test system account — WEKO3 repository software (service provider)`

```
Dear Crossref Support,

We are the development team of WEKO3, an open-source institutional repository
software developed and maintained by the National Institute of Informatics
(NII) in Japan. WEKO3 is the platform behind JAIRO Cloud, a hosted repository
service used by several hundred Japanese institutions, and it is also deployed
by institutions outside Japan.

We are currently implementing an automated Crossref XML deposit feature in
WEKO3, so that repositories running our software can register DOIs directly
with Crossref. As a service provider, we would like to verify this integration
against your test system before any of our users deposit to production.

Could you please configure an account for us on the test system
(https://test.crossref.org)?

  Software / service   : WEKO3 (https://github.com/RCOSDP/weko)
  Operating organisation: National Institute of Informatics (NII), Japan
  Hosted service        : JAIRO Cloud (https://jpcoar.repo.nii.ac.jp/)
  Contact name          : <担当者名>
  Contact email         : <担当者メール>
  Role                  : <役職・立場>

Our planned implementation is:

  - Deposit  : POST to https://test.crossref.org/servlet/deposit
               with operation=doMDUpload (multipart/form-data)
  - Results  : GET  https://test.crossref.org/servlet/submissionDownload
               with type=result
  - Schema   : Crossref schema 5.4.0

We also have two questions:

1. Is the synchronous deposit API (https://api.crossref.org/v2/deposits and
   https://test.crossref.org/v2/deposits) available for service providers and
   members to use, or should we implement against the servlet/deposit endpoint?
   The deprecated REST deposit documentation states that members should use the
   production deposit system at doi.crossref.org, so we would like to confirm
   which endpoint you recommend for a new integration.

2. Are there any rate limits or other restrictions we should be aware of on the
   test system?

We would also be interested in hearing about the Service Providers Program if
our software qualifies.

Thank you very much for your help.

Best regards,
<氏名>
<所属・役職>
National Institute of Informatics
```

**この文面のポイント**

- **サービスプロバイダであることを冒頭で明示**する。会員として DOI を登録したいのではなく、
  ソフトウェアの統合をテストしたい、という立場を最初に伝える（§2-2 経路 A の根拠に合致させる）。
- **実装予定のエンドポイントと operation を具体的に書く**。
  Crossref 側が「何をテストしたいのか」を判断しやすくなり、アカウント構成がスムーズになる。
- **§9-2 の未決事項（同期 v2 API の利用可否）を質問 1 として同梱**する。
  実装方針（結果ポーリングの要否）に直結するため、往復を増やさずに確定させる。
- Service Providers Program への言及を入れておくと、正式なプログラム参加の案内を受けられる可能性がある。

### 2-6. エンドポイント対応表

| 用途 | 本番 | テスト |
| --- | --- | --- |
| XML デポジット（HTTPS POST） | `https://doi.crossref.org/servlet/deposit` | `https://test.crossref.org/servlet/deposit` |
| 投入結果（サブミッションログ）取得 | `https://doi.crossref.org/servlet/submissionDownload` | `https://test.crossref.org/servlet/submissionDownload` |
| 同期 REST Deposit v2（§3-2 参照） | `https://api.crossref.org/v2/deposits`（要確認） | `https://test.crossref.org/v2/deposits` |
| 管理画面 | `https://doi.crossref.org` | `https://test.crossref.org` |

---

## 3. Crossref 登録 API の選択肢

### 3-1. HTTPS POST（`servlet/deposit`）— **推奨**

Crossref が公式ドキュメントで案内している標準的なデポジット方式。

**リクエスト**

```
POST https://test.crossref.org/servlet/deposit
Content-Type: multipart/form-data
```

| パラメータ | 説明 |
| --- | --- |
| `operation` | `doMDUpload`（メタデータ登録。既定） |
| `login_id` | Crossref アカウント。ロール共有の場合は `email@address.com/role` 形式 |
| `login_passwd` | パスワード（大文字小文字を区別） |
| `fname` | デポジットする XML ファイル（**パラメータ名は大文字小文字を区別**） |

**その他の operation 値**

| 値 | 用途 |
| --- | --- |
| `doMDUpload` | メタデータ登録（通常はこれ） |
| `doDOICitUpload` | 引用文献のみの登録 |
| `doQueryUpload` | クエリ投入 |
| `doDOIQueryUpload` | DOI → メタデータ照会 |
| `doTransferDOIsUpload` | 既存 DOI の解決先 URL のみ更新 |

**制約**

- XML ファイルは **10MB 以内**。
- 1 ユーザあたり **保留中サブミッション 10,000 件**が上限。超過すると `429` が返る。
- **処理は非同期**。POST は受付結果を返すだけで、登録の成否は別途取得する。

**結果の取得**

```
GET https://test.crossref.org/servlet/submissionDownload
    ?usr=<login_id>&pwd=<login_passwd>&file_name=<投入時のファイル名>&type=result
```

| パラメータ | 説明 |
| --- | --- |
| `usr` | ロール認証は `usr=_role_`、個人認証は `usr=name@example.com/role` |
| `pwd` | パスワード |
| `file_name` | 投入時のファイル名（**推奨**。`doi_batch_id` はパース後にしか使えないため、キュー滞留中も追跡できる `file_name` が適する） |
| `doi_batch_id` | `file_name` の代替 |
| `type` | `result`（デポジットログ）/ `contents`（投入した XML そのもの） |

**レスポンス（`type=result`）** — `doi_batch_diagnostic` を含む XML

```xml
<doi_batch_diagnostic status="completed" sp="...">
  <submission_id>1234567890</submission_id>
  <batch_id>WEKO-20260804-000123</batch_id>
  <record_diagnostic status="Success">
    <doi>10.xxxxx/weko.123</doi>
    <msg>Successfully added</msg>
  </record_diagnostic>
  <batch_data>
    <record_count>1</record_count>
    <success_count>1</success_count>
    <warning_count>0</warning_count>
    <failure_count>0</failure_count>
  </batch_data>
</doi_batch_diagnostic>
```

### 3-2. 同期 REST Deposit v2（`/v2/deposits`）

サブミッションが**同じスレッドで即座に処理され**、`200` とともに `doi_batch_diagnostic` が返る方式。
ポーリングが不要になるため実装は大幅に簡素化される。

```bash
curl -v -F 'operation=doMDUpload' -F 'usr=USER/ROLE' -F 'pwd=PWD' \
     -F 'mdFile=@/path/to/file.xml' \
     https://api.crossref.org/v2/deposits
```

- 認証は HTTP Basic 認証も利用可（`Authorization: Basic <base64(user:password)>`）。
- テスト系は `https://test.crossref.org/v2/deposits`。

> ⚠️ **要確認**: 旧 REST Deposit API のドキュメント（`CrossRef/rest-api-doc` の deprecated 配下）には
> 「これは他の Crossref メンバー向けではなく、メンバーは `doi.crossref.org` の本番デポジットシステムを使うこと」
> という記述があり、`api.crossref.org` 側の位置づけが明確でない。
> 現行の Knowledge Base（`crossref.gitlab.io/knowledge_base`）は認証が必要で内容を直接確認できなかった。
> **テストアカウント申請時に、同期 v2 API が自機関で利用可能かをあわせて `support@crossref.org` に確認すること。**

### 3-3. 比較と方針

| | `servlet/deposit`（3-1） | `v2/deposits`（3-2） |
| --- | --- | --- |
| ドキュメント整備 | 公式ドキュメントに明記 | Knowledge Base が要認証、位置づけ不明確 |
| 応答 | 非同期（受付のみ） | 同期（結果まで返る） |
| 結果取得 | `submissionDownload` をポーリング | レスポンスに含まれる |
| 実装コスト | 中（ポーリング + ステータス管理が必要） | 小 |
| テスト系 | あり | あり |

**方針**: 抽象化した `CrossrefDepositClient` を用意し、**設定 `WEKO_CROSSREF_API_MODE` で
`servlet`（既定）/ `rest_v2` を切り替えられる**構造にする。
まず `servlet` 方式を実装し、Crossref から v2 の利用可否を確認できたら `rest_v2` を追加する。
どちらのモードでも「デポジット → 結果判定」というインターフェースは同一に保つ。

---

## 4. 実装方針

### 4-1. 全体アーキテクチャ

```
saving_doi_pidstore()                                    [weko_workflow/utils.py]
  ├─ 既存: PID 登録 + メタデータ書き込み
  └─ 追加: doi_register_typ == 'Crossref' かつ
           is_crossref_registration_allowed() が True のとき
             ↓
        request_crossref_deposit(item_uuid, doi, record_url)   [新規 crossref.py]
             ↓ CrossrefDepositLog を status='pending' で作成
             ↓ Celery タスクを遅延投入（DB コミット後に走るよう遅延を入れる）
             ↓
        deposit_crossref_doi.delay(log_id)                     [weko_workflow/tasks.py]
             ├─ CrossrefXmlBuilder.build(record, doi, resource_url)   [新規 crossref_mapper.py]
             │     JPCOAR メタデータ → Crossref doi_batch XML
             ├─ CrossrefDepositClient.deposit(xml, filename)          [新規 crossref_client.py]
             │     status='submitted', batch_id / filename を記録
             └─ poll_crossref_submission.apply_async(countdown=N)
                   ├─ CrossrefDepositClient.get_submission_log(filename)
                   ├─ doi_batch_diagnostic を解析
                   └─ status='success' / 'failure' に更新（失敗時はリトライ）
```

### 4-2. 追加ファイル

| ファイル | 役割 |
| --- | --- |
| `modules/weko-workflow/weko_workflow/crossref_client.py` | Crossref API クライアント（デポジット / 結果取得 / モード切替） |
| `modules/weko-workflow/weko_workflow/crossref_mapper.py` | JPCOAR メタデータ → Crossref XML 変換 |
| `modules/weko-workflow/weko_workflow/crossref.py` | 登録の入口・可否判定・ログ管理（ARK の `is_ark_registration_allowed` と同じ設計） |
| `modules/weko-workflow/weko_workflow/models.py`（追記） | `CrossrefDepositLog` モデル |
| `modules/weko-workflow/weko_workflow/tasks.py`（追記） | `deposit_crossref_doi` / `poll_crossref_submission` / `retry_failed_crossref_deposits` |
| `modules/weko-workflow/weko_workflow/config.py`（追記） | `WEKO_CROSSREF_*` 設定 |
| `modules/weko-workflow/weko_workflow/alembic/xxxx_add_crossref_deposit_log.py` | マイグレーション |
| `modules/weko-admin/weko_admin/admin.py`（追記） | 管理画面「Crossref DOI 登録」 |

> **配置理由**: `saving_doi_pidstore` / `IdentifierHandle` / `item_metadata_validation` が
> すべて `weko-workflow` にあり、ARK 対応も同モジュールに追加した実績があるため。
> 独立モジュール `weko-crossref` にする案もあるが、`setup.py` / entry point / alembic ブランチの
> 追加が必要でコストが大きい。将来 JaLC / DataCite の API 登録も追加するなら再検討する。

### 4-3. フック位置の検討

| 候補 | 長所 | 短所 | 評価 |
| --- | --- | --- | --- |
| **`saving_doi_pidstore()` の末尾** | ワークフロー経由・インポート経由の**全 5 呼び出し箇所**を 1 箇所でカバーできる | 同関数は DB コミット前に呼ばれるため、タスク投入のタイミング調整が必要 | ◎ 採用 |
| `views.py` の `next_action` 内 | コミット位置が明確 | インポート経由をカバーできず、2 箇所に同じ処理が要る | △ |
| `record_viewed` などのシグナル | 疎結合 | DOI 付与のタイミングと一致しない | × |

**採用案の注意点**: `saving_doi_pidstore()` は呼び出し側で `db.session.commit()` される前に
実行されるため、Celery タスクが「まだコミットされていない PID」を読みに行く競合が起きうる。
対策として、

- タスク投入時に `countdown`（既定 10 秒）を入れる、かつ
- タスク側で対象 PID / レコードが取得できなければ最大 N 回リトライする、

の二段構えにする。より厳密にするなら SQLAlchemy の `after_commit` イベントでタスクを投入する。

### 4-4. ステータス管理テーブル

```
crossref_deposit_log
├─ id               BigInteger, PK
├─ item_uuid        UUID          -- 対象アイテム（PersistentIdentifier.object_uuid）
├─ doi              String(255)   -- 登録対象 DOI
├─ resource_url     Text          -- <doi_data><resource>
├─ record_type      String(50)    -- journal_article / dissertation / posted_content ...
├─ file_name        String(255)   -- submissionDownload の追跡キー
├─ batch_id         String(255)   -- <doi_batch_id>
├─ submission_id    String(50)    -- Crossref 側の submission_id
├─ status           String(20)    -- pending / submitted / success / failure / skipped
├─ attempt          Integer       -- 試行回数
├─ is_test          Boolean       -- テストシステム宛か
├─ request_xml      Text          -- 送信した XML（監査用）
├─ response_xml     Text          -- doi_batch_diagnostic
├─ error_message    Text
├─ created_at       DateTime
└─ updated_at       DateTime
```

**状態遷移**

```
pending ──deposit成功──> submitted ──poll──> success
   │                          │
   │                          └──poll(失敗)──> failure ──手動/自動再送──> pending
   └──deposit失敗──────────────────────────> failure
（設定オフ・必須設定不足の場合は skipped）
```

### 4-5. エラーハンドリング方針

**ARK 実装と同じ方針を踏襲する**: 外部サービスの障害がアイテム登録自体を止めてはならない。

- Crossref への送信・結果取得で発生した例外はすべて捕捉し、`ERROR` ログ + `CrossrefDepositLog` に記録する。
- ワークフローの承認処理・インポート処理は**必ず正常終了させる**。
- 恒久的な失敗（メタデータ不備など）と一時的な失敗（ネットワーク、`429`）を区別する。
  - `429`（キュー上限）/ タイムアウト / 5xx → 指数バックオフでリトライ
  - `record_diagnostic status="Failure"` → リトライせず `failure` で確定し、管理者に通知
- 失敗時は設定 `WEKO_CROSSREF_NOTIFY_EMAIL` 宛にメール通知（既存の `invenio-mail` を利用）。

---

## 5. 設定項目

`modules/weko-workflow/weko_workflow/config.py` に追加。
ARK の `WEKO_HANDLE_ARK_*` と同じ命名・検証パターンに揃える。

| 設定キー | 既定値 | 説明 |
| --- | --- | --- |
| **`WEKO_CROSSREF_ALLOW_REGISTER_DOI`** | **`False`** | **API 経由の DOI 登録のマスタースイッチ。`False` の間は従来どおりメタデータ書き込みのみ** |
| `WEKO_CROSSREF_API_MODE` | `'servlet'` | `'servlet'` / `'rest_v2'` |
| `WEKO_CROSSREF_DEPOSIT_URL` | `'https://test.crossref.org/servlet/deposit'` | デポジット先。**既定をテスト系にして事故を防ぐ** |
| `WEKO_CROSSREF_SUBMISSION_LOG_URL` | `'https://test.crossref.org/servlet/submissionDownload'` | 結果取得先 |
| `WEKO_CROSSREF_LOGIN_ID` | `None` | `login_id`（`email@example.com/role` 形式可） |
| `WEKO_CROSSREF_LOGIN_PASSWD` | `None` | `login_passwd` |
| `WEKO_CROSSREF_DEPOSITOR_NAME` | `None` | `<depositor><depositor_name>` |
| `WEKO_CROSSREF_DEPOSITOR_EMAIL` | `None` | `<depositor><email_address>`（結果通知メールの宛先にもなる） |
| `WEKO_CROSSREF_REGISTRANT` | `None` | `<registrant>` |
| `WEKO_CROSSREF_TEST_DEPOSIT` | `True` | デポジットに `test` パラメータを付与し、内容を本番反映させない |
| `WEKO_CROSSREF_SCHEMA_VERSION` | `'5.4.0'` | 生成する XML のスキーマバージョン |
| `WEKO_CROSSREF_TIMEOUT` | `30` | HTTP タイムアウト（秒） |
| `WEKO_CROSSREF_ASYNC` | `True` | `False` にすると同期送信（デバッグ用） |
| `WEKO_CROSSREF_SUBMIT_COUNTDOWN` | `10` | タスク投入の遅延（秒）。DB コミット待ち |
| `WEKO_CROSSREF_MAX_RETRY` | `3` | 送信リトライ上限 |
| `WEKO_CROSSREF_RETRY_DELAY` | `300` | リトライ間隔（秒、指数バックオフの基準） |
| `WEKO_CROSSREF_POLL_DELAY` | `60` | 結果ポーリングの初回待ち（秒） |
| `WEKO_CROSSREF_POLL_MAX_ATTEMPTS` | `20` | ポーリング上限回数 |
| `WEKO_CROSSREF_RESOURCE_URL_PATTERN` | `'{root_url}records/{recid}'` | `<doi_data><resource>` に入れる URL |
| `WEKO_CROSSREF_DEFAULT_RECORD_TYPE` | `'posted_content'` | 資源タイプが特定できない場合のレコードタイプ |
| `WEKO_CROSSREF_RECORD_TYPE_MAP` | §6-1 の dict | WEKO 資源タイプ → Crossref レコードタイプ |
| `WEKO_CROSSREF_NOTIFY_EMAIL` | `None` | 失敗時の通知先。未設定なら通知しない |
| `WEKO_CROSSREF_DRY_RUN` | `False` | `True` なら XML 生成とログ記録のみ行い、送信しない |

### 5-1. 設定の妥当性チェック

ARK の `is_ark_registration_allowed()` と同じ設計で、
「未設定」を「無効」と取り違えないようにする。

```python
def is_crossref_registration_allowed():
    """Crossref への API 登録が有効かつ設定済みかを判定する。"""
    if not current_app.config.get('WEKO_CROSSREF_ALLOW_REGISTER_DOI'):
        return False

    required = (
        'WEKO_CROSSREF_DEPOSIT_URL',
        'WEKO_CROSSREF_LOGIN_ID',
        'WEKO_CROSSREF_LOGIN_PASSWD',
        'WEKO_CROSSREF_DEPOSITOR_NAME',
        'WEKO_CROSSREF_DEPOSITOR_EMAIL',
        'WEKO_CROSSREF_REGISTRANT',
    )
    missing = [k for k in required if not current_app.config.get(k)]
    if missing:
        current_app.logger.error(
            'Crossref DOI registration is enabled but not configured: {0}'
            .format(', '.join(missing)))
        return False
    return True
```

### 5-2. オン/オフの粒度

3 段階で制御できるようにする。

| レベル | 制御 | 用途 |
| --- | --- | --- |
| インスタンス全体 | `WEKO_CROSSREF_ALLOW_REGISTER_DOI` | 機能そのものの有効化 |
| リポジトリ（コミュニティ）単位 | `doi_identifier.jalc_crossref_flag`（既存） | 既存の「Crossref DOI 付与の有効/無効」をそのまま流用 |
| 送信抑止 | `WEKO_CROSSREF_DRY_RUN` / `WEKO_CROSSREF_TEST_DEPOSIT` | 検証時に本番へ送らない |

**認証情報の格納場所** — 2 案。

- **案 A（推奨・初期実装）**: `scripts/instance.cfg` の設定値として持つ。
  実装が単純で、既存の ARK / Handle 設定と一貫する。パスワードは環境変数から読む形にもできる。
- **案 B**: `doi_identifier` テーブルにカラムを追加し、管理画面から設定する。
  マルチテナント（コミュニティごとに別の Crossref アカウント）に対応できるが、
  DB へのパスワード保存となるため暗号化の検討が必要。

まず案 A で実装し、必要になった時点で案 B に拡張する。

---

## 6. メタデータマッピング（JPCOAR → Crossref XML）

### 6-1. 資源タイプ → Crossref レコードタイプ

WEKO は `item_metadata_validation()` で既に資源タイプを分類しているので、それを流用する。

| WEKO 資源タイプ群 | 該当する値（抜粋） | Crossref レコードタイプ |
| --- | --- | --- |
| `journalarticle_type` | journal article, conference paper, data paper, departmental bulletin paper, editorial, review article, article, newspaper, software paper, periodical | `journal` > `journal_article` |
| `thesis_types` | thesis, bachelor thesis, master thesis, doctoral thesis | `dissertation` |
| `report_types` | technical report, research report, report, book, book part | `report-paper` / `book` |
| `dataset_type` | dataset, software, source code ほか | `database` > `dataset`（※ Crossref の DOI 対象外の場合あり。§9-4） |
| `datageneral_types` / 上記以外 | other, image, sound, video ほか | `posted_content type="other"` |

> `journal_article` は `<journal_metadata>`（`<full_title>` と ISSN）が必要になるため、
> `jpcoar:sourceTitle` / `jpcoar:sourceIdentifier`（ISSN）が無いアイテムでは
> `posted_content` にフォールバックする。この判断ロジックは `crossref_mapper.py` に持たせる。

### 6-2. 要素マッピング

| Crossref 要素 | JPCOAR / WEKO 側 | 必須 | 備考 |
| --- | --- | --- | --- |
| `<doi_batch_id>` | 生成（例: `WEKO-{yyyymmddHHMMSS}-{recid}`） | ✔ | `CrossrefDepositLog.batch_id` と同値 |
| `<timestamp>` | 生成（`yyyymmddHHMMSS` の数値） | ✔ | 同一 DOI の更新時、大きい値が優先される |
| `<depositor><depositor_name>` | `WEKO_CROSSREF_DEPOSITOR_NAME` | ✔ | 設定値 |
| `<depositor><email_address>` | `WEKO_CROSSREF_DEPOSITOR_EMAIL` | ✔ | 設定値 |
| `<registrant>` | `WEKO_CROSSREF_REGISTRANT` | ✔ | 設定値 |
| `<titles><title>` | `title.@value` | ✔ | `title.@attributes.xml:lang` を `language` 属性へ |
| `<contributors><person_name>` | `creator.creatorName.@value` / `creator.givenName.@value` / `creator.familyName.@value` | | 先頭を `sequence="first"`、以降 `additional`。`contributor_role="author"` |
| `<ORCID>` | `creator.nameIdentifier`（`nameIdentifierScheme=ORCID`） | | `person_name` の子要素 |
| `<publication_date>` / `<posted_date>` | `date.@value`（`dateType=Issued`） | ✔ | `<year>` `<month>` `<day>` に分解 |
| `<doi_data><doi>` | `identifierRegistration.@value` | ✔ | プレフィックス込みの DOI |
| `<doi_data><resource>` | `WEKO_CROSSREF_RESOURCE_URL_PATTERN` から生成 | ✔ | アイテム詳細画面の URL |
| `<doi_data><collection property="text-mining">` | `file.URI.@value` | | 本文ファイルの URL |
| `<jats:abstract>` | `description.@value`（`descriptionType=Abstract`） | | JATS 名前空間の宣言が必要 |
| `<institution><institution_name>` | `publisher.@value` / `publisher_jpcoar.publisherName.@value` | | `dissertation` では必須級 |
| `<journal_metadata><full_title>` | `sourceTitle.@value` | △ | `journal_article` の場合 |
| `<journal_metadata><issn>` | `sourceIdentifier.@value`（`identifierType=ISSN`） | △ | 同上 |
| `<journal_issue><publication_date>` `<volume>` `<issue>` | `date`, `volume.@value`, `issue.@value` | | 同上 |
| `<pages><first_page>` / `<last_page>` | `pageStart.@value` / `pageEnd.@value` | | |
| `<degree>` | `degreeName.@value` | | `dissertation` |
| `<approval_date>` | `dateGranted.@value` | | `dissertation` |
| `<program name="AccessIndicators"><license_ref>` | `rights.@attributes.rdf:resource` | | ライセンス URL |
| `<program name="fundref">` | `funderName` / `awardNumber` | | 助成情報 |
| `<program name="relations">` | `relation`（`relationType`） | | 関連資源 |
| `<citation_list>` | — | | WEKO 側に構造化された引用文献が無いため**当面は非対応** |

### 6-3. 実装方針

- `MappingData`（`weko_workflow/utils.py`）と `get_mapping()`（`weko_records`）で
  既に JPCOAR マッピングを解決できるため、これを再利用する。
- XML 生成は `lxml.etree` を使う（`weko-schema-ui` や `invenio-oaiserver` で既に依存済み）。
- 生成した XML は `CrossrefDepositLog.request_xml` に保存し、後から検証・再送できるようにする。
- **必須要素が欠けている場合は送信せず** `failure`（理由付き）にする。
  ここは `item_metadata_validation()` の既存ロジックと役割が重なるので、
  DOI 付与時のバリデーションを強化するか、送信直前に再チェックするかを設計時に決める。

---

## 7. 管理 UI

### 7-1. 設定画面

管理画面に「Crossref DOI 登録」を追加（`weko-admin`）。

- API 登録の有効/無効トグル（`WEKO_CROSSREF_ALLOW_REGISTER_DOI` の値を表示）
- 接続先（本番 / テスト）の表示
- `login_id` / `depositor` / `registrant` の表示（パスワードはマスク）
- **疎通テストボタン** — 既存の `validate_certification()` と同様に、
  ダミーのクエリで認証情報の妥当性を確認する

### 7-2. 登録状況の一覧・再送画面

`CrossrefDepositLog` の一覧を Flask-Admin のモデルビューで表示する。

- 絞り込み: ステータス、DOI、アイテム、期間
- 各行から: 送信 XML / 応答 XML の表示、**手動再送**
- 一括操作: 失敗分の一括再送

---

## 8. 段階的な実装計画

| Phase | 内容 | Crossref アカウント | 見積 |
| --- | --- | --- | --- |
| **Phase 0** | **JAIRO Cloud / WEKO3 の開発者（サービスプロバイダ）として `support@crossref.org` へテストアカウント申請**（§2-2 経路 A、文面 §2-5）。並行して §9 の未決事項を確定 | 不要 | — |
| **Phase 1** | `crossref_mapper.py` の実装。XML を生成して `CrossrefDepositLog.request_xml` に保存するだけ（`WEKO_CROSSREF_DRY_RUN=True`）。生成物を Crossref XML parser / `xmllint` で検証 | 不要 | 10〜16 人日 |
| **Phase 2** | `crossref_client.py`（`servlet` モード）を実装し、`test.crossref.org` へ同期送信。`WEKO_CROSSREF_ASYNC=False` で動作確認 | **テスト系が必要** | 2〜3 人日 |
| **Phase 3** | Celery 非同期化 + `submissionDownload` によるポーリング + `CrossrefDepositLog` の状態遷移・リトライ | テスト系 | 5〜8 人日 |
| **Phase 4** | 管理 UI（設定画面・一覧・再送）+ 失敗通知メール | テスト系 | 4〜6 人日 |
| **Phase 5** | `rest_v2` モードの追加（Crossref から利用可と回答があった場合）、DOI 更新・URL 変更への対応 | 本番系 | 1〜2 人日 |

Phase 1 はアカウントが無くても着手できるため、**申請と並行して進められる**。

### 8-1. 工数見積

**工数の支配要因は XML マッパー（Phase 1）とテストであり、API 手法の選択ではない。**

#### Phase 1 の内訳

| 作業 | 備考 | 人日 |
| --- | --- | --- |
| 資源タイプ → レコードタイプ判定 | 既存 `item_metadata_validation()` のロジックを流用 | 1〜2 |
| `journal_article` | `journal_metadata` + `journal_issue` + 本体。要素数が最多 | 3〜4 |
| `dissertation` | | 1.5〜2 |
| `posted_content` | フォールバック用 | 1〜1.5 |
| `book` / `report-paper` | | 1.5〜2 |
| 共通要素 | contributors / dates / abstract / license / fundref。**JPCOAR の多値・多言語の扱いが面倒** | 2〜3 |
| XSD 検証・Crossref parser 通し | | 1〜1.5 |
| **小計** | | **10〜16** |

#### 全体

| 項目 | 人日 |
| --- | --- |
| Phase 1（XML マッパー） | 10〜16 |
| Phase 2（クライアント） | 2〜3 |
| Phase 3（非同期化・状態管理） | 5〜8 |
| Phase 4（管理 UI） | 4〜6 |
| Phase 5（`rest_v2` 追加） | 1〜2 |
| テスト | 10〜16 |
| 結合検証（`test.crossref.org` との往復、エラーケース） | 3〜5 |

- **MVP（Phase 1〜3、テスト最小、管理 UI なし）: 20〜30 人日 ≒ 1〜1.5 か月**
- **フル（Phase 1〜5 + WEKO 相当のテスト）: 35〜56 人日 ≒ 2〜3 か月**

いずれも 1 人で作業した場合。テスト工数は WEKO のテスト文化を前提としている
（`weko-workflow` は本体 7,016 行に対しテスト 26,095 行、`test_views.py` だけで 7,827 行）。

**キャリブレーション**: 同じ「外部 API への識別子登録」である ARK 実装は
約 446 行・3 ファイル・テストなし・管理 UI なしで **3〜5 人日相当**。
Crossref は XML 文書生成・非同期状態管理・管理 UI が加わるため、**その約 10 倍規模**になる。

#### API 手法（§3-3）による差

| | `servlet`（非同期） | `rest_v2`（同期） |
| --- | --- | --- |
| クライアント実装 | 2〜3 人日 | 2〜3 人日 |
| 結果取得 | `submissionDownload` ポーリング + 状態遷移 **+3〜4 人日** | レスポンスに含まれる **0 人日** |

**差は 3〜4 人日（全体の約 1 割）**。`WEKO_CROSSREF_API_MODE` で抽象化する設計のため、
`servlet` で作った後に `rest_v2` を足すのは +1〜2 人日で済む。
**どちらに決まっても見積は大きく動かないので、§9-2 の回答を待たずに着手してよい。**

### 8-2. 工数を圧縮する選択肢

**対応レコードタイプを絞るのが最も効く。**
機関リポジトリのアイテムをすべて `posted_content type="other"` で登録する割り切りなら、
Phase 1 が **10〜16 → 4〜6 人日**に落ちる。
まずこれで動かし、`journal_article` / `dissertation` を後から追加する進め方が現実的。

その他の圧縮余地:

- Phase 4（管理 UI）を後回しにし、当面は CLI コマンドでの再送のみとする（−4〜6 人日）
- `citation_list` / `fundref` / `relations` など任意要素を初期実装から外す（−1〜2 人日）

### 8-3. リスク要因

1. **JPCOAR 実データのばらつき** — 多言語・多値・欠損の組み合わせでマッパーが膨らむ。**見積が最もブレる箇所**。
2. **Crossref のスキーマ検証の厳しさ** — XSD を通っても Crossref 側で弾かれるケースがあり、テスト系との往復が増える。
3. **§9-5 の課題** — 現在の DOI 付与バリデーションは Crossref XML の必須要素と一致していないため、
   「ワークフローの承認は通るが Crossref 登録だけ失敗する」アイテムが発生する。
   この手当てが Phase 3 に上乗せされる可能性がある。

---

## 9. 未決事項・要確認事項

### 9-1. Crossref との関係・会員資格 ← **最優先**

WEKO の既存フィールド名 `jalc_crossref_doi` は「JaLC を通じて登録する Crossref DOI」を意味する
（日本の JaLC 会員機関のユースケース）。一方、WACREN 参加機関は Crossref の**直接会員**として
登録する想定であり、前提が異なる。

**2026-08 時点で判明していること**

| 項目 | 状況 |
| --- | --- |
| WACREN 側機関の Crossref 会員資格 | **未加入**。Member ID / DOI プレフィックスとも保有していない |
| 本番登録の可否 | 会員登録とプレフィックス割り当てが済むまで**不可** |
| 費用 | 所在国が GEM 対象なら**年会費・登録料とも無料**（§2-3）。Nigeria は 2026-01-01 から対象 |
| **開発・検証段階の進め方** | **JAIRO Cloud / WEKO3 の開発者（サービスプロバイダ）としてテストアカウントを申請する**（§2-2 経路 A、文面は §2-5）。この経路なら申請者自身の会員資格は不要 |

**確認すべき点**

- WACREN 側機関の所在国と GEM 対象可否（郵送先・請求先の両方が対象国内であること）
- 会員申請の実施主体とスケジュール（機関単体か、WACREN 経由か、Sponsor 経由か）
- 割り当てられる DOI プレフィックス
- 既存の `jalc_crossref_doi` フィールドを流用するか、新たに `crossref_doi` を設けるか

**設計への影響**: プレフィックスの持ち方と設定画面の設計（§5-2 の案 A / 案 B）がここで決まる。
ただし **§8 Phase 1〜3（XML 生成・テスト系への送信・非同期化）は会員資格が無くても進められる**ため、
会員申請の完了を待たずに実装に着手してよい。

### 9-2. 同期 REST Deposit v2 の利用可否

§3-2 のとおり、`api.crossref.org/v2/deposits` がメンバー／サービスプロバイダ向けに
開かれているかが不明。**§2-5 の申請メールの質問 1 として同梱済み**。
回答によって結果ポーリング（§4-1）の要否が変わる。

### 9-3. DOI の更新・削除

- **更新**: 同じ DOI に対して `timestamp` を大きくして再デポジットすると、メタデータが上書きされる。
  WEKO でアイテムのメタデータが更新された際に**自動で再デポジットするか**を決める必要がある。
  （案: 設定 `WEKO_CROSSREF_UPDATE_ON_EDIT`、既定 `False`）
- **削除**: **Crossref は登録済み DOI の削除を認めていない。**
  WEKO の `delete_pidstore_doi()`（DOI 削除）が呼ばれても Crossref 側には反映できない。
  解決先 URL を「取り下げ」ページに変更する（`doTransferDOIsUpload`）などの運用方針を決める必要がある。

### 9-4. 対象とする資源タイプ

Crossref は主に学術出版物を対象としており、研究データについては DataCite が使われるのが一般的。
`dataset_type` の扱い（Crossref に登録するか、対象外とするか）を決める。

### 9-5. 既存メタデータ検証との整合

`item_metadata_validation()` の Crossref 必須項目は現状 `title` / `type` / `pageStart` /
`sourceIdentifier` / `sourceTitle` / `fileURI` 程度で、
Crossref XML の必須要素（`<titles>`, `<publication_date>`, `<doi_data>`）とは一致しない。
API 登録を有効にした場合、**DOI 付与時点でのバリデーションを Crossref の要件に合わせて強化すべきか**を決める。
（強化しないと、承認は通るが Crossref 登録だけ失敗する状態が発生する）

### 9-6. 既存 DOI の一括登録

API 登録を有効化する以前に付与済みの Crossref DOI について、
遡って一括登録するバッチ（CLI コマンド）が必要かを確認する。

### 9-7. JaLC / DataCite への展開 → **解決済み: 共通基盤として設計**

本書の作成時点では「将来を見越すなら `DoiRegistrationAgency` のような共通インターフェースを
切っておく」という指摘にとどめていたが、DataCite への対応が具体化したため、
**共通基盤を独立した設計仕様として起こした。**

- [`WACREN_datacite.md`](./WACREN_datacite.md) — DataCite 固有仕様
- **[`WACREN_doi_registration.md`](./WACREN_doi_registration.md) — DOI 登録共通基盤の設計仕様**

共通基盤側で扱う事項（本書 §4 の内容は共通基盤側に移る）:

- `DoiRegistrationAgency` 抽象と同期／非同期の吸収
- `doi_deposit_log`（エージェンシー共通の単一テーブル）
- オーケストレータと Celery タスク、リトライ
- `saving_doi_pidstore()` へのフックとコミット競合対策
- 設定の階層構造、エラー分類、管理 UI

**実装順序は DataCite → Crossref を推奨**（共通基盤の検証を安価に済ませるため）。
詳細は [`WACREN_doi_registration.md` §15](./WACREN_doi_registration.md) を参照。

---

## 10. 参考リンク

- [XML deposit using HTTPS POST — Crossref](https://www.crossref.org/documentation/register-maintain-records/direct-deposit-xml/https-post/)
- [Submission queue and log — Crossref](https://www.crossref.org/documentation/register-maintain-records/verify-your-registration/submission-queue-and-log/)
- [Testing your XML — Crossref](https://www.crossref.org/documentation/register-maintain-records/direct-deposit-xml/testing-your-xml/)
- [Verifying and testing your XML — Crossref Support Center](https://support.crossref.org/hc/en-us/articles/214236806-Verifying-and-testing-your-XML)
- [Schema versions — Crossref](https://www.crossref.org/documentation/content-registration/metadata-deposit-schema/schema-versions/)
- [Schema library — Crossref](https://www.crossref.org/documentation/schema-library/)
- [Posted content (includes preprints) markup guide — Crossref](https://www.crossref.org/documentation/schema-library/markup-guide-record-types/posted-content-includes-preprints/)
- [Journals and articles markup guide — Crossref](https://www.crossref.org/documentation/schema-library/markup-guide-record-types/journals-and-articles/)
- [Example XML metadata — Crossref](https://www.crossref.org/xml-samples/)
- [crossref/schema — GitLab（XSD・best-practice-examples）](https://gitlab.com/crossref/schema)
- [Service providers — Crossref](https://www.crossref.org/community/service-providers/)
- [Become a member — Crossref](https://www.crossref.org/membership/)
- [Global Equitable Membership (GEM) program — Crossref](https://www.crossref.org/gem/)
- [The GEM program - Year Three and program expansion for 2026 — Crossref](https://www.crossref.org/blog/the-gem-program-year-three-and-program-expansion-for-2026/)
- [Sponsors program — Crossref](https://www.crossref.org/community/sponsors/)
- [Deposit API（deprecated）— CrossRef/rest-api-doc](https://github.com/CrossRef/rest-api-doc/blob/master/deprecated/deposit_api.md)
- [Synchronous REST API Deposit v2 — Crossref Knowledge Base（要認証）](https://crossref.gitlab.io/knowledge_base/docs/services/xml-deposit-synchronous-2/)
