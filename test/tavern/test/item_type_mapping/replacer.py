import argparse
import os
import re

# Constants and global variables should be defined after imports
ROLE_DICT = {
    "sysadmin": {
        "name": "システム管理者",
        "login": "login_sysadmin",
        "mark": "system_admin"
    },
    "repoadmin": {
        "name": "リポジトリ管理者",
        "login": "login_repoadmin",
        "mark": "repository_admin"
    },
    "comadmin": {
        "name": "コミュニティ管理者",
        "login": "login_comadmin",
        "mark": "community_admin"
    },
    "contributor": {
        "name": "コントリビュータ",
        "login": "login_contributor",
        "mark": "contributor"
    },
    "user": {
        "name": "一般ユーザー",
        "login": "login_user",
        "mark": "user"
    },
    "guest": {
        "name": "ゲスト",
        "login": "",
        "mark": "guest"
    }
}

SUCCESS_FILE = "test/item_type_mapping/base/item_type_mapping_200.yaml"
REDIRECT_FILE = "test/item_type_mapping/base/item_type_mapping_302.yaml"
FORBIDDEN_FILE = "test/item_type_mapping/base/item_type_mapping_403.yaml"
FOLDER_TO_SEARCH = "request_params/item_type_mapping/test_data"

def find_files_in_matching_folders(partial_string):
    """Find all files in folders whose names contain the partial_string.

    Args:
        partial_string (str): The partial string to match folder names.

    Returns:
        list: A list of file paths found in matching folders.
    """
    all_files = []

    for root, dirs, _ in os.walk(FOLDER_TO_SEARCH):
        for dir_name in dirs:
            if partial_string in dir_name:
                matching_folder = os.path.join(root, dir_name)
                for sub_root, _, sub_files in os.walk(matching_folder):
                    for file in sub_files:
                        all_files.append(os.path.join(sub_root, file))

    return all_files

def replace_placeholders(data, replacements):
    """Replace placeholders in the data with corresponding values from replacements.

    Args:
        data (list): List of strings containing placeholders.
        replacements (dict): Dictionary with placeholder-value pairs.
    """
    start_char = "<"
    end_char = ">"
    replaced_data = []
    for d in data:
        login_flg = False
        while True:
            start_index = d.find(start_char)
            end_index = d.find(end_char, start_index + 1)
            if start_index == -1 or end_index == -1:
                break
            placeholder = d[start_index:end_index + 1]
            if placeholder in replacements:
                if placeholder == "<login>":
                    login_flg = True
                    if replacements["<login>"] != "":
                        replaced_data.append("  - usefixtures:")
                        replaced_data.append("    - " + replacements["<login>"])
                    break
                else:
                    d = d.replace(placeholder, replacements[placeholder])
        if not login_flg:
            replaced_data.append(d)
    replaced_data.append("")
    return replaced_data

def create_test_cases(file_list, success_content, redirect_content, forbidden_content, output_file, target_dir, exe_type):
    """Create test cases by replacing placeholders in the template content.

    Args:
        file_list (list): List of file paths to extract information from.
        success_content (list): Template content for success cases as a list of strings.
        redirect_content (list): Template content for redirect cases as a list of strings.
        forbidden_content (list): Template content for forbidden cases as a list of strings.
        output_file (str): Path to the output file.
        target_dir (str): Target directory name to include in the test case names.
        exe_type (str): Execution type to include in the test case names.
    """
    test_cases = []
    schema_name = ""
    counts = {}
    for file_path in file_list:
        role_dir = file_path.split(os.sep)[-3]
        file_name = os.path.basename(file_path)
        match = re.search(r"\w+_mapping", file_name.replace("mapping_all_schemalist_", ""))
        if match:
            extracted = match.group()
        if extracted not in counts:
            counts[extracted] = 1
        else:
            counts[extracted] += 1
        schema_name = extracted
        target_role_info = ROLE_DICT.get(role_dir, {})
        replacements = {
            "<role_ja>": target_role_info.get("name", ""),
            "<mapping_type>": schema_name,
            "<No>": str(counts.get(extracted, 1)),
            "<login>": target_role_info.get("login", ""),
            "<role_mark>": target_role_info.get("mark", ""),
            "<type>": schema_name.replace("_mapping", ""),
            "<role_folder>": role_dir,
            "<target_dir>": target_dir,
            "<file_name>": file_name,
            "<exe_type>": exe_type
        }

        if role_dir in ['sysadmin', 'repoadmin']:
            modified_content = replace_placeholders(success_content, replacements)
        elif role_dir in ['guest']:
            modified_content = replace_placeholders(redirect_content, replacements)
        else:
            modified_content = replace_placeholders(forbidden_content, replacements)
        test_cases.append("\n".join(modified_content))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n---\n".join(test_cases))

def parse_args():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate test cases from template.")
    parser.add_argument("--output", type=str, help="Output file path", required=True)
    parser.add_argument("--target_dir", type=str, help="Target directory name to search for", required=True)
    parser.add_argument("--exe_type", type=str, help="Execution type", required=True)
    return parser.parse_args()

def main():
    """Main function to generate test cases."""
    args = parse_args()
    output_file = args.output
    target_dir = args.target_dir
    exe_type = args.exe_type
    with open(SUCCESS_FILE, "r", encoding="utf-8") as f:
        success_content = f.read().splitlines()
    with open(REDIRECT_FILE, "r", encoding="utf-8") as f:
        redirect_content = f.read().splitlines()
    with open(FORBIDDEN_FILE, "r", encoding="utf-8") as f:
        forbidden_content = f.read().splitlines()
    result = find_files_in_matching_folders(target_dir)
    print(f"Found {len(result)} files in folders matching '{target_dir}'")
    create_test_cases(result, success_content, redirect_content, forbidden_content, output_file, target_dir, exe_type)

if __name__ == "__main__":
    main()
