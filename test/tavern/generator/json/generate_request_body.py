import argparse
import copy
import json
import os
import random
import sys
import time
from datetime import datetime
from contextlib import closing

from psycopg2.extras import DictCursor

sys.path.append(os.path.abspath(os.getcwd()))

from helper.common.connect_helper import connect_db

VALUE_ANNOTATION = "@value"
ATTRIBUTES_ANNOTATION = "@attributes"
MAPPING_DIR_BASE = "request_params/item_type_mapping"

def remove_xsd_prefix(jpcoar_lists):
    """Remove prefixes from jpcoar mapping type schemas.

    Args:
        jpcoar_lists(dict): The original jpcoar mapping type schemas with prefixes.

    Returns:
        dict: A new dictionary with prefixes removed from the keys.
    """
    def remove_prefix(jpcoar_src, jpcoar_dst):
        """Recursively remove prefixes from the keys in the jpcoar mapping type schemas.

        Args:
            jpcoar_src(dict): The source dictionary with prefixes.
            jpcoar_dst(dict): The destination dictionary to store the results without prefixes.
        """
        for key, value in jpcoar_src.items():
            if key == 'type':
                jpcoar_dst[key] = value
                continue
            new_key = key.split(':').pop()
            jpcoar_dst[new_key] = {}
            if isinstance(value, dict):
                remove_prefix(value, jpcoar_dst[new_key])

    jpcoar_copy = {}
    remove_prefix(jpcoar_lists, jpcoar_copy)
    return jpcoar_copy


def get_db_json(table, columns, where=None):
    """Fetch JSON data from the database.

    Args:
        table(str): The name of the database table to query.
        columns(str or list): The column name(s) to retrieve.
            Can be a single column name as a string or a list of column names.
        where(str, optional): An optional WHERE clause to filter the query results.
            Defaults to None.

    Returns:
        dict or list: Fetched JSON data.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor(cursor_factory=DictCursor)) as cur:
            if isinstance(columns, list):
                col_str = ", ".join(columns)
            else:
                col_str = columns
            query = f"SELECT {col_str} FROM {table}"
            if where:
                query += f" WHERE {where}"
            cur.execute(query)
            rows = cur.fetchall()

    if not rows:
        return None
    if len(rows) == 1:
        row = rows[0]
        if isinstance(columns, str) and ',' not in columns and not isinstance(columns, list):
            data = row[columns]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    pass
            return data
        return dict(row)
    else:
        return [dict(r) for r in rows]


def get_property_keys(schema):
    """Get property keys from item schema.

    Args:
        schema(dict): Item schema.

    Returns:
        dict: Property keys with list of keys for each property.
    """
    def collect_keys(prop, prefix=""):
        """Recursively collect keys from schema property.

        Args:
            prop(dict): Schema property to collect keys from.
            prefix(str, optional): Prefix to add to the keys for nested properties. Defaults to "".

        Returns:
            list: A list of keys collected from the schema property, with prefixes for nested properties.
        """
        keys = []
        if prop.get("type") == "object" and "properties" in prop:
            for k, v in prop["properties"].items():
                keys.extend(collect_keys(v, f"{prefix}{k}." if prefix else f"{k}."))
        elif prop.get("type") == "array" and "items" in prop:
            items = prop["items"]
            if items.get("type") in ("object", "array"):
                keys.extend(collect_keys(items, prefix))
            else:
                keys.append(prefix[:-1] if prefix.endswith('.') else prefix)
        else:
            keys.append(prefix[:-1] if prefix.endswith('.') else prefix)
        return keys

    result = {}
    properties = schema.get("properties", {})
    for prop_name, prop_value in properties.items():
        if prop_name == "pubdate":
            result[prop_name] = [prop_name]
        else:
            result[prop_name] = collect_keys(prop_value)
    return result


def find_attribute_leaves(node, path=()):
    """Find leaf nodes that have attributes anywhere in the schema.

    Args:
        node(dict): Current node in schema.
        path(tuple, optional): Current path of keys. Defaults to ().

    Returns:
        list: List of tuples (leaf_path, attribute_names).
    """
    def get_attr_names(n):
        """Get attribute names for a given node.

        Args:
            n(dict): Node to get attribute names from.

        Returns:
            list: List of attribute names for the node.
        """
        if not isinstance(n, dict):
            return []
        names = []
        attrs = n.get("attributes", [])
        names += [attr.get("name") for attr in attrs
                  if isinstance(attr, dict) and "name" in attr]
        if "type" in n and isinstance(n["type"], dict):
            names += get_attr_names(n["type"])
        return names

    leaves = []
    if not isinstance(node, dict):
        return []
    keys = [k for k in node.keys() if k != "type"]
    if not keys:
        attr_names = get_attr_names(node)
        if attr_names:
            leaves.append((path, attr_names))
        return leaves
    for k in keys:
        val = node[k]
        if isinstance(val, dict):
            leaves.extend(find_attribute_leaves(val, path + (k,)))
    return leaves


def add_empty_mappings(mapping_item):
    """Add empty string mappings for fixed mapping types.

    Args:
        mapping_item(dict): Mapping item to add empty mappings to.
    """
    mapping_item["display_lang_type"] = ""
    mapping_item["junii2_mapping"] = ""
    mapping_item["lido_mapping"] = ""
    mapping_item["spase_mapping"] = ""


def save_body(body, output_dir, output_file_name):
    """Save body to JSON file.

    Args:
        body(dict): Body to save.
        output_dir(str): Output directory.
        output_file_name(str): Output file name.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    base_name, ext = os.path.splitext(output_file_name)
    if not base_name.endswith("_1"):
        base_name += "_1"
    output_file_name = base_name + ext
    output_path = os.path.join(output_dir, output_file_name)
    idx = 2
    while os.path.exists(output_path):
        output_path = os.path.join(output_dir, f"{base_name[:-2]}_{idx}{ext}")
        idx += 1
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, indent=2)


