# -*- coding: utf-8 -*-
"""台帳・スナップショット等の所在解決。

WEKO3 リポジトリは **public** なので、所見(sec_*)や実証結果(dynamic_verified)を
含むデータは一切置かない。データはプライベートリポジトリで管理し、環境変数で指し示す。

    export WEKO_API_INVENTORY_DIR=/path/to/weko-secret

このディレクトリに置くもの:
    weko3_api_list_full.tsv   台帳(57列・所見つき)
    weko3_api_list.tsv        台帳(24列)
    api_snapshot.json         経路のベースライン
    reconcile_allow.json      実機に無い行の許可リスト
"""
import os
import sys

ENV = 'WEKO_API_INVENTORY_DIR'


def data_dir(required=True):
    """データディレクトリを返す。未設定なら理由を添えて中断する。"""
    d = os.environ.get(ENV)
    if d and os.path.isdir(d):
        return d
    if not required:
        return None
    sys.exit(
        f'{ENV} が未設定、または存在しないディレクトリです。\n'
        '  このリポジトリは public のため、台帳・スナップショットは同梱していません。\n'
        f'  プライベートリポジトリの場所を指定してください:  export {ENV}=/path/to/weko-secret\n'
        '  詳細は tools/api-inventory/ci/README.md')


def data_path(name, required=True):
    d = data_dir(required=required)
    return os.path.join(d, name) if d else None
