from contextlib import closing
from datetime import datetime, timezone
from time import sleep
from urllib.parse import urlencode
import json

import requests
from box import Box
from bs4 import BeautifulSoup
from psycopg2.extras import RealDictCursor

from helper.common.connect_helper import connect_db
from helper.index.data_transformation_helper import transform_index_data


def verify_indexedit_elements(
        response,
        lang,
        coverpage,
        map_groups={},
        nodeid="0"
    ):
    """Verify elements in index edit page

    Args:
        response(Response): Response object from the index edit page request
        lang(str): Expected language code
        coverpage(str): Expected coverpage setting value
        map_groups(dict, optional): Expected map groups. Defaults to {}.
        nodeid(str, optional): Expected node ID. Defaults to "0".
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    # lang-code
    lang_code = soup.find(id='lang-code').get('value')
    assert lang_code == lang

    # get_tree_json
    get_tree_json = soup.find(id='get_tree_json').text
    assert get_tree_json == '/api/tree'

    # upt_tree_json
    upt_tree_json = soup.find(id='upt_tree_json').text
    assert upt_tree_json == ''

    # mod_tree_detail
    mod_tree_detail = soup.find(id='mod_tree_detail').text
    assert mod_tree_detail == '/api/tree/index/'

    # admin_coverpage_setting
    admin_coverpage_setting = soup.find(id='admin_coverpage_setting').text
    assert admin_coverpage_setting == str(coverpage)

    # show_modal
    show_modal = soup.find(id='show_modal').get('value')
    assert show_modal == 'False'

    # app-root-tree-hensyu
    app_root_tree_hensyu = soup.find('app-root-tree-hensyu')
    assert app_root_tree_hensyu['nodeid'] == nodeid

    if map_groups:
        with closing(connect_db()) as conn:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                if map_groups.get("add"):
                    role_query = "SELECT id FROM accounts_role WHERE name IN %s;"
                    cursor.execute(role_query, (tuple(map_groups["add"]),))
                    added_roles = cursor.fetchall()
                    index_query = "SELECT browsing_role, contribute_role FROM index;"
                    cursor.execute(index_query)
                    index_roles = cursor.fetchall()
                    for index in index_roles:
                        browsing_role_ids = index["browsing_role"].split(',')
                        contribute_role_ids = index["contribute_role"].split(',')
                        added_roles_ids = [str(role["id"]) for role in added_roles]
                        assert all(role_id in browsing_role_ids for role_id in added_roles_ids)
                        assert all(role_id in contribute_role_ids for role_id in added_roles_ids)
                elif map_groups.get("delete"):
                    index_query = "SELECT browsing_role, contribute_role FROM index;"
                    cursor.execute(index_query)
                    index_roles = cursor.fetchall()
                    for index in index_roles:
                        browsing_role_ids = index["browsing_role"].split(',')
                        contribute_role_ids = index["contribute_role"].split(',')
                        deleted_roles_ids = json.loads(map_groups["delete"])
                        assert all(str(role_id) not in browsing_role_ids for role_id in deleted_roles_ids)
                        assert all(str(role_id) not in contribute_role_ids for role_id in deleted_roles_ids)


def verify_index_tree(
        response,
        expected_tree_file,
        role_id,
        edited_id_list=None,
        deleted_id_list=None,
        no_action=False
    ):
    """Verify the index tree structure in the response.

    Args:
        response(Response): Response object from the index tree request.
        expected_tree_file(str): Path to the file containing the expected index tree structure.
        role_id(str): Role ID to filter the tree information.
        edited_id_list(list, optional): List of IDs of the edited index nodes. Defaults to None.
        deleted_id_list(list, optional): List of IDs of the deleted index nodes. Defaults to None.
        no_action(bool, optional): Flag to indicate no action. Defaults to False.

    Raises:
        ValueError: If an edited index ID is not found in the database.
    """
    def get_browsing_treeinfo(tree, role_id):
        """Recursively get the browsing tree information for a given role ID.

        Args:
            tree(list): Current tree structure.
            role_id(str): Role ID to filter the tree information.

        Returns:
            list: Filtered tree structure based on the browsing role.
        """
        hide_keys = ["browsing_group", "browsing_role", "contribute_group", "contribute_role", "public_date", "public_state"]
        browsing_info = []
        for node in tree:
            public_state = node.get("public_state", "")
            browsing_role = node.get("browsing_role", "")
            for key in hide_keys:
                if key in node:
                    del node[key]
            if public_state and str(role_id) in browsing_role.split(','):
                node["children"] = get_browsing_treeinfo(node.get("children", []), role_id)
                browsing_info.append(node)
            if node.get("id") == "more":
                browsing_info.append(node)
        return browsing_info

    def upsert_node(tree, node_json, my_id, parent_id):
        """Upsert a node in the tree structure.

        Args:
            tree(list): Current tree structure.
            node_json(dict): Node data to upsert.
            my_id(str): ID of the node to upsert.
            parent_id(int): Parent ID of the node.
        """
        if parent_id == 0:
            for idx, node in enumerate(tree):
                if node["id"] == my_id:
                    tree[idx] = node_json
                    return
            tree.append(node_json)
            return
        for node in tree:
            if node["id"] == "more":
                continue
            if node["id"] == str(parent_id):
                for idx, child in enumerate(node["children"]):
                    if child["id"] == str(my_id):
                        node_json["children"] = child.get("children", [])
                        node["children"][idx] = node_json
                        return
                node["children"].append(node_json)
                return
            upsert_node(node["children"], node_json, my_id, parent_id)
    def delete_node(tree, my_id):
        """Delete a node from the tree structure.

        Args:
            tree(list): Current tree structure.
            my_id(str): ID of the node to delete.
        """
        for idx, node in enumerate(tree):
            if node["id"] == "more":
                continue
            if node["id"] == str(my_id):
                del tree[idx]
                return
            delete_node(node["children"], my_id)

    with open(expected_tree_file, 'r') as f:
        expected_tree = json.load(f)
    if role_id not in [1, 2] and not no_action:
        browsing_tree = get_browsing_treeinfo(expected_tree, role_id)
    else:
        browsing_tree = expected_tree
    actual_tree = response.json()

    if edited_id_list:
        edited_id_list = json.loads(str(edited_id_list))
        for edited_id in edited_id_list:
            tree_json = transform_index_data(edited_id)
            if tree_json is None:
                raise ValueError(f"Index with ID {edited_id} not found in the database.")
            index_id = tree_json["id"]
            parent_id = tree_json["pid"]
            upsert_node(browsing_tree, tree_json, index_id, parent_id)

    if deleted_id_list:
        deleted_id_list = json.loads(str(deleted_id_list))
        for deleted_id in deleted_id_list:
            delete_node(browsing_tree, deleted_id)

    try:
        assert actual_tree == browsing_tree
    except AssertionError as e:
        print("Actual Tree:", actual_tree)
        print("Expected Tree:", browsing_tree)
        raise e


def verify_index_info(response, id, within_community=True):
    """Verify the index information in the response.

    Args:
        response(Response): Response object from the index info request.
        id(int): ID of the index to verify.
        within_community(bool, optional): Whether to verify within the community context. Defaults to True.
    """
    def is_gakunin_group(name):
        """Check if the role name is a Gakunin group.

        Args:
            name(str): Role name.

        Returns:
            bool: True if it's a Gakunin group, False otherwise.
        """
        return name.startswith("jc_") and name.find("_groups") != -1

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            index_query = "SELECT * FROM index WHERE id = %s;"
            role_query = "SELECT id, name FROM accounts_role WHERE name NOT IN ('System Administrator', 'Repository Administrator');"
            cursor.execute(index_query, (id,))
            index_data = cursor.fetchone()
            cursor.execute(role_query)
            roles = cursor.fetchall()

            roles.append({"id": -98, "name": "Authenticated User"})
            roles.append({"id": -99, "name": "Guest"})

            response_data = response.json()

            for k in response_data:
                if k == "can_edit":
                    assert response_data[k] == within_community
                elif k == "have_children":
                    children_query = "SELECT id FROM index WHERE parent = %s;"
                    cursor.execute(children_query, (id,))
                    children = cursor.fetchall()
                    assert response_data[k] == (len(children) > 0)
                elif k in ["browsing_role", "contribute_role"]:
                    expected_roles = {
                        "allow": [],
                        "deny": []
                    }

                    splited_roles = index_data[k].split(',')
                    for r in roles:
                        if is_gakunin_group(r["name"]):
                            continue
                        if str(r["id"]) in splited_roles:
                            expected_roles["allow"].append(dict(r))
                        else:
                            expected_roles["deny"].append(dict(r))

                    assert sorted(response_data[k]["allow"], key=lambda x: x["id"])\
                        == sorted(expected_roles["allow"], key=lambda x: x["id"])
                    assert sorted(response_data[k]["deny"], key=lambda x: x["id"])\
                        == sorted(expected_roles["deny"], key=lambda x: x["id"])
                elif k in ["browsing_group", "contribute_group"]:
                    expected_groups = {
                        "allow": [],
                        "deny": []
                    }

                    splited_groups = index_data[k].split(',')
                    for r in roles:
                        if is_gakunin_group(r["name"]):
                            if str(r["id"]) in splited_groups:
                                expected_groups["allow"].append({
                                    "id": str(r["id"]) + "gr",
                                    "name": r["name"]
                                })
                            else:
                                expected_groups["deny"].append({
                                    "id": str(r["id"]) + "gr",
                                    "name": r["name"]
                                })

                    assert sorted(response_data[k]["allow"], key=lambda x: x["id"])\
                        == sorted(expected_groups["allow"], key=lambda x: x["id"])
                    assert sorted(response_data[k]["deny"], key=lambda x: x["id"])\
                        == sorted(expected_groups["deny"], key=lambda x: x["id"])
                else:
                    assert response_data[k] == (index_data[k] if index_data[k] is not None else "")


def verify_created_index(response, id, name, user_id, map=False, parent_id=0):
    """Verify the created index information in the response and database.

    Args:
        response(Response): Response object from the index creation request.
        id(int): ID of the created index.
        name(str): Name of the created index.
        user_id(int): User ID of the owner of the created index.
        map(bool, optional): Whether the index is created through map. Defaults to False.
        parent_id(int, optional): Parent ID of the created index. Defaults to 0.
    """
    expected_response = {
        "status": 201,
        "message": "Index created successfully.",
        "errors": []
    }
    assert response.json() == expected_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            query = "SELECT * FROM index WHERE id = %s;"
            cursor.execute(query, (id,))
            index_data = cursor.fetchone()

            with open('response_data/index/created_index.json', 'r') as f:
                expected_data = json.load(f)

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            expected_data["created"] = now
            expected_data["updated"] = now
            expected_data["id"] = id
            expected_data["index_name"] = name
            expected_data["index_name_english"] = name
            expected_data["index_link_name_english"] = name
            expected_data["owner_user_id"] = user_id

            if map:
                roles_query = "SELECT id, name FROM accounts_role WHERE name like 'jc_%';"
                cursor.execute(roles_query)
                roles = cursor.fetchall()
                role_ids_str = ",".join(str(role["id"]) for role in roles)
                expected_data["browsing_role"] = "1,2,3,4," + role_ids_str + ",-98,-99"
                expected_data["contribute_role"] = "1,2,3,4," + role_ids_str + ",-98,-99"

            if parent_id:
                select_query = "SELECT * FROM index WHERE id = %s;"
                count_query = "SELECT COUNT(*) FROM index WHERE parent = %s;"
                cursor.execute(select_query, (parent_id,))
                parent_data = cursor.fetchone()
                cursor.execute(count_query, (parent_id,))
                count = cursor.fetchone()["count"] - 1
                expected_data["parent"] = parent_id
                expected_data["position"] = count
                expected_data["harvest_public_state"] = parent_data["harvest_public_state"]
                expected_data["display_format"] = parent_data["display_format"]
                if parent_data["recursive_public_state"]:
                    expected_data["public_state"] = parent_data["public_state"]
                    expected_data["public_date"] = parent_data["public_date"]
                    expected_data["recursive_public_state"] = True
                if parent_data["recursive_browsing_role"]:
                    expected_data["browsing_role"] = parent_data["browsing_role"]
                    expected_data["recursive_browsing_role"] = True
                if parent_data["recursive_contribute_role"]:
                    expected_data["contribute_role"] = parent_data["contribute_role"]
                    expected_data["recursive_contribute_role"] = True
                if parent_data["recursive_browsing_group"]:
                    expected_data["browsing_group"] = parent_data["browsing_group"]
                    expected_data["recursive_browsing_group"] = True
                if parent_data["recursive_contribute_group"]:
                    expected_data["contribute_group"] = parent_data["contribute_group"]
                    expected_data["recursive_contribute_group"] = True

    for k in index_data:
        print(f"{k}: {index_data[k]} (expected: {expected_data.get(k)})")
        if k in ["created", "updated"]:
            assert abs((index_data[k] - expected_data[k]).total_seconds()) < 1
        else:
            assert index_data[k] == expected_data[k]


def verify_edited_index(
        response,
        file_path,
        public=None,
        harvest=None,
        thumbnail="",
        image_delete=False,
        oai_action=""
    ):
    """Verify the edited index information in the response and database.

    Args:
        response(Response): Response object from the index edit request.
        file_path(str): Path to the file containing the expected index data.
        public(bool, optional): Expected public state. Defaults to None.
        harvest(bool, optional): Expected harvest state. Defaults to None.
        thumbnail(str, optional): Expected thumbnail image name. Defaults to "".
        image_delete(bool, optional): Whether the image was deleted. Defaults to False.
        oai_action(str, optional): Expected OAI action. Defaults to "".
    """
    def get_children(cursor, parent_id):
        """Recursively get all children of a given parent index.

        Args:
            cursor(cursor): Database cursor.
            parent_id(int): Parent index ID.

        Returns:
            list: List of child indices.
        """
        cursor.execute("SELECT * FROM index WHERE parent = %s;", (parent_id,))
        children = cursor.fetchall()
        all_children = []
        for child in children:
            all_children.append(child)
            all_children.extend(get_children(cursor, child["id"]))
        return all_children

    def get_roles(group_dict, role_dict):
        """Extract allowed role IDs from group and role dictionaries.

        Args:
            group_dict(dict): Dictionary containing group information.
            role_dict(dict): Dictionary containing role information.

        Returns:
            list: List of allowed role IDs.
        """
        allow_roles = [role["id"] for role in role_dict.get("allow", [])]
        allow_roles.extend([int(gr["id"][:-2]) for gr in group_dict.get("allow", [])
                            if gr["id"].endswith("gr")])
        return allow_roles

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

    expected_response = {
        "status": 200,
        "message": "Index updated successfully.",
        "errors": [],
        "delete_flag": image_delete
    }
    assert response.json() == expected_response

    with open(file_path, "r", encoding="utf-8") as f:
        expected_data = json.load(f)

    expected_data["image_name"] = thumbnail

    target_id = expected_data["id"]
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            cursor.execute("SELECT * FROM index WHERE id = %s;", (target_id,))
            index_data = cursor.fetchone()
            recursive_list = get_children(cursor, target_id)
            roles_query = "SELECT id, name FROM accounts_role;"
            cursor.execute(roles_query)
            roles = cursor.fetchall()
            roles_dict = {str(r["id"]): r["name"] for r in roles}
            roles_dict["-98"] = "Authenticated User"
            roles_dict["-99"] = "Guest"

            for k in expected_data:
                if k in ["id", "parent", "position", "can_edit", "have_children"]:
                    continue
                if k in ["browsing_group", "contribute_group"]:
                    assert index_data[k] == ""
                elif k == "biblio_flag":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            assert rid["online_issn"] == index_data["online_issn"]
                        else:
                            pass
                elif k == "browsing_role":
                    expected_roles = get_roles(expected_data["browsing_group"], expected_data["browsing_role"])
                    splited_roles = index_data[k].split(',')
                    assert sorted([int(r) for r in splited_roles if r]) == sorted(expected_roles)
                elif k == "contribute_role":
                    expected_roles = get_roles(expected_data["contribute_group"], expected_data["contribute_role"])
                    splited_roles = index_data[k].split(',')
                    assert sorted([int(r) for r in splited_roles if r]) == sorted(expected_roles)
                elif k == "recursive_browsing_group":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            assert rid["browsing_group"] == index_data["browsing_group"]
                            expected_gakunin_groups = [gr for gr in expected_data["browsing_group"].get("allow", [])
                                                        if gr["id"].endswith("gr")]
                            splited_roles = rid["browsing_role"].split(',')
                            for gr in expected_gakunin_groups:
                                assert gr["id"][:-2] in splited_roles
                        else:
                            pass
                elif k == "recursive_browsing_role":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            rid_splited_roles = rid["browsing_role"].split(',')
                            index_data_splited_roles = index_data["browsing_role"].split(',')
                            for role in index_data_splited_roles:
                                if roles_dict.get(role).startswith("jc_") and roles_dict.get(role).find("_groups") != -1:
                                    assert role not in rid_splited_roles
                                else:
                                    assert role in rid_splited_roles
                        else:
                            pass
                elif k == "recursive_contribute_group":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            assert rid["contribute_group"] == index_data["contribute_group"]
                            expected_gakunin_groups = [gr for gr in expected_data["contribute_group"].get("allow", [])
                                                        if gr["id"].endswith("gr")]
                            splited_roles = rid["contribute_role"].split(',')
                            for gr in expected_gakunin_groups:
                                assert gr["id"][:-2] in splited_roles
                        else:
                            pass
                elif k == "recursive_contribute_role":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            rid_splited_roles = rid["contribute_role"].split(',')
                            index_data_splited_roles = index_data["contribute_role"].split(',')
                            for role in index_data_splited_roles:
                                if roles_dict.get(role).startswith("jc_") and roles_dict.get(role).find("_groups") != -1:
                                    assert role not in rid_splited_roles
                                else:
                                    assert role in rid_splited_roles
                        else:
                            pass
                elif k == "recursive_coverpage_check":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            assert rid["coverpage_state"] == index_data["coverpage_state"]
                        else:
                            pass
                elif k == "recursive_public_state":
                    assert index_data[k] == False
                    for rid in recursive_list:
                        if expected_data[k]:
                            assert rid["public_state"] == index_data["public_state"]
                            assert rid["public_date"] == index_data["public_date"]
                        else:
                            pass
                elif k == "thumbnail_delete_flag":
                    if image_delete:
                        assert index_data["image_name"] == ""
                    else:
                        assert index_data["image_name"] == expected_data["image_name"]
                elif k == "public_date":
                    expected_date = None
                    if expected_data[k]:
                        expected_date = datetime.fromisoformat(expected_data[k])
                    assert index_data[k] == expected_date
                elif k == "public_state":
                    if public is not None:
                        assert index_data[k] == public
                    else:
                        assert index_data[k] == expected_data[k]
                elif k == "harvest_public_state":
                    if harvest is not None:
                        assert index_data[k] == harvest
                    else:
                        assert index_data[k] == expected_data[k]
                else:
                    assert index_data[k] == expected_data[k]

            if public and harvest and expected_data["public_state"] and expected_data["harvest_public_state"]:
                root = get_parents(cursor, target_id)
                spec = ""
                description = ""
                for r in root:
                    spec += f"{r['id']}:"
                    description += f"{r['index_name_english']}->"
                spec = spec[:-1]
                if index_data["parent"] == 0:
                    description = index_data["index_name"]
                else:
                    description = description[:-2]

                now = datetime.now(timezone.utc).replace(tzinfo=None)
                expected_oai_set = {
                    "created": now,
                    "updated": now,
                    "id": target_id,
                    "spec": spec,
                    "name": index_data["index_name"],
                    "description": description,
                    "search_pattern": f'path:"{target_id}"'
                }

                oai_query = "SELECT * FROM oaiserver_set WHERE id = %s;"
                for attempt in range(10):
                    cursor.execute(oai_query, (target_id,))
                    oai_data = cursor.fetchone()
                    if oai_data:
                        break
                    if attempt == 9:
                        raise AssertionError("OAI Set data not found after multiple attempts.")
                    sleep(1)

                for k in expected_oai_set:
                    if k in ["created", "updated"]:
                        if image_delete:
                            continue
                        assert abs((oai_data[k] - expected_oai_set[k]).total_seconds()) < 1
                    else:
                        assert oai_data[k] == expected_oai_set[k]

            if oai_action:
                if oai_action == "edit":
                    root = get_parents(cursor, target_id)
                    spec = ""
                    description = ""
                    for r in root:
                        spec += f"{r['id']}:"
                        description += f"{r['index_name_english']}->"
                    spec = spec[:-1]
                    if index_data["parent"] == 0:
                        description = index_data["index_name"]
                    else:
                        description = description[:-2]

                    expected_oai_set = {
                        "id": target_id,
                        "spec": spec,
                        "name": index_data["index_name"],
                        "description": description,
                        "search_pattern": f'path:"{target_id}"'
                    }

                    oai_query = "SELECT * FROM oaiserver_set WHERE id = %s;"
                    for attempt in range(10):
                        cursor.execute(oai_query, (target_id,))
                        oai_data = cursor.fetchone()
                        if oai_data:
                            if oai_data["created"] != oai_data["updated"]:
                                break
                        if attempt == 9:
                            raise AssertionError("OAI Set data not found after multiple attempts.")
                        sleep(1)
                    for k in expected_oai_set:
                        assert oai_data[k] == expected_oai_set[k]
                elif oai_action == "delete":
                    oai_query = "SELECT * FROM oaiserver_set WHERE id = %s;"
                    for attempt in range(10):
                        cursor.execute(oai_query, (target_id,))
                        oai_data = cursor.fetchone()
                        if oai_data is None:
                            break
                        if attempt == 9:
                            raise AssertionError("OAI Set data not found after multiple attempts.")
                        sleep(1)
                    assert oai_data is None


def verify_upload_thumbnail(response, file_name):
    """Verify the upload thumbnail response.

    Args:
        response(Response): Response object from the upload thumbnail request.
        file_name(str): Expected file name of the uploaded thumbnail.
    """
    expected_response = {
        "code": 0,
        "data": {
            "path": f"/data/indextree/{file_name}"
        },
        "msg": "file upload success"
    }
    assert response.json() == expected_response


def verify_deleted_index(response, deleted_ids, single_item_ids=[], multi_item_ids=[]):
    """Verify the deleted index information in the response and database.

    Args:
        response(Response): Response object from the index deletion request.
        deleted_ids(list): List of IDs of the deleted indices.
        single_item_ids(list, optional): List of single item IDs associated with the deleted index. Defaults to [].
        multi_item_ids(list, optional): List of multi item IDs associated with the deleted index. Defaults to [].
    """
    expected_response = {
        "status": 200,
        "message": "Index deleted successfully.",
        "errors": []
    }
    assert response.json() == expected_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            index_query = "SELECT is_deleted FROM index WHERE id IN %s;"
            cursor.execute(index_query, (tuple(deleted_ids),))
            index_data = cursor.fetchall()
            for data in index_data:
                assert data["is_deleted"] == True

            oai_query = "SELECT * FROM oaiserver_set WHERE id IN %s;"
            for i in range(10):
                cursor.execute(oai_query, (tuple(deleted_ids),))
                oai_data = cursor.fetchone()
                if oai_data is None:
                    break
                if i == 9:
                    raise AssertionError("OAI Set data not found after multiple attempts.")
                sleep(1)
            assert oai_data is None

            deleted_pid_query = "SELECT status FROM pidstore_pid " \
                "WHERE pid_type = 'recid' AND pid_value IN %s;"
            if single_item_ids:
                cursor.execute(deleted_pid_query, (tuple([str(id) for id in single_item_ids]),))
                pid_data = cursor.fetchall()
                for pid in pid_data:
                    assert pid["status"] == "D"
            updated_pid_query = "SELECT object_uuid FROM pidstore_pid " \
                "WHERE pid_type = 'recid' AND pid_value = %s;"
            records_query = "SELECT json FROM records_metadata WHERE id = %s;"
            for item_id in multi_item_ids:
                cursor.execute(updated_pid_query, (str(item_id),))
                pid_data = cursor.fetchone()
                assert pid_data is not None
                object_uuid = pid_data["object_uuid"]
                cursor.execute(records_query, (object_uuid,))
                record_data = cursor.fetchone()
                record_json = record_data["json"]
                for deleted_id in deleted_ids:
                    assert str(deleted_id) not in record_json.get("path", [])


def verify_not_deleted_index(response, target_ids, item_ids):
    """Verify that the index is not deleted in the response and database.

    Args:
        response(Response): Response object from the index deletion request.
        target_ids(list): List of target index IDs.
        item_ids(list): List of item IDs associated with the target indices.
    """
    expected_response = {
        "status": 200,
        "message": "Index deleted successfully.",
        "errors": []
    }
    assert response.json() == expected_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            index_query = "SELECT is_deleted FROM index WHERE id IN %s;"
            cursor.execute(index_query, (tuple(target_ids),))
            index_data = cursor.fetchall()
            for data in index_data:
                assert data["is_deleted"] == False

            pid_query = "SELECT status FROM pidstore_pid WHERE pid_type = 'recid' AND pid_value IN %s;"
            cursor.execute(pid_query, (tuple([str(id) for id in item_ids]),))
            pid_data = cursor.fetchall()
            for pid in pid_data:
                assert pid["status"] == "R"


def verify_delete_not_exist_index(response):
    """Verify that the response indicates the index deletion failed due to non-existence.

    Args:
        response(Response): Response object from the index deletion request.
    """
    expected_response = {
        "status": 200,
        "message": "Failed to delete index.",
        "errors": []
    }
    assert response.json() == expected_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            index_query = "SELECT is_deleted FROM index;"
            cursor.execute(index_query)
            index_data = cursor.fetchall()
            for data in index_data:
                assert data["is_deleted"] == False


def verify_private_with_doi(response, index):
    """Verify that the response indicates the index cannot be private due to DOI links.

    Args:
        response(Response): Response object from the request.
        index(dict): Expected index data.
    """
    expected_response = {
        "status": 200,
        "message": "",
        "errors": [
            "The index cannot be kept private because there are links from items that have a DOI."
        ],
        "delete_flag": False
    }
    assert response.json() == expected_response

    verify_index(index)


def verify_harvest_private_with_doi(response, index):
    """Verify that the response indicates the index harvest cannot be private due to DOI links.

    Args:
        response(Response): Response object from the request.
        index(dict): Expected index data.
    """
    expected_response = {
        "status": 200,
        "message": "",
        "errors": [
            "Index harvests cannot be kept private because there are links from items that have a DOI."
        ],
        "delete_flag": False
    }
    assert response.json() == expected_response

    verify_index(index)


def verify_index_locked(response, count=None, index=None, is_edit=False):
    """Verify that the response indicates the index is locked and the count of indices remains unchanged.

    Args:
        response(Response): Response object from the request.
        count(int, optional): Expected count of indices.
        index(dict, optional): Expected index data.
        is_edit(bool, optional): Whether the operation is an edit. Defaults to False.
    """
    expected_response = {
        "status": 200,
        "message": "",
        "errors": [
            "Index Delete is in progress on another device."
        ]
    }
    if is_edit:
        expected_response["delete_flag"] = False
    assert response.json() == expected_response

    if count is not None:
        verify_count(count)
    if index is not None:
        verify_index(index)


def verify_edit_during_import(response, index):
    """Verify that the response indicates the index cannot be edited due to an import in progress.

    Args:
        response(Response): Response object from the index edit request.
        index(dict): Expected index data.
    """
    try:
        expected_response = {
            "status": 200,
            "message": "",
            "errors": [
                "The index cannot be updated becase import is in progress."
            ],
            "delete_flag": False
        }
        assert response.json() == expected_response

        verify_index(index)
    except AssertionError as e:
        print("Response JSON:", response.json())
        raise e


def verify_delete_with_doi(response, delete_id):
    """Verify that the response indicates the index cannot be deleted due to DOI links.

    Args:
        response(Response): Response object from the request.
        delete_id(int): ID of the index attempted to be deleted.
    """
    excepted_response = {
        "status": 200,
        "message": "",
        "errors": [
            "The index cannot be deleted because there is a link from an item that has a DOI."
        ]
    }
    assert response.json() == excepted_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            query = "SELECT is_deleted FROM index WHERE id = %s;"
            cursor.execute(query, (delete_id,))
            index_data = cursor.fetchone()
            assert index_data["is_deleted"] == False


def verify_delete_with_editing(response, delete_id):
    """Verify that the response indicates the index cannot be deleted due to being edited.

    Args:
        response(Response): Response object from the request.
        delete_id(int): ID of the index attempted to be deleted.
    """
    excepted_response = {
        "status": 200,
        "message": "",
        "errors": [
            "This index cannot be deleted because the item belonging to this index is being edited."
        ]
    }
    assert response.json() == excepted_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            query = "SELECT is_deleted FROM index WHERE id = %s;"
            cursor.execute(query, (delete_id,))
            index_data = cursor.fetchone()
            assert index_data["is_deleted"] == False


def verify_delete_with_harvesting(response, delete_id):
    """Verify that the response indicates the index cannot be deleted due to being harvested.

    Args:
        response(Response): Response object from the request.
        delete_id(int): ID of the index attempted to be deleted.
    """
    excepted_response = {
        "status": 200,
        "message": "",
        "errors": [
            "The index cannot be deleted becase the index in harvester settings."
        ]
    }
    assert response.json() == excepted_response

    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            query = "SELECT is_deleted FROM index WHERE id = %s;"
            cursor.execute(query, (delete_id,))
            index_data = cursor.fetchone()
            assert index_data["is_deleted"] == False


def verify_delete_no_specify_index(_, indices):
    """Verify that no indices are deleted.

    Args:
        _(Response): Response object from the request.
        indices(list): Expected list of indices.
    """
    verify_indices(indices)


def verify_no_filename(response, path, code, expected_location=None, host=None):
    """Verify that the response indicates a bad request due to no filename.

    Args:
        response(Response): Response object from the initial request.
        path(str): Path to the file to be uploaded.
        code(int): Expected status code of the response.
        expected_location(str, optional): Expected value of the Location header for redirection. Defaults to None.
        host(str, optional): Host URL for constructing the expected Location header. Defaults to None.
    """
    target_url = response.url + 'admin/indexedit/upload'
    cookies = response.cookies
    with open(path, "rb") as f:
        files = {
            "uploadFile": ('', f, 'multipart/form-data'),
        }
        r = requests.post(target_url, files=files, verify=False, cookies=cookies, allow_redirects=False)
    assert r.status_code == code
    soup = BeautifulSoup(r.text, 'html.parser')
    h1 = soup.find('h1')
    if code == 400:
        assert h1.text == "Bad Request"
    elif code == 403:
        assert h1.text.endswith("Permission required")
    elif code == 302 and expected_location is not None and host is not None:
        verify_location_header(r, expected_location, host)

def verify_location_header(response, expected_location, host):
    """Verify that the response contains the expected Location header.

    Args:
        response(Response): The response object to check.
        expected_location(str): The expected value of the Location header.
        host(str): The host URL
    """
    location_header = response.headers.get('Location')
    encoded_expected_location = urlencode({'next': expected_location})
    full_expected_location = f"{host}/login/?{encoded_expected_location}"
    assert location_header == full_expected_location


def verify_bad_request(response, message, count=None, index=None, indices=None):
    """Verify that the response indicates a bad request with the expected message.

    Args:
        response(Response): Response object from the request.
        message(str, optional): Expected error message.
        count(int, optional): Expected count of indices.
        index(dict, optional): Expected index data.
        indices(list, optional): Expected list of indices.
    """
    expected_response = {
        "message": message,
        "status": 400,
    }
    assert response.json() == expected_response

    if count is not None:
        verify_count(count)
    if index is not None:
        verify_index(index)
    if indices is not None:
        verify_indices(indices)


def verify_bad_request_html(response):
    """Verify that the response indicates a bad request in HTML format.

    Args:
        response(Response): Response object from the request.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.find('h1')
    assert h1.text == "Bad Request"


