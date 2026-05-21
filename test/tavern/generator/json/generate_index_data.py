import argparse
import copy
import json
import os
import random
import string
import sys
from datetime import datetime, timedelta
from contextlib import closing

sys.path.append(os.path.abspath(os.getcwd()))

from helper.common.connect_helper import connect_db

EMPTY_TARGET_COLUMNS = ["index_name", "index_name_english"]

class Group:
    def __init__(self, id, name):
        """Initialize a Group instance.

        Args:
            id(int): Group ID.
            name(str): Group name.
        """
        self.id = id
        self.name = name

    def to_dict(self):
        """Convert the Group instance to a dictionary.

        Returns:
            dict: Dictionary representation of the Group.
        """
        return {
            "id": self.id,
            "name": self.name
        }


class Role:
    def __init__(self, id, name):
        """Initialize a Role instance.

        Args:
            id(int): Role ID.
            name(str): Role name.
        """
        self.id = id
        self.name = name

    def to_dict(self):
        """Convert the Role instance to a dictionary.

        Returns:
            dict: Dictionary representation of the Role.
        """
        return {
            "id": self.id,
            "name": self.name
        }


class Index:
    def __init__(self, id, parent, position):
        """Initialize an Index instance.

        Args:
            id(int): Index ID.
            parent(int): Parent index ID.
            position(int): Position of the index.
        """
        self.id = id
        self.parent = parent
        self.position = position

    def to_dict(self):
        """Convert the Index instance to a dictionary.

        Returns:
            dict: Dictionary representation of the Index.
        """
        return {
            "id": self.id,
            "parent": self.parent,
            "position": self.position
        }


def get_groups():
    """Retrieve groups from the database.

    Returns:
        list[Group]: List of Group instances.
    """
    groups = []
    query = "SELECT id, name FROM accounts_group;"
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(query)
            result = cur.fetchall()
    for g in result:
        groups.append(Group(g[0], g[1]))
    return groups


def get_roles():
    """Retrieve roles from the database.

    Returns:
        list[Role]: List of Role instances.
    """
    roles = []
    query = "SELECT id, name FROM accounts_role;"
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(query)
            result = cur.fetchall()
    for r in result:
        roles.append(Role(r[0], r[1]))

    # Add predefined roles
    roles.append(Role(-98, "Authenticated User"))
    roles.append(Role(-99, "Guest"))
    return roles


def get_indices():
    """Retrieve indices from the database.

    Returns:
        list[Index]: List of Index instances.
    """
    indices = []
    query = "SELECT id, parent, position FROM index;"
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(query)
            result = cur.fetchall()
    for i in result:
        indices.append(Index(i[0], i[1], i[2]))
    return indices


def set_groups_to_template(groups):
    """Assign groups to allow or deny lists in the template.

    Args:
        groups(list[Group]): List of Group instances.

    Returns:
        dict: Dictionary with allow and deny lists.
    """
    set_value = {
        "allow": [],
        "deny": []
    }
    for group in groups:
        if random.choice([True, False]):
            set_value["allow"].append(group.to_dict())
        else:
            set_value["deny"].append(group.to_dict())
    return set_value


def set_roles_to_template(roles):
    """Assign roles to allow or deny lists in the template.

    Args:
        roles(list[Role]): List of Role instances.

    Returns:
        dict: Dictionary with allow and deny lists.
    """
    super_role = ["System Administrator", "Repository Administrator"]
    set_value = {
        "allow": [],
        "deny": []
    }
    for role in roles:
        if role.name in super_role:
            continue
        if random.choice([True, False]):
            set_value["allow"].append(role.to_dict())
        else:
            set_value["deny"].append(role.to_dict())
    return set_value


def set_index_to_template(indices, is_community, recursive):
    """Select an index for the template.

    Args:
        indices(list[Index]): List of Index instances.
        recursive(bool): Whether to consider recursive indices.
        is_community(bool): Whether the index is for a community.

    Returns:
        dict: Dictionary representation of the selected index.
    """
    target_indices = []
    community_indices = []
    no_community_indices = []
    for index in indices:
        if index.id == 1:
            community_indices.append(index)
        else:
            community_indices_ids = [i.id for i in community_indices]
            if index.parent in community_indices_ids:
                community_indices.append(index)
            else:
                no_community_indices.append(index)

    loop_indices = []
    if is_community is None:
        loop_indices = indices
    elif is_community:
        loop_indices = community_indices
    else:
        loop_indices = no_community_indices

    if recursive:
        for index in loop_indices:
            if [i for i in indices if i.parent == index.id]:
                target_indices.append(index)
    else:
        target_indices = loop_indices
    target_index = random.choice(target_indices)
    return {
        "id": target_index.id,
        "parent": target_index.parent,
        "position": target_index.position
    }

