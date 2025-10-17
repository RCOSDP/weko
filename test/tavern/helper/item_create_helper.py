import json
import requests

from .request_helper import (
    request_create_validate_param,
    request_create_save_activity_data_param,
    request_create_save_param,
    request_create_deposits_items_param,
    request_create_deposits_redirect_param,
    request_create_deposits_items_index_param,
    request_create_action_param
) 
from .response_helper import (
    response_save_next_path,
    response_save_recid,
    response_save_tree_data,
    response_save_identifier_grant
)
    

def create_item(response, host, create_info_file, creation_count):
    """Create items based on the provided creation information.

    Args:
        response: The response object from the initial request.
        host: The base URL of the WEKO instance.
        create_info_file: Path to the JSON file containing creation information.
        creation_count: Number of items to create.

    Raises:
        Exception: If any step in the item creation process fails.
    """
    # Get the necessary headers from the response
    request_headers = response.request.headers
    header = {
        'Cookie': request_headers.get('Cookie', ''),
        'X-CSRFToken': request_headers.get('X-CSRFToken', ''),
    }

    with open(create_info_file, 'r') as f:
        create_info = json.loads(f.read())
    
    session = requests.Session()
    session.headers.update(header)

    for i in range(creation_count):
        # create activity
        activity_response = activity_init(host,
                                        session,
                                        create_info['flow_id'],
                                        create_info['itemtype_id'],
                                        create_info['workflow_id'])
        
        # next path
        next_path(host, session, activity_response['next_path'])

        # item_validate
        item_validate(host, session, create_info['data_file'])

        # save activity data
        save_activity_data(
            host,
            session,
            activity_response['activity_id'],
            create_info['data_file'],
            create_info['title_key']
        )

        # iframe model save
        iframe_model_save(host, session, create_info['data_file'])

        # deposits item
        deposits_response = deposits_items(host, session, create_info['data_file'])

        # deposits redirect
        deposits_redirect(
            host,
            session,
            deposits_response['recid'],
            create_info['data_file'],
            create_info['title_key']
        )

        # api tree
        tree_response = api_tree(host, session, deposits_response['recid'])

        # deposits items recid
        deposits_items_recid(
            host,
            session,
            deposits_response['recid'],
            str(tree_response['tree_data'])
        )

        # activity 3
        activity_3(
            host,
            session,
            activity_response['activity_id'],
            create_info['action_version']['3']
        )

        # activity 5
        activity_5(
            host,
            session,
            activity_response['activity_id'],
            create_info['action_version']['5']
        )

        # activity detail
        activity_detail_response = activity_detail(
            host,
            session,
            activity_response['activity_id']
        )

        # activity 7
        activity_7(
            host,
            session,
            activity_response['activity_id'],
            create_info['action_version']['7'],
            activity_detail_response['identifier_grant']
        )

        # activity 4
        activity_4(
            host,
            session,
            activity_response['activity_id'],
            create_info['action_version']['4']
        )

