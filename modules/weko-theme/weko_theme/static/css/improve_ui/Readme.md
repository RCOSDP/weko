# improve-ui

less 開発環境の構築

```sh
cd modules/weko-theme/weko_theme/static/css/improve_ui
npm install
```

less/ ディレクトリ内に .less ファイルを追加した場合は、`__main.less` で `@import` する。

## less コンパイル

```sh
npm run build
```

実行されるコマンドは package.json に記述。

```sh
lessc --clean-css less/__main.less ../weko_theme/improve_ui.min.css
```

## Docker ビルド手順

```sh
git clone https://github.com/burnworks/weko.git
git switch feature/improve-ui

docker-compose build
docker-compose up -d
docker-compose exec web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type3.sql $(docker-compose ps -q postgresql):/tmp/item_type.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker-compose exec web invenio workflow init action_status,Action
docker cp scripts/demo/resticted_access.sql $(docker-compose ps -q postgresql):/tmp/resticted_access.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/resticted_access.sql
docker-compose exec web invenio workflow init gakuninrdm_data
docker-compose exec web invenio assets build
docker-compose exec web invenio collect -v
```