def set_gakunin_groups(browsing_role, contribute_role):
    """Separate Gakunin groups from roles.

    Args:
        browsing_role(dict): Browsing role data.
        contribute_role(dict): Contribute role data.

    Returns:
        dict: Dictionary with separated Gakunin groups.
    """
    def is_gakunin_group(role_name):
        """Check if the role name corresponds to a Gakunin group.

        Args:
            role_name(str): Name of the role.

        Returns:
            bool: True if it is a Gakunin group, False otherwise.
        """
        return role_name.startswith("jc_") and role_name.find("groups") != -1

    allow_browsing_role = []
    deny_browsing_role = []
    allow_contribute_role = []
    deny_contribute_role = []
    allow_browsing_group = []
    deny_browsing_group = []
    allow_contribute_group = []
    deny_contribute_group = []
    for role in browsing_role["allow"]:
        if is_gakunin_group(role["name"]):
            allow_browsing_group.append({
                "id": str(role["id"]) + "gr",
                "name": role["name"]
            })
        else:
            allow_browsing_role.append(role)
    for role in browsing_role["deny"]:
        if is_gakunin_group(role["name"]):
            deny_browsing_group.append({
                "id": str(role["id"]) + "gr",
                "name": role["name"]
            })
        else:
            deny_browsing_role.append(role)
    for role in contribute_role["allow"]:
        if is_gakunin_group(role["name"]):
            allow_contribute_group.append({
                "id": str(role["id"]) + "gr",
                "name": role["name"]
            })
        else:
            allow_contribute_role.append(role)
    for role in contribute_role["deny"]:
        if is_gakunin_group(role["name"]):
            deny_contribute_group.append({
                "id": str(role["id"]) + "gr",
                "name": role["name"]
            })
        else:
            deny_contribute_role.append(role)
    return {
        "browsing_group": {
            "allow": allow_browsing_group,
            "deny": deny_browsing_group
        },
        "contribute_group": {
            "allow": allow_contribute_group,
            "deny": deny_contribute_group
        },
        "browsing_role": {
            "allow": allow_browsing_role,
            "deny": deny_browsing_role
        },
        "contribute_role": {
            "allow": allow_contribute_role,
            "deny": deny_contribute_role
        }
    }


def generate_index_data(indices, is_community=None, recursive = False):
    """Generate index data based on the template.

    Args:
        indices(list[Index]): List of Index instances.
        is_community(bool, optional): Whether to generate data for community index. Defaults to None.
        recursive(bool, optional): Whether to generate recursive index data. Defaults to False.

    Returns:
        dict: Generated index data.
    """
    file = "generator/json/template_file/index_template.json"
    generated_data = {}
    groups = get_groups()
    roles = get_roles()
    with open(file, "r") as f:
        data = json.load(f)
    for k, v in data.items():
        if v == "str":
            length = random.randint(5, 15)
            generated_data[k] = "".join(random.choices(string.ascii_letters, k=length))
        elif v == "int":
            generated_data[k] = random.randint(1, 100)
        elif v == "bool":
            generated_data[k] = random.choice([True, False])
        elif v == "date":
            today = datetime.now()
            one_month_ago = today - timedelta(days=30)
            one_month_later = today + timedelta(days=30)
            random_date = one_month_ago + (one_month_later - one_month_ago) * random.random()
            generated_data[k] = random_date.strftime("%Y%m%d")
        elif v == "Group":
            generated_data[k] = set_groups_to_template(groups)
        elif v == "Role":
            generated_data[k] = set_roles_to_template(roles)

    generated_data.update(set_index_to_template(indices, is_community, recursive))
    generated_data.update(set_gakunin_groups(
        generated_data["browsing_role"],
        generated_data["contribute_role"]
    ))

    return generated_data


