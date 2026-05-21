from contextlib import closing
from datetime import datetime

from psycopg2.extras import RealDictCursor

from helper.common.connect_helper import connect_db


def transform_index_data(index_id):
    """Transform index data from the database into the expected format.

    Args:
        index_id(int): ID of the index to transform.

    Returns:
        dict: Transformed index data.
        int: Parent ID of the index.
    """
    def get_parents(cursor, index_id):
        """Recursively get all parent indices of a given index.

        Args:
            cursor(cursor): Database cursor.
            index_id(int): Index ID.

        Returns:
            list: List of parent indices.
        """
        parent_list = []
        if index_id == 0:
            return parent_list
        cursor.execute("SELECT * FROM index WHERE id = %s;", (index_id,))
        parent = cursor.fetchone()
        if parent:
            parent_list = get_parents(cursor, parent["parent"])
            parent_list.append(parent)
        return parent_list

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM index WHERE id = %s;", (index_id,))
            index_data = cursor.fetchone()

            if index_data is None:
                return None
            transformd_data = {
                "browsing_group": index_data["browsing_group"],
                "browsing_role": index_data["browsing_role"],
                "children": [],
                "cid": index_data["id"],
                "contribute_group": index_data["contribute_group"],
                "contribute_role": index_data["contribute_role"],
                "coverpage_state": index_data["coverpage_state"],
                "display_no": index_data["display_no"],
                "emitLoadNextLevel": False,
                "id": str(index_data["id"]),
                "index_link_enabled": index_data["index_link_enabled"],
                "is_deleted": index_data["is_deleted"],
                "link_name": index_data["index_link_name_english"],
                "more_check": index_data["more_check"],
                "name": index_data["index_name_english"],
                "pid": index_data["parent"],
                "position": index_data["position"],
                "public_date": datetime.strftime(
                    index_data["public_date"], "%Y-%m-%dT%H:%M:%S")
                    if index_data["public_date"] else None,
                "public_state": index_data["public_state"],
                "recursive_coverpage_check": index_data["recursive_coverpage_check"],
                "settings": {
                    "checked": False,
                    "isCollapsedOnInit": True
                },
                "value": index_data["index_name_english"]
            }
            if index_data["parent"]:
                parents = get_parents(cursor, index_data["parent"])
                parent_id = ""
                for p in parents:
                    parent_id += str(p["id"]) + "/"
                transformd_data["parent"] = parent_id[:-1]
            return transformd_data
