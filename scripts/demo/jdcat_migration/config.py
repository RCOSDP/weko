# -*- coding: utf-8 -*-
"""Load / schema-validate / cross-check mapping_config.json (design spec 5.1 / 5.3).

This module loads ``mapping_config.json`` (design spec 3.2), the actual input of
the migration program, and validates its structure, types and consistency.

Policy:
    - **DB-independent** (does not import invenio / weko_records).
      Runs under plain ``python`` as well as ``invenio shell``, so it is easy
      to unit test.
    - Checks that need the DB or the property definitions (``properties/*.py``)
      -- coverage of the referenced ``cus_<id>``, existence of a property
      definition for each new id -- are exposed as hooks the engine calls with
      real data
      (:meth:`MigrationConfig.unmapped_property_ids` /
      :meth:`MigrationConfig.missing_property_definitions`).

mapping_config.json schema (design spec 3.2)::

    {
      "meta": { "source": "...xlsx", "target_item_types": [12, 20] },
      "property_id_map": { "8": 1014, "17": 1010, ... },   # old propId -> new propId
      "item_key_map": {                                    # old item key -> prop_name
        "12": { "item_1551264308487": "title", ... },
        "20": { "item_1551264308487": "title", ... }
      }
    }

``property_id_map`` drives the property ID conversion
(render.meta_list[*].input_type: cus_<old id> -> cus_<new id>).
``item_key_map`` drives the item key conversion, per item_type
(top-level item keys: item_15xxxx -> item_<item_type_id>_<prop_name>_<seq>).
"""

from __future__ import unicode_literals

import io
import json
import re

try:
    from dataclasses import dataclass, field
    _HAS_DATACLASS = True
except ImportError:  # pragma: no cover - Python 2 fallback (production is 3.x)
    _HAS_DATACLASS = False


# --- Defaults and patterns -------------------------------------------------

#: Target item_type (design spec 2.3). Default when meta.target_item_types is
#: omitted.
DEFAULT_TARGET_ITEM_TYPES = (12, 20)

#: Old top-level item key (e.g. ``item_1551264308487``). ``item_`` + digits only.
OLD_ITEM_KEY_RE = re.compile(r'^item_\d+$')

#: New top-level item key (e.g. ``item_12_title_0``). ``item_<typeid>_<name>...``.
NEW_ITEM_KEY_RE = re.compile(r'^item_\d+_\S+')

#: prop_name (e.g. ``title`` / ``unit_of_analysis``). Identifier-like.
PROP_NAME_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')


class ConfigError(Exception):
    """Fatal error in the config JSON (unreadable, or bad structure/types).

    When this is raised, the migration is aborted before it starts
    (design spec 6.0).
    """


class ValidationResult(object):
    """Validation result (fatal errors and warnings kept separately).

    - ``errors``   : fatal problems that must abort the migration.
    - ``warnings`` : problems that still allow the migration but deserve a look
                     (unmapped identifiers, no target, etc.).
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    @property
    def ok(self):
        """True when there are no fatal errors."""
        return not self.errors

    def error(self, msg):
        self.errors.append(msg)
        return self

    def warn(self, msg):
        self.warnings.append(msg)
        return self

    def extend(self, other):
        """Merge in another :class:`ValidationResult`."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def raise_if_errors(self):
        """Raise :class:`ConfigError` if there are fatal errors."""
        if self.errors:
            raise ConfigError(
                '設定JSONの検証に失敗しました:\n  - '
                + '\n  - '.join(self.errors)
            )
        return self

    def summary(self):
        """Return a human-readable summary string (for reports/logs)."""
        lines = []
        if self.errors:
            lines.append('[ERROR] {0}件'.format(len(self.errors)))
            lines.extend('  - ' + m for m in self.errors)
        if self.warnings:
            lines.append('[WARN] {0}件'.format(len(self.warnings)))
            lines.extend('  - ' + m for m in self.warnings)
        if not lines:
            lines.append('検証OK（エラー・警告なし）')
        return '\n'.join(lines)

    def __repr__(self):
        return 'ValidationResult(errors={0}, warnings={1})'.format(
            len(self.errors), len(self.warnings))


