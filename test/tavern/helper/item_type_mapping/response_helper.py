import random
from contextlib import closing

from box import Box
from helper.common.connect_helper import connect_db

def delete_itemtypes(_):
    """Delete all item types and their related mappings from the database.

    Args:
        _(Response): Placeholder parameter for compatibility with the caller.
    """
    delete_query = [
        "TRUNCATE TABLE item_type_name CASCADE;",
        "TRUNCATE TABLE item_type_mapping;",
        "TRUNCATE TABLE item_type_mapping_version;",
        "TRUNCATE TABLE item_type_version;"
    ]

    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            for query in delete_query:
                cursor.execute(query)
            conn.commit()


def delete_xsd(_):
    """Set the xsd field to NULL for a random record in the oaiserver_schema table.

    Args:
        _(Response): Placeholder parameter for compatibility with the caller.

    Returns:
        Box: A Box object containing the schema_name of the updated record.

    Raises:
        Exception: If no records are found in the oaiserver_schema table.
    """
    # Set the xsd field to NULL for a random record in the oaiserver_schema table
    select_query = "SELECT id, schema_name FROM oaiserver_schema;"
    update_query = "UPDATE oaiserver_schema SET xsd = '{}' WHERE id = %s;"

    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(select_query)
            records = cursor.fetchall()
            if records:
                random_record = random.choice(records)
                cursor.execute(update_query, (random_record[0],))
                conn.commit()
                return Box({"schema_name": random_record[1]})
            else:
                raise Exception("No records found in oaiserver_schema table.")


def get_table_rows_count(_, table_names):
    """Get the row count for the specified tables.

    Args:
        _(Response): Placeholder parameter for compatibility with the caller.
        table_names(list): A list of table names to retrieve row counts for.

    Returns:
        Box: A Box object containing the row count for each specified table,
        structured as {"row_count": {table_name: count}}.
    """
    count_dict = {}
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            for table_name in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                count_dict[table_name] = count
    return Box({"row_count": count_dict})
