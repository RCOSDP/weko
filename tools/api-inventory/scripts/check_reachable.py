# -*- coding: utf-8 -*-
"""C/D 区分エンドポイントの登録チェーンを静的に確認する。"""
import re, os, subprocess, sys
ROOT='/home/mhaya/wekov2'

# (表示名, blueprint変数が定義されたファイル, blueprint名, 期待する登録経路の検索パターン)
TARGETS = [
 ("weko_records_ui (UI)",   "modules/weko-records-ui/weko_records_ui",  "weko_records_ui",
  [("setup.py","invenio_base.apps"),("ext.py","register_blueprint")]),
 ("weko_deposit_rest (API)","modules/weko-deposit/weko_deposit",        "weko_deposit_rest",
  [("setup.py","invenio_base.api_apps"),("ext.py","register_blueprint")]),
 ("weko_gridlayout (UI)",   "modules/weko-gridlayout/weko_gridlayout",  "weko_gridlayout",
  [("setup.py","invenio_base.blueprints")]),
 ("weko_gridlayout_api",    "modules/weko-gridlayout/weko_gridlayout",  "weko_gridlayout_api",
  [("setup.py","invenio_base.api_blueprints")]),
 ("weko_handle (UI)",       "modules/weko-handle/weko_handle",          "weko_handle",
  [("setup.py","invenio_base.blueprints")]),
 ("weko_items_ui_api",      "modules/weko-items-ui/weko_items_ui",      "weko_items_ui_api",
  [("setup.py","invenio_base.api_blueprints")]),
 ("weko_schema_rest (API)", "modules/weko-schema-ui/weko_schema_ui",    "weko_schema_rest",
  [("setup.py","invenio_base.api_apps"),("ext.py","register_blueprint")]),
]

def grep(path, pat):
    if not os.path.isfile(path): return None
    txt=open(path,encoding='utf-8',errors='replace').read()
    for i,l in enumerate(txt.splitlines(),1):
        if pat in l: return i,l.strip()[:100]
    return None

for name, pkg, bpname, checks in TARGETS:
    mod=os.path.dirname(os.path.join(ROOT,pkg))
    print(f"\n■ {name}")
    ok=True
    for fname, pat in checks:
        p = os.path.join(mod,'setup.py') if fname=='setup.py' else os.path.join(ROOT,pkg,'ext.py')
        r = grep(p, pat)
        rel=os.path.relpath(p,ROOT)
        if r: print(f"   OK  {rel}:{r[0]}  {r[1]}")
        else: print(f"   NG  {rel}  ('{pat}' が見つからない)"); ok=False
    print(f"   => {'到達可能' if ok else '要確認'}")