def verify_unauthorized(response, count=None, index=None, indices=None, target_ids=None, item_ids=None):
    """Verify that the response indicates an unauthorized access with the expected message.

    Args:
        response(Response): Response object from the request.
        count(int, optional): Expected count of indices.
        index(dict, optional): Expected index data.
        indices(list, optional): Expected list of indices.
        target_ids(list, optional): List of target index IDs.
        item_ids(list, optional): List of item IDs.
    """
    expected_response = {
        "message": "The server could not verify that you are authorized "
            "to access the URL requested. You either supplied the wrong credentials "
            "(e.g. a bad password), or your browser doesn't understand how to supply the credentials required.",
        "status": 401
    }
    assert response.json() == expected_response

    if count is not None:
        verify_count(count)
    if index is not None:
        verify_index(index)
    if indices is not None:
        verify_indices(indices)

    if target_ids is not None and item_ids is not None:
        with closing(connect_db()) as conn:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                index_query = "SELECT is_deleted FROM index WHERE id IN %s;"
                cursor.execute(index_query, (tuple(target_ids),))
                index_data = cursor.fetchall()
                for data in index_data:
                    assert data["is_deleted"] == False

                pid_query = "SELECT status FROM pidstore_pid WHERE pid_type = 'recid' AND pid_value IN %s;"
                cursor.execute(pid_query, (tuple([str(id) for id in item_ids]),))
                pid_data = cursor.fetchall()
                for pid in pid_data:
                    assert pid["status"] == "R"


