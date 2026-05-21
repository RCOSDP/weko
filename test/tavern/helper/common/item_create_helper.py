import json
import requests
from os import path

from helper.common.request_helper import (
    request_create_action_param,
    request_create_deposits_items_index_param,
    request_create_deposits_items_param,
    request_create_deposits_redirect_param,
    request_create_save_activity_data_param,
    request_create_save_param,
    request_create_validate_param,
)
from helper.common.response_helper import (
    response_save_file_upload_info,
    response_save_identifier_grant,
    response_save_next_path,
    response_save_recid,
    response_save_tree_data,
    response_save_url,
)


def create_item(
    response,
    host,
    create_info_file,
    creation_count,
    target_index=None,
    file_path=None,
    is_doi=False,
    prepare_edit=False,
    id=2000001,
    replace_title=True,
):
    """Create items based on the provided creation information.

    Args:
        response(Response): The response object from the initial request.
        host(str): The base URL of the WEKO instance.
        create_info_file(str): Path to the JSON file containing creation information.
        creation_count(int): Number of items to create.
        target_index(int, optional): The target index ID to assign to the created items. If None, no index assignment is made.
        file_path(str, optional): Path to the file to upload with the item.
        is_doi(bool, optional): Boolean indicating whether to assign a DOI to the item.
        prepare_edit(bool, optional): Boolean indicating whether to prepare the item for editing after creation.
        id(int, optional): Optional ID to assign to the created item.
        replace_title(bool, optional): Boolean indicating whether to replace the title of the item.

    Raises:
        Exception: If any step in the item creation process fails.
    """
    # Get the necessary headers from the response
    request_headers = response.request.headers
    header = {
        "Cookie": request_headers.get("Cookie", ""),
        "X-CSRFToken": request_headers.get("X-CSRFToken", ""),
    }

    with open(create_info_file, "r") as f:
        create_info = json.loads(f.read())

    session = requests.Session()
    session.headers.update(header)
    with open(create_info["data_file"], "r") as f:
        data = json.loads(f.read())

    if create_info.get("file_key") and data.get(create_info["file_key"]) is not None:
        url = data[create_info["file_key"]][0]["url"]["url"]
        replaced_url = url.replace("{id}", str(id))
        data[create_info["file_key"]][0]["url"]["url"] = replaced_url

    if replace_title:
        title_key = create_info["title_key"].split(".")
        title = data[title_key[0]][int(title_key[1])][title_key[2]]
        replaced_title = title + f"_{id}"
        data[title_key[0]][int(title_key[1])][title_key[2]] = replaced_title

    if create_info.get("identifier_key") and data.get(create_info["identifier_key"]) is not None:
        identifier = data[create_info["identifier_key"]][0]["subitem_identifier_uri"]
        replaced_identifier = identifier + f"_{id}"
        data[create_info["identifier_key"]][0]["subitem_identifier_uri"] = replaced_identifier

    for _ in range(creation_count):
        # create activity
        activity_response = activity_init(
            host,
            session,
            create_info["flow_id"],
            create_info["itemtype_id"],
            create_info["workflow_id"],
        )

        # next path
        next_path(host, session, activity_response["next_path"])

        if file_path:
            # deposits item
            deposits_response = deposits_items(host, session)

            # upload file to bucket
            file_upload_info = bucket_file(
                deposits_response["url"]["bucket"], session, file_path
            )

            # item validate
            item_validate(
                host,
                session,
                data,
                file_metadata=file_upload_info["file_metadata"],
            )

            # save activity data
            save_activity_data(
                host,
                session,
                activity_response["activity_id"],
                data,
                create_info["title_key"],
            )

            # iframe model save
            iframe_model_save(
                host,
                session,
                data,
                url=json.dumps(deposits_response["url"]),
                file_upload_info=file_upload_info["file_upload_info"],
                file_metadata=file_upload_info["file_metadata"],
            )

        else:
            # item_validate
            item_validate(host, session, data)

            # save activity data
            save_activity_data(
                host,
                session,
                activity_response["activity_id"],
                data,
                create_info["title_key"],
            )

            # iframe model save
            iframe_model_save(host, session, data)

            # deposits item
            deposits_response = deposits_items(host, session, data)

            # deposits redirect
            deposits_redirect(
                host,
                session,
                deposits_response["recid"],
                data,
                create_info["title_key"],
            )

        no_random = False
        if target_index:
            no_random = True
            if isinstance(target_index, int):
                tree_response = {"tree_data": [str(target_index)]}
            elif isinstance(target_index, list):
                tree_response = {"tree_data": [str(i) for i in target_index]}
        else:
            # api tree
            tree_response = api_tree(host, session, deposits_response["recid"])
        # deposits items recid
        deposits_items_recid(
            host,
            session,
            deposits_response["recid"],
            str(tree_response["tree_data"]),
            no_random,
        )

        # activity 3
        activity_3(
            host,
            session,
            activity_response["activity_id"],
            create_info["action_version"]["3"],
        )

        # activity 5
        activity_5(
            host,
            session,
            activity_response["activity_id"],
            create_info["action_version"]["5"],
        )

        # activity detail
        activity_detail_response = activity_detail(
            host, session, activity_response["activity_id"]
        )

        # activity 7
        activity_7(
            host,
            session,
            activity_response["activity_id"],
            create_info["action_version"]["7"],
            activity_detail_response["identifier_grant"],
            is_doi=is_doi,
        )

        # activity 4
        activity_4(
            host,
            session,
            activity_response["activity_id"],
            create_info["action_version"]["4"],
        )

        if prepare_edit:
            # prepare edit item
            prepare_edit_item(host, session, deposits_response["recid"])


