import copy
import json
from bs4 import BeautifulSoup
from contextlib import closing
from urllib.parse import urlencode
import xmltodict

from helper.common.connect_helper import connect_db

def verify_contains(response, expected_substring):
    """Verify that the response contains the expected substring.

    Args:
        response(Response): The response object to check.
        expected_substring(str): The substring expected to be found in the response content.

    Raises:
        AssertionError: If the expected substring is not found in the response content.
    """
    content = response.text
    assert expected_substring in content


def verify_selected_value(response, select_id, expected_value, is_sysadmin):
    """Verify that the selected value in a dropdown matches the expected value.

    Args:
        response(Response): The response object containing HTML content.
        select_id(str): The id attribute of the select element to check.
        expected_value(str): The expected selected value.
        is_sysadmin(bool): Boolean indicating if the user is a system administrator.

    Raises:
        AssertionError: If the select element or options do not meet the expected conditions.
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the select element by id
    select_element = soup.find('select', id=select_id)
    if not select_element:
        raise AssertionError(f"Select element with id '{select_id}' not found.")

    # Find all option elements within the select
    options = select_element.find_all('option')
    if not options:
        raise AssertionError(f"No options found in select element with id '{select_id}'.")

    # Check if the expected value is selected and if other options are not selected
    for option in options:
        option_value = option.get('value')
        if option_value == expected_value:
            assert option.has_attr('selected')
        else:
            assert not option.has_attr('selected')

    if not is_sysadmin:
        # Verify that all radio buttons and parent lists are disabled for non-sysadmin users
        radio_parent_lists = soup.find_all(name='radio_parent_list')
        assert all(radio.has_attr('disabled') for radio in radio_parent_lists)
        parent_lists = soup.find_all(name='parent_list')
        assert all(parent.has_attr('disabled') for parent in parent_lists)


def verify_select_invalid_mapping(response):
    """Verify that the response contains a list with specific classes in its <li> elements.

    Args:
        response(Response): The response object containing HTML content.

    Raises:
        AssertionError: If the <ul> element or <li> elements do not meet the expected conditions.
    """
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the <ul> element with the specified id
    ul = soup.find('ul', id="ul_system_identifier_doi")
    if not ul:
        raise AssertionError("No <ul> element with id 'ul_system_identifier_doi' found in response.")

    # Check that each <li> element has the required classes
    li_elements = ul.find_all('li')
    check_class = ['list-group-item', 'hide']
    for li in li_elements:
        element_class = li.get('class', [])
        missing_class = [cls for cls in check_class if cls not in element_class]
        assert not missing_class


def verify_schema_definitions(response, schema_name=None):
    """Verify that the schema definitions in the response match the expected values from the database.

    Args:
        response(Response): The response object containing JSON content.
        schema_name(str, optional): Optional schema name to filter the database query.

    Raises:
        AssertionError: If the response JSON does not match the expected JSON from the database.
    """
    def remove_prefix(data):
        """Remove prefixes from dictionary keys recursively.

        Args:
            data(dict | list | any): The input data, which can be a dictionary, a list, or other types.

        Returns:
            dict | list | any: The data with prefixes removed from dictionary keys.
        """
        if isinstance(data, dict):
            return {
                key.split(":")[-1]: remove_prefix(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [remove_prefix(item) for item in data]
        else:
            return data

    select_query = "SELECT schema_name, xsd FROM oaiserver_schema"
    if schema_name:
        select_query += f" WHERE schema_name = '{schema_name}'"
    select_query += ";"

    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(select_query)
            records = cursor.fetchall()

    # Construct the expected JSON from the database records
    expect_json = {}
    for record in records:
        expect_json[record[0]] = remove_prefix(json.loads(record[1]))

    assert response.json() == expect_json


def verify_oai_pmh(response, item_type_id, schema_name):
    """Verify that the OAI-PMH response matches the expected metadata based on the item type mapping.

    Args:
        response(Response): The response object containing the OAI-PMH XML content.
        item_type_id(int): The ID of the item type to retrieve the mapping for.
        schema_name(str): The schema name to filter the mapping.

    Raises:
        AssertionError: If the OAI-PMH response does not match the expected metadata.
    """
    def recursive_set(dic, key):
        """Recursively set values in a dictionary based on specific rules.

        Args:
            dic(dict): The input dictionary to process.
            key(str): The key being set (for logging purposes).

        Returns:
            dict: The processed dictionary with values set according to the rules.
        """
        return_dict = {}
        for k, v in dic.items():
            if key == 'pubdate':
                return_dict[k] = key
            elif isinstance(v, dict):
                return_dict[k] = recursive_set(v, key)
            else:
                split_v = v.split(',')
                if len(split_v) > 1:
                    return_dict[k] = [f"{key}.{item.strip()}" for item in split_v]
                else:
                    return_dict[k] = f"{key}.{v}"
        return return_dict

    def merge_values(existing, new):
        """Merge two values, which can be dictionaries, lists, or other types.

        Args:
            existing (dict | list | any): The existing value to merge into.
                Can be a dictionary, list, or other types.
            new (dict | list | any): The new value to merge from.
                Can be a dictionary, list, or other types.

        Returns:
            dict | list: The merged result of the existing and new values.
                If both are dictionaries, they are merged recursively.
                If both are lists, they are merged while avoiding duplicates.
                For other types, they are combined into a list.
        """
        # If both values are dictionaries, merge them recursively
        if isinstance(existing, dict) and isinstance(new, dict):
            merged = existing.copy()
            for key, value in new.items():
                if key in merged:
                    merged[key] = merge_values(merged[key], value)
                else:
                    merged[key] = value
            return merged

        if not isinstance(existing, list):
            existing = [existing]
        if not isinstance(new, list):
            new = [new]

        # Merge the two lists while avoiding duplicates
        merged_list = existing[:]
        for item in new:
            if item not in merged_list:
                merged_list.append(item)

        return merged_list

    def set_identifiers(metadata, doi):
        """Set the system identifier fields in the metadata based on the provided DOI.

        Args:
            metadata(dict): The original metadata dictionary to update.
            doi(str): The DOI to set in the metadata.

        Returns:
            dict: The metadata dictionary with system identifiers set.
        """
        metadata_dict = copy.deepcopy(metadata)
        metadata_dict['system_identifier_doi'] = {
            'subitem_systemidt_identifier': doi,
            'subitem_systemidt_identifier_type': 'DOI'
        }
        host = response.request.url.split('/oai')[0]
        metadata_dict['system_identifier_uri'] = {
            'subitem_systemidt_identifier': f"{host}/records/2000001",
            'subitem_systemidt_identifier_type': 'URI'
        }
        return metadata_dict

    def get_value_from_path(data_dict, path_list, set_key):
        """Retrieve a value from a nested dictionary based on a list of keys representing the path.

        Args:
            data_dict(dict): The dictionary to retrieve the value from.
            path_list(list): A list of keys representing the path to the desired value.
            set_key(str): The key being set (for logging purposes).

        Returns:
            list or dict or str: The value retrieved from the dictionary based on the provided path.
        """
        target_key = path_list[0]
        if target_key not in data_dict:
            return
        current = data_dict[target_key]
        return_value = []
        if isinstance(current, list):
            for item in current:
                if len(path_list) > 1:
                    sub_value = get_value_from_path(item, path_list[1:], set_key)
                    if sub_value is not None:
                        return_value.append(sub_value)
                else:
                    return_value.append(item)
        else:
            if len(path_list) > 1:
                sub_value = get_value_from_path(current, path_list[1:], set_key)
                if sub_value is not None:
                    return_value.append(sub_value)
            else:
                return_value.append(current)
        if len(return_value) == 0:
            return None
        if len(return_value) == 1:
            return return_value[0]
        return return_value

    def prepare_compare_dict(mapping, expect):
        """Prepare a dictionary for comparison by extracting values based on the mapping.

        Args:
            mapping(dict): The mapping dictionary that defines
                how to extract values from the expected metadata.
            expect(dict): The expected metadata dictionary to extract values from.

        Returns:
            dict: A dictionary containing the extracted values based on the mapping.
        """
        expect_dict = {}
        for key, value in mapping.items():
            if isinstance(value, dict):
                expect_dict[key] = prepare_compare_dict(value, expect)
            else:
                target_value = [value] if not isinstance(value, list) else value
                for item in target_value:
                    if not isinstance(item, str):
                        continue
                    keys = item.split('.')
                    expect_value = get_value_from_path(expect, keys, key)
                    if expect_dict.get(key) is not None:
                        if isinstance(expect_dict[key], list) and expect_value is not None:
                            if isinstance(expect_value, list):
                                expect_dict[key].extend(expect_value)
                            else:
                                expect_dict[key].append(expect_value)
                        elif expect_value is not None:
                            expect_dict[key] = [expect_dict[key], expect_value]
                    else:
                        expect_dict[key] = expect_value
        return expect_dict

    def prepare_data(dic, result_flg=False):
        """Prepare data for comparison by processing the dictionary according to specific rules.

        Args:
            dic(dict | list | any): The input data to prepare,
                which can be a dictionary, a list, or other types.
            result_flg(bool): A flag indicating whether the data being prepared
                is from the result (True) or expected (False).

        Returns:
            dict | list | any: The prepared data, processed according to the rules defined in the function.
        """
        result_dict = {}
        if isinstance(dic, list):
            for item in dic:
                prepared_item = prepare_data(item, result_flg)
                if isinstance(prepared_item, dict):
                    for k, v in prepared_item.items():
                        if v is None:
                            continue
                        if k in result_dict:
                            if isinstance(result_dict[k], list):
                                result_dict[k].append(v)
                            elif isinstance(result_dict[k], dict):
                                result_dict[k].update(v)
                            else:
                                result_dict[k] = [result_dict[k], v]
                        else:
                            result_dict[k] = v
            if not result_dict:
                return dic
        elif not isinstance(dic, dict):
            return dic
        else:
            for k, v in dic.items():
                if result_flg:
                    if k.startswith('@'):
                        result_dict[k] = prepare_data(v, result_flg)
                    else:
                        result_dict[k.split(':')[-1]] = prepare_data(v, result_flg)
                elif k == '@value':
                    if isinstance(v, list) and len(v) == 1:
                        result_dict['#text'] = v[0]
                    else:
                        result_dict['#text'] = v
                elif k == '@attributes':
                    for attr_key, attr_value in v.items():
                        if isinstance(attr_value, list) and len(attr_value) == 1:
                            result_dict[f"@{attr_key}"] = attr_value[0]
                        else:
                            result_dict[f"@{attr_key}"] = attr_value
                elif isinstance(v, dict):
                    result_dict[k.split(':')[-1]] = prepare_data(v, result_flg)
                else:
                    result_dict[k.split(':')[-1]] = v

        if '#text' in result_dict and len(result_dict) == 1:
            return result_dict['#text']
        return result_dict

    def clean_dict(d):
        """Clean a dictionary by removing keys with None values and empty dictionaries or lists.

        Args:
            d(dict | list | any): The input data to clean, which can be a dictionary, a list, or other types.

        Returns:
            dict | list | any: The cleaned data, with keys removed according to the rules defined in the function.
        """
        if not isinstance(d, dict):
            return d
        cleaned = {}
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, dict):
                v = clean_dict(v)
                if not v:
                    continue
            elif isinstance(v, list):
                v = [clean_dict(i) if isinstance(i, dict) else i for i in v if i is not None]
                if not v:
                    continue
            cleaned[k] = v

        if isinstance(cleaned, dict) and cleaned.keys() == {'#text'}:
            return cleaned['#text']
        return cleaned

    def deep_compare(obj1, obj2, key_path=""):
        """Deeply compare two objects (dictionaries, lists, or other types) and return a list of differences.

        Args:
            obj1 (dict | list | any): The first object to compare.
            obj2 (dict | list | any): The second object to compare.
            key_path (str): The current path of keys being compared (used for logging differences).

        Returns:
            list: A list of differences found during the comparison,
            where each difference is represented as a tuple containing the key path,
            the value from obj1, and the value from obj2.
        """
        assert_false_list = []
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            # For dictionaries, compare keys and values recursively
            if set(obj1.keys()) != set(obj2.keys()):
                assert_false_list.append((key_path, obj1, obj2))
                return assert_false_list
            for key in obj1:
                assert_false_list.extend(deep_compare(obj1[key], obj2[key], key_path + f".{key}"))
            return assert_false_list

        if isinstance(obj1, list) and isinstance(obj2, list):
            # For lists, compare ignoring order
            if len(obj1) != len(obj2):
                assert_false_list.append((key_path, obj1, obj2))
                return assert_false_list
            list_compare = []
            for item1 in obj1:
                for item2 in obj2:
                    list_compare.append(deep_compare(item1, item2, key_path + "[]"))
            if all(x != [] for x in list_compare):
                assert_false_list.append((key_path, obj1, obj2))
            return assert_false_list

        # For other types, use simple comparison
        if obj1 != obj2:
            assert_false_list.append((key_path, obj1, obj2))
        return assert_false_list

    response_dict = xmltodict.parse(response.text)

    # Retrieve the mapping from the database based on the item_type_id and schema_name
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            select_query = f"SELECT mapping FROM item_type_mapping WHERE item_type_id = {item_type_id} ORDER BY created DESC;"
            cursor.execute(select_query)
            record = cursor.fetchone()

            uuid_query = "SELECT object_uuid FROM pidstore_pid WHERE pid_type = 'recid' AND pid_value = '2000001';"
            cursor.execute(uuid_query)
            uuid_record = cursor.fetchone()
            metadata_query = f"SELECT json FROM item_metadata WHERE id = '{uuid_record[0]}';"
            cursor.execute(metadata_query)
            metadata_record = cursor.fetchone()
            doi_query = f"SELECT pid_value FROM pidstore_pid WHERE pid_type = 'doi' AND object_uuid = '{uuid_record[0]}';"
            cursor.execute(doi_query)
            doi_record = cursor.fetchone()

    # Set the system identifier fields in the metadata based on the retrieved DOI
    metadata_mapping = set_identifiers(metadata_record[0], doi_record[0])

    # Construct the expected JSON based on the mapping and the retrieved metadata
    expect_json = {}
    for key, value in record[0].items():
        if schema_name in value:
            target_value = value[schema_name]
            for target_key in target_value:
                if target_key not in expect_json:
                    expect_json[target_key] = recursive_set(target_value[target_key], key)
                else:
                    # Merge existing and new values
                    existing_value = expect_json[target_key]
                    new_value = recursive_set(target_value[target_key], key)
                    expect_json[target_key] = merge_values(existing_value, new_value)

    target_response = response_dict['OAI-PMH']['GetRecord']['record']['metadata']
    target_metadata = target_response[list(target_response.keys())[0]]
    missing_keys = []
    assert_result = []
    assert_sucess = True

    print('target_metadata:', target_metadata)
    for key, value in target_metadata.items():
        if key.startswith('@'):
            continue
        target_key = key.split(':')[-1]
        if key == 'oaire:version':
            target_key = 'versiontype'
        if key == 'jpcoar:publisher':
            target_key = 'publisher_jpcoar'
        if key == 'dcterms:date':
            target_key = 'date_dcterms'
        if target_key not in expect_json:
            missing_keys.append(target_key)
            continue
        prepare_dict = prepare_compare_dict(expect_json[target_key], metadata_mapping)
        expect_dict = prepare_data(prepare_dict, result_flg=False)
        expect_dict = clean_dict(expect_dict)
        result_value = prepare_data(value, result_flg=True)
        assert_result.extend(deep_compare(expect_dict, result_value, key))
    if missing_keys:
        print("Missing keys in expected JSON:", missing_keys)
        assert_sucess = False
    if assert_result:
        for key_path, expect, result in assert_result:
            print("Mismatch found at:", key_path)
            print("Expected:", expect)
            print("Result:", result)
        assert_sucess = False
    assert assert_sucess


def verify_success(response, row_count, file_path):
    """Verify that the response indicates a successful operation and that the database has been updated accordingly.

    Args:
        response(Response): The response object to check.
        row_count(str): The expected row count in the item_type_mapping table.
        file_path(str): The path to the file containing the expected mapping.
    """
    response_json = response.json()
    assert response_json == {"msg": "Successfully saved new mapping."}

    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM item_type_mapping;")
            count = cursor.fetchone()[0]
            assert count == int(row_count) + 1

            with open(file_path, "r", encoding="utf-8") as f:
                expected_mapping = json.load(f)
            select_query = "SELECT mapping FROM item_type_mapping ORDER BY created DESC LIMIT 1;"
            cursor.execute(select_query)
            record = cursor.fetchone()
            assert record[0] == expected_mapping['mapping']


def verify_unexpected_error(response, row_count):
    """Verify that the response indicates an 'Unexpected error' and that the database has not been modified.

    Args:
        response(Response): The response object to check.
        row_count(str): The expected row count in the item_type_mapping table.
    """
    response_json = response.json()
    assert response_json == {"msg": "Unexpected error occured."}

    verify_record_count(row_count)


def verify_header_error(response, row_count):
    """Verify that the response indicates a 'Header Error' and that the database has not been modified.

    Args:
        response(Response): The response object to check.
        row_count(str): The expected row count in the item_type_mapping table.
    """
    response_json = response.json()
    assert response_json == {"msg": "Header Error"}

    verify_record_count(row_count)


def verify_duplicate_error(response, row_count):
    """Verify that the response indicates a 'Duplicate mapping' error and that the database has not been modified.

    Args:
        response(Response): The response object to check.
        row_count(str): The expected row count in the item_type_mapping table.
    """
    response_json = response.json()
    response_keys = list(response_json.keys())
    assert all(key in response_keys for key in ['msg', 'duplicate'])
    assert response_json['msg'] == "Duplicate mapping as below:"
    assert response_json['duplicate'] == True

    verify_record_count(row_count)


def verify_location_header(response, expected_location, host):
    """Verify that the Location header in the response matches the expected location.

    Args:
        response(Response): The response object to check.
        expected_location(str): The expected location to be included in the Location header.
        host(str): The host URL to be included in the expected Location header.
    """
    location_header = response.headers.get('Location')
    encoded_expected_location = urlencode({'next': expected_location})
    full_expected_location = f"{host}/login/?{encoded_expected_location}"
    assert location_header == full_expected_location


def verify_bad_request(response):
    """Verify that the response indicates a 'Bad Request' error.

    Args:
        response(Response): The response object to check.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    if not title:
        raise AssertionError("No <title> element found in response.")
    assert 'Bad Request' in title.text


