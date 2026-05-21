#!/bin/bash

check_connection() {
  cd ../../
  docker-compose exec web bash -c "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg"
  docker compose restart web

  local HOST="$1"
  local SLEEP="$2"
  local MAX_RETRY="$3"
  local TIMEOUT="$4"

  local count=0
  until STATUS_CODE=$(timeout "$TIMEOUT" curl -sk -o /dev/null -w "%{http_code}" "$HOST") && [ "$STATUS_CODE" -eq 200 ]; do
    count=$((count + 1))
    if [ "$count" -ge "$MAX_RETRY" ]; then
      echo "再起動に失敗しました。処理を終了します。"
      exit 1
    fi
    echo "再起動待機中... ステータスコード: $STATUS_CODE"
    sleep "$SLEEP"
  done
  echo "接続成功: $HOST (ステータスコード: $STATUS_CODE)"
}

start_time=$(date +%s)

docker cp test/tavern/prepare_data/index.sql $(docker compose ps -q postgresql):/tmp/index.sql
docker compose exec postgresql psql -U invenio -d invenio -f /tmp/index.sql

SETTING_FILE=$(pwd)/scripts/instance.cfg
CONFIG_PATH=test/tavern/test/config.yaml
host=$(grep '^  host:' "$CONFIG_PATH" | awk '{print $2}')
sleep_wait=$(grep '^  sleep_wait:' "$CONFIG_PATH" | awk '{print $2}')
max_count=$(grep '^  max_count:' "$CONFIG_PATH" | awk '{print $2}')
timeout=$(grep '^  timeout:' "$CONFIG_PATH" | awk '{print $2}')
entity_id=$(grep '^    entity_id:' "$CONFIG_PATH" | awk '{print $2}')
test_file1=$(grep '^    index_test_file1:' "$CONFIG_PATH" | awk '{print $2}')
test_file2=$(grep '^    index_test_file2:' "$CONFIG_PATH" | awk '{print $2}')
test_file3=$(grep '^    index_test_file3:' "$CONFIG_PATH" | awk '{print $2}')
depth=$(grep '^    depth:' "$CONFIG_PATH" | awk '{print $2}')
num_per_level=$(grep '^    num_per_level:' "$CONFIG_PATH" | awk '{print $2}')

option_cmd=${1:-all}
shift

pytest_opts=""

pytest_opts="$pytest_opts -vv"
TARGET_TEST_PATH="test/tavern/test/index/target_test.txt"
ROLE_TEST_PATH="test/tavern/test/index/role_test.txt"
if [ "$option_cmd" = "select" ]; then
  if [ ! -f "$TARGET_TEST_PATH" ] || [ ! -s "$TARGET_TEST_PATH" ]; then
    echo "エラー: $TARGET_TEST_PATH が存在しないか空です。"
    exit 1
  fi
  # 対象テストを取得
  target_result=""
  for line in $(grep -v '^\s*#' "$TARGET_TEST_PATH" | grep -v '^\s*$'); do
    if [ -z "$target_result" ]; then
      target_result="$line"
    else
      target_result="$target_result or $line"
    fi
  done
  if [ ! -f "$ROLE_TEST_PATH" ] || [ ! -s "$ROLE_TEST_PATH" ]; then
    echo "エラー: $ROLE_TEST_PATH が存在しないか空です。"
    exit 1
  fi
  # 役割テストを取得
  role_result=""
  for line in $(grep -v '^\s*#' "$ROLE_TEST_PATH" | grep -v '^\s*$'); do
    if [ -z "$role_result" ]; then
      role_result="$line"
    else
      role_result="$role_result or $line"
    fi
  done
  if [ -z "$target_result" ] && [ -z "$role_result" ]; then
    echo "エラー: 対象テストまたは役割テストの指定が不十分です。"
    exit 1
  fi
  if [ -n "$target_result" ] && [ -n "$role_result" ]; then
    pytest_opts="$pytest_opts -m '($target_result) and ($role_result)'"
  elif [ -n "$target_result" ]; then
    pytest_opts="$pytest_opts -m \"$target_result\""
  elif [ -n "$role_result" ]; then
    pytest_opts="$pytest_opts -m \"$role_result\""
  fi
fi

log_file="logs/index_test_$(date +%Y%m%d_%H%M%S).log"
mkdir -p test/tavern/logs

# generate test data
cd test/tavern
docker compose exec -T tavern python generator/json/generate_index_data.py

# WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = False
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False
# 他設定値の影響しないテスト

# WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False
grep -E "^WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo 'WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False' >> $SETTING_FILE
else
  sed -i.bak 's/WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS *= *True/WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False/' $SETTING_FILE
fi
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = False
grep -E "^WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo 'WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = False' >> $SETTING_FILE
else
  sed -i.bak 's/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION *= *True/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = False/' $SETTING_FILE
fi
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False
grep -E "^WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo 'WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False' >> $SETTING_FILE
else
  sed -i.bak 's/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION *= *True/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False/' $SETTING_FILE
fi
# WEKO_ACCOUNTS_IDP_ENTITY_ID = entity_id
grep -E "^WEKO_ACCOUNTS_IDP_ENTITY_ID *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo "WEKO_ACCOUNTS_IDP_ENTITY_ID = \"$entity_id\"" >> $SETTING_FILE
else
  sed -i.bak "s|WEKO_ACCOUNTS_IDP_ENTITY_ID *= *.*|WEKO_ACCOUNTS_IDP_ENTITY_ID = $entity_id|" $SETTING_FILE
fi

check_connection "$host" "$sleep_wait" "$max_count" "$timeout"

# execute test
cd test/tavern
echo "target test: $test_file1" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts $(ls test/index/$test_file1) | tee -a "$log_file"
echo "\n\n" >> "$log_file"

# WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = True
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = True
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = True
# WEKO_THEME_INSTANCE_DATA_DIR = ""
# CELERY_GET_STATUS_TIMEOUT = "a"

# WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = True
sed -i 's/WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS *= *False/WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = True/' $SETTING_FILE
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = True
sed -i 's/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION *= *False/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = True/' $SETTING_FILE
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = True
sed -i 's/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION *= *False/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = True/' $SETTING_FILE
# WEKO_THEME_INSTANCE_DATA_DIR = ""
grep -E "^WEKO_THEME_INSTANCE_DATA_DIR *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo 'WEKO_THEME_INSTANCE_DATA_DIR = ""' >> $SETTING_FILE
else
  sed -i.bak 's/WEKO_THEME_INSTANCE_DATA_DIR *= *.*$/WEKO_THEME_INSTANCE_DATA_DIR = ""/' $SETTING_FILE
fi
# CELERY_GET_STATUS_TIMEOUT = "a"
grep -E "^CELERY_GET_STATUS_TIMEOUT *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo 'CELERY_GET_STATUS_TIMEOUT = "a"' >> $SETTING_FILE
else
  sed -i.bak 's/CELERY_GET_STATUS_TIMEOUT *= *.*$/CELERY_GET_STATUS_TIMEOUT = "a"/' $SETTING_FILE
fi

check_connection "$host" "$sleep_wait" "$max_count" "$timeout"

# execute test
cd test/tavern
echo "target test: $test_file2" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/index/"$test_file2" | tee -a "$log_file"
echo "\n\n" >> "$log_file"

# WEKO_ACCOUNTS_IDP_ENTITY_ID = ""
sed -i "s|WEKO_ACCOUNTS_IDP_ENTITY_ID *= *.*|WEKO_ACCOUNTS_IDP_ENTITY_ID = \"\"|" $SETTING_FILE
# WEKO_PERMISSION_SUPER_ROLE_USER = 1
grep -E "^WEKO_PERMISSION_SUPER_ROLE_USER *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
  echo 'WEKO_PERMISSION_SUPER_ROLE_USER = 1' >> $SETTING_FILE
else
  sed -i.bak 's/WEKO_PERMISSION_SUPER_ROLE_USER *= *\["System Administrator", "Repository Administrator"\]/WEKO_PERMISSION_SUPER_ROLE_USER = 1/' $SETTING_FILE
fi

check_connection "$host" "$sleep_wait" "$max_count" "$timeout"

# execute test
cd test/tavern
echo "target test: $test_file3" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/index/"$test_file3" | tee -a "$log_file"
echo "\n\n" >> "$log_file"

# restore settings
# WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False
sed -i 's/WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS *= *True/WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False/' $SETTING_FILE
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = False
sed -i 's/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION *= *True/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION = False/' $SETTING_FILE
# WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False
sed -i 's/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION *= *True/WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False/' $SETTING_FILE
# WEKO_PERMISSION_SUPER_ROLE_USER = ['System Administrator', 'Repository Administrator']
sed -i 's/WEKO_PERMISSION_SUPER_ROLE_USER *= *1/WEKO_PERMISSION_SUPER_ROLE_USER = ["System Administrator", "Repository Administrator"]/' $SETTING_FILE
# WEKO_THEME_INSTANCE_DATA_DIR = 'data'
sed -i 's/WEKO_THEME_INSTANCE_DATA_DIR *= *""/WEKO_THEME_INSTANCE_DATA_DIR = "data"/' $SETTING_FILE
# CELERY_GET_STATUS_TIMEOUT = 3.0
sed -i 's/CELERY_GET_STATUS_TIMEOUT *= *"a"/CELERY_GET_STATUS_TIMEOUT = 3.0/' $SETTING_FILE

check_connection "$host" "$sleep_wait" "$max_count" "$timeout"

# generate_prepare_index.py を用いたインデックスの正常系テスト
cd test/tavern
docker compose exec -T tavern python generator/json/generate_prepare_index.py -d "$depth" -n "$num_per_level"
echo "prepare_index.sql" >> prepare_data/execute_order.txt

cd ../../
docker cp test/tavern/prepare_data/prepare_index.sql $(docker compose ps -q postgresql):/tmp/prepare_index.sql
docker compose exec postgresql psql -U invenio -d invenio -f /tmp/prepare_index.sql

# get count of generated index data
cd test/tavern
line_count=$(($(wc -l < prepare_data/prepare_index.sql) + 1))
echo "生成されたインデックスの数: $line_count"
docker compose exec -T tavern python generator/json/generate_index_data.py -s 101 -e $((100 + line_count))

# execute test
docker compose exec -T tavern python test/index/replacer.py --output /tavern/test/index/test_index_generated.tavern.yaml
echo "target test: test_index_generated.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/index/test_index_generated.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"

sed -i "/prepare_index.sql/d" prepare_data/execute_order.txt
mv test/index/test_index_generated.tavern.yaml request_params/index/test_data/
mv prepare_data/prepare_index.sql request_params/index/test_data/

# execute during importing test
echo "target test: test_index_import.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/index/test_index_import.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"

# execute stopping DB test
cd ../../
docker compose stop postgresql pgpool
cd test/tavern
echo "target test: test_index_stop_db.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/index/test_index_stop_db.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"
mv "$log_file" request_params/index/test_data/
cd ../../
docker compose start postgresql pgpool

# zip test files
cd test/tavern/request_params/index/
zip -rq test_data_$(date +%Y%m%d_%H%M%S).zip test_data
echo "test_dataディレクトリをzip化し、 request_params/index に出力しました。"
rm -rf test_data/*

echo "処理が終了しました。"

end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "所要時間: $((elapsed / 60))分 $((elapsed % 60))秒"
