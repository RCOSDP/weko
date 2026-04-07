# Database Guide

This page explains how to inspect WEKO's database structure without starting
from the full schema dump every time.

## Where to look first

1. Open `docs/database_inventory.md` to find the relevant module, migration, or SQL file.
2. If the table belongs to a Python module, inspect that module's `models.py` and `alembic/` directory.
3. If the change is implemented by raw SQL, inspect `postgresql/ddl` and `postgresql/update`.
4. If you need the full current schema, open `docs/source/developer/database.rst`.

## Repository-level DB sources

The project uses more than one source to describe DB structure:

- SQLAlchemy models under `modules/*/*/models.py`
- Alembic migrations under `modules/*/*/alembic/`
- Raw SQL DDL and upgrade scripts under `postgresql/ddl/` and `postgresql/update/`
- A large schema dump in `docs/source/developer/database.rst`

## Migration policy

- New schema changes must be implemented with Alembic.
- `postgresql/ddl/` and `postgresql/update/` are legacy directories and should not receive new version-upgrade SQL files.
- See `docs/database_migration_policy.md` for the repository policy.
- See `docs/legacy_sql_inventory.md` for the current legacy SQL review list.

## Recommended lookup order

When investigating a table or column:

1. Search the table name in `docs/database_inventory.md`.
2. Read the owning module's model definition to understand ORM usage.
3. Read the matching Alembic migration to understand how the table evolved.
4. Read raw SQL files if the table is created or modified outside Alembic.
5. Confirm column types, keys, and constraints in `docs/source/developer/database.rst`.

## Useful local commands

Run these commands from the repository root:

```console
$ python3 scripts/generate_db_reference.py
$ rg -n "__tablename__\\s*=\\s*['\\\"]TABLE_NAME['\\\"]" modules
$ rg -n "CREATE TABLE( IF NOT EXISTS)? .*TABLE_NAME" postgresql
$ rg -n "op\\.create_table\\(|op\\.add_column\\(" modules/*/*/alembic
```

## Notes

- `docs/database_inventory.md` is generated. Re-run `python3 scripts/generate_db_reference.py` after DB-related changes.
- `docs/source/developer/database.rst` is useful for exact schema confirmation, but it is too large to use as the first entry point.
- New files under `postgresql/ddl/` and `postgresql/update/` are blocked by CI so schema changes move toward Alembic.
