# -*- coding: utf-8 -*-
"""Helper tool that generates properties/*.py drafts (development-time). Design spec 4.2.

Uses the current DB ``item_type_property`` as a template and generates draft ``.py``
files that conform to the same contract as the existing ``properties/*.py``. While
generating, subitem keys are replaced using a conversion map (別紙1 / the xlsx subitem
sheet). **A development-time tool: not used by the migration itself (Phase1-3).**

Scope (design spec 4.2):
    - The main use is generating drafts for "newly added" properties. Properties that
      already exist in the standard set use the existing ``properties/*.py`` instead
      (this avoids reproducing the old structure).
    - The output is a **starting draft**. It is expected to be adjusted by hand and
      verified against 別紙2 and 別紙3.
    - ``mapping`` is not in the DB, so ``config.DEFAULT_MAPPING`` is placed instead.
    - The output is **UTF-8**. Put the generated files under ``properties/`` and pull
      them into ``properties/__init__.py`` so Phase1 registers them automatically.

It depends on the DB, so run it in invenio shell. IPython swallows ``--`` flags, so
input is given via **environment variables** (same approach as migrate.py)::

    docker compose exec \\
        -e JDCAT_GEN_IDS=1042,305 \\
        -e JDCAT_GEN_OUT=scripts/demo/jdcat_migration/_gen \\
        -e JDCAT_GEN_SUBITEM=scripts/demo/jdcat_migration/subitem_map.json \\
        web invenio shell scripts/demo/jdcat_migration/gen_properties.py

Environment variables:
    JDCAT_GEN_IDS      property_id values to generate (comma-separated; required)
    JDCAT_GEN_OUT      Output directory (required; created if missing)
    JDCAT_GEN_SUBITEM  subitem key conversion map (.json={old: new} or .xlsx). Optional
    JDCAT_GEN_SUBITEM_SHEET  Sheet name for xlsx input (default 'subitem')
"""

from __future__ import unicode_literals

import argparse
import copy
import io
import json
import os
import pprint
import re
import sys


def _setup_import_path():
    here = os.path.dirname(os.path.abspath(__file__))
    demo = os.path.dirname(here)
    for path in (here, demo):
        if path not in sys.path:
            sys.path.insert(0, path)


_setup_import_path()


# --- Load the subitem key conversion map ------------------------------------

def load_subitem_map(path, sheet='subitem'):
    """Load the subitem key conversion map {old subitem: new subitem}.

    - ``.json``: ``{"subitem_old": "subitem_new", ...}`` is used as-is.
    - ``.xlsx``: built from the subitem sheet (col0=変更前, col2=変更後), reusing
      the stdlib reader in convert_xlsx. #N/A and blank entries are skipped.
    """
    if not path:
        return {}
    if path.lower().endswith('.json'):
        with io.open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        return {str(k): str(v) for k, v in data.items()
                if k and v and str(v).strip().lower() not in ('', '#n/a', '-')}
    # xlsx
    from convert_xlsx import read_xlsx, _filled, _find_header_row
    rows = read_xlsx(path).get(sheet, [])
    if not rows:
        return {}
    hidx, cols = _find_header_row(rows, ['変更前', '変更後'])
    if hidx is None:
        # Fallback: first column=変更前, third column=変更後 (layout observed in
        # the actual file)
        hidx, cols = 0, {'変更前': 0, '変更後': 2}
    c_old, c_new = cols['変更前'], cols['変更後']
    result = {}
    for row in rows[hidx + 1:]:
        if len(row) <= max(c_old, c_new):
            continue
        old, new = row[c_old], row[c_new]
        if _filled(old) and _filled(new):
            result[str(old).strip()] = str(new).strip()
    return result


