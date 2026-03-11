from datetime import datetime, timedelta
import json
import os
import random
import string
import sys

from generate_config import DATE_FORMAT, DATETIME_FORMAT, DEFAULT_VALUE

mode = 0

def generate_data(data, output_file_name):
    """Generate data based on the schema.
    
    Args:
        data (dict): Schema data.
        output_file_name (str): Output file name.
    
    Returns:
        None
    """
    generate_number = 1
    if mode == 0:
        # Set the maximum number of selections if the mode is normal
        generate_number = check_generate_number(data)

    # Create an output directory if it does not exist
    output_dir = '../output/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate data
    for i in range(generate_number):
        generated_data = generator(data, i)

        if mode == 0:
            # If the mode is normal, generate multiple files
            with open(output_dir + output_file_name + '_' + str(i) + '.json', 'w') as f:
                json.dump(generated_data, f, indent=4)
        if mode == 1:
            # If the mode is less than, generate a file with less than the specified value
            with open(output_dir + output_file_name + '_less.json', 'w') as f:
                json.dump(generated_data, f, indent=4)
        if mode == 2:
            # If the mode is minimum, generate a file with the minimum value
            with open(output_dir + output_file_name + '_min.json', 'w') as f:
                json.dump(generated_data, f, indent=4)
        if mode == 3:
            # If the mode is maximum, generate a file with the maximum value
            with open(output_dir + output_file_name + '_max.json', 'w') as f:
                json.dump(generated_data, f, indent=4)
        if mode == 4:
            # If the mode is over, generate a file with over the specified value
            with open(output_dir + output_file_name + '_over.json', 'w') as f:
                json.dump(generated_data, f, indent=4)

def check_generate_number(data):
    """Check the maximum number of selections.
    
    Args:
        data (dict): Schema data.
        
    Returns:
        int: Maximum number of selections.
    """
    generate_number = 1
    for value in data.values():
        if type(value) is dict and 'type' in value:
            if value['type'] == 'select':
                generate_number = max(generate_number, len(value['options']))
            elif value['type'] == 'list':
                generate_number = max(generate_number, check_generate_number_list(value['items']))
            elif value['type'] == 'dict':
                generate_number = max(generate_number, check_generate_number(value['properties']))
            elif value['type'] == 'pair':
                generate_number = max(generate_number, len(value['pairs']))
            elif value['type'] == 'semi_pair':
                generate_number = max(generate_number, len(value['pairs']), check_generate_number(value['properties']))
            elif value['type'] == 'bool':
                generate_number = max(generate_number, 2)
    return generate_number

def check_generate_number_list(items):
    """Check the maximum number of selections in the list.
    
    Args:
        items (dict): Items data.
        
    Returns:
        int: Maximum number of selections.
    """
    generate_number = 1
    if type(items) is dict and 'type' in items:
        if items['type'] == 'select':
            generate_number = max(generate_number, len(items['options']))
        elif items['type'] == 'list':
            generate_number = max(generate_number, check_generate_number_list(items['items']))
        elif items['type'] == 'dict':
            generate_number = max(generate_number, check_generate_number(items['properties']))
        elif items['type'] == 'pair':
            generate_number = max(generate_number, len(items['pairs']))
        elif items['type'] == 'semi_pair':
            generate_number = max(generate_number, len(items['pairs']), check_generate_number(items.get('properties', {})))
        elif items['type'] == 'bool':
            generate_number = max(generate_number, 2)
    return generate_number

