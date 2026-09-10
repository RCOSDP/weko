# -*- coding: utf-8 -*-
"""台帳の列定義。**列に関する唯一の正**。

列名・列数はツール・README・awk の例・CI の検算がそれぞれ持っていて、これまでは
どれかを直しても他が古びるだけだった(v2.0.4 時点で README は 57列/24列/926行 と
書いたまま、実ファイルは 62列/32列/1048行 になっていた)。

ここを直せば、次がまとめて追随する:

  - `build_checklist.py`  … 24列版(実際は32列)の出力列
  - 公開側 `tests/`       … README の記述との整合検査
  - 非公開側 `tests/`     … 実台帳のヘッダ検査

列名だけなので public リポジトリに置いてよい(所見・実証結果は含まない)。
"""

# 詳細版 weko3_api_list_full.tsv の 62列。
FULL_COLUMNS = [
    # 経路の同定 (1-15)
    'no', 'module', 'api_type', 'app', 'method', 'uri', 'path_params',
    'query_params', 'body_params', 'request_content_type', 'blueprint',
    'endpoint', 'impl_func', 'impl_file', 'impl_line',
    # 入出力 (16-20)
    'summary', 'response', 'response_content_type', 'status_codes', 'exceptions',
    # 認証・認可 (21-25)
    'auth_required', 'auth_method', 'oauth_scope', 'roles', 'access_variance',
    # データ操作・運用 (26-33)
    'data_op', 'data_store', 'side_effects', 'cache_ratelimit', 'config_deps',
    'api_version', 'deprecated', 'test_file',
    # git 由来 (34-37) — enrich_git.py が上書きする
    'last_commit', 'last_commit_date', 'last_commit_subject', 'release_tag',
    # 分類・備考 (38-39)
    'category_tags', 'notes',
    # セキュリティ所見と実測 (40-44)
    'sec_pattern', 'sec_detail', 'sec_exposed', 'sec_evidence', 'dynamic_verified',
    # 攻撃観点 (45-54)
    'csrf_protection', 'input_validation', 'audit_logged', 'triggers_task',
    'resource_limit', 'redirect_target', 'ssrf_surface', 'idempotency',
    'auth_mechanism', 'bola_risk',
    # 優先度 (55-56) — prioritize.py が上書きする
    'priority', 'priority_reason',
    # テスト観点と整理 (57-62) — test_coverage.py / prioritize.py が上書きする
    'test_normal', 'test_abnormal', 'test_boundary', 'test_exception',
    'test_gap', 'cleanup',
]

# チェックリスト版 weko3_api_list.tsv の 32列。build_checklist.py が生成する。
# **末尾に足す。** 既存列の位置を動かすと README の awk 例(`$20` など)が全部壊れる。
CHECKLIST_COLUMNS = [
    'no', 'module', 'api_type', 'method', 'uri', 'impl', 'summary',
    'auth', 'roles_scope', 'access_variance', 'data_op', 'data_store',
    'side_effects', 'security_finding', 'security_flags', 'dynamic_verified',
    'api_version', 'deprecated', 'test_file', 'last_change', 'tags', 'notes',
    'config_deps', 'response',
    'priority', 'priority_reason',
    'test_normal', 'test_abnormal', 'test_boundary', 'test_exception',
    'test_gap', 'cleanup',
]

# スクリプトが毎回上書きする派生列。手編集しても次の実行で消える。
DERIVED_COLUMNS = [
    'priority', 'priority_reason',
    'test_normal', 'test_abnormal', 'test_boundary', 'test_exception',
    'test_gap', 'cleanup',
]

# 値の語彙。台帳側で新しい値が現れたら、まずここに足すか、書き間違いを疑う。
APPS = ['UIアプリ', 'APIアプリ(/api)', '両方']
API_TYPES = [
    'REST API', 'AJAX', '画面ビュー', '管理画面', '管理画面(ModelView自動生成)',
    'ファイル配信', 'フレームワーク', 'OAI-PMH', 'SWORD', 'ResourceSync',
    'RSS/Sitemap', '認証',
]
HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
AUTH_REQUIRED = ['要', '要(管理)', '要(設計上)', '不要', '任意(匿名可)']
PRIORITIES = ['P1', 'P2', 'P3', 'P4', 'P5', '整理対象', '環境依存', '対象外']
TEST_MARKS = ['○', '-', '?']
TEST_ASPECTS = [('test_normal', '正常値'), ('test_abnormal', '異常値'),
                ('test_boundary', '境界値'), ('test_exception', '例外処理')]

assert len(FULL_COLUMNS) == 62
assert len(CHECKLIST_COLUMNS) == 32
assert len(set(FULL_COLUMNS)) == len(FULL_COLUMNS)
assert len(set(CHECKLIST_COLUMNS)) == len(CHECKLIST_COLUMNS)
assert FULL_COLUMNS[-8:] == DERIVED_COLUMNS
