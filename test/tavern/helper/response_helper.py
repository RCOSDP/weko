from bs4 import BeautifulSoup
from box import Box
from datetime import datetime, timezone
import json
import random
import string
from urllib.parse import urlencode, urlparse

from helper.config import RESOURCE_TYPE_URI, SWORD_CONFIG_FILE
from helper.verify_database_helper import connect_db


def response_save_next_path(response):
    """Save data from "{host}/workflow/activity/init"'s response
    
    Args:
        response (requests.models.Response): response from {host}/workflow/activity/init
    
    Returns:
        Box: next_path and activity_id
            next_path (str): next path
            activity_id (str): activity id
    """
    json = response.json()
    return Box({
        'next_path': json['data']['redirect'],
        'activity_id': json['data']['redirect'].split('/')[-1],
        'activity_start_time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    })

def response_save_recid(response):
    """Save data from "{host}/api/deposits/items"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/deposits/items
        
    Returns:
        Box: recid
            recid (str): recid
    """
    json = response.json()
    return Box({'recid': json['id']})

def response_save_register_data(response, file_name):
    """Save data from target file
    
    Args:
        response (requests.models.Response): response from {host}{next_path}
        file_name (str): name of the file containing the data to be registered
    
    Returns:
        Box: register_data
            register_data (str): register data
    """
    with open('request_params/' + file_name, 'r') as f:
        return Box({'register_data': f.read()})

def response_save_tree_data(response):
    """Save data from "{host}/api/tree/{recid}"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/tree/{recid}
    
    Returns:
        Box: tree_data
            tree_data (list): index id list
    """
    json = response.json()
    return Box({'tree_data': [t['id'] for t in json]})

def response_save_identifier_grant(response):
    """Save data from "{host}/workflow/activity/detail/{activity_id}?page=1&size=20"'s response
    
    Args:
        response (requests.models.Response): response from {host}/workflow/activity/detail/{activity_id}?page=1&size=20
    
    Returns:
        Box: identifier_grant
            identifier_grant (str): identifier grant written in json string
    """
    soup = BeautifulSoup(response.content, 'html.parser')
    jalc_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_1'})
    jalc_doi_suffix = jalc_doi_suffix_input['value'] if jalc_doi_suffix_input else ''
    try:
        jalc_doi_link = soup.find('span', {'name': 'idf_grant_link_1'}).text
    except:
        jalc_doi_link = ''
    jalc_cr_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_2'})
    jalc_cr_doi_suffix = jalc_cr_doi_suffix_input['value'] if jalc_cr_doi_suffix_input else ''
    try:
        jalc_cr_doi_link = soup.find('span', {'name': 'idf_grant_link_2'}).text
    except:
        jalc_cr_doi_link = ''
    jalc_dc_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_3'})
    jalc_dc_doi_suffix = jalc_dc_doi_suffix_input['value'] if jalc_dc_doi_suffix_input else ''
    try:
        jalc_dc_doi_link = soup.find('span', {'name': 'idf_grant_link_3'}).text
    except:
        jalc_dc_doi_link = ''
    ndl_jalc_doi_suffix_input = soup.find('input', {'name': 'idf_grant_input_4'})
    ndl_jalc_doi_suffix = ndl_jalc_doi_suffix_input['value'] if ndl_jalc_doi_suffix_input else ''
    try:
        ndl_jalc_doi_link = soup.find('span', {'name': 'idf_grant_link_4'}).text
    except:
        ndl_jalc_doi_link = ''
    crni_link_span = soup.find('span', {'name': 'idf_grant_link_5'})
    crni_link = crni_link_span.text if crni_link_span else ''
    return Box({
        'identifier_grant': json.dumps({
            'jalc_doi_suffix': jalc_doi_suffix,
            'jalc_doi_link': jalc_doi_link,
            'jalc_cr_doi_suffix': jalc_cr_doi_suffix,
            'jalc_cr_doi_link': jalc_cr_doi_link,
            'jalc_dc_doi_suffix': jalc_dc_doi_suffix,
            'jalc_dc_doi_link': jalc_dc_doi_link,
            'ndl_jalc_doi_suffix': ndl_jalc_doi_suffix,
            'ndl_jalc_doi_link': ndl_jalc_doi_link,
            'crni_link': crni_link
        })
    })

def response_save_author_prefix_settings(response):
    """Save data from "{host}/api/items/author_prefix_settings"'s response

    Args:
        response (requests.models.Response): response from {host}/api/items/author_prefix_settings

    Returns:
        Box: settings
            settings (list): author prefix settings
    """
    settings = [j['scheme'] for j in response.json()]
    settings.insert(0, None)
    return Box({'settings': settings})

def response_save_group_list(response):
    """Save data from "{host}/accounts/settings/groups/grouplist"'s response

    Args:
        response (requests.models.Response): response from {host}/accounts/settings/groups/grouplist
    
    Returns:
        Box: group_list
            group_list (list): group list
    """
    return Box({'group_list': list(response.json().keys())})

def response_save_url(response):
    """Save data from "{host}/api/deposits/items"'s response

    Args:
        response (requests.models.Response): response from {host}/api/deposits/items
    
    Returns:
        Box: url
            url (dict): url lists
    """
    url = response.json()['links']
    recid = url['r'].split('/')[-1]
    return Box({'url': url, 'recid': recid})

def response_save_file_upload_info(response, file_key, item_id):
    """Save data from "{url.bucket}"/[file_name]"'s response
    
    Args:
        response (requests.models.Response): response from {url.bucket}/[file_name]
        file_key (str): key of file
        item_id (str): item id
    
    Returns:
        Box:
            file_upload_info (dict): file upload info
            file_metadata (dict): file metadata
    """
    file_upload_info = response.json()
    with open('request_params/item_type_template/schema/item_type_' + str(item_id) + '.json', 'r') as f:
        schema = json.load(f)
    file_schema = schema['schema'][file_key]
    file_metadata = {}
    for key in file_schema['items']['properties'].keys():
        if key == 'url':
            parse = urlparse(file_upload_info['links']['self'])
            url = parse.scheme + '://' + parse.netloc + '/record/2000001/files/' + file_upload_info['key']
            file_metadata[key] = {'url': url} 
        elif key == 'date':
            created_str = file_upload_info['created']
            created = datetime.strptime(created_str, '%Y-%m-%dT%H:%M:%S.%f%z').date()
            file_metadata[key] = [{'dateType': 'Available', 'dateValue': created.strftime('%Y-%m-%d')}]
        elif key == 'format':
            file_metadata[key] = file_upload_info['mimetype']
        elif key == 'filename':
            file_metadata[key] = file_upload_info['key']
        elif key == 'filesize':
            size = file_upload_info['size']
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            count = 0
            while size > 1024:
                size /= 1024
                count += 1
            int_size = int(size)
            if size > int_size:
                int_size += 1
            file_metadata[key] = [{'value': str(int_size) + ' ' + units[count]}]
        elif key == 'accessrole':
            file_metadata[key] = 'open_access'
    file_metadata['version_id'] = file_upload_info['version_id']

    return Box({'file_upload_info': json.dumps(file_upload_info), 'file_metadata': json.dumps({file_key: [file_metadata]})})

def response_save_csrf_token(response):
    """Save CSRF token from response

    Args:
        response (requests.models.Response): response from {host}/accounts/settings/groups/grouplist

    Returns:
        Box: csrf_token
            csrf_token (str): CSRF token value
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find(id='csrf_token').get('value')
    return Box({'csrf_token': csrf_token})

def response_save_url_described_in_email(response, target, save_key):
    """Extract a URL from an email file and save it in a Box object.

    Args:
        response (requests.models.Response): The response object (not used in this function).
        target (str): The target email file name to read from the 'mail' directory.
        save_key (str): The key under which the extracted URL will be saved in the Box object.

    Returns:
        Box: A Box object containing the extracted URL under the specified save_key.
    Raises:
        ValueError: If no URL is found in the email file.
    """
    with open('mail/' + target) as f:
        lines = f.readlines()
    url = ''
    for line in lines:
        if 'http://' in line or 'https://' in line:
            idx = line.find('http')
            url = line[idx:].strip()
            break
    if not url:
        raise ValueError(f'No URL found in the email for target: {target}')
    return Box({save_key: url})

def response_save_register_data_with_change(response, file_name, key_dict_file, change_type):
    """Save and modify register data from a file based on the specified change type.
    
    Args:
        response (requests.models.Response): response from {host}{next_path}
        file_name (str): name of the file containing the data to be registered
        key_dict_file (str): name of the file containing the keys for title, resource type, and creator
        change_type (int): type of change to apply to the register data
            1: Title variations in full-width/half-width, uppercase/lowercase, and character form
            2: Conversion within the same character type
            3: Resource type variations
            4: Creator name variations
            5: Creator order change
            6: Change creator name to 'たかはし さぶろう'
            
    Returns:
        Box: register_data
            register_data (str): modified register data in JSON format"""
    with open('request_params/' + file_name, 'r') as f:
        register_data = json.load(f)
    
    with open('request_params/' + key_dict_file, 'r') as f:
        key_dict = json.load(f)
    
    # get title
    title_key = key_dict.get('title')
    title_key_split = title_key.split('.')
    title = register_data[title_key_split[0]][int(title_key_split[1])][title_key_split[2]]
    
    # get resource type
    resource_type_key = key_dict.get('resource_type')
    resource_type_key_split = resource_type_key.split('.')
    resource_type = register_data[resource_type_key_split[0]][resource_type_key_split[1]]

    # get creator
    creator_key = key_dict.get('creator')
    creator = register_data[creator_key]
    
    if change_type == 1:
        # Title variations in full-width/half-width, uppercase/lowercase, and character form
        converted_title_chars = []
        for c in title:
            choices = [c]
            # Full-width and half-width variations
            if c.isascii() and c.isalpha():
                choices.append(c.upper())
                choices.append(c.lower())
                offset = ord(c.lower()) - ord('a')
                choices.append(chr(ord('ａ') + offset))
                choices.append(chr(ord('Ａ') + offset))
            # Full-width and half-width digits
            elif c.isdigit():
                choices.append(chr(ord('０') + int(c)))
            converted_title_chars.append(random.choice(list(set(choices))))
        register_data[title_key_split[0]][int(title_key_split[1])][title_key_split[2]] = ''.join(converted_title_chars)
    elif change_type == 2:
        # conversion within the same character type
        while True:
            converted_title_chars = []
            for c in title:
                if c in string.ascii_lowercase:
                    converted_title_chars.append(random.choice(string.ascii_lowercase))
                elif c in string.ascii_uppercase:
                    converted_title_chars.append(random.choice(string.ascii_uppercase))
                elif c in string.digits:
                    converted_title_chars.append(random.choice(string.digits))
                else:
                    converted_title_chars.append(c)
            converted_title = ''.join(converted_title_chars)
            if converted_title != title:
                register_data[title_key_split[0]][int(title_key_split[1])][title_key_split[2]] = converted_title
                break
    elif change_type == 3:
        # Resource type variations
        while True:
            replaced_resource_type = random.choice(list(RESOURCE_TYPE_URI.keys()))
            if replaced_resource_type != resource_type:
                register_data[resource_type_key_split[0]][resource_type_key_split[1]] = replaced_resource_type
                register_data[resource_type_key_split[0]][resource_type_key_split[1].replace('type', 'uri')] = RESOURCE_TYPE_URI[replaced_resource_type]
                break
    elif change_type == 4:
        # Creator name variations
        while True:
            name_range = (0x4E00, 0x9FAF)
            random_name = ''.join(random.choice([chr(random.randint(*name_range)) for _ in range(2)]))
            creator_name = creator[0]['creatorNames'][0]['creatorName']
            replaced_creator_name = creator_name.replace(creator_name[:2], random_name)
            if replaced_creator_name != creator_name:
                register_data[creator_key][0] = {'creatorNames': [{'creatorName': replaced_creator_name}]}
                break
    elif change_type == 5:
        # Creator order change
        creators = []
        creator_1 = register_data[creator_key][0]
        creator_2 = register_data[creator_key][1]
        creators.append(creator_2)
        creators.append(creator_1)
        register_data[creator_key] = creators
    elif change_type == 6:
        # change creator name
        register_data[creator_key][0]['creatorNames'][0]['creatorName'] = 'たかはし さぶろう'

    return Box({'register_data': json.dumps(register_data)})

def response_save_author_search(response):
    """Save author ID from "{host}/api/author/search"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/author/search
        
    Returns:
        Box: author_id
            author_id (str): author ID"""
    json = response.json()
    return Box({'author_id': json['hits']['hits'][0]['_id']})

def response_save_changed_data(response):
    """Save changed data from "{host}/workflow/activity/detail/{activity_id}?status="'s response

    Args:
        response (requests.models.Response): response from {host}/api/records/{recid}
        
    Returns:
        Box: changed_data
            changed_data (dict): changed data from the response
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    invenio_records = soup.find('invenio-records')
    return Box({'changed_data': invenio_records['record']})

def response_save_notification_token(response):
    """Save notification token from response

    Args:
        response (requests.models.Response): response from {host}/account/settings/notifications

    Returns:
        Box: notification_token
            notification_token (str): notification token value
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find(id='notifications-csrf_token')
    if token_input:
        return Box({'notification_token': token_input['value']})
    else:
        raise ValueError('Notification token not found in the response.')
