# -*- coding: utf-8 -*-
"""Filled-in xlsx -> config JSON (mapping_config.json) converter. Design spec 4.1 / 3.1.

Input: filled-in ``マッピング必要データ_XXXXXXXX.xlsx``
    - item sheet     : col 'item_key' -> col '変更後' (=prop_name), col 'item_type_ids'
    - property sheet : col '旧id' -> col '新id'
Output: ``mapping_config.json`` (design spec 3.2)
    - property_id_map : property sheet, 旧id -> 新id (property ID conversion)
    - item_key_map    : item sheet, item_key -> prop_name per item_type
                        (item key conversion)

No dependencies (**stdlib only**). Reads the xlsx directly with zipfile + xml.etree
(openpyxl and friends are unavailable on the VM/container). It does not touch the DB,
so it can be run standalone with ``python3``::

    python3 convert_xlsx.py マッピング必要データ_20260423.xlsx mapping_config.json \\
        --item-types 12,20

Cells that are not filled in (#N/A) and inconsistencies are written to stderr as
warnings.
"""

from __future__ import unicode_literals

import argparse
import io
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


DEFAULT_TARGET_ITEM_TYPES = (12, 20)
_NA = ('', '#n/a', 'n/a', '-', 'none', 'null')
_OLD_ITEM_KEY_RE = re.compile(r'^item_\d+$')
_PROP_NAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')


# --- stdlib xlsx reader ---------------------------------------------------

def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _si_text(si):
    """Extract the text of a sharedStrings <si> (furigana <rPh> excluded)."""
    parts = []
    for child in si:
        lt = _local(child.tag)
        if lt == 't':
            parts.append(child.text or '')
        elif lt == 'r':          # rich text run
            for rc in child:
                if _local(rc.tag) == 't':
                    parts.append(rc.text or '')
        # rPh (phonetic / furigana) is ignored
    return ''.join(parts)


def _col_index(cell_ref):
    m = re.match(r'^([A-Z]+)\d+$', cell_ref or '')
    if not m:
        return None
    col = 0
    for ch in m.group(1):
        col = col * 26 + (ord(ch) - ord('A') + 1)
    return col - 1


def read_xlsx(path):
    """Read a .xlsx and return ``{sheet_name: [ [cell, ...], ... ]}`` (stdlib only)."""
    z = zipfile.ZipFile(path)
    names = z.namelist()

    shared = []
    if 'xl/sharedStrings.xml' in names:
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root:
            if _local(si.tag) == 'si':
                shared.append(_si_text(si))

    wb = ET.fromstring(z.read('xl/workbook.xml'))
    sheet_defs = []
    for s in wb.iter():
        if _local(s.tag) == 'sheet':
            rid = None
            for k, v in s.attrib.items():
                if _local(k) == 'id':
                    rid = v
            sheet_defs.append((s.get('name'), rid))

    rels = {}
    rroot = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    for rel in rroot:
        rels[rel.get('Id')] = rel.get('Target')

    result = {}
    for name, rid in sheet_defs:
        target = rels.get(rid, '')
        path_in = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        if path_in not in names:
            result[name] = []
            continue
        result[name] = _read_sheet(ET.fromstring(z.read(path_in)), shared)
    return result


def _read_sheet(sroot, shared):
    rows = []
    for row in sroot.iter():
        if _local(row.tag) != 'row':
            continue
        cells = {}
        maxc = -1
        for c in row:
            if _local(c.tag) != 'c':
                continue
            ci = _col_index(c.get('r'))
            if ci is None:
                continue
            ctype = c.get('t')
            val = None
            for child in c:
                lt = _local(child.tag)
                if lt == 'v':
                    val = child.text
                elif lt == 'is':
                    val = ''.join(n.text or '' for n in child.iter()
                                  if _local(n.tag) == 't')
            if ctype == 's' and val is not None:
                try:
                    val = shared[int(val)]
                except (ValueError, IndexError):
                    pass
            cells[ci] = val
            maxc = max(maxc, ci)
        rows.append([cells.get(i) for i in range(maxc + 1)])
    return rows


# --- helpers --------------------------------------------------------------

def _filled(value):
    return value is not None and str(value).strip().lower() not in _NA


def _as_int(value):
    s = str(value).strip()
    if re.match(r'^-?\d+$', s):
        return int(s)
    # handle numeric cells such as "1014.0"
    m = re.match(r'^(-?\d+)\.0+$', s)
    if m:
        return int(m.group(1))
    return None