def verify_forbidden(response, count=None, index=None, indices=None, target_ids=None, item_ids=None):
    """Verify that the response indicates a forbidden access with the expected message.

    Args:
        response(Response): Response object from the request.
        count(int, optional): Expected count of indices.
        index(dict, optional): Expected index data.
        indices(list, optional): Expected list of indices.
        target_ids(list, optional): List of target index IDs.
        item_ids(list, optional): List of item IDs.
    """
    expected_response = {
        "message": "You don't have the permission to access the requested resource. "
            "It is either read-protected or not readable by the server.",
        "status": 403,
    }
    assert response.json() == expected_response

    if count is not None:
        verify_count(count)
    if index is not None:
        verify_index(index)
    if indices is not None:
        verify_indices(indices)

    if target_ids is not None and item_ids is not None:
        with closing(connect_db()) as conn:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                index_query = "SELECT is_deleted FROM index WHERE id IN %s;"
                cursor.execute(index_query, (tuple(target_ids),))
                index_data = cursor.fetchall()
                for data in index_data:
                    assert data["is_deleted"] == False

                pid_query = "SELECT status FROM pidstore_pid WHERE pid_type = 'recid' AND pid_value IN %s;"
                cursor.execute(pid_query, (tuple([str(id) for id in item_ids]),))
                pid_data = cursor.fetchall()
                for pid in pid_data:
                    assert pid["status"] == "R"


