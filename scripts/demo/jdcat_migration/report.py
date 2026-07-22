# -*- coding: utf-8 -*-
"""Report formatting (dry-run / progress / post-run verification). Design spec 3.3 / 6.3.

:func:`format_report` formats the result dict returned by
:meth:`engine.MigrationEngine.run` into human-readable text. When a phase has no
target, that is stated explicitly as "no target" (design spec 3.3).
"""

from __future__ import unicode_literals

import io


def _hr(title):
    return '=' * 60 + '\n' + title + '\n' + '=' * 60


def _sub(title):
    return '-- ' + title + ' ' + '-' * max(0, 54 - len(title))


def format_report(results, config=None):
    """Format the result dict and return it as a string."""
    if not results:
        return '(結果なし)'
    lines = []
    mode = 'dry-run（DB無更新）' if results.get('dry_run') else '本実行'
    lines.append(_hr('JDCat マスタデータ移行 レポート'))
    lines.append('モード       : {0}'.format(mode))
    lines.append('対象item_type: {0}'.format(
        ', '.join(str(t) for t in results.get('item_types', []))))
    if config is not None and getattr(config, 'source', None):
        lines.append('設定元       : {0}'.format(config.source))
    lines.append('')

    _fmt_pre_validation(lines, results.get('pre_validation'))
    if 'phase1' in results:
        _fmt_phase1(lines, results['phase1'])
    if 'phase2' in results:
        _fmt_phase2(lines, results['phase2'])
    if 'phase3' in results:
        _fmt_phase3(lines, results['phase3'])

    lines.append(_hr('総合判定'))
    lines.append(_overall(results))
    return '\n'.join(lines)


def _fmt_pre_validation(lines, pre):
    lines.append(_sub('実行前検証（設定JSON × DB）'))
    if not pre:
        lines.append('  （スキップ）')
        lines.append('')
        return
    errors = pre.get('errors', [])
    warnings = pre.get('warnings', [])
    if errors:
        lines.append('  [ERROR] {0}件'.format(len(errors)))
        lines.extend('    - ' + m for m in errors)
    if warnings:
        lines.append('  [WARN]  {0}件'.format(len(warnings)))
        lines.extend('    - ' + m for m in warnings)
    if not errors and not warnings:
        lines.append('  OK（エラー・警告なし）')
    lines.append('')


def _fmt_phase1(lines, p):
    lines.append(_sub('Phase1: properties（非破壊更新）'))
    if p.get('no_target'):
        lines.append('  対象なし（更新すべき標準プロパティが存在しません）')
        lines.append('')
        return
    lines.append('  更新対象 : {0}件（追加 {1} / 更新 {2}）'.format(
        p.get('target_count', 0), len(p.get('to_add', [])), len(p.get('to_update', []))))
    if p.get('to_add'):
        lines.append('  追加ID     : ' + _ids(p['to_add']))
    if p.get('to_update'):
        lines.append('  更新ID     : ' + _ids(p['to_update']))
    if 'error' in p:
        lines.append('  [ERROR] {0}'.format(p['error']))
    elif p.get('applied'):
        lines.append('  → 適用済み（commit）')
    else:
        lines.append('  → 未適用（dry-run）')
    lines.append('')


