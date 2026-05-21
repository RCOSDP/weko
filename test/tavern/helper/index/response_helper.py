from contextlib import closing
from datetime import datetime, timezone
import json

from box import Box
import dill
from psycopg2.extras import RealDictCursor

from helper.common.connect_helper import connect_db, connect_redis


def set_pdfcoverpage(response, avail, lang, map=None):
    """Set the availability of PDF cover page and update session language.

    Args:
        response(Response): The response object from which to extract cookies.
        avail(str): The availability status to set for PDF cover page.
        lang(str): The language to set in the session.
        map(str, optional): determine the mapping for group settings.

    Returns:
        Box: A Box object containing role IDs if map is "delete", otherwise empty.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
            update_query = "UPDATE pdfcoverpage_set SET avail = %s;"
            cur.execute(update_query, (avail,))
            conn.commit()

            cookie = response.cookies.get_dict()
            session_key = cookie.get('session', '').split(".")[0]

            # Connect to Redis and update the session with the new language settings
            redis_1 = connect_redis(db=1)
            session = dill.loads(redis_1.get(session_key))
            session["language"] = str(lang)
            session["selected_language"] = str(lang)
            redis_1.set(session_key, dill.dumps(session, protocol=4))

            role_ids = []
            if map == "register":
                redis_4 = connect_redis(db=4)
                key = "weko3_example_org_gakunin_groups"
                value = {
                    "updated_at": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    "groups": "jc_weko3_example_org_groups_add1,"
                        "jc_weko3_example_org_groups_add2,jc_weko3_example_org_groups_add3"
                }
                redis_4.hset(key, mapping=value)
            elif map == "delete":
                redis_4 = connect_redis(db=4)
                key = "weko3_example_org_gakunin_groups"
                value = {
                    "updated_at": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                    "groups": ""
                }
                redis_4.hset(key, mapping=value)

                insert_queries = [
                    "INSERT INTO accounts_role(name) VALUES ('jc_weko3_example_org_groups_delete1');",
                    "INSERT INTO accounts_role(name) VALUES ('jc_weko3_example_org_groups_delete2');",
                    "INSERT INTO accounts_role(name) VALUES ('jc_weko3_example_org_groups_delete3');"
                ]
                for query in insert_queries:
                    cur.execute(query)
                conn.commit()
                search_query = "SELECT id FROM accounts_role WHERE name IN " \
                    "('jc_weko3_example_org_groups_delete1', 'jc_weko3_example_org_groups_delete2', 'jc_weko3_example_org_groups_delete3');"
                cur.execute(search_query)
                role_ids = [row[0] for row in cur.fetchall()]
                index_updatequery = "UPDATE index SET browsing_role = browsing_role || %s, contribute_role = contribute_role || %s;"
                role_ids_str = ",".join(str(role_id) for role_id in role_ids)
                cur.execute(index_updatequery, ("," + role_ids_str, "," + role_ids_str))
                conn.commit()
    return Box({
        "role_ids": role_ids
    })


def count_indices(_):
    """Count the number of indices in the database.

    Args:
        _ (Response): Unused parameter for compatibility.

    Returns:
        Box: A Box object containing the count of indices.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM index;")
            count = cursor.fetchone()[0]
    return Box({"index_count": count})


def set_lock_index(_, index_id, edit=False):
    """Set a lock on an index and optionally retrieve its details.

    Args:
        _ (Response): Unused parameter for compatibility.
        index_id (int): The ID of the index to lock.
        edit (bool, optional): Boolean flag indicating whether to retrieve index details.

    Returns:
        Box: A Box object containing index details if edit is True, otherwise the count of indices.
    """
    redis_0 = connect_redis()
    key = f"lock_index_{index_id}"
    redis_0.set(key, "1")
    if edit:
        with closing(connect_db()) as conn:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                cursor.execute("SELECT * FROM index WHERE id = %s;", (index_id,))
                index = cursor.fetchone()

        index_serializable = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in index.items()
        }
        return Box({
            "index": json.dumps(index_serializable),
        })
    else:
        return count_indices(_)


def set_target_id(_, file_path, invalid=False):
    """Set the target ID from a file and optionally retrieve its details.

    Args:
        _ (Response): Unused parameter for compatibility.
        file_path (str): The path to the file containing target information.
        invalid (bool, optional): Boolean flag indicating whether to retrieve index details.

    Returns:
        Box: A Box object containing target ID list and index details if invalid is True.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        target_info = json.load(f)
    target_id_list = [target_info.get("id")]
    if invalid:
        with closing(connect_db()) as conn:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                cursor.execute("SELECT * FROM index WHERE id = %s;", (target_id_list[0],))
                index = cursor.fetchone()

        index_serializable = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in index.items()
        }
        return Box({
            "target_id_list": target_id_list,
            "index": json.dumps(index_serializable),
        })
    else:
        return Box({
            "target_id_list": target_id_list,
        })


def get_indices(_):
    """Retrieve all indices from the database and return them as a JSON string.

    Args:
        _ (Response): Unused parameter for compatibility.

    Returns:
        Box: A Box object containing the list of indices as a JSON string.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM index ORDER BY id;")
            rows = cursor.fetchall()

    index_list = []
    for row in rows:
        index_serializable = {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in row.items()
        }
        index_list.append(index_serializable)
    return Box({
        "index_list": json.dumps(index_list),
    })


def set_thumbnail_path(response):
    """Extract thumbnail path from the response JSON.

    Args:
        response (Response): The response object containing JSON data.

    Returns:
        Box: A Box object containing the thumbnail path.
    """
    response_data = response.json()
    return Box({"thumbnail_path": response_data.get("data", {}).get("path", "")})


def set_harvest(_, index_id):
    """Set harvest settings for a given index ID.

    Args:
        _ (Response): Unused parameter for compatibility.
        index_id (int): The ID of the index to set harvest settings for.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            insert_query = "INSERT INTO harvest_settings" \
                "(repository_name, base_url, metadata_prefix, index_id, update_style, auto_distribution)"\
                " VALUES (%s, %s, %s, %s, %s, %s);"
            cursor.execute(
                insert_query,
                ("Test Repository", "http://example.com/oai", "oai_dc", index_id, "1", "1"))
            conn.commit()


def set_index_view_permission(_, index_id, role_id=""):
    """Set the browsing role for a given index ID.

    Args:
        _ (Response): Unused parameter for compatibility.
        index_id (int): The ID of the index to set the browsing role for.
        role_id (str, optional): The ID of the role to set as the browsing role.
            If empty, it will clear the browsing role.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            update_query = "UPDATE index SET browsing_role = %s WHERE id = %s;"
            cursor.execute(update_query, (role_id, index_id))
            conn.commit()