def set_nested_mapping(mapping_dict, leaf_node, value, attr_dict=None):
    """Set value and attributes in nested mapping dict.

    Args:
        mapping_dict(dict): Mapping dictionary to set values in.
        leaf_node(str): Dot-separated path to the leaf node.
        value(str): Value to set at the leaf node.
        attr_dict(dict, optional): Optional attributes to set at the leaf node.
    """
    keys = leaf_node.split('.')
    current_dict = mapping_dict
    for k in keys[:-1]:
        current_dict = current_dict.setdefault(k, {})
    current_dict[keys[-1]] = {VALUE_ANNOTATION: value}
    if attr_dict:
        current_dict[keys[-1]][ATTRIBUTES_ANNOTATION] = attr_dict


def build_schema_list(schema_mt):
    """Build schema list from mapping type schema.

    Args:
        schema_mt(dict): Mapping type schema.

    Returns:
        list: List of tuples (leaf_path, attribute_names).
    """
    leaves = find_attribute_leaves(schema_mt)
    result = []
    for leaf, attr_names in leaves:
        result.append((".".join(leaf), attr_names))
    return result


def build_schema_leaf_attr_list(schema_mt):
    """Build schema leaf attribute list from mapping type schema.

    Args:
        schema_mt(dict): Mapping type schema.

    Returns:
        list: List of tuples (leaf_path, attribute_name).
    """
    leaves = find_attribute_leaves(schema_mt)
    result = []
    for leaf, attr_names in leaves:
        leaf_path = ".".join(leaf)
        result.append((leaf_path, VALUE_ANNOTATION))
        for attr in attr_names:
            result.append((leaf_path, attr))
    return result


