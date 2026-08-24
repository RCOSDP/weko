#!/bin/bash
#
# ユニットテストが使うサービス(PostgreSQL / Elasticsearch / Redis / RabbitMQ)の
# 起動待ち。COMPOSE_FILE を設定した状態で呼ぶこと。
#
# 旧 CI は nginx 経由の HTTPS 疎通を最大300秒待っていたが、ユニットテストは
# アプリを自前で起動するので web / nginx の起動を待つ必要はない。

set -uo pipefail

TIMEOUT=${WAIT_TIMEOUT:-300}

wait_for() {
  local name=$1
  shift
  local start=$SECONDS
  until "$@" >/dev/null 2>&1; do
    if (( SECONDS - start > TIMEOUT )); then
      echo "❌ ${name} が ${TIMEOUT}s 以内に応答しませんでした"
      docker compose ps
      docker compose logs --tail=80 "${name}"
      return 1
    fi
    sleep 3
  done
  echo "✓ ${name} ready ($((SECONDS - start))s)"
}

wait_for postgresql    docker compose exec -T postgresql pg_isready -U invenio -d invenio || exit 1
wait_for redis         docker compose exec -T redis redis-cli ping || exit 1
wait_for rabbitmq      docker compose exec -T rabbitmq rabbitmq-diagnostics -q ping || exit 1
# ES はコンテナ内から見る。ホストの公開ポート(29201)を叩くと、
# 手元で別の WEKO を動かしているときに他方の ES を掴んでしまう。
wait_for elasticsearch docker compose exec -T elasticsearch \
  curl -sf "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s" || exit 1
