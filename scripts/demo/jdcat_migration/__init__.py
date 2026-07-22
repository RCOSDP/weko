# -*- coding: utf-8 -*-
"""JDCat master data migration program package.

A configuration-driven, non-destructive and idempotent set of programs that
migrates master data (item_type / item_type_property / item_type_mapping)
from the develop_v1.0.8 line (+ feature/jdcat_202601) to develop_v2.0.0.

Layout (design spec 5.1):
    config.py         Load and validate the config JSON (mapping_config.json)
    convert_xlsx.py   Tool that generates mapping_config.json from the answer xlsx
    gen_properties.py Helper that generates properties/*.py drafts (development-time)
    engine.py         The conversion engine itself (Phase1-3)
    migrate.py        CLI entry point (run from invenio shell)
    report.py         dry-run / progress / post-run verification report

See ``JDCat_Master_Data_Migration_Design_Spec.md`` in this directory for details.
"""