class MigrationConfig(object):
    """Hold a validated mapping_config.

    Attributes:
        source              : meta.source (name of the source xlsx; optional).
        target_item_types   : list[int]. Target item_type.
        property_id_map     : dict[int, int]. Old propId -> new propId
                              (property ID conversion).
        item_key_map        : dict[int, dict[str, str]].
                              item_type_id -> {old item key: prop_name}
                              (item key conversion).
        raw                 : the source dict as loaded (unprocessed).
        path                : path it was loaded from (None when built from a dict).
        validation          : :class:`ValidationResult` (set by load/validate).
    """

    def __init__(self, source, target_item_types, property_id_map,
                 item_key_map, raw=None, path=None):
        self.source = source
        self.target_item_types = list(target_item_types)
        self.property_id_map = dict(property_id_map)
        self.item_key_map = dict(item_key_map)
        self.raw = raw if raw is not None else {}
        self.path = path
        self.validation = ValidationResult()

    # --- Construction ------------------------------------------------------

    @classmethod
    def load(cls, path, validate=True):
        """Load from a file path.

        A JSON read failure or bad structure/types raises :class:`ConfigError`.
        With ``validate=True`` the consistency checks are run too and any fatal
        error is raised (warnings remain in ``config.validation.warnings``).
        """
        try:
            with io.open(path, 'r', encoding='utf-8') as fp:
                raw = json.load(fp)
        except (IOError, OSError) as exc:
            raise ConfigError(
                '設定JSONを開けません: {0} ({1})'.format(path, exc))
        except ValueError as exc:
            raise ConfigError(
                '設定JSONの構文が不正です: {0} ({1})'.format(path, exc))

        config = cls.from_dict(raw, path=path)
        if validate:
            config.validate().raise_if_errors()
        return config

    @classmethod
    def from_dict(cls, raw, path=None):
        """Build from a dict (includes parse-time type validation).

        Raises :class:`ConfigError` when the structure/types are broken (fatal).
        Returns a :class:`MigrationConfig` normalized as far as it can be parsed.
        The consistency checks (warning level) are run separately by
        :meth:`validate`.
        """
        if not isinstance(raw, dict):
            raise ConfigError(
                '設定JSONの最上位はオブジェクトである必要があります'
                '（実際: {0}）'.format(type(raw).__name__))

        meta = raw.get('meta', {})
        if not isinstance(meta, dict):
            raise ConfigError('"meta" はオブジェクトである必要があります')

        source = meta.get('source')
        if source is not None and not _is_text(source):
            raise ConfigError('"meta.source" は文字列である必要があります')

        target_item_types = _parse_target_item_types(meta.get('target_item_types'))
        property_id_map = _parse_property_id_map(raw.get('property_id_map'))
        item_key_map = _parse_item_key_map(raw.get('item_key_map'))

        # If target_item_types is omitted, use the item_key_map keys, else the default.
        if not target_item_types:
            if item_key_map:
                target_item_types = sorted(item_key_map.keys())
            else:
                target_item_types = list(DEFAULT_TARGET_ITEM_TYPES)

        return cls(source, target_item_types, property_id_map,
                   item_key_map, raw=raw, path=path)

    # --- Validation (consistency checks; DB-independent scope) --------------

    def validate(self):
        """Run the consistency checks; store in ``self.validation`` and return.

        Only DB-independent validation happens here (the structural part of
        design spec 5.3). The coverage checks that need the DB are done
        separately by the engine via :meth:`unmapped_property_ids` /
        :meth:`missing_property_definitions`.
        """
        r = ValidationResult()

        # -- property_id_map (property ID conversion) --
        if not self.property_id_map:
            r.warn('property_id_map が空です（③プロパティID変換の対象なし）')
        # Warn on duplicate new ids (conversion targets). Several old ids
        # collapsing onto one new id may be an intended merge, so warn, not error.
        seen = {}
        for old_id, new_id in self.property_id_map.items():
            seen.setdefault(new_id, []).append(old_id)
        for new_id, olds in seen.items():
            if len(olds) > 1:
                r.warn('property_id_map: 新id {0} に複数の旧idが対応'
                       '（{1}）'.format(new_id, ', '.join(str(o) for o in sorted(olds))))
        # old id == new id needs no conversion (harmless, but warn to flag it).
        for old_id, new_id in self.property_id_map.items():
            if old_id == new_id:
                r.warn('property_id_map: 旧id と新id が同一（{0}）'
                       '＝変換不要のエントリ'.format(old_id))

        # -- item_key_map (item key conversion) --
        if not self.item_key_map:
            r.warn('item_key_map が空です（①itemキー変換の対象なし）')

        # -- consistency between target_item_types and item_key_map --
        tset = set(self.target_item_types)
        kset = set(self.item_key_map.keys())
        for tid in sorted(kset - tset):
            r.warn('item_key_map に target_item_types 外の item_type '
                   '{0} が含まれます'.format(tid))
        for tid in sorted(tset - kset):
            r.warn('target_item_types の item_type {0} に対応する '
                   'item_key_map エントリがありません'.format(tid))

        # -- key format and prop_name of each item_key_map entry --
        for tid, mapping in self.item_key_map.items():
            for item_key, prop_name in mapping.items():
                if NEW_ITEM_KEY_RE.match(item_key):
                    # Already in the new format = converted. An idempotent-skip
                    # target, but warn to flag it.
                    r.warn('item_key_map[{0}]: キー "{1}" は既に新形式です'
                           '（変換済み/冪等スキップ対象）'.format(tid, item_key))
                elif not OLD_ITEM_KEY_RE.match(item_key):
                    r.error('item_key_map[{0}]: キー "{1}" が旧itemキー形式'
                            '（item_<数字>）ではありません'.format(tid, item_key))
                if not PROP_NAME_RE.match(prop_name):
                    r.warn('item_key_map[{0}]: prop_name "{1}" が識別子形式'
                           'ではありません（キー {2}）'.format(tid, prop_name, item_key))

        self.validation = r
        return r

    # --- DB hooks (the engine calls these with real data) -------------------

    def unmapped_property_ids(self, referenced_old_ids):
        """Return referenced old propIds missing from property_id_map (design spec 5.3).

        Args:
            referenced_old_ids: the set of ``<id>`` from the ``cus_<id>`` values
                referenced by render.meta_list of item_type 12/20
                (old item_type_property.id).

        Returns:
            list[int]: old propIds not covered by property_id_map (ascending).
                Empty means full coverage.
        """
        mapped = set(self.property_id_map.keys())
        return sorted(set(int(i) for i in referenced_old_ids) - mapped)

    def missing_property_definitions(self, known_property_ids):
        """Return new ids in property_id_map that have no definition (design spec 5.3).

        Args:
            known_property_ids: the set of property_id values registerable from
                ``properties/*.py`` (the engine obtains these from e.g.
                ``register_properties.get_properties_id()``).

        Returns:
            list[int]: new ids with no matching property definition (ascending).
        """
        known = set(int(i) for i in known_property_ids)
        return sorted(set(self.property_id_map.values()) - known)

    # --- Convenience accessors ---------------------------------------------

    def old_property_ids(self):
        """Set of source (old) propIds."""
        return set(self.property_id_map.keys())

    def new_property_ids(self):
        """Set of target (new) propIds."""
        return set(self.property_id_map.values())

    def item_keys_for(self, item_type_id):
        """Return ``{old item key: prop_name}`` for the item_type (empty dict if none)."""
        return dict(self.item_key_map.get(int(item_type_id), {}))

    def __repr__(self):
        return ('MigrationConfig(source={0!r}, target_item_types={1}, '
                'property_id_map={2}件, item_key_map={3})'.format(
                    self.source, self.target_item_types,
                    len(self.property_id_map),
                    {k: len(v) for k, v in self.item_key_map.items()}))


