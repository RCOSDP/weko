#!/bin/bash

start_time=$(date +%s)

docker cp test/tavern/prepare_data/item_type_name.sql $(docker compose ps -q postgresql):/tmp/item_type_name.sql
docker compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type_name.sql
docker cp test/tavern/prepare_data/item_type.sql $(docker compose ps -q postgresql):/tmp/item_type.sql
docker compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker cp test/tavern/prepare_data/item_type_mapping.sql $(docker compose ps -q postgresql):/tmp/item_type_mapping.sql
docker compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type_mapping.sql

# get config values from config.yaml
CONFIG_PATH="test/tavern/test/config.yaml"
SETTING_FILE=$(pwd)/scripts/instance.cfg

host=$(grep '^  host:' "$CONFIG_PATH" | awk '{print $2}')
item_type_id=$(grep '^    item_type_id:' "$CONFIG_PATH" | awk '{print $2}')
metadata_id1=$(grep '^    metadata_id1:' "$CONFIG_PATH" | awk '{print $2}')
metadata_id2=$(grep '^    metadata_id2:' "$CONFIG_PATH" | awk '{print $2}')
test_file1=$(grep '^    test_file1:' "$CONFIG_PATH" | awk '{print $2}')
test_file2=$(grep '^    test_file2:' "$CONFIG_PATH" | awk '{print $2}')
sleep_wait=$(grep '^  sleep_wait:' "$CONFIG_PATH" | awk '{print $2}')
max_count=$(grep '^  max_count:' "$CONFIG_PATH" | awk '{print $2}')

# determine test mode (e.g., select or all, default: all)
option_cmd=${1:-all}
shift

pytest_opts=""
use_marker=0

pytest_opts="$pytest_opts -v"
TARGET_TEST_PATH="test/tavern/test/item_type_mapping/target_test.txt"
ROLE_TEST_PATH="test/tavern/test/item_type_mapping/role_test.txt"
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

loop_count=${1:-1}
shift

continue_flag=${1:-false}
shift
continue_opt=""
if [ "$continue_flag" = "true" ]; then
  continue_opt="-c"
fi

log_file="logs/item_type_mapping_test_$(date +%Y%m%d_%H%M%S).log"
mkdir -p test/tavern/logs

# (1) generate test data
cd test/tavern
docker compose exec -T tavern python generator/json/generate_request_body.py "$item_type_id" -m "$metadata_id1" "$metadata_id2" -l "$loop_count" $continue_opt

# (2) execute tests
eval docker compose exec -T tavern pytest $pytest_opts $(ls test/item_type_mapping/$test_file1) | tee "$log_file"

# (3) generate all schema test and execute tests
docker compose exec -T tavern python test/item_type_mapping/replacer.py --output /tavern/test/item_type_mapping/test_mapping_all_schema.tavern.yaml --target_dir "all_schema_mappings" --exe_type "全件使用"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/item_type_mapping/test_mapping_all_schema.tavern.yaml | tee -a "$log_file"
mv test/item_type_mapping/test_mapping_all_schema.tavern.yaml request_params/item_type_mapping/test_data/

# (4) generate all success test and execute tests
docker compose exec -T tavern python test/item_type_mapping/replacer.py --output /tavern/test/item_type_mapping/test_mapping_all_success.tavern.yaml --target_dir "success" --exe_type "ランダム"
eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/item_type_mapping/test_mapping_all_success.tavern.yaml | tee -a "$log_file"
mv test/item_type_mapping/test_mapping_all_success.tavern.yaml request_params/item_type_mapping/test_data/

if [ "$option_cmd" = "all" ] || [ "$(echo '$pytest_opts' | grep -q 'mapping_duplicate_success')" ] ; then
  # (5) change setting value to True
  grep -E "^DISABLE_DUPLICATION_CHECK *= *.*$" $SETTING_FILE
  if [ $? -ne 0 ]; then
      echo 'DISABLE_DUPLICATION_CHECK = True' >> $SETTING_FILE
  else
      sed -i.bak 's/DISABLE_DUPLICATION_CHECK *= *False/DISABLE_DUPLICATION_CHECK = True/' $SETTING_FILE
  fi
  echo "設定値を変更しました: DISABLE_DUPLICATION_CHECK = True"
  cd ../../
  docker-compose exec web bash -c "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg"
  docker-compose restart web

  # wait for web to restart
  count=0
  until curl -sk -o /dev/null -w "%{http_code}" "$host" | grep -q "200"; do
    echo "再起動待機中..."
    sleep "$sleep_wait"
    count=$((count + 1))
    if [ "$count" -ge "$max_count" ]; then
      echo "再起動に失敗しました。処理を終了します。"
      exit 1
    fi
  done

  # (6) execute duplicate check tests
  cd test/tavern
  eval docker compose exec -T tavern pytest $pytest_opts /tavern/test/item_type_mapping/"$test_file2" | tee -a "$log_file"
fi

# (7) verify all schemas are used
docker compose exec -T tavern python helper/item_type_mapping/verify_schema_usage.py "$item_type_id" $continue_opt
mv "$log_file" request_params/item_type_mapping/test_data/

# (8) zip test_data directory
cd request_params/item_type_mapping/
zip -rq test_data_$(date +%Y%m%d_%H%M%S).zip test_data
echo "test_dataディレクトリをzip化し、 request_params/item_type_mapping に出力しました。"

# (9) clear test_data directory
rm -rf test_data/*

# (10) change setting value to False
if [ "$option_cmd" = "all" ] || [ "$(echo '$pytest_opts' | grep -q 'mapping_duplicate_success')" ] ; then
  grep -E "^DISABLE_DUPLICATION_CHECK *= *.*$" $SETTING_FILE
  if [ $? -ne 0 ]; then
      echo 'DISABLE_DUPLICATION_CHECK = False' >> $SETTING_FILE
  else
      sed -i.bak 's/DISABLE_DUPLICATION_CHECK *= *True/DISABLE_DUPLICATION_CHECK = False/' $SETTING_FILE
  fi
  echo "設定値を変更しました: DISABLE_DUPLICATION_CHECK = False"
  cd ../../../../
  docker-compose exec web bash -c "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg"
  docker-compose restart web
fi

echo "全ての処理が完了しました。"

end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "所要時間: $((elapsed / 60))分 $((elapsed % 60))秒"
