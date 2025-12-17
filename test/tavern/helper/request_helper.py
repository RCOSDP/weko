import json
import random


def request_create_validate_param(data, file_metadata=None):
    """Create params for {host}/api/items/validate
    
    Args:
        data (str): register data written in json string
        file_upload_info (str): file upload info written in json string
    
    Returns:
        dict: params for {host}/api/items/validate
            item_id (str): item id
            data (dict): register data
    """
    data = json.loads(data)
    item_id = data['$schema'].split('/')[-1]
    params = {
        'item_id': item_id,
        'data': data
    }
    if file_metadata is not None:
        metadata = json.loads(file_metadata)
        keys = list(metadata.keys())
        params['data'][keys[0]] = metadata[keys[0]]
    return params

def request_create_save_activity_data_param(activity_id, data, title_key):
    """ Create params for {host}/workflow/save_activity_data
    
    Args:
        activity_id (str): activity_id
        data (str): register data written in json string
        title_key (str): key of title from item type schema
    
    Returns:
        dict: params for {host}/workflow/save_activity_data
            activity_id (str): activity id
            shared_user_id (int): shared user id
            title (str): title
    """
    data = json.loads(data)
    try:
        if len(title_key.split('.')) == 3:
            title = data[title_key.split('.')[0]][int(title_key.split('.')[1])][title_key.split('.')[2]]
        else:
            title = data[title_key.split('.')[0]][title_key.split('.')[1]]
    except:
        title = ''
    return {
        'activity_id': activity_id,
        'shared_user_id': data['shared_user_id'],
        'title': title
    }

def request_create_save_param(data, url=None, file_upload_info=None, file_metadata=None):
    """Create params for {host}/items/iframe/model/save
    
    Args:
        data (str): register data written in json string
        url (str): url written in json string
        file_upload_info (str): file upload info written in json string
        file_metadata (str): file metadata written in json string
        
    Returns:
        dict: params for {host}/items/iframe/model/save
            endpoints (dict): endpoints
            files (list): files
            metainfo (dict): metainfo
    """
    data = json.loads(data)
    params = {
        'endpoints': {
            'initialization': '/api/deposits/items'
        },
        'files': [],
        'metainfo': data
    }
    if url is not None:
        url_dict = json.loads(url.replace('\'', '"'))
        for k, v in url_dict.items():
            params['endpoints'][k] = v
    if file_upload_info is not None:
        file_info = json.loads(file_upload_info)
        file_info['completed'] = True
        file_info['filename'] = file_info['key']
        file_info['multipart'] = False
        file_info['progress'] = 100
        file_info['uri'] = False
        params['files'].append(file_info)
    if file_metadata is not None:
        metadata = json.loads(file_metadata)
        keys = list(metadata.keys())
        params['metainfo'][keys[0]] = metadata[keys[0]]
    return params

def request_create_deposits_items_param(data=None):
    """Create params for {host}/api/deposits/items
    
    Args:
        data (str): register data written in json string
    
    Returns:
        dict: params for {host}/api/deposits/items
            $schema (str): schema
    """
    if data is None:
        return {}
    data = json.loads(data)
    return {
        '$schema': data['$schema']
    }

def request_create_deposits_redirect_param(data, title_key, file_metadata=None):
    """Create params for {host}/api/deposits/redirect/{recid}
    
    Args:
        data (str): register data written in json string
        title_key (str): key of title from item type schema
    
    Returns:
        dict: params for {host}/api/deposits/redirect/{recid}
            $schema (str): schema
            lang (str): lang
            pubdate (str): publish date
            shared_user_id (int): shared user id
            title (str): title
            [key] (list or dict): item data with value
            deleted_items (list): item keys with no value 
    """
    data = json.loads(data)
    if file_metadata is not None:
        metadata = json.loads(file_metadata)
        keys = list(metadata.keys())
        data[keys[0]] = metadata[keys[0]]
    item_id = data['$schema'].split('/')[-1]
    try:
        if len(title_key.split('.')) == 3:
            title = data[title_key.split('.')[0]][int(title_key.split('.')[1])][title_key.split('.')[2]]
        else:
            title = data[title_key.split('.')[0]][title_key.split('.')[1]]
    except:
        title = ''

    return_params = {
        '$schema': data['$schema'],
        'lang': 'ja',
        'pubdate': data['pubdate'],
        'shared_user_id': data['shared_user_id'],
        'title': title
    }

    with open('request_params/item_type_template/template/item_type_' + item_id + '.json', 'r') as f:
        template = json.load(f)
    template_item_keys = [key for key in template.keys() if key.startswith('item_')]
    deleted_items = []
    for key in template_item_keys:
        if key not in data.keys():
            deleted_items.append(key)
        else:
            return_params[key] = data[key]
    return_params['deleted_items'] = deleted_items
    return return_params