# --- parse helpers (type validation; fatal issues raise ConfigError) -------

def _is_text(value):
    """Whether the value is a text type (Python 2/3 compatible)."""
    try:
        string_types = (str, unicode)  # noqa: F821  (Python2)
    except NameError:
        string_types = (str,)
    return isinstance(value, string_types)


def _to_int(value, ctx):
    """Coerce an int (or int string) to int; reject bool; ConfigError on failure."""
    if isinstance(value, bool):
        raise ConfigError('{0}: 真偽値は数値として不正です（{1!r}）'.format(ctx, value))
    if isinstance(value, int):
        return value
    if _is_text(value):
        s = value.strip()
        if re.match(r'^-?\d+$', s):
            return int(s)
    raise ConfigError('{0}: 整数として解釈できません（{1!r}）'.format(ctx, value))


def _parse_target_item_types(value):
    """Convert meta.target_item_types to list[int]. Omitted -> []."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError('"meta.target_item_types" は配列である必要があります')
    result = []
    for i, v in enumerate(value):
        result.append(_to_int(v, 'meta.target_item_types[{0}]'.format(i)))
    return result


def _parse_property_id_map(value):
    """Normalize property_id_map to dict[int, int].

    Keys (old propId) are strings in JSON; values (new propId) are integers.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError('"property_id_map" はオブジェクトである必要があります')
    result = {}
    for k, v in value.items():
        old_id = _to_int(k, 'property_id_map のキー "{0}"'.format(k))
        new_id = _to_int(v, 'property_id_map["{0}"] の値'.format(k))
        if old_id in result:
            raise ConfigError(
                'property_id_map: 旧id {0} が重複しています'.format(old_id))
        result[old_id] = new_id
    return result


