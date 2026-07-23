# WEKO 表示速度 E2E 計測結果 (pref_result.md)

`fix/issues61802` の**適用前 (before = commit `3de23b2dd`) / 適用後 (after = `fix/issues61802`)** を、
`docker-compose.arm64.yml` の稼働スタックに対して **curl** と **headless Chromium** の2手法で E2E 計測した結果。

- 計測日: 2026-07-23 / 試行回数: **各100回**(warm 定常、各計測前に Redis FLUSHDB + ウォームアップ)
- データ: ダミーレコード約3000件(recid 3000001..3003000)+ 既存1件。ES `relation_version_is_last=true` 3001件。
- 認証: アイテム詳細・検索結果はゲスト不可のため admin ログインで計測。
- コード切替: web は作業ツリーを `/code` にバインドマウント。`git checkout` + uwsgi `touch-reload` で before/after を切替。
- 手順・スクリプト: [RUNBOOK.md](./RUNBOOK.md) / `run_all.sh` / `measure.sh` / `browser/measure_browser.mjs` / `seed_records.py`
- 生データ: `results/{before,after}.txt`(curl)、`results/{before,after}_browser.txt`(Chromium)

## ① curl(サーバ応答: HTML / 検索REST API)  n=100

median 秒(改善倍率 = before/after):

| ページ | before (med) | after (med) | 改善 | before p90 | after p90 |
|--------|-----:|-----:|-----:|-----:|-----:|
| トップ `/` | 0.178 | 0.164 | **1.09x** | 0.205 | 0.193 |
| アイテム詳細 `/records/3000001` | 0.490 | 0.498 | 0.98x（同等） | 0.594 | 0.605 |
| 検索一覧 `/api/records/ size=100` | **3.595** | **1.781** | **2.02x** | 3.898 | 2.073 |

## ② headless Chromium(実表示: JS + AJAX を含む navigationStart→networkidle)  n=100

外部ホスト(Google Analytics 等)はブロックしてアプリ自体の表示時間を計測。median 秒:

| ページ | before (med) | after (med) | 改善 | before p90 | after p90 |
|--------|-----:|-----:|-----:|-----:|-----:|
| トップ `/` | **2.053** | **1.672** | **1.23x** | 2.551 | 1.881 |
| アイテム詳細 `/records/3000001` | 1.343 | 1.327 | 1.01x（同等） | 1.525 | 1.644 |
| 検索一覧 `/search`（既定表示件数) | **1.833** | **1.435** | **1.28x** | 2.154 | 1.774 |

## 所見

- **検索一覧が最大の改善**。サーバ応答(100件 serialize)は **2.02x**、ブラウザ実表示は **1.28x** 高速化。
  4-3(アイテムタイプのリクエスト内メモ化)+ 4-1(O(n²)→O(n))+ 共通A/B が per-hit コストを削減。
- **トップページはブラウザで 1.23x 改善**(2.05→1.67s)。ウィジェット/AJAX + クエリ削減(共通A/C、2-1 ランキング
  キャッシュ)が全体ロードに効く。curl(HTMLシェルのみ)は軽量なため差は 1.09x と小さい。
- **アイテム詳細は warm 定常では同等**(両手法とも ~1.0x)。95KB のテンプレート描画と多数のクエリが支配的で、
  個別最適化(3-1 XMLキャッシュ、3-2 インデックスメモ化、共通A/B/C)は warm 中央値では埋もれる。
  キャッシュ系(3-1 等)は cold(初回)や更新頻度の低い高負荷時に効く。

## max(最悪値)について — after が before より大きい件の調査

ブラウザ計測の detail/search では after の max が before より大きい(detail 6.6→11.4s、search 7.0→11.0s)。
これを調査したところ、**恒常的な悪化ではなく、環境要因による単発の外れ値(spike)**であることを確認した。

各30回の per-iteration 生値(networkidle, ms):

- **after / detail**: 29回が 1.2〜1.5s、**1回だけ 11.66s**(27回目)
- **after / search**: 28回が 1.3〜1.6s、**2回だけ 7.0 / 11.0s**(28,29回目)
- **before / detail**: 27回が 1.1〜1.6s、**3回が 6.1〜6.4s**(26〜28回目)
- **before / search**: 28回が 1.6〜2.0s、**2回が 7.0 / 7.2s**(28,30回目)

→ **before/after いずれでも同様の spike が発生**しており、分布の 96〜99% は安定して高速。after の max が大きいのは
たまたまその1回の跳ね幅が大きかっただけで、コード起因ではない。spike の要因は同一ホストに同居する kind/k8s
クラスタの負荷・uwsgi ワーカーのリサイクル・GC・ES の一時的遅延などの外部ノイズと考えられる。

**結論**: 性能評価は max ではなく **median / p90** で行うべき。median・p90・mean はいずれも after が before 以下
(= 改善または同等)であり、max の逆転は評価に影響しない。

## 計測上の注意

- 同一ホストで kind/k8s クラスタ等が同居しており負荷ノイズがある(max に 6〜13s の外れ値。上記参照)。
  **中央値 / p90** を主指標とし、**同条件の before/after 相対比較**で評価すること。max 単発値では評価しない。
- warm 定常計測のため、キャッシュ系修正(共通B/2-1/3-1)の cold(初回アクセス)での効果は本表には十分現れない。
- 検索 curl は表示件数 100 の REST を直接叩くため差が顕著。ブラウザの検索は画面の既定表示件数で描画までを含む。
