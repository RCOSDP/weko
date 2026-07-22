# -*- coding: utf-8 -*-
"""CLI entry point (run from invenio shell). Design spec 5.2 / 6.0.

Responsibilities:
    - Parse the command line arguments.
    - **Suppress Timestamp updates**: the whole run is wrapped in try/finally, so the
      ``Timestamp.before_update`` listener of ``weko_records`` is temporarily removed
      at the start and restored at the end (this keeps the ``updated`` column of
      ``item_type`` / ``item_type_property`` / ``item_type_mapping`` clean).
    - Set up the import path (add ``scripts/demo`` and this package to sys.path).
    - Start :class:`engine.MigrationEngine` and emit the report via :mod:`report`.

How to run (important):
    ``invenio shell`` is really IPython, and IPython itself intercepts ``--`` flags
    such as ``--config`` (they never reach the script). For that reason, **arguments
    are passed via environment variables when running through invenio shell**
    (IPython does not touch environment variables).

    Via invenio shell (how it is run in production)::

        docker compose exec \\
            -e JDCAT_CONFIG=scripts/demo/jdcat_migration/mapping_config.json \\
            -e JDCAT_ITEM_TYPES=12,20 -e JDCAT_PHASE=all -e JDCAT_DRY_RUN=1 \\
            web invenio shell scripts/demo/jdcat_migration/migrate.py

    Plain python run (development-time; an app context is needed separately)::

        python migrate.py --config mapping_config.json --item-types 12,20 \\
            --phase all --dry-run

Environment variables:
    JDCAT_CONFIG      Path to the config JSON (required)
    JDCAT_ITEM_TYPES  Target item_type values (comma-separated; defaults to
                      target_item_types in the config)
    JDCAT_PHASE       all|1|2|3|pre (default all)
    JDCAT_DRY_RUN     1/true/yes for a dry-run
    JDCAT_CLEANUP     1/true/yes for Phase3 logical deletion (opt-in)
    JDCAT_REPORT_OUT  Report output file (standard output if unset)
"""

from __future__ import unicode_literals

import argparse
import os
import sys