def main(start_index, end_index):
    """Main function to generate index data JSON files.

    Args:
        start_index(int): Starting index ID for data generation.
        end_index(int): Ending index ID for data generation.
    """
    index_data = {
        "biblio_flag": False,
        "image_name": "",
        "is_deleted": False,
        "recursive_browsing_group": False,
        "recursive_browsing_role": False,
        "recursive_contribute_group": False,
        "recursive_contribute_role": False,
        "recursive_coverpage_check": False,
        "recursive_public_state": False,
        "thumbnail_delete_flag": False
    }
    output_folder = "request_params/index/test_data"
    indices = get_indices()
    users = {
        "sysadmin": 1,
        "repoadmin": 2,
        "comadmin": 5,
        "contributor": 3,
        "user": 4,
        "guest": 0
    }
    for user, user_id in users.items():
        if not os.path.exists(f"{output_folder}/{user}"):
            os.makedirs(f"{output_folder}/{user}")

        if start_index is not None and end_index is not None:
            indices = [index for index in indices if start_index <= index.id <= end_index]
            for index in indices:
                generated_data = copy.deepcopy(index_data)
                generated_data.update(generate_index_data([index]))
                generated_data["owner_user_id"] = user_id
                with open(f"{output_folder}/{user}/generated_index_data_{index.id}.json", "w") as f:
                    json.dump(generated_data, f, indent=4)
        else:
            for index in indices:
                generated_data = copy.deepcopy(index_data)
                generated_data.update(generate_index_data([index]))
                generated_data["owner_user_id"] = user_id
                with open(f"{output_folder}/{user}/index_data_{index.id}.json", "w") as f:
                    json.dump(generated_data, f, indent=4)

            recursive_key = [k for k in index_data.keys() if k.startswith("recursive_")] + ["biblio_flag"]
            if user in ["comadmin", "contributor"]:
                for key in recursive_key:
                    generated_recursive_data = copy.deepcopy(index_data)
                    generated_recursive_data[key] = True
                    generated_recursive_data.update(
                        generate_index_data(indices, is_community=True, recursive=True))
                    generated_recursive_data["owner_user_id"] = user_id
                    with open(f"{output_folder}/{user}/index_data_{key}_in_community.json", "w") as f:
                        json.dump(generated_recursive_data, f, indent=4)

                    generated_recursive_data = copy.deepcopy(index_data)
                    generated_recursive_data[key] = True
                    generated_recursive_data.update(
                        generate_index_data(indices, is_community=False, recursive=True))
                    generated_recursive_data["owner_user_id"] = user_id
                    with open(f"{output_folder}/{user}/index_data_{key}_out_community.json", "w") as f:
                        json.dump(generated_recursive_data, f, indent=4)

                for col in EMPTY_TARGET_COLUMNS:
                    # Generate data with empty string for the target column
                    generated_empty_data = copy.deepcopy(index_data)
                    generated_empty_data.update(generate_index_data(indices, is_community=True))
                    generated_empty_data[col] = ""
                    generated_empty_data["owner_user_id"] = user_id
                    with open(f"{output_folder}/{user}/index_data_empty_{col}_in_community.json", "w") as f:
                        json.dump(generated_empty_data, f, indent=4)

                    generated_empty_data[col] = "".join(random.choices(string.ascii_letters, k=1))
                    with open(f"{output_folder}/{user}/index_data_1char_{col}_in_community.json", "w") as f:
                        json.dump(generated_empty_data, f, indent=4)

                    generated_empty_data = copy.deepcopy(index_data)
                    generated_empty_data.update(generate_index_data(indices, is_community=False))
                    generated_empty_data[col] = ""
                    generated_empty_data["owner_user_id"] = user_id
                    with open(f"{output_folder}/{user}/index_data_empty_{col}_out_community.json", "w") as f:
                        json.dump(generated_empty_data, f, indent=4)

                    generated_empty_data[col] = "".join(random.choices(string.ascii_letters, k=1))
                    with open(f"{output_folder}/{user}/index_data_1char_{col}_out_community.json", "w") as f:
                        json.dump(generated_empty_data, f, indent=4)

            else:
                for key in recursive_key:
                    generated_recursive_data = copy.deepcopy(index_data)
                    generated_recursive_data[key] = True
                    generated_recursive_data.update(generate_index_data(indices, recursive=True))
                    generated_recursive_data["owner_user_id"] = user_id
                    with open(f"{output_folder}/{user}/index_data_{key}.json", "w") as f:
                        json.dump(generated_recursive_data, f, indent=4)

                for col in EMPTY_TARGET_COLUMNS:
                    # Generate data with empty string for the target column
                    generated_empty_data = copy.deepcopy(index_data)
                    generated_empty_data.update(generate_index_data(indices))
                    generated_empty_data[col] = ""
                    generated_empty_data["owner_user_id"] = user_id
                    with open(f"{output_folder}/{user}/index_data_empty_{col}.json", "w") as f:
                        json.dump(generated_empty_data, f, indent=4)

                    generated_empty_data[col] = "".join(random.choices(string.ascii_letters, k=1))
                    with open(f"{output_folder}/{user}/index_data_1char_{col}.json", "w") as f:
                        json.dump(generated_empty_data, f, indent=4)


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate index data JSON.")
    parser.add_argument("-s", "--start", type=int, help="Starting index ID")
    parser.add_argument("-e", "--end", type=int, help="Ending index ID")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    start_index = args.start
    end_index = args.end
    main(start_index, end_index)
