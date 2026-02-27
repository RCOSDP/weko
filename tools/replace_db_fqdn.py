import sys
import os
import time
import traceback
from sqlalchemy import create_engine, text

if len(sys.argv) < 3:
    print("Usage: python replace_db_fqdn.py <old_fqdn> <new_fqdn>")
    sys.exit(1)

ofqdn = sys.argv[1]
nfqdn = sys.argv[2]
ofqdn_underscore = ofqdn.replace(".", "_").replace("-", "_")
nfqdn_underscore = nfqdn.replace(".", "_").replace("-", "_")

USERNAME = os.getenv("INVENIO_POSTGRESQL_DBUSER")
PASSWORD = os.getenv("INVENIO_POSTGRESQL_DBPASS")
HOST = os.getenv("INVENIO_POSTGRESQL_HOST")
PORT = 5432
DBNAME = os.getenv("INVENIO_POSTGRESQL_DBNAME")
DATABASE_URL = f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

engine = create_engine(DATABASE_URL)

def update_records(
    select_sql, update_sql, table_name="", column_name="", batch_size=1000
):
    """Executes SQL queries.

    Executes batch updates on a specified table and column using provided SQL queries.

    Args:
        select_sql (str): SQL query to select the target record IDs.
        update_sql (str):
            SQL update statement, using :ids as a parameter for batch IDs.
        table_name (str, optional):
            Name of the table being updated (for logging). Defaults to "".
        column_name (str, optional):
            Name of the column being updated (for logging). Defaults to "".
        batch_size (int, optional):
            Number of records to update per batch. Defaults to 1000.

    Behavior:
        - Fetches IDs using select_ids_sql.
        - Updates records in batches using update_sql_template.
        - Commits the transaction only if all batches succeed; rolls back if any batch fails.
        - Logs progress and errors.
    """
    with engine.connect() as conn:
        trans = conn.begin()
        result = conn.execute(text(select_sql))
        total = 0
        batch_num = 1
        total_start = time.time()
        success = True
        while True:
            rows = result.fetchmany(batch_size)
            if not rows:
                break
            batch_ids = [row[0] for row in rows]
            try:
                conn.execute(text(update_sql), {"ids": tuple(batch_ids)})
            except Exception as e:
                print(f"[ERROR] {table_name}.{column_name}: Batch {batch_num} failed")
                print(f"Error: {e}")
                traceback.print_exc()
                success = False
                break
            elapsed = time.time() - total_start
            total += len(batch_ids)
            if total % 1000 == 0:
                print(f"[INFO] {table_name}.{column_name}: {total} records processed (elapsed time: {elapsed:.2f} seconds)")
            batch_num += 1
        total_elapsed = time.time() - total_start
        if success:
            trans.commit()
            print(f"[INFO] {table_name}.{column_name}: {total} records replaced/updated, elapsed time: {total_elapsed:.2f} seconds")
        else:
            trans.rollback()
            print(f"[ERROR] {table_name}.{column_name}: Rolled back due to error")


# files_location
select_files_location = """
    SELECT id from files_location;
"""
update_files_location = f"""
    UPDATE files_location
    SET uri = regexp_replace(uri, '{ofqdn_underscore}', '{nfqdn_underscore}')
    WHERE id IN :ids;
"""

# files_files.uri
select_files_files_uri = """
    SELECT id FROM files_files;
"""
update_files_files_uri = f"""
    UPDATE files_files
    SET uri = regexp_replace(uri, '{ofqdn_underscore}', '{nfqdn_underscore}')
    WHERE id IN :ids;
"""

# files_files
select_files_files_json = """
    SELECT id FROM files_files WHERE json ? 'url' AND (json->'url') ? 'url' AND json->'url'->>'url' IS NOT NULL;
"""
update_files_files_json = f"""
    UPDATE files_files
    SET json = jsonb_set(
        json,
        '{{url,url}}',
        to_jsonb(
            regexp_replace(json->'url'->>'url', '{ofqdn}', '{nfqdn}')
        )
    )
    WHERE id IN :ids;
"""

# records_metadata
select_records_metadata = """
    SELECT id FROM records_metadata;
"""
update_records_metadata = f"""
    UPDATE records_metadata
    SET json = regexp_replace(json::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE id IN :ids;
"""

# pidstore_pid
select_pidstore_pid = """
    SELECT id FROM pidstore_pid
    WHERE pid_type = 'oai';
"""
update_pidstore_pid = f"""
    UPDATE pidstore_pid
    SET pid_value = regexp_replace(pid_value, '{ofqdn}', '{nfqdn}')
    WHERE id IN :ids;
"""