def request_create_deposits_items_index_param(indexes):
    """Create params for {host}/api/deposits/items/{recid}
    
    Args:
        indexes (str): index id list written in string
    
    Returns:
        dict: params for {host}/api/deposits/items/{recid}
            actions (str): actions
            index (str): index id what item belongs to
    """
    return {
        'actions': 'private',
        'index': [random.choice(eval(indexes))]
    }

def request_create_action_param(action_version, link_data = None, identifier = None, community = None):
    """Create params for {host}/workflow/activity/action/{activity_id}/{action_id}
    
    Args:
        action_version (str): action version
        link_data (str): link data written in json string
        identifier (str): identifier written in json string
        community (str): community id
    
    Returns:
        dict: params for {host}/workflow/activity/action/{activity_id}/{action_id}
            action_version (str): action version
            link_data (dict): link data
            identifier_grant (str): identifier grant
            identifier_grant_crni_link (str): identifier grant crni link
            identifier_grant_jalc_cr_doi_link (str): identifier grant jalc cr doi link
            identifier_grant_jalc_cr_doi_suffix (str): identifier grant jalc cr doi suffix
            identifier_grant_jalc_dc_doi_link (str): identifier grant jalc dc doi link
            identifier_grant_jalc_dc_doi_suffix (str): identifier grant jalc dc doi suffix
            identifier_grant_jalc_doi_link (str): identifier grant jalc doi link
            identifier_grant_jalc_doi_suffix (str): identifier grant jalc doi suffix
            identifier_grant_ndl_jalc_doi_link (str): identifier grant ndl jalc doi link
            identifier_grant_ndl_jalc_doi_suffix (str): identifier grant ndl jalc doi suffix
            community (str): community id
            commond (str): commond
            temporary_save (int): temporary save
    """
    return_params = {
        'action_version': action_version
    }
    if link_data is not None:
        return_params['link_data'] = link_data
    if identifier is not None:
        identifier = json.loads(identifier)
        return_params['identifier_grant'] = '0'
        return_params['identifier_grant_crni_link'] = identifier['crni_link']
        return_params['identifier_grant_jalc_cr_doi_link'] = identifier['jalc_cr_doi_link'] + identifier['jalc_cr_doi_suffix']
        return_params['identifier_grant_jalc_cr_doi_suffix'] = identifier['jalc_cr_doi_suffix']
        return_params['identifier_grant_jalc_dc_doi_link'] = identifier['jalc_dc_doi_link'] + identifier['jalc_dc_doi_suffix']
        return_params['identifier_grant_jalc_dc_doi_suffix'] = identifier['jalc_dc_doi_suffix']
        return_params['identifier_grant_jalc_doi_link'] = identifier['jalc_doi_link'] + identifier['jalc_doi_suffix']
        return_params['identifier_grant_jalc_doi_suffix'] = identifier['jalc_doi_suffix']
        return_params['identifier_grant_ndl_jalc_doi_link'] = identifier['ndl_jalc_doi_link'] + identifier['ndl_jalc_doi_suffix']
        return_params['identifier_grant_ndl_jalc_doi_suffix'] = identifier['ndl_jalc_doi_suffix']
    if community is not None:
        return_params['community'] = community
    else:
        return_params['commond'] = ''
        return_params['temporary_save'] = 0
    return return_params

def request_create_author_edit_param(file_name, author_id):
    """Create params for {host}/api/author/edit
    
    Args:
        file_name (str): file name of author register data
        author_id (str): author id
        
    Returns:
        dict: params for {host}/api/author/edit
            author (dict): author register data
            forceChangeFlag (bool): force change flag
    """
    with open(file_name, 'r') as f:
        register_data = json.load(f)[0]
    register_data['id'] = author_id
    register_data['pk_id'] = '1'
    author_id_info = register_data['authorIdInfo']
    for i in range(len(author_id_info)):
        if author_id_info[i]['idType'] == '1':
            author_id_info[i]['authorId'] = '1'
            break
    register_data['authorIdInfo'] = author_id_info
    return {
        'author': register_data,
        'forceChangeFlag': False
    }
