import argparse
import datetime
import json
import os
import sys
from contextlib import closing
from psycopg2.extras import DictCursor

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from helper.common.connect_helper import connect_db

VALUE_ANNOTATION = "@value"
ATTRIBUTES_ANNOTATION = "@attributes"
NOT_USED = "[未使用]"
MAPPING_DIR_BASE = "request_params/item_type_mapping"

def remove_xsd_prefix(jpcoar_lists):
    """Remove the 'xsd:' prefix from the keys in the jpcoar schema lists.

    Args:
        jpcoar_lists(dict): The original jpcoar schema lists with 'xsd:' prefixes.

    Returns:
        dict: A copy of the jpcoar schema lists with 'xsd:' prefixes removed.
    """
    def remove_prefix(jpcoar_src, jpcoar_dst):
        """Recursively remove the 'xsd:' prefix from the keys in the jpcoar schema lists.

        Args:
            jpcoar_src (dict): The source dictionary to process.
            jpcoar_dst (dict): The destination dictionary to store the processed keys and values.
        """
        for key, value in jpcoar_src.items():
            if key == 'type':
                jpcoar_dst[key] = value
                continue
            new_key = key.split(":").pop()
            jpcoar_dst[new_key] = {}
            if isinstance(value, dict):
                remove_prefix(value, jpcoar_dst[new_key])

    jpcoar_copy = {}
    remove_prefix(jpcoar_lists, jpcoar_copy)
    return jpcoar_copy

