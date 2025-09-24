import click
from flask.cli import with_appcontext
from datetime import datetime
import re
from .api import AuthorIndexer
def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()
        
@click.group()
def authors():
    """Authors commands."""

def normalize_date(date):
    """
    start_dateに与えられた値を、以下のパターンで補完する処理
      - yyyy-MM-ddTHH:mm:ss の場合：yyyy-MM-ddTHH:mm:ss
      - yyyy-MM-dd の場合：yyyy-MM-ddT00:00:00
      - yyyy-MM の場合：yyyy-MM-01T00:00:00
      - yyyy の場合：yyyy-01-01T00:00:00
    """
    if not date:
        return None
    # yyyy-MM-ddTHH:mm:ss
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", date):
        return date
    # yyyy-MM-dd
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return f"{date}T00:00:00"
    # yyyy-MM
    elif re.fullmatch(r"\d{4}-\d{2}", date):
        return f"{date}-01T00:00:00"
    # yyyy
    elif re.fullmatch(r"\d{4}", date):
        return f"{date}-01-01T00:00:00"
    else:
        raise ValueError("start_dateの形式が不正です")

def validate_date(start_date, end_date):
    if start_date:
        try:
            start_date = normalize_date(start_date)
        except ValueError as e:
            raise click.UsageError(str(e))
    if end_date:
        try:
            end_date = normalize_date(end_date)
        except ValueError as e:
            raise click.UsageError(str(e))
    
    date_format = "%Y-%m-%dT%H:%M:%S"
    dt_start = datetime.strptime(start_date, date_format) if start_date else None
    dt_end = datetime.strptime(end_date, date_format) if end_date else None
    if dt_start and dt_end and dt_start > dt_end:
        raise click.UsageError("start_dateはend_date以前の日付を指定してください")
    return start_date, end_date
    
import os
@authors.command('reindex')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to reindex all records?')
@click.option('-f','--file', type=str, default=None,
              help='Path to a file containing author IDs to reindex.')
@click.option('--id', type=str,help='Specific author ID to reindex.')
@click.option('--start-date', type=str,help='Start date for reindexing (YYYY-MM-DD).')
@click.option('--end-date', type=str,help='End date for reindexing (YYYY-MM-DD).')
@click.option(
    '--with-deleted', type=bool,default=True,
    help='Include deleted records in the indexing process.')
@click.option(
    '--raise-on-error', type=bool,default=True,
    help='raise BulkIndexError containing errors (as .errors) from the execution of the last chunk when some occur. By default we raise.')
@click.option(
    '--raise-on-exception', type=bool,default=True,
    help='if False then don’t propagate exceptions from call to bulk and just report the items that failed as failed.')
@click.option('--chunk-size',type=int,default=500,help='number of docs in one chunk sent to es (default: 500)')
@click.option('--max-chunk-bytes',type=int,default=104857600,help='the maximum size of the request in bytes (default: 100MB)')
@click.option('--max-retries',type=int,default=0,help='maximum number of times a document will be retired when 429 is received, set to 0 (default) for no retries on 429')
@click.option('--initial_backoff',type=int,default=2,help='number of secconds we should wait before the first retry.')
@click.option('--max-backoff',type=int,default=600,help='maximim number of seconds a retry will wait')
def reindex(file, id, start_date, end_date, with_deleted=True,
            raise_on_error=True,raise_on_exception=True,chunk_size=500,
            max_chunk_bytes=104857600,max_retries=0,initial_backoff=2,
            max_backoff=600):
    """Reindex authors."""
    if file and id:
        raise click.UsageError('Cannot use both --file and --id options together.')
    uuids = []
    if file:
        # 存在確認
        if not os.path.exists(file):
            raise click.UsageError(f'File {file} does not exist.')
        # ファイル読み込み
        try:
            with open(file, 'r') as f:
                uuids = [line.strip() for line in f if line.strip()]
        except Exception as e:
            raise click.UsageError(f'Error reading file {file}: {e}')
    elif id:
        uuids = [id]
    
    start_date, end_date = validate_date(start_date, end_date)

    es_bulk_kwargs = {
        "raise_on_error": raise_on_error,
        "raise_on_exception": raise_on_exception,
        "chunk_size": chunk_size,
        "max_chunk_bytes": max_chunk_bytes,
        "max_retries": max_retries,
        "initial_backoff": initial_backoff,
        "max_backoff": max_backoff,
        "stats_onlye": False
    }
    click.secho('Reindexing authors...', fg='green')
    AuthorIndexer().bulk_process_authors(es_bulk_kwargs, uuids, start_date, end_date, with_deleted)
    click.secho('Authors reindexed successfully.', fg='green')