def convert_subitem_keys(obj, subitem_map):
    """Convert subitem keys via dump to JSON, string replace, load back.

    Longer keys are replaced first.
    """
    if not subitem_map or obj is None:
        return copy.deepcopy(obj)
    s = json.dumps(obj, ensure_ascii=False)
    for old, new in sorted(subitem_map.items(), key=lambda kv: len(kv[0]), reverse=True):
        if old != new:
            s = s.replace(old, new)
    return json.loads(s)


# --- Module text generation -------------------------------------------------

_TEMPLATE = '''# coding:utf-8
"""Definition of {name_ja} property.

★GENERATED DRAFT（gen_properties.py 生成物・要手修正）★
- 現状DB(item_type_property id={pid})を雛形に生成。subitemキーは変換マップ適用済。
- mapping はDBに無いため DEFAULT_MAPPING を仮置き。JPCOAR等の実mappingは
  別紙2・別紙3 を見て手修正すること。
- name_en / multiple_flag は要確認（DBから確定できないため既定値）。
- 本ファイルは properties/ 配下へ置き properties/__init__.py に取り込むこと。
"""
import copy
import json

from . import property_config as config
from .property_func import set_post_data

property_id = "{pid}"
multiple_flag = {multiple_flag}
name_ja = {name_ja_lit}
name_en = {name_en_lit}

mapping = config.DEFAULT_MAPPING

_SCHEMA = {schema_lit}

_FORM = {form_lit}

_FORMS = {forms_lit}


def schema(title="", multi_flag=multiple_flag):
    """Get schema text of item type（DB由来の最終形をそのまま返す）。"""
    d = copy.deepcopy(_SCHEMA)
    if multi_flag:
        return {{
            "type": "array",
            "title": title,
            "minItems": "1",
            "maxItems": "9999",
            "items": copy.deepcopy(_SCHEMA),
        }}
    if title:
        d["title"] = title
    return d


def form(key="", title="", title_ja=name_ja, title_en=name_en,
         multi_flag=multiple_flag):
    """Get form text of item type（key指定時は parentkey を置換）。"""
    d = copy.deepcopy(_FORMS if multi_flag else _FORM)
    if key:
        d = json.loads(json.dumps(d).replace("parentkey", key))
    return d


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop("option")
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)
    if kwargs.pop("mapping", True):
        post_data["table_row_map"]["mapping"][key] = mapping
    else:
        post_data["table_row_map"]["mapping"][key] = config.DEFAULT_MAPPING
'''


def _lit(obj):
    """Return a Python literal string (readable and valid)."""
    return pprint.pformat(obj, width=88)


def render_module(pid, name, schema_obj, form_obj, forms_obj,
                  multiple_flag=True, name_en=''):
    return _TEMPLATE.format(
        pid=pid,
        name_ja=name,
        name_ja_lit=repr(name or ''),
        name_en_lit=repr(name_en or ''),
        multiple_flag=bool(multiple_flag),
        schema_lit=_lit(schema_obj if schema_obj is not None else {}),
        form_lit=_lit(form_obj if form_obj is not None else {}),
        forms_lit=_lit(forms_obj if forms_obj is not None else {}),
    )


def _clean_name(name):
    """Return the original property name with a trailing "_unused" stripped.

    The suffix comes from test pre-processing.
    """
    s = (name or '').strip()
    if s.endswith('_unused'):
        s = s[:-len('_unused')].strip()
    return s


def _safe_slug(name, pid):
    """Build the output file name from the original property name.

    Strips _unused and replaces only characters not allowed in a file name.
    Example: name="権利者情報_unused" -> "権利者情報". If the name is empty,
    "prop_<id>" is used.
    """
    base = _clean_name(name)
    base = re.sub(r'[\\/:*?"<>|\r\n\t]+', '_', base).strip()
    return base[:80] if base else 'prop_{0}'.format(pid)


# --- Generation core (DB-dependent) -----------------------------------------