def generator(data, number):
    """Generate data based on the schema.
    
    Args:
        data (dict): Schema data.
        number (int): Selection number.
    
    Returns:
        dict: Generated data.
    """
    result = {}
    for key, value in data.items():
        if type(value) is not dict or 'type' not in value:
            # If the value is not a dictionary or the dictionary does not have a type key, set the value as it is
            result[key] = value
            continue

        if value['type'] == 'string':
            result[key] = generate_string(value.get('min', DEFAULT_VALUE['string']['min']), value.get('max', DEFAULT_VALUE['string']['max']))
        elif value['type'] == 'int':
            result[key] = generate_int(value.get('min', DEFAULT_VALUE['int']['min']), value.get('max', DEFAULT_VALUE['int']['max']))
        elif value['type'] == 'float':
            result[key] = generate_float(value.get('min', DEFAULT_VALUE['float']['min']), value.get('max', DEFAULT_VALUE['float']['max']))
        elif value['type'] == 'date':
            result[key] = generate_date(value.get('min', DEFAULT_VALUE['date']['min']), value.get('max', DEFAULT_VALUE['date']['max']))
        elif value['type'] == 'datetime':
            result[key] = generate_datetime(value.get('min', DEFAULT_VALUE['datetime']['min']), value.get('max', DEFAULT_VALUE['datetime']['max']))
        elif value['type'] == 'bool':
            result[key] = generate_bool(number)
        elif value['type'] == 'list':
            result[key] = generate_list(value.get('min', DEFAULT_VALUE['list']['min']), value.get('max', DEFAULT_VALUE['list']['max']), value['items'], number)
        elif value['type'] == 'dict':
            result[key] = generator(value['properties'], number)
        elif value['type'] == 'select':
            result[key] = generate_select(value['options'], number)
        elif value['type'] == 'pair':
            result[key] = generate_pair(value['keys'], value['pairs'], number)
        elif value['type'] == 'semi_pair':
            result[key] = generate_semi_pair(value['keys'], value['pairs'], value.get('properties', {}), number)
        else:
            type_error()
    return result

def generate_string(min, max):
    """Generate a random string.
    
    Args:
        min (int): Minimum length of the string.
        max (int): Maximum length of the string.
        
    Returns:
        str: Random string what length is specified.
    """
    if mode == 0:
        # Normal mode
        length = random.randint(min, max)
    elif mode == 1:
        # Less than mode
        if min == 0:
            # If the minimum length is 0, set the length to 0
            length = 0
        else:
            length = min - 1
    elif mode == 2:
        # Minimum mode
        length = min
    elif mode == 3:
        # Maximum mode
        length = max
    elif mode == 4:
        # Over mode
        length = max + 1
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_int(min, max):
    """Generate a random integer.
    
    Args:
        min (int): Minimum value of the integer.
        max (int): Maximum value of the integer.
        
    Returns:
        int: Random integer what value is specified.
    """
    if mode == 0:
        # Normal mode
        return random.randint(min, max)
    elif mode == 1:
        # Less than mode
        return min - 1
    elif mode == 2:
        # Minimum mode
        return min
    elif mode == 3:
        # Maximum mode
        return max
    elif mode == 4:
        # Over mode
        return max + 1

def generate_float(min, max, precision=2):
    """Generate a random float.

    Args:
        min (float): Minimum value of the float.
        max (float): Maximum value of the float.
        precision (int): Precision of the float.

    Returns:
        float: Random float what value is specified.
    """
    if mode == 0:
        # Normal mode
        return round(random.uniform(min, max), precision)
    elif mode == 1:
        # Less than mode
        value = round(min, precision)
        minus_value = 10 ** -precision
        return value - minus_value
    elif mode == 2:
        # Minimum mode
        return round(min, precision)
    elif mode == 3:
        # Maximum mode
        return round(max, precision)
    elif mode == 4:
        # Over mode
        value = round(max, precision)
        plus_value = 10 ** -precision
        return value + plus_value

def generate_date(min, max):
    """Generate a random date.
    
    Args:
        min (str): Minimum date.
        max (str): Maximum date.
        
    Returns:
        str: Random date what value is specified.
    """
    min_date = datetime.strptime(min, DATE_FORMAT)
    max_date = datetime.strptime(max, DATE_FORMAT)
    if mode == 0:
        # Normal mode
        days_between = (max_date - min_date).days
        random_days = random.randint(0, days_between)
        return (min_date + timedelta(days=random_days)).strftime(DATE_FORMAT)
    elif mode == 1:
        # Less than mode
        return (min_date - timedelta(days=1)).strftime(DATE_FORMAT)
    elif mode == 2:
        # Minimum mode
        return min_date.strftime(DATE_FORMAT)
    elif mode == 3:
        # Maximum mode
        return max_date.strftime(DATE_FORMAT)
    elif mode == 4:
        # Over mode
        return (max_date + timedelta(days=1)).strftime(DATE_FORMAT)

