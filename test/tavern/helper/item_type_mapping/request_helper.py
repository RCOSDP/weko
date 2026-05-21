import json

def generate_request_body(file_path):
    """Generate a request body by reading a JSON file.

    Args:
        file_path(str): The path to the JSON file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
