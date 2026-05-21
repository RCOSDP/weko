import argparse
import os

# Constants and global variables should be defined after imports
ROLE_DICT = {
    "sysadmin": {
        "name": "システム管理者",
        "login": "login_sysadmin",
        "mark": "system_admin",
        "user_id": 1
    },
    "repoadmin": {
        "name": "リポジトリ管理者",
        "login": "login_repoadmin",
        "mark": "repository_admin",
        "user_id": 2
    },
    "comadmin": {
        "name": "コミュニティ管理者",
        "login": "login_comadmin",
        "mark": "community_admin",
        "user_id": 5
    },
    "contributor": {
        "name": "コントリビュータ",
        "login": "login_contributor",
        "mark": "contributor",
        "user_id": 3
    },
    "user": {
        "name": "一般ユーザー",
        "login": "login_user",
        "mark": "user",
        "user_id": 4
    },
    "guest": {
        "name": "ゲスト",
        "login": "",
        "mark": "guest",
        "user_id": 0
    }
}

SUCCESS_FILE = "test/index/base/index_200.yaml"
UNAUTHORIZED_FILE = "test/index/base/index_401.yaml"
FORBIDDEN_FILE = "test/index/base/index_403.yaml"
FOLDER_TO_SEARCH = "request_params/index/test_data"

def find_matching_files():
    """Find all files in folders whose names contain '_random_'.

    Returns:
        list: A list of file paths found in matching folders.
    """
    all_files = []

    for root, dirs, _ in os.walk(FOLDER_TO_SEARCH):
        for dir_name in dirs:
            folder_name = os.path.join(root, dir_name)
            for sub_root, _, sub_files in os.walk(folder_name):
                for file in sub_files:
                    if file.startswith("generated_index_data_") and file.endswith(".json"):
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

def create_test_cases(file_list, success_content, unauthorized_content, forbidden_content, output_file):
    """Create test cases by replacing placeholders in the content and write to output file.

    Args:
        file_list (list): List of file paths to create test cases for.
        success_content (list): List of strings representing the template for successful test cases.
        unauthorized_content (list): List of strings representing the template for unauthorized test cases.
        forbidden_content (list): List of strings representing the template for forbidden test cases.
        output_file (str): The path to the output file where the generated test cases will be written.
    """
    test_cases = []
    for file_path in file_list:
        role_dir = file_path.split(os.sep)[-2]
        file_name = os.path.basename(file_path)
        no = os.path.splitext(file_name)[0].split("_")[-1]
        target_role_info = ROLE_DICT.get(role_dir, {})
        replacements = {
            "<role_ja>": target_role_info.get("name", ""),
            "<No>": no,
            "<login>": target_role_info.get("login", ""),
            "<role_mark>": target_role_info.get("mark", ""),
            "<role_folder>": role_dir,
            "<file_name>": file_name,
            "<user_id>": str(target_role_info.get("user_id", 0))
        }

        if role_dir in ["sysadmin", "repoadmin"]:
            modified_content = replace_placeholders(success_content, replacements)
        elif role_dir in ["comadmin", "contributor", "user"]:
            modified_content = replace_placeholders(forbidden_content, replacements)
        else:
            modified_content = replace_placeholders(unauthorized_content, replacements)

        test_cases.append("\n".join(modified_content))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n---\n".join(test_cases))

def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate test cases from template.")
    parser.add_argument("--output", type=str, help="Output file path", required=True)
    return parser.parse_args()

def main():
    """Main function to execute the test case generation process."""
    args = parse_args()
    output_file = args.output
    with open(SUCCESS_FILE, "r", encoding="utf-8") as f:
        success_content = f.read().splitlines()
    with open(UNAUTHORIZED_FILE, "r", encoding="utf-8") as f:
        unauthorized_content = f.read().splitlines()
    with open(FORBIDDEN_FILE, "r", encoding="utf-8") as f:
        forbidden_content = f.read().splitlines()
    result = find_matching_files()
    print(f"Found {len(result)} files in folders matching '{FOLDER_TO_SEARCH}'")
    create_test_cases(result, success_content, unauthorized_content, forbidden_content, output_file)

if __name__ == "__main__":
    main()