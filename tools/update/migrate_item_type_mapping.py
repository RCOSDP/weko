# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 National Institute of Informatics.
# WEKO is free software; you can redistribute it and/or modify it under the
# terms of the MIT License; see LICENSE file for more details.

"""Migrate item_type_mapping table to versioning.

This script is used to migrate the `item_type_mapping` table and
`item_type_mapping_version`.

>>> invenio shell tools/update/migrate_item_type_mapping.py

"""

import sys
import datetime
import traceback
from contextlib import contextmanager

from click import progressbar
from flask import current_app, Flask
from flask_sqlalchemy.model import DefaultMeta as Meta
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import func, text
from sqlalchemy.engine.result import ResultProxy

from invenio_db import InvenioDB, db
from weko_records.models import (
    timestamp_before_update, Timestamp, ItemTypeMapping
)


def info(msg):
    print(f"[INFO]  {msg}")

def warn(msg):
    print(f"\033[43m[WARN]\033[0m {msg}")

def error(msg):
    print(f"\033[41m[ERROR]\033[0m {msg}")


def get_versioned_model(app: Flask, master):
    """Get the versioned table for the given master table."""
    invenio_db: InvenioDB = app.extensions.get("invenio-db")
    manager = invenio_db.versioning_manager
    if not manager.transaction_cls:
        return None

    versioned_table: Meta = manager.version_class_map.get(master, None)
    return versioned_table


def has_duplicate_item_type_ids():
    """Check if there are duplicate item_type_id values in ItemTypeMapping."""
    duplicate_count = (
        db.session.query(func.count(ItemTypeMapping.item_type_id))
        .group_by(ItemTypeMapping.item_type_id)
        .having(func.count(ItemTypeMapping.item_type_id) > 1)
        .count()
    )
    info(f"{duplicate_count} Item Type Mapping needs to be migrated.")
    return bool(duplicate_count > 0)


def create_temp_tables(*models: Meta):
    """Create temporary tables for migration."""
    for model in models:
        if model is None:
            continue
        info(f"Creating temporary table for {model.__tablename__}...")
        db.session.execute(text(f"""
            CREATE TABLE {model.__tablename__}_tmp AS
            SELECT * FROM {model.__tablename__};
        """))

    db.session.commit()


def recover_from_temp_tables(*models: Meta):
    """Recover data from temporary tables."""
    for model in models:
        if model is None:
            continue
        db.session.execute(text(f"""
            TRUNCATE TABLE {model.__tablename__};
            INSERT INTO {model.__tablename__}
            SELECT * FROM {model.__tablename__}_tmp;
        """))
    db.session.commit()
    info("Recovered data from temporary tables.")


def drop_temp_tables(*models: Meta):
    """Drop temporary tables."""
    for model in models:
        if model is None:
            continue
        db.session.execute(text(f"""
            DROP TABLE IF EXISTS {model.__tablename__}_tmp;
        """))
    db.session.commit()
    info("Dropped temporary tables.")


@contextmanager
def atomic_migration_stream(*models: Meta):
    """Context manager to create temporary tables for migration."""
    start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    info(f"Migration started at {start}.")
    from sqlalchemy.orm import sessionmaker
    create_temp_tables(*models)
    Session = sessionmaker(bind=db.engine)
    temp_session = Session()
    
    stream: ResultProxy = temp_session.execute(
        text("SELECT * FROM {}_tmp ORDER BY id ASC".format(
            models[0].__tablename__
        )).execution_options(stream_results=True)
    )

    try:
        yield stream
    except BaseException as e:
        stream.close()
        temp_session.close() 
        faild = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        error(f"Migration failed at {faild}.")
        traceback.print_exc()
        db.session.rollback()
        recover_from_temp_tables(*models)

        drop_temp_tables(*models)

    else:
        stream.close()
        temp_session.close() 
        drop_temp_tables(*models)

        end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        info(f"Migration completed at {end}.")


@contextmanager
def without_before_update_timestamp():
    """Context manager to temporarily disable the before_update timestamp."""
    db.event.remove(Timestamp, "before_update", timestamp_before_update)
    try:
        yield
    finally:
        db.event.listen(
            Timestamp, "before_update", timestamp_before_update, propagate=True
        )


def create_or_update_mapping(created, updated, item_type_id, mapping):
    """Create or update ItemTypeMapping."""
    obj = ItemTypeMapping.query.filter_by(item_type_id=item_type_id).first()
    if obj:
        obj.updated = updated
        obj.mapping = mapping
        print(f"  Updated: item_type_id={item_type_id}, version_id={obj.version_id}")
    else:
        obj = ItemTypeMapping(
            item_type_id=item_type_id,
            mapping=mapping,
            created=created,
            updated=updated,
        )
        db.session.add(obj)
        print(f"  Created: item_type_id={item_type_id}")
    db.session.commit()


def main():
    """Main function to migrate item_type_mapping."""

    ItemTypeMappingVersion = get_versioned_model(current_app, ItemTypeMapping)
    if not ItemTypeMappingVersion:
        warn("Metadata of versioned table for ItemTypeMapping not found.")

    table_names = inspect(db.engine).get_table_names()
    if (
        ItemTypeMapping.__tablename__ + "_tmp" in table_names
        or (
            ItemTypeMappingVersion is not None
            and ItemTypeMappingVersion.__tablename__ + "_tmp" in table_names
        )
    ):
        error("Temporary table for migration already exists.")
        info("Run the script with 'recovery' argument to recover.")
        return

    if not has_duplicate_item_type_ids():
        info("Not need to migrate item_type_mapping.")
        return

    num_record = ItemTypeMapping.query.count()

    with without_before_update_timestamp(), \
        atomic_migration_stream(ItemTypeMapping, ItemTypeMappingVersion) as tmp_record_stream, \
        progressbar(tmp_record_stream, label="Migrating", length=num_record, show_eta=False) as bar:

        db.session.execute(text(f"""
            TRUNCATE TABLE {ItemTypeMapping.__tablename__};
        """))
        if ItemTypeMappingVersion is not None:
            db.session.execute(text(f"""
                TRUNCATE TABLE {ItemTypeMappingVersion.__tablename__};
            """))
        db.session.commit()

        for row in bar:
            create_or_update_mapping(
                created=row.created,
                updated=row.updated,
                item_type_id=row.item_type_id,
                mapping=row.mapping,
            )


def recovery():
    """Recover from temporary tables."""
    ItemTypeMappingVersion = get_versioned_model(current_app, ItemTypeMapping)
    table_names = inspect(db.engine).get_table_names()
    if (
        ItemTypeMapping.__tablename__ + "_tmp" not in table_names
        or (
            ItemTypeMappingVersion is not None
            and ItemTypeMappingVersion.__tablename__ + "_tmp" not in table_names
        )
    ):
        warn("Temporary table for recovery not found.")
        return
    info("Temporary table for recovery found.")

    recover_from_temp_tables(ItemTypeMapping, ItemTypeMappingVersion)
    drop_temp_tables(ItemTypeMapping, ItemTypeMappingVersion)


if __name__ == "__main__":
    if "recovery" in sys.argv:
        recovery()
        sys.exit(0)

    main()
