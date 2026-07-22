# -*- coding: utf-8 -*-
"""Conversion engine core (Phase1-3). Design spec chapter 6 / implementation
handoff chapter 3.

Design policy:
    - **dry-run updates nothing**: every phase is split into "plan" (read-only,
      computes the planned changes) and "apply" (write + commit); a dry-run runs
      the plan only.
    - **Idempotent**: both the item key conversion and the property ID conversion
      are driven by an "old -> new" map. Data already in the new form yields zero
      replacement targets and is naturally skipped.
    - Faithful to the existing proven code:
        Phase1 = ``register_properties.register_properties_from_folder``
        (does not TRUNCATE)
        Phase2 = first half of ``fix_issue_47128_jdcat.py`` (property ID / item
        key replacement) plus ``ItemTypes.reload``
        (the metadata conversion part, i.e. the second half, is not taken over;
        see 2.4, the re-harvest policy)
    - Each phase returns its result as a structured dict, which ``report.py``
      formats.

This module depends on invenio / weko_records (run it in an invenio shell).
For DB-independent config validation see :mod:`config`.
"""

from __future__ import unicode_literals

import json
import re

from flask import current_app
from invenio_db import db
from sqlalchemy.orm.attributes import flag_modified

from weko_records.api import ItemTypes, ItemTypeProps, Mapping
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeProperty

# Modules directly under scripts/demo (migrate.py adds scripts/demo to sys.path)
import properties
from properties import property_config
from register_properties import (
    get_properties_id,
    register_properties_from_folder,
)

from config import OLD_ITEM_KEY_RE, NEW_ITEM_KEY_RE

#: Extracts <id> from the render.meta_list[key].input_type value "cus_<id>".
CUS_RE = re.compile(r'^cus_(\d+)$')


def get_properties_mapping():
    """Build ``{property_id: prop.mapping}`` from ``properties/*.py``.

    The mapping base passed to ``reload()``. Identical to the same-named function
    in ``update_W2025-29.py`` / ``fix_issue_47128_jdcat.py``.
    """
    mapping = {}
    for name in dir(properties):
        prop = getattr(properties, name)
        pid = getattr(prop, 'property_id', None)
        if pid:
            mapping[int(pid)] = prop.mapping
    return mapping


def folder_property_ids():
    """Set of property_id values exposed by ``properties/*.py``."""
    ids = set()
    for name in dir(properties):
        prop = getattr(properties, name)
        pid = getattr(prop, 'property_id', None)
        if pid:
            ids.add(int(pid))
    return ids


def _iter_form_item_keys(render):
    """Yield (idx, item_key) for render.table_row_map.form keys starting with item_."""
    form = (render or {}).get('table_row_map', {}).get('form', [])
    for idx, entry in enumerate(form):
        if isinstance(entry, dict) and 'key' in entry:
            key = entry['key']
            if isinstance(key, str) and key.startswith('item_'):
                yield idx, key