def create_all_schema_mappings(
        required_types,
        mapping_type_schemas,
        db_item_keys,
        property_keys,
        item_type_id,
        output_dir
    ):
    """Create mapping body test files covering all schema leaves.

    Args:
        required_types(list): List of mapping types
        mapping_type_schemas(dict): Mapping type schemas
        db_item_keys(list): Item keys from database
        property_keys(dict): Property keys
        item_type_id(int): Item type ID
        output_dir(str): Output directory
    """
    for mapping_type in required_types:
        schema_mt = mapping_type_schemas.get(mapping_type)
        if not schema_mt:
            continue
        schema_leaf_attr_list = build_schema_leaf_attr_list(schema_mt)
        schema_leaf_attr_copy = schema_leaf_attr_list.copy()
        file_idx = 1

        while schema_leaf_attr_copy:
            mapping = {}
            for item in db_item_keys:
                value_keys = property_keys.get(item, [])
                mapping_dict = {}
                v_idx = 0
                schema_leaf_attr_inner = schema_leaf_attr_copy.copy()
                for leaf_path, attr in schema_leaf_attr_inner:
                    if v_idx >= len(value_keys):
                        break
                    keys = leaf_path.split('.')
                    current_dict = mapping_dict
                    for k in keys[:-1]:
                        current_dict = current_dict.setdefault(k, {})
                    if attr == VALUE_ANNOTATION:
                        current_dict[keys[-1]] = current_dict.get(keys[-1], {})
                        current_dict[keys[-1]][VALUE_ANNOTATION] = value_keys[v_idx]
                    else:
                        current_dict[keys[-1]] = current_dict.get(keys[-1], {})
                        current_dict[keys[-1]].setdefault(ATTRIBUTES_ANNOTATION, {})
                        current_dict[keys[-1]][ATTRIBUTES_ANNOTATION][attr] = value_keys[v_idx]
                    v_idx += 1
                    schema_leaf_attr_copy.pop(0)
                    if not schema_leaf_attr_copy:
                        break
                mapping[item] = {mt: "" for mt in required_types}
                mapping[item][mapping_type] = mapping_dict if mapping_dict else ""
                add_empty_mappings(mapping[item])

            body = {
                "item_type_id": item_type_id,
                "mapping": mapping,
                "mapping_type": mapping_type
            }
            save_body(body, output_dir, f"mapping_all_schemalist_{mapping_type}.json")


def create_duplicate_metadata(current_dict, mapping_type):
    """Function to generate a mapping that causes a duplication error.

    Args:
        current_dict(dict): Current mapping dictionary.
        mapping_type(str): Mapping type.

    Returns:
        dict: New mapping dictionary with duplication.
    """
    def get_leaf_keys(d, parent_path=""):
        """Recursively get leaf keys from a nested dictionary.

        Args:
            d(dict): The dictionary to search for leaf keys.
            parent_path(str, optional): The path to the current dictionary. Defaults to "".

        Returns:
            list: A list of leaf keys in the format "key1.key2.key3".
        """
        leaf_keys = []
        for key, value in d.items():
            current_path = f"{parent_path}.{key}" if parent_path else key
            if isinstance(value, dict):
                leaf_keys.extend(get_leaf_keys(value, current_path))
            else:
                leaf_keys.append(current_path)
        return leaf_keys

    def delete_key_by_path(d, path):
        """Delete a key from a nested dictionary by its path.

        Args:
            d(dict): The dictionary to delete the key from.
            path(str): The path to the key in the format "key1.key2.key3".
        """
        keys = path.split('.')
        for key in keys[:-1]:
            d = d.get(key, {})
        del d[keys[-1]]

    if not isinstance(current_dict, dict):
        return current_dict
    new_dict = copy.deepcopy(current_dict)
    target_dict = new_dict[mapping_type]
    if isinstance(target_dict, dict):
        leaf_keys = get_leaf_keys(target_dict)
        delete_key_by_path(target_dict, random.choice(leaf_keys))
    new_dict[mapping_type] = target_dict
    return new_dict

