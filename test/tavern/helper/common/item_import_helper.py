import csv
import os
import zipfile
from time import sleep

import requests
from box import Box


def import_item(response, host, file_path, target_index, csrf_token):
    """Import item via admin API.

    Args:
        response(Response): Response object from previous request to get headers.
        host(str): Host URL.
        file_path(str): Path to the file to be imported.
        target_index(int): Target index ID to replace in the import data.
        csrf_token(str): CSRF token for authentication.

    Returns:
        Box: A Box object containing import task details.
    """
    request_headers = response.request.headers
    header = {
        "Referer": host,
        "Cookie": request_headers.get("Cookie", ""),
        "X-CSRFToken": csrf_token,
    }

    session = requests.Session()
    session.headers.update(header)

    # Prepare import data
    import_data_path = prepare_import_data(file_path, target_index)

    # Import check
    check_import_task_id = import_check(host, session, import_data_path)

    # Get check status
    while True:
        check_result = get_check_status(host, session, check_import_task_id)
        if check_result.get("end_date"):
            break
        sleep(1)

    # Import
    import_response = start_import(
        host, session, check_result["data_path"], check_result["list_record"]
    )

    return Box({"import_tasks": import_response["data"]["tasks"]})


def prepare_import_data(file_path, target_index):
    """Prepare import data by replacing placeholder with target index ID
    and zipping the data directory.

    Args:
        file_path(str): Path to the file to be prepared.
        target_index(int): Target index ID to replace in the import data.

    Returns:
        str: Path to the zipped import data.
    """
    replace_path = file_path.replace("prepare", "data")
    with open(file_path, "r", encoding="utf-8") as read_file, \
            open(replace_path, "w", encoding="utf-8") as write_file:
        reader = csv.reader(read_file, delimiter="\t")
        writer = csv.writer(write_file, delimiter="\t")

        for row in reader:
            new_row = [cell.replace("<インデックスID>", str(target_index)) for cell in row]
            writer.writerow(new_row)

    target_dir = "/".join(replace_path.split("/")[:-1])
    output_zip_path = target_dir + ".zip"
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_full_path = os.path.join(root, file)
                arcname = os.path.relpath(file_full_path, os.path.dirname(target_dir))
                zipf.write(file_full_path, arcname)

    return output_zip_path


def import_check(host, session, file_path):
    """Check import item via admin API.

    Args:
        host(str): Host URL.
        session(requests.Session): Requests session with appropriate headers.
        file_path(str): Path to the file to be checked.

    Returns:
        str: Check import task ID.

    Raises:
        Exception: If the request fails.
    """
    url = f"{host}/admin/items/import/check"
    params = {"is_change_identifier": "false"}
    with open(file_path, "rb") as file:
        files = {
            "file": (file_path.split("/")[-1], file, "application/x-zip-compressed"),
        }
        response = session.post(url, data=params, files=files, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to check import item: {response.text}")

    return response.json()["check_import_task_id"]


def get_check_status(host, session, check_import_task_id):
    """Get check import status via admin API.

    Args:
        host(str): Host URL.
        session(requests.Session): Requests session with appropriate headers.
        check_import_task_id(str): Check import task ID.

    Returns:
        dict: Check import status details.

    Raises:
        Exception: If the request fails.
    """
    params = {"task_id": check_import_task_id}
    url = f"{host}/admin/items/import/get_check_status"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to get check status: {response.text}")
    return response.json()


def start_import(host, session, data_path, list_record):
    """Start import item via admin API.

    Args:
        host(str): Host URL.
        session(requests.Session): Requests session with appropriate headers.
        data_path(str): Data path for import.
        list_record(list): List of records to be imported.

    Returns:
        dict: Import task details.

    Raises:
        Exception: If the request fails.
    """
    params = {
        "data_path": data_path,
        "list_doi": ["" for _ in range(len(list_record))],
        "list_record": list_record,
    }
    url = f"{host}/admin/items/import/import"
    response = session.post(url, json=params, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to start import: {response.text}")
    return response.json()