def _find_header_row(rows, required):
    """Return the index of the row holding all required header words (matched by
    prefix) and a {word: column} mapping.
    """
    for idx, row in enumerate(rows):
        norm = [str(c).strip() if c is not None else '' for c in row]
        col_of = {}
        ok = True
        for key in required:
            found = None
            for ci, cell in enumerate(norm):
                if cell == key or cell.startswith(key):
                    found = ci
                    break
            if found is None:
                ok = False
                break
            col_of[key] = found
        if ok:
            return idx, col_of
    return None, None


# --- conversion core ------------------------------------------------------

class ConvertResult(object):
    def __init__(self):
        self.config = {}
        self.warnings = []
        self.errors = []

    def warn(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)


def build_config(path, target_item_types=DEFAULT_TARGET_ITEM_TYPES):
    """Build the config dict from the xlsx."""
    res = ConvertResult()
    target = [int(t) for t in target_item_types]
    data = read_xlsx(path)

    property_id_map = _build_property_id_map(data, res)
    item_key_map = _build_item_key_map(data, target, res)

    res.config = {
        'meta': {
            'source': os.path.basename(path),
            'target_item_types': target,
        },
        'property_id_map': property_id_map,
        'item_key_map': item_key_map,
    }
    return res


def _get_sheet(data, name):
    """Get a sheet case-insensitively (handles 'property'/'Property' variants)."""
    for k, v in data.items():
        if k.strip().lower() == name.lower():
            return v
    return None


def _find_property_cols(rows):
    """Return the property sheet's (header row idx, 旧id col, 変更後id col).

    Handles both formats. Old format: headers '旧id' / '新id'.
    New format (別紙2): headers 'id' / 'id_'.
    """
    for i, row in enumerate(rows):
        cells = [str(c).strip() if c is not None else '' for c in row]
        c_old = c_new = None
        for j, c in enumerate(cells):
            if c_old is None and c in ('旧id', 'id'):
                c_old = j
            if c_new is None and c in ('新id', 'id_'):
                c_new = j
        if c_old is not None and c_new is not None and c_old != c_new:
            return i, c_old, c_new
    return None, None, None


def _build_property_id_map(data, res):
    """property sheet: 旧id -> 新id (property ID conversion). Old/new formats.

    - Old format: headers '旧id'/'新id'.
    - New format (別紙2): headers 'id'/'id_'. Rows whose 変更後 cell is
      "変更しない" (= do not change) need no conversion and are excluded.
    """
    rows = _get_sheet(data, 'property')
    if not rows:
        res.error('property シートが見つかりません')
        return {}
    hidx, c_old, c_new = _find_property_cols(rows)
    if hidx is None:
        res.error('property シートに 旧id列(旧id/id) と 変更後id列(新id/id_) が'
                  '見つかりません')
        return {}
    result = {}
    na = same = 0
    for row in rows[hidx + 1:]:
        if len(row) <= max(c_old, c_new):
            continue
        old_id = _as_int(row[c_old])
        if old_id is None:
            continue
        val = row[c_new]
        sval = str(val).strip() if val is not None else ''
        if sval == '変更しない':
            same += 1                       # no conversion needed (id unchanged)
            continue
        if not _filled(val):
            na += 1
            continue
        new_id = _as_int(val)
        if new_id is None:
            res.warn('property: 旧id {0} の変更後 "{1}" が整数ではありません'.format(
                old_id, val))
            continue
        if str(old_id) in result and result[str(old_id)] != new_id:
            res.warn('property: 旧id {0} が重複（{1} と {2}）'.format(
                old_id, result[str(old_id)], new_id))
        result[str(old_id)] = new_id
    if same:
        res.warn('property: 「変更しない」{0}件（③変換対象外）'.format(same))
    if na:
        res.warn('property: 変更後 未記入（#N/A）が {0}件（未確定プロパティ）'.format(na))
    if not result:
        res.warn('property_id_map が0件です（③の記入が無い可能性）')
    return result


def _find_item_cols(rows):
    """Return the item sheet's (header row idx, item_key col, prop_name col,
    item_type_ids col).

    Old format: 'item_key' / '変更後' / 'item_type_ids'.
    New format (別紙2): '変更前…item_key' / '変更後…item_key'
    (no item_type_ids column -> None).
    """
    for i, row in enumerate(rows):
        cells = [str(c).replace('\n', '').strip() if c is not None else ''
                 for c in row]
        key_col = name_col = type_col = None
        for j, c in enumerate(cells):
            if 'item_type_ids' in c:
                type_col = j
            elif '変更後' in c:
                if name_col is None:
                    name_col = j
            elif c == 'item_key' or '変更前' in c or 'item_key' in c:
                if key_col is None:
                    key_col = j
        if key_col is not None and name_col is not None:
            return i, key_col, name_col, type_col
    return None, None, None, None