def verify_forbidden_html(response, language, map_groups={}):
    """Verify that the response indicates a 'Forbidden' error.

    Args:
        response(Response): The response object to check.
        language(str): The expected language of the error message.
        map_groups(dict, optional): Dictionary containing group mapping information for verification. Defaults to {}.
    """
    permisssion_required_messages = {
        "en": "Permission required",
        "ja": "権限が必要です",
    }
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.find('h1')
    assert h1.text.endswith(permisssion_required_messages[language])

    if map_groups:
        with closing(connect_db()) as conn:
            with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
                if map_groups.get("add"):
                    role_query = "SELECT id FROM accounts_role WHERE name IN %s;"
                    cursor.execute(role_query, (tuple(map_groups["add"]),))
                    added_roles = cursor.fetchall()
                    assert len(added_roles) == 0
                elif map_groups.get("delete"):
                    deleted_roles_ids = json.loads(map_groups["delete"])
                    role_query = "SELECT id FROM accounts_role WHERE id IN %s;"
                    cursor.execute(role_query, (tuple(deleted_roles_ids),))
                    deleted_roles = cursor.fetchall()
                    assert len(deleted_roles) == len(deleted_roles_ids)


def verify_internal_server_error(response, count=None, index=None, indices=None):
    """Verify that the response indicates an internal server error with the expected message.

    Args:
        response(Response): Response object from the request.
        count(int, optional): Expected count of indices.
        index(dict, optional): Expected index data.
        indices(list, optional): Expected list of indices.
    """
    expected_response = {
        "message": "The server encountered an internal error and was unable "
            "to complete your request. Either the server is overloaded or "
            "there is an error in the application.",
        "status": 500,
    }
    assert response.json() == expected_response

    if count is not None:
        verify_count(count)
    if index is not None:
        verify_index(index)
    if indices is not None:
        verify_indices(indices)


