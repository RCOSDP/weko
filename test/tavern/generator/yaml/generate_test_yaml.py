import os
import sys

def create_tests_from_template(target_dir, template_file, output_file_name, replace_csv):
    """Create test yaml files from template file.
    
    Args:
        target_dir (str): Target directory path.
        template_file (str): Template file path.
        output_file_name (str): Output file name.
        replace_csv (str): Replace csv file path.
        
    Returns:
        None
    """
    # Read template file
    with open(template_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    tests = []
    replace_dict = None
    if replace_csv is not None:
        # Create replace dict
        replace_dict = create_replace_dict(replace_csv)
    # Create test data
    file_names = os.listdir(target_dir)
    for i, file_name in enumerate(file_names):
        suffix = ""
        if '_' in file_name:
            suffix = file_name.split('_')[-1].split('.')[0]
        replaced_lines = []
        for line in lines:
            if line.startswith('test_name:'):
                line += '_' + suffix
            if '[file_name]' in line:
                line = line.replace('[file_name]', file_name)
            if replace_dict is not None:
                target_dict = replace_dict[file_name]
                for key, value in target_dict.items():
                    target_str = '[' + key + ']'
                    if target_str in line:
                        line = line.replace(target_str, value)
            replaced_lines.append(line)
        tests.extend(replaced_lines)
        if i != len(file_names) - 1:
            # Add separator
            tests.extend(['', '---'])

    # Write test data
    with open(output_file_name + '.tavern.yaml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(tests))

def create_replace_dict(replace_csv):
    """Create replace dict from csv file.

    Args:
        replace_csv (str): Replace csv file path.

    Returns:
        dict: Replace dict.
    """
    # Read replace csv file
    with open(replace_csv, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    replace_dict = {}
    header = lines[0].split(',')[1:]
    lines = lines[1:]

    for line in lines:
        values = line.split(',')
        key = values[0]
        replace_dict[key] = {}
        for i, value in enumerate(values[1:]):
            replace_dict[key][header[i]] = value
    
    return replace_dict

def command_error():
    """Print command error message and exit."""
    print('次のコマンドを使用してください: python3 generate_test_yaml.py [target_dir] [template_file] [output_file_name] ([replace_csv])')
    sys.exit(1)

def main():
    """Main function."""
    if len(sys.argv) < 4:
        command_error()
    target_dir = sys.argv[1]
    template_file = sys.argv[2]
    output_file_name = sys.argv[3]
    replace_csv = None
    if len(sys.argv) == 5:
        replace_csv = sys.argv[4]
    create_tests_from_template(target_dir, template_file, output_file_name, replace_csv)

if __name__ == '__main__':
    main()