def activity_init(host, session, flow_id, itemtype_id, workflow_id):
    """Initialize a workflow activity.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        flow_id(str): The ID of the workflow flow.
        itemtype_id(str): The ID of the item type.
        workflow_id(str): The ID of the workflow.

    Returns:
        dict: The response containing the activity ID and next path.

    Raises:
        Exception: If the request fails or the response is not as expected.
    """
    url = f"{host}/workflow/activity/init"
    data = {
        "flow_id": flow_id,
        "itemtype_id": itemtype_id,
        "workflow_id": workflow_id,
    }
    response = session.post(url, json=data, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to initialize activity: {response.text}")
    return response_save_next_path(response)


def next_path(host, session, path):
    """Get the next path in the workflow.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        path(str): The next path to navigate to.

    Raises:
        Exception: If the request fails or the response is not as expected.
    """
    url = f"{host}{path}"
    response = session.get(url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get next path: {response.text}")


def item_validate(host, session, data, file_metadata=None):
    """Validate item data.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        data(dict): The item data written in json string.
        file_metadata(str, optional): File upload info written in json string.

    Raises:
        Exception: If the validation fails or the response is not as expected.
    """
    params = request_create_validate_param(data, file_metadata)
    url = f"{host}/api/items/validate"
    response = session.post(url, json=params, verify=False)

    if response.status_code != 200:
        raise Exception(f"Validation failed: {response.text}")


def save_activity_data(host, session, activity_id, data, title_key):
    """Save activity data.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        activity_id(str): The ID of the activity to save data for.
        data(dict): The activity data written in json string.
        title_key(str): The key for the title in the data.

    Raises:
        Exception: If the save operation fails or the response is not as expected.
    """
    params = request_create_save_activity_data_param(activity_id, data, title_key)
    url = f"{host}/workflow/save_activity_data"
    response = session.post(url, json=params, verify=False)

    if response.status_code != 200:
        raise Exception(f"Failed to save activity data: {response.text}")


def iframe_model_save(
    host,
    session,
    data,
    url=None,
    file_upload_info=None,
    file_metadata=None,
):
    """Save item data in iframe model format.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        data(dict): The item data written in json string.
        url(str, optional): URL written in json string.
        file_upload_info(str, optional): File upload info written in json string.
        file_metadata(str, optional): File metadata written in json string.

    Raises:
        Exception: If the save operation fails or the response is not as expected.
    """
    params = request_create_save_param(data, url, file_upload_info, file_metadata)
    url = f"{host}/items/iframe/model/save"
    response = session.post(url, json=params, verify=False)

    if response.status_code != 200:
        raise Exception(f"Failed to save item: {response.text}")


def deposits_items(host, session, data=None):
    """Deposit items based on the provided data file.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        data(dict, optional): The item data written in json string.

    Returns:
        dict: The response containing the recid of the deposited item.

    Raises:
        Exception: If the deposit operation fails or the response is not as expected.
    """
    params = {}
    if data is not None:
        params = request_create_deposits_items_param(data)

    url = f"{host}/api/deposits/items"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to deposit item: {response.text}")

    if data:
        return response_save_recid(response)
    else:
        return response_save_url(response)


def deposits_redirect(host, session, recid, data, title_key):
    """Redirect a deposit based on the provided recid and data file.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        recid(str): The recid of the deposit to redirect.
        data(dict): The data for redirection written in json string or dict.
        title_key(str): The key for the title in the data.

    Raises:
        Exception: If the redirection fails or the response is not as expected.
    """
    params = request_create_deposits_redirect_param(data, title_key)
    url = f"{host}/api/deposits/redirect/{recid}"
    response = session.put(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to redirect deposit: {response.text}")


def api_tree(host, session, recid):
    """Get the tree data for a specific recid.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        recid(str): The recid of the item to get tree data for.

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


def deposits_items_recid(host, session, recid, tree_data, no_random):
    """Update deposits items with the provided recid and tree data.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        recid(str): The recid of the item to update.
        tree_data(str): The tree data to update the item with.
        no_random(bool): no random choice if True

    Raises:
        Exception: If the update operation fails or the response is not as expected.
    """
    params = request_create_deposits_items_index_param(tree_data, no_random)
    url = f"{host}/api/deposits/items/{recid}"
    response = session.put(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get deposits items: {response.text}")


def activity_3(host, session, activity_id, version):
    """Perform activity action 3.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        activity_id(str): The ID of the activity to perform action on.
        version(str): The version of the action to perform.

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
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        activity_id(str): The ID of the activity to perform action on.
        version(str): The version of the action to perform.

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
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        activity_id(str): The ID of the activity to get details for.

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


def activity_7(host, session, activity_id, version, identifier, is_doi=False):
    """Perform activity action 7.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        activity_id(str): The ID of the activity to perform action on.
        version(str): The version of the action to perform.
        identifier(str): The identifier to use in the action.
        is_doi(bool): Whether to assign a DOI.

    Raises:
        Exception: If the action fails or the response is not as expected.
    """
    params = request_create_action_param(version, identifier=identifier, is_doi=is_doi)
    url = f"{host}/workflow/activity/action/{activity_id}/7"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to perform activity action: {response.text}")


def activity_4(host, session, activity_id, version):
    """Perform activity action 4.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        activity_id(str): The ID of the activity to perform action on.
        version(str): The version of the action to perform.

    Raises:
        Exception: If the action fails or the response is not as expected.
    """
    params = request_create_action_param(version, community="")
    url = f"{host}/workflow/activity/action/{activity_id}/4"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to perform activity action: {response.text}")


def bucket_file(url, session, file_path):
    """Upload a file to the specified bucket URL.

    Args:
        url(str): The bucket URL to upload the file to.
        session(requests.Session): The session object for making requests.
        file_path(str): The path to the file to upload.

    Returns:
        dict: The response containing file upload info and metadata.
    Raises:
        Exception: If the file upload fails.
    """
    file_name = file_path.split("/")[-1]
    response = session.put(
        path.join(url, file_name),
        headers={"Content-Type": "text/plain"},
        files={"file": (file_name, open(file_path, "rb"))},
        verify=False,
    )
    if response.status_code != 200:
        raise Exception(f"Failed to upload file: {response.text}")

    return response_save_file_upload_info(response, "item_30002_file35", 30002)


def prepare_edit_item(host, session, recid):
    """Prepare an item for editing.

    Args:
        host(str): The base URL of the WEKO instance.
        session(requests.Session): The session object for making requests.
        recid(str): The recid of the item to prepare for editing.

    Raises:
        Exception: If the prepare edit operation fails.
    """
    params = {"pid_value": recid}
    url = f"{host}/items/prepare_edit_item"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to prepare edit item: {response.text}")