def _parse_item_key_map(value):
    """Normalize item_key_map to dict[int, dict[str, str]]."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError('"item_key_map" はオブジェクトである必要があります')
    result = {}
    for type_key, mapping in value.items():
        type_id = _to_int(type_key, 'item_key_map のキー "{0}"'.format(type_key))
        if not isinstance(mapping, dict):
            raise ConfigError(
                'item_key_map["{0}"] はオブジェクトである必要があります'.format(type_key))
        inner = {}
        for item_key, prop_name in mapping.items():
            if not _is_text(item_key) or not item_key:
                raise ConfigError(
                    'item_key_map["{0}"]: itemキーは非空文字列である必要が'
                    'あります（{1!r}）'.format(type_key, item_key))
            if not _is_text(prop_name) or not prop_name:
                raise ConfigError(
                    'item_key_map["{0}"]["{1}"]: prop_name は非空文字列である'
                    '必要があります（{2!r}）'.format(type_key, item_key, prop_name))
            inner[item_key] = prop_name
        result[type_id] = inner
    return result


# dataclass could back a lightweight validation result, but we settled on plain
# classes here. Only the dataclass probe is kept, as an extension point for when
# config grows later.
_ = _HAS_DATACLASS


def _main(argv):
    """Simple dev CLI: ``python config.py <mapping_config.json>``.

    Validates only the structure of the config JSON, with no need for invenio,
    and prints the result to stdout. The DB-dependent coverage checks are not
    run (use migrate.py --dry-run for those).
    """
    if len(argv) < 2:
        print('usage: python config.py <mapping_config.json>')
        return 2
    path = argv[1]
    try:
        config = MigrationConfig.load(path, validate=False)
    except ConfigError as exc:
        print('ConfigError: {0}'.format(exc))
        return 1
    result = config.validate()
    print(repr(config))
    print(result.summary())
    return 0 if result.ok else 1


if __name__ == '__main__':
    import sys
    sys.exit(_main(sys.argv))
