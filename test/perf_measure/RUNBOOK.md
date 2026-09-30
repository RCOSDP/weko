# WEKO 表示速度 E2E 計測 手順書 (test/perf_measure)

`fix/issues61802` の**適用前 (before) / 適用後 (after)** で、トップページ・アイテム詳細
(ランディングページ)・検索結果一覧の表示速度を E2E 計測するための手順とスクリプト。

## 構成物

| ファイル | 役割 |
|----------|------|
| `seed_records.py` | 既存レコードをクローンしてダミーレコードを N 件投入(DB+ES、バージョニング付き) |
| `measure.sh` | curl 計測。3ページの応答時間(min/median/mean/p90/max)を `results/<label>.txt` に保存 |
| `browser/measure_browser.mjs` | headless Chromium(Playwright)計測。JS+AJAX込みの実表示時間を `results/<label>_browser.txt` に保存 |
| `nginx-override.yml` | nginx を 18080/18443 に再マップ(kind/k8s が 80/443 を占有しているため) |
| `results/` | 計測結果(before/after) |

## 前提

- スタックは `docker-compose.arm64.yml`(プロジェクト名 `weko`)。web は**ホストのリポジトリ `.` を `/code` に
  バインドマウント**するため、稼働コードは作業ツリーの現在の内容。→ before/after は git 切替 + uwsgi リロードで行う。
- `invenio` DB は初期化済み(アイテムタイプ・インデックス・既存レコード有り)。
- ポート: nginx は 80/443 が kind/k8s と競合するため `nginx-override.yml` で 18080/18443 に再マップ。
- 対象ホスト名: `weko3.example.org`(`INVENIO_WEB_HOST_NAME`)。

## 手順

### 1. スタック起動

```bash
cd /home/mhaya/weko
# postgres/redis/es は起動済み。残りを起動(web は初回ビルドあり)
docker compose -f docker-compose.arm64.yml -p weko up -d pgpool rabbitmq web worker
# nginx はポート再マップして起動
docker compose -f docker-compose.arm64.yml -f test/perf_measure/nginx-override.yml -p weko up -d nginx
```

疎通確認:
```bash
curl -sk -o /dev/null -w "%{http_code} %{time_total}s\n" \
  -H "Host: weko3.example.org" https://127.0.0.1:18443/
```

### 2. ダミーレコード投入(約3000件)

インデックスをゲスト可視にする(公開):
```bash
docker exec weko-postgresql-1 psql -U invenio -d invenio -c \
  "UPDATE index SET public_state=true, public_date=now() WHERE public_state=false;"
```

投入(テンプレート recid=2000001、3000001 から 3000 件、バッチ200):
```bash
docker compose -f docker-compose.arm64.yml -p weko exec -T web bash -lc \
  'source /home/invenio/.virtualenvs/invenio/bin/activate && \
   python /code/test/perf_measure/seed_records.py 2000001 3000001 3000 200'
```

### 3. 計測(after = 現在の作業ツリー = fix/issues61802)

```bash
# キャッシュを揃えるため Redis をフラッシュしてから計測(warm 計測は measure.sh 内でウォームアップ済み)
docker exec weko-redis-1 redis-cli -n 0 FLUSHDB
OUTDIR=test/perf_measure/results test/perf_measure/measure.sh after 3000001 30
```

### 4. before に切替(私の修正を全て外す)

```bash
git checkout 3de23b2dd            # 私の最初の perf コミットの親(=修正前)
# uwsgi をリロード(touch-reload)
docker compose -f docker-compose.arm64.yml -p weko exec -T web bash -lc \
  'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini'
sleep 5   # ワーカー再起動待ち
docker exec weko-redis-1 redis-cli -n 0 FLUSHDB
test/perf_measure/measure.sh before 3000001 30
```

### 5. after に復帰

```bash
git checkout fix/issues61802
docker compose -f docker-compose.arm64.yml -p weko exec -T web bash -lc \
  'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini'
```

### 6. 結果比較

`test/perf_measure/results/before.txt` と `after.txt` を突き合わせる(median を主指標)。

## 後片付け(任意)

- 投入レコード削除: recid 3000001..3003000 の pidstore_pid / records_metadata / pidrelations と ES doc を削除。
- スタック停止: `docker compose -f docker-compose.arm64.yml -p weko down`(ボリュームは保持)。

## 注意

- キャッシュ系の修正(共通B/2-1/3-1)は**初回(cold)アクセスで効果が大きい**。`measure.sh` はウォームアップ後の
  warm 計測。cold 差を見るには各リクエスト前に Redis FLUSHDB する派生計測が必要(必要に応じ追記)。
- 計測値は環境(同居する k8s クラスタ等)の負荷に影響される。相対比較(before/after 同条件)で評価する。