def _fmt_phase2(lines, p):
    lines.append(_sub('Phase2: itemtype（③プロパティID／①itemキー → reload）'))
    per = p.get('item_types', {})
    if not per:
        lines.append('  対象なし')
        lines.append('')
        return
    for tid in sorted(per.keys(), key=lambda x: int(x)):
        e = per[tid]
        if not e.get('exists'):
            lines.append('  [item_type {0}] DBに存在しません'.format(tid))
            continue
        if e.get('no_target'):
            lines.append('  [item_type {0}] 変換対象なし（変換済み/冪等スキップ）'.format(tid))
            continue
        pc = e.get('property_id_changes', [])
        ic = e.get('item_key_changes', {})
        lines.append('  [item_type {0}] ③ {1}件 / ① {2}件'.format(tid, len(pc), len(ic)))
        for item_key, old, new in pc[:20]:
            lines.append('      ③ {0}: {1} → {2}'.format(item_key, old, new))
        if len(pc) > 20:
            lines.append('      ③ ... 他 {0}件'.format(len(pc) - 20))
        shown = 0
        for old_key, new_key in ic.items():
            lines.append('      ① {0} → {1}'.format(old_key, new_key))
            shown += 1
            if shown >= 20:
                if len(ic) > 20:
                    lines.append('      ① ... 他 {0}件'.format(len(ic) - 20))
                break
        if 'reload' in e:
            r = e['reload']
            lines.append('      reload: code={0} msg={1}'.format(
                r.get('code'), r.get('msg')))
        if 'error' in e:
            lines.append('      [ERROR] {0}'.format(e['error']))
        elif e.get('applied'):
            lines.append('      → 適用済み（commit）')
        else:
            lines.append('      → 未適用（dry-run）')
    lines.append('')


def _fmt_phase3(lines, p):
    lines.append(_sub('Phase3: verify & cleanup'))
    per = p.get('item_types', {})
    for tid in sorted(per.keys(), key=lambda x: int(x)):
        e = per[tid]
        if not e.get('exists'):
            lines.append('  [item_type {0}] DBに存在しません'.format(tid))
            continue
        status = 'OK' if e.get('ok') else 'NG'
        lines.append('  [item_type {0}] {1}  旧キー残 {2}件 / 未知プロパティ参照 {3}件'.format(
            tid, status, e.get('old_item_keys_count', 0), e.get('unknown_property_count', 0)))
        if e.get('old_item_keys_remaining'):
            lines.append('      旧キー: ' + ', '.join(e['old_item_keys_remaining'][:20]))
        if e.get('unknown_property_refs'):
            lines.append('      未知cus_id: ' + _ids(e['unknown_property_refs']))
    cleanup = p.get('cleanup')
    if cleanup is not None:
        cand = cleanup.get('candidates', [])
        if not cand:
            lines.append('  cleanup: 論理削除対象なし')
        elif cleanup.get('applied'):
            lines.append('  cleanup: {0}件を論理削除（delflg=true）'.format(
                len(cleanup.get('deleted', []))))
        else:
            lines.append('  cleanup: {0}件が対象（dry-run/未適用）: {1}'.format(
                len(cand), _ids(cand)))
        if 'error' in cleanup:
            lines.append('  cleanup [ERROR] {0}'.format(cleanup['error']))
    lines.append('')


def _overall(results):
    pre = results.get('pre_validation') or {}
    if pre.get('errors'):
        return 'NG: 実行前検証エラーにより中断されました。'
    problems = []
    p2 = results.get('phase2', {}).get('item_types', {})
    for tid, e in p2.items():
        if e.get('error'):
            problems.append('Phase2 item_type {0} エラー'.format(tid))
        r = e.get('reload')
        if r and r.get('code') not in (0, None):
            problems.append('Phase2 item_type {0} reload失敗'.format(tid))
    p3 = results.get('phase3', {}).get('item_types', {})
    for tid, e in p3.items():
        if e.get('exists') and not e.get('ok'):
            problems.append('Phase3 item_type {0} 未達（旧キー/未知参照 残存）'.format(tid))
    p1 = results.get('phase1', {})
    if p1.get('error'):
        problems.append('Phase1 エラー')

    if results.get('dry_run'):
        head = 'dry-run 完了（DBは更新していません）。'
    else:
        head = '本実行 完了。'
    if problems:
        return head + ' 要確認:\n  - ' + '\n  - '.join(problems)
    return head + ' 問題は検出されませんでした。'


def _ids(id_list, limit=40):
    ids = list(id_list)
    shown = ', '.join(str(i) for i in ids[:limit])
    if len(ids) > limit:
        shown += ', ... 他 {0}件'.format(len(ids) - limit)
    return shown


def write_report(text, path):
    """Write the report to a file as UTF-8."""
    with io.open(path, 'w', encoding='utf-8') as fp:
        fp.write(text)
    return path