def verify_internal_server_error_html(response):
    """Verify that the response indicates an internal server error in HTML format.

    Args:
        response(Response): Response object from the request.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.find('h1')
    assert h1.text.endswith("Internal server error")


def verify_count(count):
    """Verify the count of indices in the database.

    Args:
        count(int): Expected count of indices.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM index;")
            actual_count = cursor.fetchone()[0]
            assert actual_count == int(count)


def verify_index(index):
    """Verify the index data in the database.

    Args:
        index (dict): Expected index data.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            index = json.loads(str(index))
            replaced_index = {}
            for k, v in index.items():
                if isinstance(v, str):
                    try:
                        replaced_index[k] = datetime.fromisoformat(v)
                    except ValueError:
                        replaced_index[k] = v
                else:
                    replaced_index[k] = v
            cursor.execute("SELECT * FROM index WHERE id = %s;", (index["id"],))
            index_data = cursor.fetchone()
            assert index_data == replaced_index


def verify_indices(indices):
    """Verify the list of indices in the database.

    Args:
        indices(list): Expected list of indices.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=RealDictCursor)) as cursor:
            expected_indices = json.loads(str(indices))
            replaced_indices = []
            for index in expected_indices:
                replaced_index = {}
                for k, v in index.items():
                    if isinstance(v, str):
                        try:
                            replaced_index[k] = datetime.fromisoformat(v)
                        except ValueError:
                            replaced_index[k] = v
                    else:
                        replaced_index[k] = v
                replaced_indices.append(replaced_index)
            cursor.execute("SELECT * FROM index ORDER BY id;")
            index_data = cursor.fetchall()
            assert index_data == replaced_indices