class MigrationEngine(object):
    """Master data migration engine.

    Args:
        config: Validated :class:`config.MigrationConfig`.
        item_types: List of target item_types (defaults to config.target_item_types).
        dry_run: If True, only compute the planned changes without updating the DB.
        cleanup: Whether Phase3 logically deletes unreferenced JDCat-specific
            properties (opt-in).
        logger: Logger (defaults to current_app.logger).
    """

    def __init__(self, config, item_types=None, dry_run=False, cleanup=False,
                 logger=None):
        self.config = config
        self.item_types = [int(t) for t in (item_types or config.target_item_types)]
        self.dry_run = bool(dry_run)
        self.cleanup = bool(cleanup)
        self.log = logger or current_app.logger
        self.results = {}

    # --- Entry points ------------------------------------------------------

    def run(self, phase='all'):
        """Run the given phase and return the result dict.

        Args:
            phase: 'all' | '1' | '2' | '3' (or 'pre' for pre-validation only).
        """
        self.results = {'dry_run': self.dry_run, 'item_types': list(self.item_types)}

        # Pre-execution validation (design spec 5.3). Abort on fatal errors.
        pre = self.validate_against_db()
        self.results['pre_validation'] = pre
        if pre['errors']:
            self.log.error('[jdcat_migration] 事前検証エラーのため中断します')
            return self.results

        want = self._resolve_phases(phase)
        if 1 in want:
            self.results['phase1'] = self.phase1_properties()
        if 2 in want:
            self.results['phase2'] = self.phase2_itemtypes()
        if 3 in want:
            self.results['phase3'] = self.phase3_verify()
        return self.results

    @staticmethod
    def _resolve_phases(phase):
        if phase in (None, 'all', 'ALL'):
            return {1, 2, 3}
        if phase in ('pre', 'PRE'):
            return set()
        return {int(phase)}

    # --- Pre-execution validation (DB access. design spec 5.3) -------------

    def validate_against_db(self):
        """Validate the config JSON against the live DB.

        - Whether a property definition exists for each new id (the target of the
          property ID conversion).
        - Whether property_id_map covers every ``cus_<id>`` referenced by the
          target item_types.

        Returns:
            dict: {'errors': [...], 'warnings': [...],
                   'missing_property_defs': [...], 'unmapped_property_ids': {tid: [...]}}
        """
        errors = []
        warnings = []

        # Existence of a property definition for each new id (folder + existing
        # DB are treated as known).
        known_ids = folder_property_ids() | set(get_properties_id())
        missing = self.config.missing_property_definitions(known_ids)
        for new_id in missing:
            errors.append(
                'property_id_map の新id {0} に対応する property定義が '
                'properties/ にもDBにも存在しません'.format(new_id))

        # Coverage of the old cus_ids referenced by each target item_type's render.
        unmapped = {}
        for tid in self.item_types:
            item_type = self._get_item_type(tid)
            if item_type is None:
                warnings.append('item_type {0} がDBに存在しません'.format(tid))
                continue
            referenced = self._referenced_property_ids(item_type.render)
            miss = self.config.unmapped_property_ids(referenced)
            # Ids already pointing at the new side (i.e. property_id_map values)
            # are treated as covered.
            new_ids = self.config.new_property_ids()
            miss = [i for i in miss if i not in new_ids]
            if miss:
                unmapped[tid] = miss
                warnings.append(
                    'item_type {0}: property_id_map 未網羅の cus_id {1}'.format(
                        tid, ', '.join(str(i) for i in miss)))

        return {
            'errors': errors,
            'warnings': warnings,
            'missing_property_defs': missing,
            'unmapped_property_ids': unmapped,
        }

    def _referenced_property_ids(self, render):
        """Set of <id> values from render.meta_list[*].input_type = "cus_<id>"."""
        ids = set()
        meta_list = (render or {}).get('meta_list', {})
        for _idx, item_key in _iter_form_item_keys(render):
            meta = meta_list.get(item_key)
            if not meta:
                continue
            m = CUS_RE.match(str(meta.get('input_type', '')))
            if m:
                ids.add(int(m.group(1)))
        return ids

    # --- Phase 1: properties (non-destructive update / add missing) --------

    def phase1_properties(self):
        """Update the v2.0.0 standard properties non-destructively.

        Existing rows are updated and missing ones added; this does not TRUNCATE.
        JDCat-specific properties (ids outside the folder) are never touched.
        If there is nothing to update, "no target" is stated explicitly
        (design spec 6.1).
        """
        exclusion_list = [int(x) for x in property_config.EXCLUSION_LIST]
        target = folder_property_ids() - set(exclusion_list)
        existing = set(get_properties_id())
        to_add = sorted(target - existing)
        to_update = sorted(target & existing)

        result = {
            'phase': 1,
            'target_count': len(target),
            'to_add': to_add,
            'to_update': to_update,
            'no_target': (len(target) == 0),
            'applied': False,
        }

        if result['no_target']:
            self.log.info('[jdcat_migration][Phase1] 更新対象なし')
            return result

        self.log.info('[jdcat_migration][Phase1] 更新対象 {0}件'
                      '（追加 {1} / 更新 {2}）'.format(
                          len(target), len(to_add), len(to_update)))

        if self.dry_run:
            self.log.info('[jdcat_migration][Phase1] dry-run: DB無更新')
            return result

        # Real run: non-destructive (does not TRUNCATE; updates existing rows and
        # adds missing ones). Reuses the existing helper as-is.
        try:
            register_properties_from_folder(exclusion_list)
            db.session.commit()
            result['applied'] = True
            # Confirm the result
            after = set(get_properties_id())
            result['added_confirmed'] = sorted(set(to_add) & after)
            self.log.info('[jdcat_migration][Phase1] 完了')
        except Exception as ex:  # noqa: BLE001
            db.session.rollback()
            result['error'] = str(ex)
            self.log.error('[jdcat_migration][Phase1] 失敗: {0}'.format(ex))
        return result

    # --- Phase 2: itemtype (property ID / item key conversion -> reload) ---

    def phase2_itemtypes(self):
        """Convert and reload the target item_types (12/20).

        Rewrites render / schema / form / mapping for each target item_type.
        """
        result = {'phase': 2, 'item_types': {}}
        for tid in self.item_types:
            result['item_types'][tid] = self._phase2_one(tid)
        return result

    def _phase2_one(self, tid):
        item_type = self._get_item_type(tid)
        if item_type is None:
            return {'exists': False}

        plan = self._phase2_plan(item_type)
        entry = {
            'exists': True,
            'property_id_changes': plan['prop_changes'],   # [(item_key, old, new)]
            'item_key_changes': plan['id_match_key'],       # {old_key: new_key}
            'no_target': (not plan['prop_changes'] and not plan['id_match_key']),
            'applied': False,
        }

        if entry['no_target']:
            self.log.info('[jdcat_migration][Phase2][{0}] 変換対象なし'
                          '（変換済み/冪等スキップ）'.format(tid))
        else:
            self.log.info('[jdcat_migration][Phase2][{0}] ③{1}件 / ①{2}件'.format(
                tid, len(plan['prop_changes']), len(plan['id_match_key'])))

        if self.dry_run:
            self.log.info('[jdcat_migration][Phase2][{0}] dry-run: DB無更新'.format(tid))
            return entry

        # Idempotency: skip apply/reload when there is nothing to convert (no update)
        if entry['no_target']:
            return entry

        # Single transaction per item_type. The item key conversion, property ID
        # conversion, mapping update and reload are committed together in one
        # final commit; on an exception or a reload failure everything is rolled
        # back so the DB stays as it was before (design spec chapter 7).
        try:
            self._phase2_apply(item_type, plan)   # does not commit here
            reload_ret = ItemTypes.reload(tid, get_properties_mapping(), [], 'ALL')
            entry['reload'] = reload_ret
            if reload_ret.get('code') != 0:
                db.session.rollback()
                self.log.error('[jdcat_migration][Phase2][{0}] reload失敗（ロールバック）: {1}'
                               .format(tid, reload_ret.get('msg')))
                return entry
            db.session.commit()
            entry['applied'] = True
            self.log.info('[jdcat_migration][Phase2][{0}] 完了'.format(tid))
        except Exception as ex:  # noqa: BLE001
            db.session.rollback()
            entry['applied'] = False
            entry['error'] = str(ex)
            self.log.error('[jdcat_migration][Phase2][{0}] 失敗（ロールバック）: {1}'.format(tid, ex))
        return entry

    def _phase2_plan(self, item_type):
        """Build the input_type reassignment and item key rename plan, **read-only**."""
        render = item_type.render or {}
        meta_list = render.get('meta_list', {})
        prop_map = self.config.property_id_map          # {old_int: new_int}

        # Property ID conversion (cus_<old> -> cus_<new>)
        prop_changes = []
        for _idx, item_key in _iter_form_item_keys(render):
            meta = meta_list.get(item_key)
            if not meta:
                continue
            cur = str(meta.get('input_type', ''))
            m = CUS_RE.match(cur)
            if not m:
                continue
            old_id = int(m.group(1))
            if old_id in prop_map:
                new_cus = 'cus_{0}'.format(prop_map[old_id])
                if new_cus != cur:
                    prop_changes.append((item_key, cur, new_cus))

        # Item key conversion (item_15xxxx -> item_<type>_<prop_name>_<seq>)
        # The sequence number follows table_row order and is numbered from 1
        # across the mapped keys.
        id_match_key = {}
        key_map = self.config.item_keys_for(item_type.id)   # {old_key: prop_name}
        count = 1
        for item_key in render.get('table_row', []):
            if item_key in key_map and OLD_ITEM_KEY_RE.match(item_key):
                new_key = 'item_{0}_{1}_{2}'.format(
                    item_type.id, key_map[item_key], count)
                id_match_key[item_key] = new_key
                count += 1

        return {'prop_changes': prop_changes, 'id_match_key': id_match_key}

    def _phase2_apply(self, item_type, plan):
        """Apply the plan to item_type and item_type_mapping (everything before reload).

        Note: this does not commit. The caller :meth:`_phase2_one` commits exactly
        once per item_type, reload included, keeping a single transaction so that a
        failure partway through can roll everything back.
        """
        tid = item_type.id

        # Property ID conversion: reassign input_type (edits render directly)
        render = item_type.render
        for item_key, _old, new_cus in plan['prop_changes']:
            render['meta_list'][item_key]['input_type'] = new_cus

        # Item key rename: JSON string replacement over schema/form/render
        # (longest key first to avoid collisions)
        id_match_key = plan['id_match_key']
        if id_match_key or plan['prop_changes']:
            ordered = sorted(id_match_key.items(), key=lambda kv: len(kv[0]), reverse=True)
            schema_s = json.dumps(item_type.schema)
            form_s = json.dumps(item_type.form)
            render_s = json.dumps(render)
            for old_key, new_key in ordered:
                schema_s = schema_s.replace(old_key, new_key)
                form_s = form_s.replace(old_key, new_key)
                render_s = render_s.replace(old_key, new_key)
            item_type.schema = json.loads(schema_s)
            item_type.form = json.loads(form_s)
            item_type.render = json.loads(render_s)
            flag_modified(item_type, 'schema')
            flag_modified(item_type, 'form')
            flag_modified(item_type, 'render')

        # Item key rename in item_type_mapping (so reload can look up static
        # values by the new keys)
        if id_match_key:
            mapping_row = self._latest_mapping_row(tid)
            if mapping_row is not None:
                mapping_s = json.dumps(mapping_row.mapping)
                for old_key, new_key in sorted(
                        id_match_key.items(), key=lambda kv: len(kv[0]), reverse=True):
                    mapping_s = mapping_s.replace(old_key, new_key)
                mapping_row.mapping = json.loads(mapping_s)
                flag_modified(mapping_row, 'mapping')

    def _latest_mapping_row(self, tid):
        """Latest ItemTypeMapping row for item_type_id (the one reload reads)."""
        return (ItemTypeMapping.query
                .filter(ItemTypeMapping.item_type_id == tid)
                .order_by(ItemTypeMapping.created.desc())
                .first())

    # --- Phase 3: verify & cleanup ----------------------------------------

    def phase3_verify(self):
        """Verify zero remaining old keys and zero unknown property references.

        Optionally (opt-in) clean up afterwards (design spec 6.3).
        """
        result = {'phase': 3, 'item_types': {}, 'cleanup': None}
        for tid in self.item_types:
            item_type = self._get_item_type(tid)
            if item_type is None:
                result['item_types'][tid] = {'exists': False}
                continue

            # Number of remaining old item_15xxxx keys (across the whole
            # schema/form/render/mapping)
            blobs = [json.dumps(item_type.schema),
                     json.dumps(item_type.form),
                     json.dumps(item_type.render)]
            mapping_row = self._latest_mapping_row(tid)
            if mapping_row is not None:
                blobs.append(json.dumps(mapping_row.mapping))
            # Detection of remaining old item_15xxxx keys.
            # Note: a naive r'item_\d+' false-positives on (1) "item_<type>", the
            # prefix of the new key item_<type>_<name>, and (2) the "item_15xxx"
            # inside "subitem_15xxx".
            # -> Start only where the preceding character is not a letter (which
            #    excludes subitem_), capture the full token including any trailing
            #    _-suffixed parts, and count only the old form (item_<digits> only).
            old_keys = set()
            for b in blobs:
                for mk in re.findall(r'(?<![A-Za-z])item_\d+(?:_\w+)*', b):
                    if OLD_ITEM_KEY_RE.match(mk):
                        old_keys.add(mk)

            # Unknown property references (cus_<id> not in item_type_property)
            unknown = []
            for cus_id in sorted(self._referenced_property_ids(item_type.render)):
                if ItemTypeProps.get_record(cus_id) is None:
                    unknown.append(cus_id)

            entry = {
                'exists': True,
                'old_item_keys_remaining': sorted(old_keys),
                'old_item_keys_count': len(old_keys),
                'unknown_property_refs': unknown,
                'unknown_property_count': len(unknown),
                'ok': (not old_keys and not unknown),
            }
            result['item_types'][tid] = entry
            level = self.log.info if entry['ok'] else self.log.warning
            level('[jdcat_migration][Phase3][{0}] 旧キー残 {1} / 未知参照 {2}'.format(
                tid, entry['old_item_keys_count'], entry['unknown_property_count']))

        if self.cleanup:
            result['cleanup'] = self._phase3_cleanup()
        return result

    def _phase3_cleanup(self):
        """Logically delete JDCat-specific properties no item_type references (opt-in)."""
        # Collect the cus_ids referenced by every item_type
        referenced = set()
        for it in db.session.query(ItemType).all():
            referenced |= self._referenced_property_ids(it.render)
        # Unreferenced ones among the JDCat-specific properties, i.e. those
        # outside the folder (= non-standard)
        std_ids = folder_property_ids()
        all_ids = set(get_properties_id())
        candidates = sorted((all_ids - std_ids) - referenced)

        cleanup = {'candidates': candidates, 'deleted': [], 'applied': False}
        if not candidates:
            self.log.info('[jdcat_migration][Phase3][cleanup] 論理削除対象なし')
            return cleanup
        if self.dry_run:
            self.log.info('[jdcat_migration][Phase3][cleanup] dry-run: {0}件が対象'.format(
                len(candidates)))
            return cleanup
        try:
            (db.session.query(ItemTypeProperty)
             .filter(ItemTypeProperty.id.in_(candidates))
             .update({ItemTypeProperty.delflg: True}, synchronize_session='fetch'))
            db.session.commit()
            cleanup['deleted'] = candidates
            cleanup['applied'] = True
            self.log.info('[jdcat_migration][Phase3][cleanup] {0}件を論理削除'.format(
                len(candidates)))
        except Exception as ex:  # noqa: BLE001
            db.session.rollback()
            cleanup['error'] = str(ex)
            self.log.error('[jdcat_migration][Phase3][cleanup] 失敗: {0}'.format(ex))
        return cleanup

    # --- Common ------------------------------------------------------------

    def _get_item_type(self, tid):
        return db.session.query(ItemType).filter(ItemType.id == int(tid)).one_or_none()
