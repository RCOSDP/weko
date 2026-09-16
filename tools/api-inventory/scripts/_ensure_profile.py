#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_profile.json が無ければ既定値で作る。

測定条件をコードではなくデータに置くための土台。
バージョンが増えてもスクリプトを増やさずに済むよう、条件はここに集約する。
"""
import json
import os
import sys

# 実機の場所は環境変数から取る(未設定ならこの既定値)。
# 作成後は JSON が正で、環境変数を変えても既に在るファイルは書き換えない。
# 条件を変えたいときは JSON を直す(README「実測はいつも measure.sh 1本」)。
DEFAULT = {
    "_comment": "実測の条件。バージョンをまたいで比較するため、正当な理由なく変えないこと。"
                "変えると measure_report.md に載るハッシュも変わるので、差が後から追える。",
    "allow_writes": True,
    "refresh_fixtures": 40,
    "web_container": os.environ.get("WEKO_WEB_CONTAINER", "weko-web-1"),
    "base_url": os.environ.get("WEKO_BASE_URL", "https://localhost:8443"),
    "host_header": os.environ.get("WEKO_HOST_HEADER", "weko3.example.org"),
    "skip_category_tags": ["shadowed"],
}

def main():
    path = sys.argv[1]
    if os.path.exists(path):
        return
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'  measure_profile.json を既定値で作成した: {path}')

if __name__ == '__main__':
    main()