def verify_import(response, role=None, code=None, index=None, result={}):
    """Verify the import response based on the expected status code and index data.

    Args:
        response(Response): Response object from the import request.
        role(str, optional): The role of the user performing the import. Defaults to None.
        code(int, optional): Expected status code of the response. If None, the function will check the overall import result. Defaults to None.
        index(dict, optional): Expected index data for verification. Defaults to None.
        result(dict, optional): Dictionary to store the import result for each role. Defaults to {}

    Returns:
        Box: A Box object containing the import result for each role if code is provided, otherwise
             it will assert the overall import result and print any errors.
    """
    if result:
        result = json.loads(str(result))

    if code is not None:
        role_result = {
            "status": "",
            "error": "",
        }
        try:
            if code == 200:
                verify_edit_during_import(response, index)
            elif code == 401:
                verify_unauthorized(response, index=index)
            elif code == 403:
                verify_forbidden(response, index=index)

            role_result["status"] = "success"
        except AssertionError as e:
            role_result["status"] = "failed"
            role_result["error"] = str(e)
        result[role] = role_result
        return Box({'import_result': json.dumps(result)})
    else:
        is_success = True
        for r in result:
            if result[r]["status"] == "failed":
                is_success = False
                print(f"Role: {r}, Error: {result[r]['error']}")
        assert is_success == True
