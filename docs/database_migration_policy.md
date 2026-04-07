# Database Migration Policy

This repository currently has two kinds of DB change artifacts:

- Module Alembic migrations under `modules/*/*/alembic/`
- Legacy raw SQL files under `postgresql/ddl/` and `postgresql/update/`

## Policy

- New schema changes must be implemented with Alembic.
- New files under `postgresql/ddl/` and `postgresql/update/` are prohibited.
- Existing files under `postgresql/ddl/` and `postgresql/update/` are treated as legacy assets that should be migrated or retired over time.
- Raw SQL should be limited to exceptional cases such as one-time operational repair work, and the reason should be documented.

## Practical rules

1. If you add or alter a table for application behavior, create or update the owning module's Alembic migration.
2. If a legacy SQL file describes a change that should become part of the normal upgrade path, plan to port it into Alembic.
3. If raw SQL must remain for operational reasons, document why it cannot be expressed as a normal Alembic migration.

## Current goal

- Stop new legacy SQL from being added.
- Gradually classify existing files as migrated, still-needed, or removable.
- Move normal version-upgrade schema changes into Alembic by default.