def activity_init(host, session, flow_id, itemtype_id, workflow_id):
    """Initialize a workflow activity.
    
    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        flow_id (str): The ID of the workflow flow.
        itemtype_id (str): The ID of the item type.
        workflow_id (str): The ID of the workflow. 

    Returns:
        dict: The response containing the activity ID and next path.

    Raises:
        Exception: If the request fails or the response is not as expected.
    """
    url = f"{host}/workflow/activity/init"
    data = {
        'flow_id': flow_id,
        'itemtype_id': itemtype_id,
        'workflow_id': workflow_id,
    }
    response = session.post(url, json=data, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to initialize activity: {response.text}")
    return response_save_next_path(response)

def next_path(host, session, path):
    """Get the next path in the workflow.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        path (str): The next path to navigate to.

    Raises:
        Exception: If the request fails or the response is not as expected.
    """
    url = f"{host}{path}"
    response = session.get(url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get next path: {response.text}")

def item_validate(host, session, data_file):
    """Validate item data.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        data_file (str): Path to the JSON file containing item data to validate.

    Raises:
        Exception: If the validation fails or the response is not as expected.
    """
    with open(data_file, 'r') as f:
        data = f.read()
    
    params = request_create_validate_param(data)
    url = f"{host}/api/items/validate"
    response = session.post(url, json=params, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Validation failed: {response.text}")

def save_activity_data(host, session, activity_id, data_file, title_key):
    """Save activity data.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        activity_id (str): The ID of the activity to save data for.
        data_file (str): Path to the JSON file containing activity data to save.
        title_key (str): The key for the title in the data.

    Raises:
        Exception: If the save operation fails or the response is not as expected.
    """
    with open(data_file, 'r') as f:
        data = f.read()
    
    params = request_create_save_activity_data_param(activity_id, data, title_key)
    url = f"{host}/workflow/save_activity_data"
    response = session.post(url, json=params, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to save activity data: {response.text}")

def iframe_model_save(host, session, data_file):
    """Save item data in iframe model format.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        data_file (str): Path to the JSON file containing item data to save.

    Raises:
        Exception: If the save operation fails or the response is not as expected.
    """
    with open(data_file, 'r') as f:
        data = f.read()
    
    params = request_create_save_param(data)
    url = f"{host}/items/iframe/model/save"
    response = session.post(url, json=params, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to save item: {response.text}")

def deposits_items(host, session, data_file):
    """Deposit items based on the provided data file.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        data_file (str): Path to the JSON file containing item data to deposit.
    
    Returns:
        dict: The response containing the recid of the deposited item.

    Raises:
        Exception: If the deposit operation fails or the response is not as expected.
    """
    with open(data_file, 'r') as f:
        data = f.read()
    
    params = request_create_deposits_items_param(data)
    url = f"{host}/api/deposits/items"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to deposit item: {response.text}")
    
    return response_save_recid(response)

def deposits_redirect(host, session, recid, data_file, title_key):
    """Redirect a deposit based on the provided recid and data file.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        recid (str): The recid of the deposit to redirect.
        data_file (str): Path to the JSON file containing data for redirection.
        title_key (str): The key for the title in the data.

    Raises:
        Exception: If the redirection fails or the response is not as expected.
    """
    with open(data_file, 'r') as f:
        data = f.read()

    params = request_create_deposits_redirect_param(data, title_key)
    url = f"{host}/api/deposits/redirect/{recid}"
    response = session.put(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to redirect deposit: {response.text}")

def api_tree(host, session, recid):
    """Get the tree data for a specific recid.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        recid (str): The recid of the item to get tree data for.

    Returns:
        dict: The response containing the tree data.

    Raises:
        Exception: If the request fails or the response is not as expected.
    """
    url = f"{host}/api/tree/{recid}"
    response = session.get(url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get tree: {response.text}")
    
    return response_save_tree_data(response)

def deposits_items_recid(host, session, recid, tree_data):
    """Update deposits items with the provided recid and tree data.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        recid (str): The recid of the item to update.
        tree_data (str): The tree data to update the item with.

    Raises:
        Exception: If the update operation fails or the response is not as expected.
    """
    params = request_create_deposits_items_index_param(tree_data)
    url = f"{host}/api/deposits/items/{recid}"
    response = session.put(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get deposits items: {response.text}")

def activity_3(host, session, activity_id, version):
    """Perform activity action 3.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        activity_id (str): The ID of the activity to perform action on.
        version (str): The version of the action to perform.

    Raises:
        Exception: If the action fails or the response is not as expected.
    """
    params = request_create_action_param(version)
    url = f"{host}/workflow/activity/action/{activity_id}/3"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to perform activity action: {response.text}")

def activity_5(host, session, activity_id, version):
    """Perform activity action 5.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        activity_id (str): The ID of the activity to perform action on.
        version (str): The version of the action to perform.

    Raises:
        Exception: If the action fails or the response is not as expected.
    """
    params = request_create_action_param(version, link_data=[])
    url = f"{host}/workflow/activity/action/{activity_id}/5"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to perform activity action: {response.text}")

def activity_detail(host, session, activity_id):
    """Get the details of a specific activity.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        activity_id (str): The ID of the activity to get details for.
        
    Returns:
        dict: The response containing the activity details, including identifier grant.

    Raises:
        Exception: If the request fails or the response is not as expected.
    """
    url = f"{host}/workflow/activity/detail/{activity_id}?page=1&size=20"
    response = session.get(url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get activity detail: {response.text}")
    
    return response_save_identifier_grant(response)

def activity_7(host, session, activity_id, version, identifier):
    """Perform activity action 7.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        activity_id (str): The ID of the activity to perform action on.
        version (str): The version of the action to perform.
        identifier (str): The identifier to use in the action.

    Raises:
        Exception: If the action fails or the response is not as expected.
    """
    params = request_create_action_param(version, identifier=identifier)
    url = f"{host}/workflow/activity/action/{activity_id}/7"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to perform activity action: {response.text}")

def activity_4(host, session, activity_id, version):
    """Perform activity action 4.

    Args:
        host (str): The base URL of the WEKO instance.
        session (requests.Session): The session object for making requests.
        activity_id (str): The ID of the activity to perform action on.
        version (str): The version of the action to perform.

    Raises:
        Exception: If the action fails or the response is not as expected.
    """
    params = request_create_action_param(version, community='')
    url = f"{host}/workflow/activity/action/{activity_id}/4"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to perform activity action: {response.text}")