def generate(property_ids, out_dir, subitem_map=None, logger=None):
    """Generate draft .py files for the given property_id values into out_dir.

    Returns:
        dict: {'written': [...paths], 'warnings': [...], 'missing': [...ids]}
    """
    from invenio_db import db
    from weko_records.models import ItemTypeProperty

    subitem_map = subitem_map or {}
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    ids = [int(i) for i in property_ids]
    rows = (db.session.query(ItemTypeProperty)
            .filter(ItemTypeProperty.id.in_(ids)).all())
    by_id = {r.id: r for r in rows}

    written, warnings, missing = [], [], []
    used = set()
    for pid in ids:
        r = by_id.get(pid)
        if r is None:
            missing.append(pid)
            warnings.append('property_id {0} がDBに存在しません'.format(pid))
            continue
        schema_obj = convert_subitem_keys(r.schema, subitem_map)
        form_obj = convert_subitem_keys(r.form, subitem_map)
        forms_obj = convert_subitem_keys(r.forms, subitem_map)
        delflg = getattr(r, 'delflg', None)
        if delflg:
            warnings.append('property_id {0} は論理削除(delflg)されています'.format(pid))
        clean_name = _clean_name(r.name)
        text = render_module(pid, clean_name, schema_obj, form_obj, forms_obj)
        slug = _safe_slug(r.name, pid)
        fname = slug + '.py'
        seq = 1
        while fname in used:            # Add a sequence number only on name clashes
            seq += 1
            fname = '{0}_{1}.py'.format(slug, seq)
        used.add(fname)
        fpath = os.path.join(out_dir, fname)
        with io.open(fpath, 'w', encoding='utf-8') as fp:
            fp.write(text)
        written.append(fpath)
        if logger:
            logger.info('[gen_properties] 生成: {0} (id={1}, name={2})'.format(
                fpath, pid, clean_name))
    return {'written': written, 'warnings': warnings, 'missing': missing}


# --- Input resolution (same as migrate.py: env first, -- flags supported) ---

def _resolve_options(argv):
    if any(a.startswith('--') for a in argv):
        p = argparse.ArgumentParser(prog='gen_properties.py')
        p.add_argument('--ids', required=True)
        p.add_argument('--out', required=True)
        p.add_argument('--subitem', default=None)
        p.add_argument('--subitem-sheet', default='subitem')
        a = p.parse_args(argv)
        return {'ids': a.ids, 'out': a.out, 'subitem': a.subitem,
                'sheet': a.subitem_sheet}
    env = os.environ.get
    ids = env('JDCAT_GEN_IDS')
    out = env('JDCAT_GEN_OUT')
    if not ids or not out:
        raise SystemExit('JDCAT_GEN_IDS と JDCAT_GEN_OUT（または --ids/--out）が必要です')
    return {'ids': ids, 'out': out, 'subitem': env('JDCAT_GEN_SUBITEM'),
            'sheet': env('JDCAT_GEN_SUBITEM_SHEET', 'subitem')}


def run(argv=None):
    opts = _resolve_options(sys.argv[1:] if argv is None else argv)
    try:
        from flask import current_app
        logger = current_app.logger
    except Exception:  # noqa: BLE001
        logger = None

    ids = [int(x.strip()) for x in opts['ids'].split(',') if x.strip()]
    subitem_map = load_subitem_map(opts['subitem'], opts['sheet']) if opts['subitem'] else {}
    if opts['subitem'] and not subitem_map:
        sys.stderr.write('[WARN] subitemマップが空です（変換なしで生成）\n')

    result = generate(ids, opts['out'], subitem_map, logger=logger)

    for w in result['warnings']:
        sys.stderr.write('[WARN] {0}\n'.format(w))
    sys.stderr.write('生成 {0}件 / 対象 {1}件 / subitemマップ {2}件\n'.format(
        len(result['written']), len(ids), len(subitem_map)))
    for p in result['written']:
        sys.stderr.write('  - {0}\n'.format(p))
    return result


if __name__ == '__main__':
    run()