def create_mapping_body(
        required_types,
        mapping_type_schemas,
        db_item_keys,
        property_keys,
        item_type_id,
        output_dir,
        mode="random",
        same_item_keys=[]
    ):
    """Create mapping body test files.

    Args:
        required_types(list): list of mapping types
        mapping_type_schemas(dict): mapping type schemas
        db_item_keys(list): item keys from database
        property_keys(dict): property keys
        item_type_id(int): item type ID
        output_dir(str): output directory
        mode(str, optional): "random" or "duplicate". Defaults to "random".
        same_item_keys(list, optional): list of item keys to duplicate in "duplicate" mode. Defaults to [].
    """
    file_name = "success"
    if mode == 'duplicate':
        file_name = mode

    # for each mapping_type, output a file
    for output_mapping_type in required_types:
        duplicated_key = None
        mapping = {}
        # Prepare a set of used schemas for each mapping_type (to prevent unexpected duplicates)
        used_leaves_global = {mt: set() for mt in required_types}
        for item in db_item_keys:
            value_keys = property_keys.get(item, [])
            if item in same_item_keys and mode == 'duplicate':
                if duplicated_key is None:
                    duplicated_key = item
                else:
                    duplicate_copy = copy.deepcopy(mapping[duplicated_key])
                    mapping[item] = create_duplicate_metadata(duplicate_copy, output_mapping_type)
                    if mapping[item] is None:
                        mapping[item] = ""
                    continue
            mapping[item] = {}
            for mapping_type in required_types:
                schema_mt = mapping_type_schemas.get(mapping_type)
                if not schema_mt:
                    mapping[item][mapping_type] = ""
                    continue
                schema_list = build_schema_list(schema_mt)
                schema_list_copy = schema_list.copy()
                random.shuffle(schema_list_copy)
                mapping_dict = {}
                v_idx = 0
                # Track used schema leaves to avoid duplicates per mapping_type
                used_leaves = used_leaves_global[mapping_type]
                used_leaves = used_leaves_global[mapping_type]
                for _ in range(len(value_keys)):
                    available_leaves = [s for s in schema_list_copy if s[0] not in used_leaves]
                    if not available_leaves:
                        break
                    leaf_node, attr_names = random.choice(available_leaves)
                    used_leaves.add(leaf_node)
                    if attr_names and (len(value_keys) - v_idx) >= len(attr_names) + 1:
                        attr_dict = {}
                        for i, attr in enumerate(attr_names):
                            attr_dict[attr] = value_keys[v_idx + i + 1]
                        set_nested_mapping(mapping_dict, leaf_node, value_keys[v_idx], attr_dict)
                        v_idx += len(attr_names) + 1
                    else:
                        set_nested_mapping(mapping_dict, leaf_node, value_keys[v_idx])
                        v_idx += 1
                    if v_idx >= len(value_keys):
                        break
                mapping[item][mapping_type] = mapping_dict if mapping_dict else ""
            add_empty_mappings(mapping[item])

        body = {
            "item_type_id": item_type_id,
            "mapping": mapping,
            "mapping_type": output_mapping_type
        }
        save_body(body, output_dir, f"mapping_{file_name}_{output_mapping_type}.json")


def create_mapping_body_continue(required_types, mapping_type_schemas, continue_file):
    """Create mapping body test files that continue from a given file.

    Args:
        required_types(list): list of mapping types
        mapping_type_schemas(dict): mapping type schemas
        continue_file(str): path to the continue file

    Returns:
        dict: Updated mapping type schemas with used attributes removed based on the continue file.
    """
    def check_and_remove_used_attributes(schema, data, parent_key=None):
        """Recursively check the schema against the data and remove used attributes from the schema.

        Args:
            schema(dict): The schema to check and remove attributes from.
            data(dict): The data to check against the schema.
            parent_key(str, optional): The parent key path for nested schemas. Defaults to None.

        Returns:
            dict: The updated schema with used attributes removed.
        """
        edited_schema = copy.deepcopy(schema)
        for key, value in schema.items():
            if key == "type":
                continue
            if parent_key:
                full_key = f"{parent_key}.{key}"
            else:
                full_key = key
            if full_key not in data:
                edited_schema[key] = check_and_remove_used_attributes(value, data, full_key)
            else:
                attribute = value["type"]["attributes"]
                edited_attribute = []
                for attr in attribute:
                    if attr["name"] in data[full_key][ATTRIBUTES_ANNOTATION]:
                        edited_attribute.append(attr)
                edited_schema[key]["type"]["attributes"] = edited_attribute
        return edited_schema

    with open(os.path.join(MAPPING_DIR_BASE, "save_data", continue_file), "r", encoding="utf-8") as f:
        continue_data = json.load(f)
    for mapping_type in required_types:
        mapping_type_schemas[mapping_type] = check_and_remove_used_attributes(
            mapping_type_schemas[mapping_type], continue_data[mapping_type])
    return mapping_type_schemas


