import json
import psycopg2

from helper.config import DATABASE, VERSION_TYPE_URI, ACCESS_RIGHT_TYPE_URI, RESOURCE_TYPE_URI, WEKO_RECORDS_UI_LICENSE_DICT

VERSION_TYPE_URI_KEYS = list(VERSION_TYPE_URI.keys())
ACCESS_RIGHT_TYPE_URI_KEYS = list(ACCESS_RIGHT_TYPE_URI.keys())
RESOURCE_TYPE_URI_KEYS = list(RESOURCE_TYPE_URI.keys())

def create_itemtype_template():
    """Create item type templates
    
    Args:
        None
        
    Returns:
        None
    """
    # Get item type schemas
    schemas = get_item_type_schemas()
    for schema in schemas:
        # Create schema for output to file
        name = schema[1]
        target_schema = schema[2]
        required = target_schema['required']
        properties = target_schema['properties']
        result = {
            'name': name,
            'schema': create_property_schema(properties, required)
        }
        file_name = 'item_type_' + str(schema[0])
        with open('request_params/item_type_template/schema/' + file_name + '.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, indent=4, ensure_ascii=False))
        
        # Create template for entering data
        template = create_template(result['schema'])
        template['$schema'] = '/items/jsonschema/' + str(schema[0])
        template['shared_user_id'] = -1
        with open('request_params/item_type_template/template/' + file_name + '.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(template, indent=4, ensure_ascii=False))
        
        # Create template for generating random data
        random_template, _ = create_random_template(result['schema'])
        random_template['$schema'] = '/items/jsonschema/' + str(schema[0])
        random_template['shared_user_id'] = -1
        with open('request_params/item_type_template/template/' + file_name + '_random.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(random_template, indent=4, ensure_ascii=False))

def get_item_type_schemas():
    """Get item type schemas

    Args:
        None

    Returns:
        list: item type schemas
    """
    # Connect to database
    conn = psycopg2.connect(
        host=DATABASE['host'],
        port=DATABASE['port'],
        dbname=DATABASE['dbname'],
        user=DATABASE['user'],
        password=DATABASE['password']
    )
    cur = conn.cursor()

    try:
        # Get item type schemas
        cur.execute('SELECT t.id, tn.name, t.schema FROM item_type t\
                    INNER JOIN item_type_name tn ON t.name_id = tn.id\
                    WHERE t.harvesting_type = false AND t.is_deleted = false')
        records = cur.fetchall()
        return records
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def create_property_schema(json, required):
    """Create property schema
    
    Args:
        json (dict): JSON data
        required (list): Required keys
        
    Returns:
        dict: Property schema
    """
    result = {}
    for k, v in json.items():
        target_result = {}
        if v.get('title'):
            target_result['title'] = v['title']
        if v.get('type'):
            target_result['type'] = v['type']
        if v.get('format'):
            target_result['format'] = v['format']
        child_required = v.get('required', [])
        if v.get('format'):
            if v['format'] == 'datetime':
                target_result['min_date'] = '1000-01-01'
                target_result['max_date'] = '2999-12-31'
            if v['format'] == 'select' or v['format'] == 'radios':
                target_result['enum'] = v.get('enum', [])
                if target_result['enum']:
                    target = list(filter(None, target_result['enum']))
                    if set(target).issubset(set(VERSION_TYPE_URI_KEYS)):
                        # target_result['uri'] is contained within VERSION_TYPE_URI_KEYS
                        target_result['uri'] = VERSION_TYPE_URI
                    elif set(target).issubset(set(ACCESS_RIGHT_TYPE_URI_KEYS)):
                        # target_result['uri'] is contained within ACCESS_RIGHT_TYPE_URI_KEYS
                        target_result['uri'] = ACCESS_RIGHT_TYPE_URI
                    elif set(target).issubset(set(RESOURCE_TYPE_URI_KEYS)):
                        # target_result['uri'] is contained within RESOURCE_TYPE_URI_KEYS
                        target_result['uri'] = RESOURCE_TYPE_URI
                if k == 'licensetype':
                    licenses = [l['value'] for l in WEKO_RECORDS_UI_LICENSE_DICT]
                    licenses.insert(0, None)
                    target_result['enum'] = licenses
        if v.get('type') and v['type'] == 'array':
            if v.get('minItems'):
                target_result['min_items'] = v.get('minItems')
            if v.get('maxItems'):
                target_result['max_items'] = v.get('maxItems')
        if v.get('properties'):
            target_result['properties'] = create_property_schema(v['properties'], child_required)
        if v.get('items'):
            target_result['items'] = create_items(v['items'])
        if k in required:
            target_result['required'] = True
        result[k] = target_result
    return result

def create_items(items):
    """Create items
    
    Args:
        items (dict): Items
    """
    result = {}
    if items.get('title'):
        result['title'] = items['title']
    if items.get('type'):
        result['type'] = items['type']
    if items.get('format'):
        result['format'] = items['format']
    required = items.get('required', [])
    if items.get('properties'):
        result['properties'] = create_property_schema(items['properties'], required)
    return result

def create_template(json):
    """Create template
    
    Args:
        json (dict): JSON data
        
    Returns:
        dict: Template"""
    text_type = ['text', 'textarea', 'select', 'radios']
    result = {}
    for k, v in json.items():
        if v.get('title') == 'Identifier Registration'\
            or v.get('title').startswith('Persistent Identifier')\
            or v.get('title') == 'File Information':
            continue
        if v.get('format'):
            if v.get('format') == 'datetime':
                result[k] = 'yyyy-mm-dd'
            if v.get('format') in text_type:
                result[k] = ''
            if v.get('format') == 'object':
                result[k] = create_template(v['properties'])
            if v.get('format') == 'array':
                result[k] = create_array_template(v['items'])
        elif v.get('type'):
            if v.get('type') == 'object':
                result[k] = create_template(v['properties'])
            if v.get('type') == 'array':
                result[k] = create_array_template(v['items'])
    
    return result

def create_array_template(json):
    """Create array template

    Args:
        json (dict): JSON data

    Returns:
        dict: Array template
    """
    result = []
    if json.get('properties'):
        result.append(create_template(json['properties']))
    return result

def create_random_template(json):
    """Create template for generating random data
    
    Args:
        json (dict): JSON data
        
    Returns:
        dict: Random template
    """
    result = {}
    has_uri = False
    for k, v in json.items():
        if v.get('title') == 'Identifier Registration' or v.get('title').startswith('Persistent Identifier') or v.get('title') == 'File Information':
            continue
        if v.get('format'):
            if v.get('format') == 'datetime':
                result[k] = {
                    'type': 'date',
                    'min': '1000-01-01',
                    'max': '2999-12-31'
                }
            if v.get('format') == 'text' or v.get('format') == 'textarea':
                result[k] = {
                    'type': 'string',
                    'min': 1,
                    'max': 255
                }
            if v.get('format') == 'select' or v.get('format') == 'radios':
                result[k] = {
                    'type': 'select',
                    'options': v.get('enum', [])
                }
                if v.get('uri'):
                    result[k]['uri'] = v['uri']
                    has_uri = True
            if v.get('format') == 'object':
                properties, child_has_uri = create_random_template(v['properties'])
                if not child_has_uri:
                    result[k] = {
                        'type': 'dict',
                        'properties': properties
                    }
                else:
                    if len(properties.keys()) == 2:
                        result[k] = create_pair_random_template(properties)
                    else:
                        result[k] = create_semi_pair_ramdom_template(properties)
            if v.get('format') == 'array':
                result[k] = create_array_random_template(v['items'])
                if v.get('min_items'):
                    result[k]['min'] = v['min_items']
                if v.get('max_items'):
                    result[k]['max'] = v['max_items']
        elif v.get('type'):
            if v.get('type') == 'object':
                properties, child_has_uri = create_random_template(v['properties'])
                if not child_has_uri:
                    result[k] = {
                        'type': 'dict',
                        'properties': properties
                    }
                else:
                    if len(properties.keys()) == 2:
                        result[k] = create_pair_random_template(properties)
                    else:
                        result[k] = create_semi_pair_ramdom_template(properties)
            if v.get('type') == 'array':
                result[k] = create_array_random_template(v['items'])
                if v.get('min_items'):
                    result[k]['min'] = v['min_items']
                if v.get('max_items'):
                    result[k]['max'] = v['max_items']
    
    return result, has_uri

def create_array_random_template(json):
    """Create array random template
    
    Args:
        json (dict): JSON data
        
    Returns:
        dict: Array random template
    """
    result = {}
    result['type'] = 'list'
    result['items'] = {
        'type': 'dict' if json.get('type') == 'object' else json.get('type')
    }
    if json.get('properties'):
        properties, child_has_uri = create_random_template(json['properties'])
        if not child_has_uri:
            result['items']['type'] = result['items']['type']
            result['items']['properties'] = properties
        else:
            if len(properties.keys()) == 2:
                result['items'] = create_pair_random_template(properties)
            else:
                result['items'] = create_semi_pair_ramdom_template(properties)
    return result

def create_pair_random_template(properties):
    """Create pair random template

    Args:
        properties (dict): Properties
        
    Returns:
        dict: Pair random template
    """
    result = {'type': 'pair'}
    keys = list(properties.keys())
    select_key = ''
    for key in keys:
        if properties[key]['type'] == 'select':
            select_key = key
            result['keys'] = [key]
            break
    for key in keys:
        if key not in result['keys']:
            result['keys'].append(key)
    pairs = []
    for op in properties[select_key]['options']:
        pairs.append([op, properties[select_key]['uri'].get(op, '')])
    result['pairs'] = pairs
    return result

def create_semi_pair_ramdom_template(properties):
    """Create semi-pair random template

    Args:
        properties (dict): Properties
        
    Returns:
        dict: Semi-pair random template
    """
    def get_common_prefix(str1, str2):
        """Get common prefix of two strings"""
        min_len = min(len(str1), len(str2))
        for i in range(min_len):
            if str1[i] != str2[i]:
                return str1[:i]
        return str1[:min_len]
    result = {'type': 'semi_pair'}
    keys = list(properties.keys())
    select_key = ''
    for key in keys:
        if properties[key]['type'] == 'select':
            select_key = key
            result['keys'] = [key]
            break
    for key in keys:
        if key in result['keys']:
            continue
        prefix = get_common_prefix(key, result['keys'][0])
        if prefix != 'subitem_':
            result['keys'].append(key)
        else:
            if not result.get('properties'):
                result['properties'] = {}
            result['properties'][key] = properties[key]
    pairs = []
    for op in properties[select_key]['options']:
        pairs.append([op, properties[select_key]['uri'].get(op, '')])
    result['pairs'] = pairs
    return result

if __name__ == '__main__':
    create_itemtype_template()