def get_db_json(table, columns, where=None):
    """Retrieve JSON data from the database for the specified table and columns.

    Args:
        table(str): The name of the database table to query.
        columns(str or list): The column name(s) to retrieve.
            Can be a single column name as a string or a list of column names.
        where(str, optional): An optional WHERE clause to filter the query results.

    Returns:
        dict or list: The retrieved data as a dictionary
            if a single row is returned, or a list of dictionaries if multiple rows are returned.
        None: If no rows are found.
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

def find_attribute_leaves(node, path=()):
    """Recursively find leaf nodes in the schema that have @value and @attributes.

    Args:
        node(dict): The current node in the schema to check.
        path(tuple, optional): The path to the current node, used for constructing the leaf name.

    Returns:
        list: A list of tuples, where each tuple contains the leaf name and a tuple of attribute names.
    """
    def get_attr_names(n):
        """Get the attribute names from the given node.

        Args:
            n (dict): The node to extract attribute names from.

        Returns:
            list: A list of attribute names found in the node.
        """
        if not isinstance(n, dict):
            return []
        names = []
        attrs = n.get("attributes", [])
        names += [
            attr.get("name") for attr in attrs
            if isinstance(attr, dict) and "name" in attr
        ]
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
            leaves.append((".".join(path), tuple(attr_names)))
        return leaves
    for k in keys:
        val = node[k]
        if isinstance(val, dict):
            leaves.extend(find_attribute_leaves(val, path + (k,)))
    return leaves

def collect_used_leaves_detailed(target_dir, mapping_type, schema_leaves):
    """Collect the used leaf nodes and their attributes from the mapping files in the target directory.

    Args:
        target_dir(str): The directory containing the mapping files to analyze.
        mapping_type(str): The mapping type to look for in the mapping files (e.g., "ddi_mapping").
        schema_leaves(list): A list of tuples containing leaf names and their attribute names to check against.

    Returns:
        dict: A dictionary where the keys are leaf names and the values
            are dictionaries containing sets of file names
            that use the @value and @attributes for each leaf.
    """
    result = {}
    for leaf, attr_names in schema_leaves:
        result[leaf] = {
            VALUE_ANNOTATION: set(),
            ATTRIBUTES_ANNOTATION: {attr: set() for attr in attr_names}
        }
    for fname in os.listdir(target_dir):
        if not fname.endswith(".json"):
            continue
        # Judge by directory name
        if "success" in target_dir:
            if not fname.startswith(f"mapping_success_{mapping_type}"):
                continue
        else:
            if not fname.startswith(f"mapping_all_schemalist_{mapping_type}"):
                continue
        fpath = os.path.join(target_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        mapping = data.get("mapping", {})
        for item in mapping.values():
            mt_dict = item.get(mapping_type, {})
            def walk(d, path=[]):
                if not isinstance(d, dict):
                    return
                for k, v in d.items():
                    current_path = ".".join(path + [k])
                    # @value
                    if isinstance(v, dict) and VALUE_ANNOTATION in v:
                        if current_path in result:
                            result[current_path][VALUE_ANNOTATION].add(fname)
                    # @attributes
                    if isinstance(v, dict) and ATTRIBUTES_ANNOTATION in v:
                        for attr in v[ATTRIBUTES_ANNOTATION]:
                            if current_path in result and \
                                attr in result[current_path][ATTRIBUTES_ANNOTATION]:
                                result[current_path][ATTRIBUTES_ANNOTATION][attr].add(fname)
                    walk(v, path + [k])
            walk(mt_dict)
    return result

def get_unique_log_path(output_dir):
    """Generate a unique log file path by appending an index if the file already exists.

    Args:
        output_dir(str): The desired log file path.

    Returns:
        str: A unique log file path that does not already exist.
    """
    if not os.path.exists(output_dir):
        return output_dir
    base, ext = os.path.splitext(output_dir)
    idx = 1
    while True:
        new_path = f"{base}_{idx}{ext}"
        if not os.path.exists(new_path):
            return new_path
        idx += 1

def append_usage_details(
        details,
        mapping_type,
        schema_leaves,
        usage,
        title="使用ファイル",
        only_unused=False,
        unused_dict=None,
        restore_data=None,
        restore_count=None
    ):
    """Append detailed usage information for the specified mapping type to the details list.

    Args:
        details (list): The list to append details to.
        mapping_type (str): The mapping type.
        schema_leaves (list): The list of schema leaves.
        usage (dict): The usage data.
        title (str, optional): The title for the section.
        only_unused (bool, optional): Whether to include only unused items.
        unused_dict (dict, optional): The dictionary to store unused items.
        restore_data (dict, optional): The previous restore data.
        restore_count (dict, optional): The count of restored items.
    """
    lines = [f"=== {mapping_type} {title} ===\n"]
    unused_found = False
    for leaf, attr_names in schema_leaves:
        leaf_lines = [f"{leaf}\n"]
        leaf_unused = False

        files = usage[leaf][VALUE_ANNOTATION]
        if files:
            leaf_lines.append(f"  {VALUE_ANNOTATION}: {', '.join(sorted(files))}\n")
        else:
            if restore_data is not None:
                prev_value = restore_data.get(mapping_type, {}).get(leaf, {})\
                    .get(VALUE_ANNOTATION)
                if not prev_value or prev_value != NOT_USED:
                    leaf_lines.append(f"  {VALUE_ANNOTATION}: {restore_data['log_file']}\n")
                    restore_count[mapping_type] += 1
                else:
                    leaf_lines.append(f"  {VALUE_ANNOTATION}: {NOT_USED}\n")
                    leaf_unused = True
            else:
                leaf_lines.append(f"  {VALUE_ANNOTATION}: {NOT_USED}\n")
                leaf_unused = True

        if unused_dict is not None:
            unused_dict[mapping_type].setdefault(
                leaf, {VALUE_ANNOTATION: False, ATTRIBUTES_ANNOTATION: []})[VALUE_ANNOTATION]\
            = bool(files)

        leaf_lines.append(f"  {ATTRIBUTES_ANNOTATION}: {{\n")
        for attr in attr_names:
            attr_files = usage[leaf][ATTRIBUTES_ANNOTATION][attr]
            if attr_files:
                leaf_lines.append(f"    '{attr}': {', '.join(sorted(attr_files))}\n")
            else:
                if restore_data is not None:
                    prev_attr = restore_data.get(mapping_type, {}).get(leaf, {})\
                        .get(ATTRIBUTES_ANNOTATION, {}).get(attr)
                    if not prev_attr or prev_attr != NOT_USED:
                        leaf_lines.append(f"    '{attr}': {restore_data['log_file']}\n")
                        restore_count[mapping_type] += 1
                    else:
                        leaf_lines.append(f"    '{attr}': {NOT_USED}\n")
                        leaf_unused = True
                        if unused_dict is not None:
                            unused_dict[mapping_type][leaf][ATTRIBUTES_ANNOTATION].append(attr)
                else:
                    leaf_lines.append(f"    '{attr}': {NOT_USED}\n")
                    leaf_unused = True
                    if unused_dict is not None:
                        unused_dict[mapping_type][leaf][ATTRIBUTES_ANNOTATION].append(attr)
        leaf_lines.append(f"  }}\n\n")

        if only_unused:
            if leaf_unused:
                lines.extend(leaf_lines)
                unused_found = True
        else:
            lines.extend(leaf_lines)

    if only_unused:
        if unused_found:
            details.extend(lines)
    else:
        details.extend(lines)

def restore_verification_result(previous_log_lines, mapping_types):
    """Restore verification result from previous log lines.

    Args:
        previous_log_lines (list): The lines from the previous log file.
        mapping_types (list): The list of mapping types to restore.

    Returns:
        dict: The restored verification result.
    """
    restore_data = {
        **{mt: {} for mt in mapping_types},
    }
    schema_indices = {}
    indices_list = []
    for mt in mapping_types:
        indices = [i for i, line in enumerate(previous_log_lines)
                   if line.strip().startswith(f"=== {mt}")]
        if indices:
            schema_indices[mt] = indices[0]
            indices_list.append(indices[0])
    indices_list.sort()

    for mt in mapping_types:
        if mt not in schema_indices:
            continue
        start_idx = schema_indices[mt]
        idx = indices_list.index(start_idx)
        end_idx = indices_list[idx + 1] if idx + 1 < len(indices_list) else len(previous_log_lines)
        schema_usage_log = previous_log_lines[start_idx+1:end_idx]
        schema_usage_info = {}
        key_indices = [i for i, v in enumerate(schema_usage_log) if v and not v.startswith(" ")]
        for i in range(len(key_indices)):
            target_logs = schema_usage_log[key_indices[i]:key_indices[i+1]]\
                if i + 1 < len(key_indices) else schema_usage_log[key_indices[i]:]
            key = target_logs[0].strip()
            attr_usage = {
                VALUE_ANNOTATION: target_logs[1].split(":", 1)[1].strip(),
                ATTRIBUTES_ANNOTATION: {}
            }
            attribute_start_idx = [j for j, v in enumerate(target_logs)
                                   if v.strip().startswith(f"{ATTRIBUTES_ANNOTATION}:")][0]
            attribute_end_idx = [j for j, v in enumerate(target_logs) if v.strip() == "}"][0]
            attribute_logs = target_logs[attribute_start_idx + 1:attribute_end_idx]
            for attr_log in attribute_logs:
                stripped_log = attr_log.strip()
                if not stripped_log:
                    continue
                spritted = stripped_log.split("':", 1)
                attr_usage[ATTRIBUTES_ANNOTATION][spritted[0].strip().strip("'")] = spritted[1].strip()
            schema_usage_info[key] = attr_usage
        restore_data[mt] = schema_usage_info

    return restore_data

def parse_args():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Verify schema usage in mapping files.")
    parser.add_argument("item_type_id", help="Item type ID to verify.")
    parser.add_argument(
        "-c",
        "--continue",
        dest="continue_flag",
        action="store_true",
        help="Continue from previous unused schema data.",
        default=False
    )
    return parser.parse_args()

def main():
    """Main function to verify schema usage and log details."""
    args = parse_args()
    item_type_id = args.item_type_id
    is_continue = args.continue_flag

    # Retrieve schema data from the database
    schemas_raw = get_db_json("oaiserver_schema", ["xsd", "schema_name"])
    mapping_type_schemas = {}
    if schemas_raw:
        for row in schemas_raw:
            mapping_type = row.get("schema_name")
            xsd = row.get("xsd")
            if isinstance(xsd, str):
                xsd = json.loads(xsd)
            mapping_type_schemas[mapping_type] = remove_xsd_prefix(xsd)

    # Define test roles and timestamp
    test_roles = ["sysadmin", "repoadmin", "comadmin", "contributor", "user", "guest"]
    now_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for role in test_roles:
        target_dir_list = [
            f"{MAPPING_DIR_BASE}/test_data/{role}/all_schema_mappings/",
            f"{MAPPING_DIR_BASE}/test_data/{role}/success/"
        ]
        for target_dir in target_dir_list:
            dir_suffix = os.path.basename(os.path.normpath(target_dir))
            log_path_base = f"{MAPPING_DIR_BASE}/result/verify_schema_usage_{role}_{dir_suffix}_{now_timestamp}.log"
            log_path = get_unique_log_path(log_path_base)
            save_data_path = f"{MAPPING_DIR_BASE}/save_data/unused_schema_{int(item_type_id)}_{role}_{now_timestamp}.json"
            mapping_types = [
                "ddi_mapping",
                "lom_mapping",
                "jpcoar_v1_mapping",
                "jpcoar_mapping",
                "oai_dc_mapping"
            ]

            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            restore_data = None
            if is_continue and "success" in target_dir:
                previous_save_file = sorted(
                    [
                        f for f in os.listdir(os.path.join(MAPPING_DIR_BASE, "save_data"))
                        if f.startswith(f"unused_schema_{item_type_id}_{role}_")\
                            and f.endswith(".json")
                    ],
                    reverse=True
                )[0]
                with open(os.path.join(MAPPING_DIR_BASE, "save_data", previous_save_file),
                          "r", encoding="utf-8") as f:
                    previous_unused_data = json.load(f)
                previous_log_file = previous_unused_data.get("log_file")
                if previous_log_file and os.path.exists(previous_log_file):
                    with open(previous_log_file, "r", encoding="utf-8") as prev_log:
                        prev_log_lines = prev_log.read().splitlines()
                    restore_data = restore_verification_result(prev_log_lines, mapping_types)
                    restore_data["log_file"] = previous_log_file

            # Initialize summary and unused schema data
            summary = {}
            total_unused = 0
            details = []
            unused_dict = {
                "log_file": log_path,
                **{mt: {} for mt in mapping_types},
            }
            restore_count = {
                mt: 0 for mt in mapping_types
            }

            for mapping_type in mapping_types:
                schema_mt = mapping_type_schemas.get(mapping_type)
                if not schema_mt:
                    details.append(f"[ERROR] schema not found for: {mapping_type}\n")
                    summary[mapping_type] = (0, 0)
                    continue
                schema_leaves = find_attribute_leaves(schema_mt)
                usage = collect_used_leaves_detailed(target_dir, mapping_type, schema_leaves)

                used_count = 0
                total_count = 0
                unused_count = 0

                # Count @value/@attributes for each leaf node
                for leaf, attr_names in schema_leaves:
                    total_count += 1  # @value
                    if usage[leaf][VALUE_ANNOTATION]:
                        used_count += 1
                    else:
                        unused_count += 1
                    for attr in attr_names:
                        total_count += 1
                        if usage[leaf][ATTRIBUTES_ANNOTATION][attr]:
                            used_count += 1
                        else:
                            unused_count += 1

                summary[mapping_type] = (used_count, total_count)
                total_unused += unused_count

                # Log details (only unused schemas for "success" directory)
                if "success" in target_dir:
                    append_usage_details(
                        details, mapping_type, schema_leaves, usage,
                        title="未使用スキーマ", only_unused=True,
                        unused_dict=unused_dict, restore_data=restore_data, restore_count=restore_count
                    )
                    summary[mapping_type] = (used_count + restore_count[mapping_type], total_count)
                    total_unused -= restore_count[mapping_type]
                elif "success" not in target_dir:
                    append_usage_details(details, mapping_type, schema_leaves, usage)

                # 詳細ログ（全表示、 対象テストファイルが多い場合は注意）
                # append_usage_details(details, mapping_type, schema_leaves, usage)

            if "success" in target_dir:
                # Save unused schema data to JSON
                if not os.path.exists(os.path.dirname(save_data_path)):
                    os.makedirs(os.path.dirname(save_data_path), exist_ok=True)
                with open(save_data_path, "w", encoding="utf-8") as save_file:
                    json.dump(unused_dict, save_file, ensure_ascii=False, indent=4)

            # Write log file
            with open(log_path, "w", encoding="utf-8") as log:
                log.write("=== 検証結果 ===\n")
                log.write("調査対象ディレクトリ: {}\n".format(target_dir))
                for mapping_type in mapping_types:
                    used, total = summary.get(mapping_type, (0, 0))
                    log.write(f"{mapping_type}: {used}/{total}\n")
                log.write(f"未使用: {total_unused}\n\n")
                for line in details:
                    log.write(line)
    print(f"検証結果を {MAPPING_DIR_BASE}/result に出力しました。")

if __name__ == "__main__":
    main()