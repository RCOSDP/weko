from datetime import datetime, timedelta
import json
import os
import psycopg2

from helper.config import DATABASE, REPLACEMENT_DECISION_STRING


def connect_db():
    """Connect to database
    
    Args:
        None
        
    Returns:
        psycopg2.extensions.connection: connection to database
    """
    conn = psycopg2.connect(
        dbname=DATABASE['dbname'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
        port=DATABASE['port'],
    )
    return conn

def compare_db_data(cursor, folder_path, replace_params = {}, type_conversion_params = {}, datetime_columns=[]):
    """Compare data in database with data in excel file

    Args:
        cursor (psycopg2.extensions.cursor): cursor to database
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        replace_params (dict): data to replace specific values
        type_conversion_params (dict): column's type conversion params
    
    Returns:
        None
    """
    folder_path = os.path.join('table_records', folder_path)
    file_names = os.listdir(folder_path)
    for file_name in file_names:
        with open(os.path.join(folder_path, file_name), 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        
        file_name_without_extension = file_name.split('.')[0]

        columns = lines[0].split('\t')
        records = [l.split('\t') for l in lines[1:]]
        expect_params = create_expect_params(columns, records, file_name_without_extension, replace_params, type_conversion_params)

        target_column = ', '.join(columns)
        cursor.execute(f'SELECT {target_column} FROM {file_name_without_extension} ORDER BY created')
        search_records = cursor.fetchall()

        exe_params = []
        for sr in search_records:
            exe_param = {}
            for i in range(len(columns)):
                exe_param[columns[i]] = sr[i]
            exe_params.append(exe_param)

        try:
            assert len(exe_params) == len(expect_params)
            for i in range(len(exe_params)):
                for c in columns:
                    if c in datetime_columns:
                        expect_dt = datetime.strptime(expect_params[i][c], '%Y-%m-%d %H:%M:%S')
                        second_before_expect = expect_dt + timedelta(seconds=-1)
                        assert second_before_expect <= exe_params[i][c].replace(microsecond=0) <= expect_dt
                    else:
                        assert exe_params[i][c] == expect_params[i][c]
        except AssertionError as e:
            import pprint
            import difflib
            a_str = pprint.pformat(exe_params)
            b_str = pprint.pformat(expect_params)
            diff = '\n'.join(difflib.unified_diff(
                a_str.splitlines(), b_str.splitlines(),
                fromfile='actual', tofile='expected', lineterm=''
            ))
            print("差分:\n" + diff)
            raise

def create_expect_params(columns, records, file_name, replace_params, type_conversion_params):
    """Create expected parameters
    
    Args:
        columns (list): column names
        records (list): records
        file_name (str): table name
        replace_params (dict): data to replace specific values
        type_conversion_params (dict): column's type conversion params
    
    Returns:
        list: expected parameters
    """
    expect_params = []
    replace_begin_str = REPLACEMENT_DECISION_STRING['BEGIN']
    replace_end_str = REPLACEMENT_DECISION_STRING['END']
    for record in records:
        expect_param = {}
        for i in range(len(columns)):
            if record[i] == 'NULL':
                expect_param[columns[i]] = None
                continue
            if type(record[i]) is not str:
                expect_param[columns[i]] = record[i]
                continue
            begin_idx = record[i].find(replace_begin_str)
            end_idx = record[i].find(replace_end_str)
            if begin_idx != -1 and end_idx != -1:
                temp_record = record[i]
                while begin_idx != -1 and end_idx != -1:
                    if begin_idx > end_idx:
                        end_idx = temp_record.find(replace_end_str, end_idx + 1)
                        continue
                    key = temp_record[begin_idx+2:end_idx]
                    if type(replace_params[file_name][key]) is dict:
                        temp_record = temp_record.replace(replace_begin_str + key + replace_end_str + ', ', '')
                        temp_record = json.loads(temp_record)
                        for k, v in replace_params[file_name][key].items():
                            temp_record[k] = v
                        temp_record = json.dumps(temp_record)
                    else:
                        temp_record = temp_record.replace(replace_begin_str + key + replace_end_str, replace_params[file_name][key])
                    begin_idx = temp_record.find(replace_begin_str)
                    end_idx = temp_record.find(replace_end_str)
                expect_param[columns[i]] = temp_record
            else:
                expect_param[columns[i]] = record[i]

        if type_conversion_params:
            target_keys = type_conversion_params.get(file_name)
            if target_keys:
                for key, value in target_keys.items():
                    if value == 'json':
                        expect_param[key] = json.loads(expect_param[key])
                    elif value == 'int':
                        expect_param[key] = int(expect_param[key])
                    elif value == 'bool':
                        expect_param[key] = expect_param[key].lower() == 'true'

        expect_params.append(expect_param)
    return expect_params