def generate_datetime(min, max):
    """Generate a random datetime.

    Args:
        min (str): Minimum datetime.
        max (str): Maximum datetime.

    Returns:
        str: Random datetime what value is specified.
    """
    min_date = datetime.strptime(min, DATETIME_FORMAT)
    max_date = datetime.strptime(max, DATETIME_FORMAT)
    if mode == 0:
        # Normal mode
        seconds_between = (max_date - min_date).total_seconds()
        random_seconds = random.randint(0, int(seconds_between))
        return (min_date + timedelta(seconds=random_seconds)).strftime(DATETIME_FORMAT)
    elif mode == 1:
        # Less than mode
        return (min_date - timedelta(seconds=1)).strftime(DATETIME_FORMAT)
    elif mode == 2:
        # Minimum mode
        return min_date.strftime(DATETIME_FORMAT)
    elif mode == 3:
        # Maximum mode
        return max_date.strftime(DATETIME_FORMAT)
    elif mode == 4:
        # Over mode
        return (max_date + timedelta(seconds=1)).strftime(DATETIME_FORMAT)

def generate_bool(number):
    """Generate a boolean.
    
    Args:
        number (int): Selection number.
        
    Returns:
        bool:
            True: If the selection number is an odd number.
            False: If the selection number is an even number
    """
    bools = [True, False]
    return bools[number % 2]

def generate_select(values, number):
    """Generate a value from the options.

    Args:
        values (list): Options.
        number (int): Selection number.

    Returns:
        object: The value selected from the options.
    """
    length = len(values)
    if length == 0:
        return None
    return_value = values[number % length]
    if not return_value and mode > 1:
        return_value = values[number % length + 1]
    return return_value

def generate_pair(keys, pairs, number):
    """Generate a pair of values.

    Args:
        keys (list): Keys.
        pairs (list): Pairs.
        number (int): Selection number.

    Returns:
        dict: The pair of values.
    """
    result = {}
    for i in range(len(keys)):
        result[keys[i]] = pairs[number % len(pairs)][i]
        if not result[keys[i]] and mode > 1:
            result[keys[i]] = pairs[number % len(pairs) + 1][i]
    return result

def generate_semi_pair(keys, pairs, properties, number):
    """Generate a semi-pair of values.

    Args:
        keys (list): Keys.
        pairs (list): Pairs.
        properties (dict): Properties.
        number (int): Selection number.

    Returns:
        dict: The semi-pair of values.
    """
    result = {}
    for i in range(len(keys)):
        result[keys[i]] = pairs[number % len(pairs)][i]
        if not result[keys[i]] and mode > 1:
            result[keys[i]] = pairs[number % len(pairs) + 1][i]
    result.update(generator(properties, number))
    return result

