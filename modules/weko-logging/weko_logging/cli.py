
import click
from datetime import datetime
from flask.cli import with_appcontext
from invenio_db import db

@click.group()
def logging():
    """Logging CLI group."""
    pass

@logging.group()
def partition():
    """Partition management commands."""
    pass

@partition.command('create')
@click.argument('year', nargs=1,type=int)
@click.argument('month', default=0,type=int)
@with_appcontext
def _partition_create(year, month):
    """Create partition table for user activity logs.

    YEAR: Year of the partition table.
    MONTH: Month of the partition table. If 0, create for all months in the year.
    """
    from weko_logging.models import make_user_activity_logs_partition_table,\
        get_user_activity_logs_partition_tables
        
    (sm, em) = (1, 12) if month==0 else (month, month)

    try:
        d = datetime(year, sm, 1)
    except Exception as e:
        click.secho(e, fg='red')
        return

    try:
        tables = get_user_activity_logs_partition_tables()

        for m in range(sm, em+1):
            tablename = make_user_activity_logs_partition_table(year, m)
            if tablename in tables:
                click.secho('Table {} is already exist.'.format(tablename), fg='yellow')
            else:
                click.secho('Creating partitioning table {}.'.format(tablename), fg='green')
                db.metadata.tables[tablename].create(bind=db.engine, checkfirst=True)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        click.secho(str(e), fg='red')