def create_error_files(required_types, item_type_id, output_dir):
    """Create error test files.

    Args:
        required_types(list): list of mapping types
        item_type_id(int): item type ID
        output_dir(str): output directory
    """
    # item_type_id is invalid (string, null)
    for special_id in ["abc", "null"]:
        for mapping_type in required_types:
            body = {
                "item_type_id": None if special_id == "null" else special_id,
                "mapping": {},
                "mapping_type": mapping_type
            }
            save_body(body, output_dir, f"mapping_{special_id}_{mapping_type}.json")

    # missing id key
    for mapping_type in required_types:
        body_noid = {
            "mapping": {},
            "mapping_type": mapping_type
        }
        save_body(body_noid, output_dir, f"mapping_noid_{mapping_type}.json")

    duplicate_output_dir = output_dir.replace("error", "duplicate")
    mapping = {}
    if os.path.exists(duplicate_output_dir):
        duplicate_files = [f for f in os.listdir(duplicate_output_dir) if f.endswith(".json")]
        if duplicate_files:
            with open(os.path.join(duplicate_output_dir, duplicate_files[0]), "r", encoding="utf-8") as f:
                duplicate_data = json.load(f)
            mapping = duplicate_data.get("mapping", {})
    # missing mapping_type key
    body_noid = {
        "item_type_id": item_type_id,
        "mapping": mapping
    }
    save_body(body_noid, output_dir, f"mapping_no_mapping_type.json")


def parse_args():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate request body test files.")
    parser.add_argument("item_type_id", type=int, help="target item_type_id")
    parser.add_argument(
        "-m", "--meta_ids", nargs=2, help="metadata IDs to duplicate", default=[])
    parser.add_argument(
        "-l", "--loop_count", type=int, help="number of files to generate", default=1)
    parser.add_argument(
        "-c", "--continue", dest="continue_flag", action="store_true",
        help="generate using unused data from previous run", default=False)
    return parser.parse_args()

