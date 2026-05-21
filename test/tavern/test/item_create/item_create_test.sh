#!/bin/bash

if ! rpm -q postfix > /dev/null 2>&1; then
    echo "Postfix is not installed. Installing..."
    sudo dnf install -y postfix
else
    echo "Postfix is already installed."
fi

start_time=$(date +%s)

option_cmd=${1:-all}
shift

pytest_opts=""

pytest_opts="$pytest_opts -v"
TARGET_TEST_PATH="test/tavern/test/item_create/target_test.txt"
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
  if [ -n "$target_result" ]; then
    pytest_opts="$pytest_opts -m \"$target_result\""
  fi
fi

log_file="logs/item_create_test_$(date +%Y%m%d_%H%M%S).log"
mkdir -p test/tavern/logs

cd test/tavern
echo "target test: test_item_registration.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts test/item_create/test_item_registration.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"

echo "target test: test_item_registration_file.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts test/item_create/test_item_registration_file.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"

echo "target test: test_w-oa-03.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts test/item_create/test_w-oa-03.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"

echo "target test: test_w-oa-15.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts test/item_create/test_w-oa-15.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"

mkdir -p mail/repoadmin/{new,cur,tmp}
mkdir -p mail/contributor/{new,cur,tmp}
chown -R postfix:postfix mail
chmod -R 666 mail
cd postfix
sh ./postfix_settings.sh

echo "notifications_user_settings.sql" >> prepare_data/execute_order.txt
echo "target test: test_w2024-37.tavern.yaml" >> "$log_file"
eval docker compose exec -T tavern pytest $pytest_opts test/item_create/test_w2024-37.tavern.yaml | tee -a "$log_file"
echo "\n\n" >> "$log_file"
sed -i "/notifications_user_settings.sql/d" prepare_data/execute_order.txt

echo "処理が終了しました。"

end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "所要時間: $((elapsed / 60))分 $((elapsed % 60))秒"