def _setup_import_path():
    """Make ``scripts/demo`` and this package importable (design spec / handoff 6).

    This package (``scripts/demo/jdcat_migration``) sits one level below the existing
    scripts, so ``scripts/demo`` is added to sys.path to allow importing
    ``properties`` / ``register_properties``, and this directory is added to allow
    importing ``config`` / ``engine`` / ``report``.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    demo = os.path.dirname(here)
    for path in (here, demo):
        if path not in sys.path:
            sys.path.insert(0, path)


_setup_import_path()

from flask import current_app  # noqa: E402
from invenio_db import db  # noqa: E402

from config import MigrationConfig, ConfigError  # noqa: E402
from engine import MigrationEngine  # noqa: E402
import report as report_mod  # noqa: E402


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='migrate.py',
        description='JDCat マスタデータ移行（item_type / item_type_property / '
                    'item_type_mapping）')
    parser.add_argument('--config', required=True,
                        help='設定JSON（mapping_config.json）のパス')
    parser.add_argument('--item-types', default=None,
                        help='対象item_type（カンマ区切り。既定は設定のtarget_item_types）')
    parser.add_argument('--phase', default='all',
                        choices=['all', '1', '2', '3', 'pre'],
                        help='実行フェーズ（既定 all）')
    parser.add_argument('--dry-run', action='store_true',
                        help='DBを更新せず想定変更のみ出力（事前確認）')
    parser.add_argument('--cleanup', action='store_true',
                        help='Phase3で未参照の独自プロパティを論理削除（opt-in）')
    parser.add_argument('--report-out', default=None,
                        help='レポートの出力先ファイル（未指定は標準出力/ログ）')
    return parser.parse_args(argv)


def _parse_item_types(value):
    if not value:
        return None
    return [int(x.strip()) for x in value.split(',') if x.strip()]


def _env_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on') if value else False


def resolve_options(argv):
    """Resolve the options: argparse if ``--`` flags are present, env vars otherwise.

    Through invenio shell (=IPython) the ``--`` flags never reach the script, so the
    environment variables (JDCAT_*) are the primary input. A plain ``python`` run uses
    the ``--`` flags.
    """
    if any(a.startswith('--') for a in argv):
        a = parse_args(argv)
        return {
            'config': a.config,
            'item_types': a.item_types,
            'phase': a.phase,
            'dry_run': a.dry_run,
            'cleanup': a.cleanup,
            'report_out': a.report_out,
        }
    env = os.environ.get
    cfg = env('JDCAT_CONFIG')
    if not cfg:
        raise ConfigError(
            '設定JSONのパスが未指定です（環境変数 JDCAT_CONFIG または --config）')
    return {
        'config': cfg,
        'item_types': env('JDCAT_ITEM_TYPES'),
        'phase': env('JDCAT_PHASE', 'all'),
        'dry_run': _env_bool(env('JDCAT_DRY_RUN')),
        'cleanup': _env_bool(env('JDCAT_CLEANUP')),
        'report_out': env('JDCAT_REPORT_OUT'),
    }


# --- Temporarily remove / restore the Timestamp listener --------------------

def _timestamp_targets():
    """Return the list of (Timestamp class, listener function) to remove temporarily.

    This program only updates the master tables under weko_records
    (item_type / item_type_property / item_type_mapping), so only
    Timestamp.before_update of ``weko_records`` is targeted (design spec 6.0).
    On import failure an empty list is returned and the migration still continues.
    """
    try:
        from weko_records.models import (
            Timestamp as Weko_Timestamp,
            timestamp_before_update as weko_timestamp_before_update,
        )
        return [(Weko_Timestamp, weko_timestamp_before_update)]
    except Exception as ex:  # noqa: BLE001
        current_app.logger.warning(
            '[jdcat_migration] Timestampリスナーの取得に失敗（解除スキップ）: {0}'.format(ex))
        return []


def _remove_timestamp_listeners(targets):
    removed = []
    for cls, fn in targets:
        try:
            if db.event.contains(cls, 'before_update', fn):
                db.event.remove(cls, 'before_update', fn)
                removed.append((cls, fn))
        except Exception as ex:  # noqa: BLE001
            current_app.logger.warning(
                '[jdcat_migration] Timestampリスナー解除に失敗: {0}'.format(ex))
    if removed:
        current_app.logger.info(
            '[jdcat_migration] Timestamp.before_update を一時解除（{0}件）'.format(len(removed)))
    return removed


def _restore_timestamp_listeners(removed):
    for cls, fn in removed:
        try:
            if not db.event.contains(cls, 'before_update', fn):
                db.event.listen(cls, 'before_update', fn, propagate=True)
        except Exception as ex:  # noqa: BLE001
            current_app.logger.warning(
                '[jdcat_migration] Timestampリスナー復元に失敗: {0}'.format(ex))
    if removed:
        current_app.logger.info('[jdcat_migration] Timestamp.before_update を復元')


def run(argv=None):
    """Run the migration. Returns the result dict (already reported)."""
    opts = resolve_options(sys.argv[1:] if argv is None else argv)

    # Load and validate the config JSON (fatal errors abort with ConfigError)
    try:
        config = MigrationConfig.load(opts['config'], validate=True)
    except ConfigError as ex:
        current_app.logger.error('[jdcat_migration] 設定エラー: {0}'.format(ex))
        raise
    if config.validation.warnings:
        for w in config.validation.warnings:
            current_app.logger.warning('[jdcat_migration][config] {0}'.format(w))

    engine = MigrationEngine(
        config,
        item_types=_parse_item_types(opts['item_types']),
        dry_run=opts['dry_run'],
        cleanup=opts['cleanup'],
    )

    mode = 'dry-run' if opts['dry_run'] else '本実行'
    current_app.logger.info(
        '[jdcat_migration] 開始（{0} / phase={1} / item_types={2}）'.format(
            mode, opts['phase'], engine.item_types))

    # Suppress Timestamp updates (try/finally guarantees the restore)
    removed = _remove_timestamp_listeners(_timestamp_targets())
    try:
        results = engine.run(phase=opts['phase'])
    finally:
        _restore_timestamp_listeners(removed)

    # Emit the report
    text = report_mod.format_report(results, config=config)
    if opts['report_out']:
        report_mod.write_report(text, opts['report_out'])
        current_app.logger.info('[jdcat_migration] レポート出力: {0}'.format(opts['report_out']))
    else:
        print(text)

    current_app.logger.info('[jdcat_migration] 終了')
    return results


if __name__ == '__main__':
    run()
