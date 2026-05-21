import json
from io import BytesIO

def generate_request_body(
    file_path,
    public=None,
    harvest=None,
    thumbnail=None,
    thumbnail_delete=None
):
    """Generate a request body by reading a JSON file.

    Args:
        file_path(str): The path to the JSON file.
        public(int, optional): value to set for "public_state" in the body.
        harvest (int, optional): value to set for "harvest_public_state" in the body.
        thumbnail (str, optional): value to set for "image_name" in the body.
        thumbnail_delete (bool, optional): value to set for "thumbnail_delete_flag" in the body.

    Returns:
        Dict[str, Any]: The generated request body as a dictionary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        body = json.load(f)

    if public is not None:
        body["public_state"] = public
    if harvest is not None:
        body["harvest_public_state"] = harvest
    if thumbnail is not None:
        body["image_name"] = thumbnail
    if thumbnail_delete is not None:
        body["thumbnail_delete_flag"] = thumbnail_delete
    return body


def generate_no_filename_request():
    """Generate a request body for file upload without a filename.

    Returns:
        Dict[str, bytes]: A dictionary containing the file content for upload, without a filename.
    """
    file_content = b"Test file content"
    file_stream = BytesIO(file_content)
    file_stream.name = ''
    return {"uploadFile": file_stream.read()}