def _build_item_key_map(data, target, res):
    """item sheet: item_key -> prop_name (item key conversion). Old/new formats.

    When the item_type_ids column exists (old format) rows are dispatched per
    type; when it is absent (new format, 別紙2) they are applied to all target
    item types in common.
    """
    rows = _get_sheet(data, 'item')
    if not rows:
        res.error('item シートが見つかりません')
        return {}
    hidx, c_key, c_name, c_type = _find_item_cols(rows)
    if hidx is None:
        res.error('item シートに item_key列 と 変更後列 が見つかりません')
        return {}
    tset = set(target)
    result = {str(t): {} for t in target}
    seen_prop = {str(t): {} for t in target}
    na = 0

    for row in rows[hidx + 1:]:
        need = max(c_key, c_name, c_type if c_type is not None else 0)
        if len(row) <= need:
            continue
        if not _filled(row[c_key]):
            continue
        item_key = str(row[c_key]).strip()
        if not item_key.startswith('item_'):
            continue
        # target item_type (dispatch by the type column if present, otherwise
        # applied to all target item types in common)
        if c_type is not None and _filled(row[c_type]):
            row_types = set()
            for tok in str(row[c_type]).replace(' ', '').split(','):
                ti = _as_int(tok)
                if ti is not None:
                    row_types.add(ti)
            hit = row_types & tset
        else:
            hit = set(target)
        if not hit:
            continue
        after = row[c_name]
        if not _filled(after):
            na += 1
            continue
        prop_name = str(after).strip()
        if not _OLD_ITEM_KEY_RE.match(item_key):
            res.warn('item: item_key "{0}" が旧形式(item_<数字>)ではありません'.format(
                item_key))
        if not _PROP_NAME_RE.match(prop_name):
            res.warn('item: prop_name "{0}" が識別子形式ではありません（key {1}）'.format(
                prop_name, item_key))
        for tid in hit:
            k = str(tid)
            prev = result[k].get(item_key)
            if prev is not None and prev != prop_name:
                res.warn('item[{0}]: item_key {1} が異なる変更後値で重複'
                         '（{2} → {3}・後者採用）'.format(tid, item_key, prev, prop_name))
            if prop_name in seen_prop[k] and seen_prop[k][prop_name] != item_key:
                res.warn('item[{0}]: prop_name "{1}" が複数キーで重複（{2} と {3}）'.format(
                    tid, prop_name, seen_prop[k][prop_name], item_key))
            else:
                seen_prop[k][prop_name] = item_key
            result[k][item_key] = prop_name

    if na:
        res.warn('item: 変更後 未記入(#N/A) が {0}件'.format(na))
    for t in target:
        if not result[str(t)]:
            res.warn('item_key_map[{0}] が0件です（①の記入が無い可能性）'.format(t))
    return result


def write_config(config, out_path):
    with io.open(out_path, 'w', encoding='utf-8') as fp:
        json.dump(config, fp, ensure_ascii=False, indent=2, sort_keys=False)
        fp.write('\n')
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='convert_xlsx.py',
        description='回答xlsx → mapping_config.json 変換')
    parser.add_argument('input', help='記入済み マッピング必要データ_*.xlsx')
    parser.add_argument('output', help='出力する mapping_config.json のパス')
    parser.add_argument('--item-types', default='12,20',
                        help='対象item_type（カンマ区切り。既定 12,20）')
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    target = [int(x) for x in args.item_types.split(',') if x.strip()]
    res = build_config(args.input, target)

    for e in res.errors:
        sys.stderr.write('[ERROR] {0}\n'.format(e))
    for w in res.warnings:
        sys.stderr.write('[WARN] {0}\n'.format(w))
    if res.errors:
        sys.stderr.write('変換に失敗しました。\n')
        return 1

    write_config(res.config, args.output)
    pm = res.config['property_id_map']
    im = res.config['item_key_map']
    sys.stderr.write('OK: {0} を出力（property_id_map {1}件 / item_key_map {2}）\n'.format(
        args.output, len(pm), {k: len(v) for k, v in im.items()}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