def verify_forbidden(response, row_count=None):
    """Verify that the response indicates a 'Forbidden' error and optionally check the database row count.

    Args:
        response(Response): The response object to check.
        row_count(str, optional): The expected row count
            in the item_type_mapping table to verify that it has not changed.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    p = soup.find('p')
    if not p:
        raise AssertionError("No <p> element found in response.")
    assert 'You do not have sufficient permissions to view this page.' in p.text

    if row_count is not None:
        verify_record_count(row_count)


def verify_not_found(response):
    """Verify that the response indicates a 'Not Found' error.

    Args:
        response(Response): The response object to check.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    p = soup.find('p')
    if not p:
        raise AssertionError("No <p> element found in response.")
    assert 'The page you are looking for could not be found.' in p.text


def verify_internal_server_error(response):
    """Verify that the response indicates an 'Internal Server Error'.

    Args:
        response(Response): The response object to check.
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.find('h1')
    if not h1:
        raise AssertionError("No <h1> element found in response.")
    assert 'Internal server error' in h1.text


def verify_record_count(row_count):
    """Verify that the row count in the item_type_mapping table matches the expected count.

    Args:
        row_count(str): The expected row count in the item_type_mapping table.
    """
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM item_type_mapping;")
            count = cursor.fetchone()[0]
            assert count == int(row_count)