def generate_list(min, max, items, number):
    """Generate a list of values.

    Args:
        min (int): Minimum number of values.
        max (int): Maximum number of values.
        items (dict): Items.
        number (int): Selection number.

    Returns:
        list: The list of values.
    """
    result = []
    if mode == 0:
        # Normal mode
        generated_number = random.randint(min, max)
    elif mode == 1:
        # Less than mode
        if min == 0:
            # If the minimum number of values is 0, set the number of values to 0
            generated_number = 0
        else:
            generated_number = min - 1
    elif mode == 2:
        # Minimum mode
        generated_number = min
    elif mode == 3:
        # Maximum mode
        generated_number = max
    elif mode == 4:
        # Over mode
        generated_number = max + 1

    if type(items) is not dict or 'type' not in items:
        # If items is not a dictionary or the dictionary does not have a type key, return items
        return items
    
    if items['type'] == 'string':
        for _ in range(generated_number):
            result.append(generate_string(items.get('min', DEFAULT_VALUE['string']['min']), items.get('max', DEFAULT_VALUE['string']['max'])))
    elif items['type'] == 'int':
        for _ in range(generated_number):
            result.append(generate_int(items.get('min', DEFAULT_VALUE['int']['min']), items.get('max', DEFAULT_VALUE['int']['max'])))
    elif items['type'] == 'float':
        for _ in range(generated_number):
            result.append(generate_float(items.get('min', DEFAULT_VALUE['float']['min']), items.get('max', DEFAULT_VALUE['float']['max'])))
    elif items['type'] == 'date':
        for _ in range(generated_number):
            result.append(generate_date(items.get('min', DEFAULT_VALUE['date']['min']), items.get('max', DEFAULT_VALUE['date']['max'])))
    elif items['type'] == 'datetime':
        for _ in range(generated_number):
            result.append(generate_datetime(items.get('min', DEFAULT_VALUE['datetime']['min']), items.get('max', DEFAULT_VALUE['datetime']['max'])))
    elif items['type'] == 'bool':
        for _ in range(generated_number):
            result.append(generate_bool(number))
    elif items['type'] == 'list':
        for _ in range(generated_number):
            result.append(generate_list(items.get('min', DEFAULT_VALUE['list']['min']), items.get('max', DEFAULT_VALUE['list']['max']), items['items'], number))
    elif items['type'] == 'dict':
        for _ in range(generated_number):
            result.append(generator(items['properties'], number))
    elif items['type'] == 'select':
        for _ in range(generated_number):
            result.append(generate_select(items['options'], number))
    elif items['type'] == 'pair':
        for _ in range(generated_number):
            result.append(generate_pair(items['keys'], items['pairs'], number))
    elif items['type'] == 'semi_pair':
        for _ in range(generated_number):
            result.append(generate_semi_pair(items['keys'], items['pairs'], items.get('properties', {}), number))
    else:
        type_error()
    return result    

def command_error():
    """Print the command error message and exit the program."""
    print('次のコマンドを使用してください: python3 generate_json.py [input_file] [output_file_name] ([mode])')
    print('[mode]: 0: 通常(範囲内ランダム), 1: 未満, 2: 最小値, 3: 最大値, 4: 超過')
    sys.exit(1)

def type_error():
    """Print the type error message and exit the program."""
    print('type には次の値を指定してください: string, int, float, date, datetime, bool, list, dict, select, pair')
    sys.exit(1)

def print_max_number(data, child=False):
    result = 1
    for k, v in data.items():
        if type(v) is dict and 'type' in v:
            tmp_result = 0
            if v['type'] == 'select':
                tmp_result = len(v['options'])
            elif v['type'] == 'list':
                tmp_result = print_max_number_list(v['items'])
            elif v['type'] == 'dict':
                tmp_result = print_max_number(v['properties'], child=True)
            elif v['type'] == 'pair':
                tmp_result = len(v['pairs'])
            elif v['type'] == 'semi_pair':
                tmp_result = len(v['pairs']) * print_max_number(v.get('properties', {}), child=True)
            elif v['type'] == 'bool':
                tmp_result = 2
            if tmp_result:
                result *= tmp_result
        if not child:
            print(f'{k}: {result}')
    return result

def print_max_number_list(items):
    if type(items) is dict and 'type' in items:
        if items['type'] == 'select':
            return len(items['options'])
        elif items['type'] == 'list':
            return print_max_number_list(items['items'])
        elif items['type'] == 'dict':
            return print_max_number(items['properties'], child=True)
        elif items['type'] == 'pair':
            return len(items['pairs'])
        elif items['type'] == 'semi_pair':
            return len(items['pairs']) * print_max_number(items.get('properties', {}), child=True)
        elif items['type'] == 'bool':
            return 2
    return 1

def main():
    """Main function."""
    global mode
    args = sys.argv
    if len(args) < 3:
        # If the number of arguments is less than 3, print the command error message and exit the program
        command_error()
    input_file = args[1]
    output_file_name = args[2]
    if len(args) == 4:
        if not args[3].isdigit() or int(args[3]) < 0 or int(args[3]) > 4:
            # If the mode is not a number or the number is less than 0 or greater than 4, print the command error message and exit the program
            command_error()
        # Set the mode
        mode = int(args[3])
    with open(input_file, 'r') as f:
        data = json.load(f)
    print(print_max_number(data))
    generate_data(data, output_file_name)

if __name__ == '__main__':
    main()