def main():
    """
    Main function to generate request body test files.
    Usage: python generate_request_body.py <item_type_id> [meta_id1 meta_id2]
    """
    args = parse_args()
    item_type_id = args.item_type_id
    meta_ids = args.meta_ids
    loop_count = args.loop_count
    is_continue = args.continue_flag
    print(f"item_type_id: {item_type_id}, meta_ids: {meta_ids}, "
          f"loop_count: {loop_count}, continue: {is_continue}")

    start_time = time.time()
    print(f"テストデータ生成開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    total_files_before = count_json_files(os.path.join(MAPPING_DIR_BASE, "test_data"))

    required_types = ["ddi_mapping", "lom_mapping", "jpcoar_v1_mapping", "jpcoar_mapping", "oai_dc_mapping"]
    test_roles = ["sysadmin", "repoadmin", "comadmin", "contributor", "user", "guest"]

    exists = get_db_json("item_type", "id", f"id = {item_type_id}")
    if not exists:
        print(f"Error: item_type_id {item_type_id} does not exist in item_type table.")
        sys.exit(1)

    schemas_raw = get_db_json("oaiserver_schema", ["xsd", "schema_name"])
    mapping_type_schemas = {}
    if schemas_raw:
        for row in schemas_raw:
            mapping_type = row.get("schema_name")
            xsd = row.get("xsd")
            if isinstance(xsd, str):
                xsd = json.loads(xsd)
            mapping_type_schemas[mapping_type] = remove_xsd_prefix(xsd)

    schema = get_db_json("item_type", "schema", f"id = {item_type_id}")
    property_keys = get_property_keys(schema)

    # Metadata ID List
    mapping_raw = get_db_json("item_type_mapping", "mapping", f"item_type_id = {item_type_id}")
    if not mapping_raw:
        raise Exception(f"mapping not found for item_type_id={item_type_id}")
    while isinstance(mapping_raw, list):
        if not mapping_raw:
            raise Exception(f"mapping is empty for item_type_id={item_type_id}")
        mapping_raw = mapping_raw[0]
    if isinstance(mapping_raw, dict) and "mapping" in mapping_raw:
        mapping_raw = mapping_raw["mapping"]

    # Organize Metadata ID List
    def set_db_keys(k):
        if k == "pubdate":
            return (0, "")
        elif k == "system_file":
            return (1, k)
        elif k.startswith("system_identifier"):
            return (2, k)
        elif k.startswith("item_"):
            # Sort by numerical part in ascending order
            try:
                num = int(k.split("_")[1])
            except Exception:
                num = 0
            return (3, num)
        else:
            return (4, k)
    db_item_keys = sorted(list(mapping_raw.keys()), key=set_db_keys)
    if meta_ids and len(meta_ids) == 2:
        db_item_keys = [id for id in meta_ids if id in db_item_keys] + [k for k in db_item_keys if k not in meta_ids]

    for role in test_roles:
        print(f"{role}のテストデータの生成を開始します。")
        # Generate valid data using all schema lists
        output_dir = os.path.join(MAPPING_DIR_BASE, "test_data", role, "all_schema_mappings")
        create_all_schema_mappings(required_types, mapping_type_schemas, db_item_keys, property_keys, item_type_id, output_dir)

        # Generate JSON data that will succeed (values are random and do not overlap with others)
        output_dir = os.path.join(MAPPING_DIR_BASE, "test_data", role, "success")
        if is_continue:
            save_data_file = sorted([f for f in os.listdir(os.path.join(MAPPING_DIR_BASE, "save_data")) 
                                     if f.startswith(f"unused_schema_{item_type_id}_{role}_") and f.endswith(".json")], reverse=True)
            mapping_type_schemas = create_mapping_body_continue(required_types, mapping_type_schemas, save_data_file[0])
        for _ in range(loop_count):
            create_mapping_body(
                required_types, mapping_type_schemas, db_item_keys, property_keys,
                item_type_id, output_dir, mode="random"
            )

        # Generate JSON data with duplicate metadata IDs (values other than specified metadata are random and do not overlap)
        if meta_ids and len(meta_ids) == 2:
            output_dir = os.path.join(MAPPING_DIR_BASE, "test_data", role, "duplicate")
            same_item_keys = sorted(meta_ids, reverse=False)
            create_mapping_body(required_types, mapping_type_schemas, db_item_keys,
                                property_keys, item_type_id, output_dir, mode="duplicate", 
                                same_item_keys=same_item_keys)
        else:
            print("メタデータIDの指定が不正です。重複エラー用のテストデータは生成しません。")

        # Generate test files for error cases
        output_dir = os.path.join(MAPPING_DIR_BASE, "test_data", role, "error")
        create_error_files(required_types, item_type_id, output_dir)
        print(f"{role}のテストデータの生成が終了しました。")

    total_files_after = count_json_files(os.path.join(MAPPING_DIR_BASE, "test_data"))
    elapsed = time.time() - start_time
    print(f"テストデータ生成終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"所要時間: {int(elapsed // 60)}分 {int(elapsed % 60)}秒")
    print(f"生成したJSONファイル数: {total_files_after - total_files_before}件")

def count_json_files(root_dir):
    """Count the number of JSON files in a directory and its subdirectories.

    Args:
        root_dir(str): The root directory to start counting from.

    Returns:
        int: The total count of JSON files found.
    """
    count = 0
    for _, _, filenames in os.walk(root_dir):
        count += sum(1 for f in filenames if f.endswith('.json'))
    return count

if __name__ == "__main__":
    main()