# feedback_email_setting
select_feedback_email_setting = """
    SELECT id FROM feedback_email_setting;
"""
update_feedback_email_setting = f"""
    UPDATE feedback_email_setting
    SET root_url = regexp_replace(root_url, '{ofqdn}', '{nfqdn}')
    WHERE id IN :ids;
"""

# index
select_index = """
SELECT id FROM index;
"""
update_index = f"""
    UPDATE index
    SET index_url = regexp_replace(index_url, '{ofqdn}', '{nfqdn}')
    WHERE id in :ids;
"""

# changelist_indexes
select_changelist_indexes = """
    SELECT id FROM changelist_indexes;
"""
update_changelist_indexes = f"""
    UPDATE changelist_indexes
    SET url_path = regexp_replace(url_path, '{ofqdn}', '{nfqdn}')
    WHERE id in :ids;
"""

# resourcelist_indexes
select_resourcelist_indexes = """
    SELECT id FROM resourcelist_indexes;
"""
update_resourcelist_indexes = f"""
    UPDATE resourcelist_indexes
    SET url_path = regexp_replace(url_path, '{ofqdn}', '{nfqdn}')
    WHERE id in :ids;
"""

# widget_multi_lang_data
select_widget_multi_lang_data = """
    SELECT id FROM widget_multi_lang_data;
"""
update_widget_multi_lang_data = f"""
    UPDATE widget_multi_lang_data
    SET description_data = regexp_replace(description_data::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE id IN :ids;
"""

# widget_design_page
select_widget_design_page = """
    SELECT repository_id FROM widget_design_page;
"""
update_widget_design_page = f"""
    UPDATE widget_design_page
    SET settings = regexp_replace(settings::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE repository_id IN :ids;
"""

# widget_design_setting
select_widget_design_setting = """
    SELECT repository_id FROM widget_design_setting;
"""
update_widget_design_setting = f"""
    UPDATE widget_design_setting
    SET settings = regexp_replace(settings::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE repository_id in :ids;;
"""

# workflow_activity
select_workflow_activity = """
    SELECT id FROM workflow_activity WHERE temp_data IS NOT NULL;
"""
update_workflow_activity = f"""
    UPDATE workflow_activity
    SET temp_data = regexp_replace(temp_data::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE id in :ids;
"""

# item_metadata
select_item_metadata = """
    SELECT id from item_metadata;
"""
update_item_metadata = f"""
    UPDATE item_metadata
    SET json = regexp_replace(json::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE id IN :ids;
"""

# item_metadata_version
select_item_metadata_version = """
    SELECT id from item_metadata_version;
"""
update_item_metadata_version = f"""
    UPDATE item_metadata_version
    SET json = regexp_replace(json::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE id IN :ids;
"""

# records_metadata_version
select_records_metadata_version = """
    SELECT id from records_metadata_version;
"""
update_records_metadata_version = f"""
    UPDATE records_metadata_version
    SET json = regexp_replace(json::text, '{ofqdn}', '{nfqdn}', 'g')::jsonb
    WHERE id IN :ids;
"""


if __name__ == "__main__":
    update_records(select_files_location, update_files_location, "files_location", "uri")
    update_records(select_files_files_uri, update_files_files_uri, "files_files", "uri")
    update_records(select_files_files_json, update_files_files_json, "files_files", "json")
    update_records(select_pidstore_pid, update_pidstore_pid, "pidstore_pid", "pid_value")
    update_records(select_feedback_email_setting, update_feedback_email_setting, "feedback_email_setting", "root_url")
    update_records(select_index, update_index, "index", "index_url")
    update_records(select_changelist_indexes, update_changelist_indexes, "changelist_indexes", "url_path")
    update_records(select_resourcelist_indexes, update_resourcelist_indexes, "resourcelist_indexes", "url_path")
    update_records(select_widget_multi_lang_data, update_widget_multi_lang_data, "widget_multi_lang_data", "description_data")
    update_records(select_widget_design_setting, update_widget_design_setting, "widget_design_setting", "description_data")
    update_records(select_widget_design_page, update_widget_design_page, "widget_design_page", "description_page")
    update_records(select_workflow_activity, update_workflow_activity, "workflow_activity", "temp_data")
    update_records(select_records_metadata, update_records_metadata, "records_metadata", "json")
    update_records(select_item_metadata, update_item_metadata, "item_metadata", "json")
    update_records(select_records_metadata_version, update_records_metadata_version, "records_metadata_version", "json")
    update_records(select_item_metadata_version, update_item_metadata_version, "item_metadata_version", "json")
