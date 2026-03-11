import json
import requests


def create_author(response, host, author_info_file):
    """Create authors using the provided response and host.
    
    Args:
        response: The response object from a previous request.
        host: The base URL of the Weko instance.
        author_info_file: Path to the JSON file containing author information.

    Raises:
        Exception: If the author creation fails.
    """
    request_header = response.request.headers
    header = {
        'Cookie': request_header.get('Cookie', ''),
        'X-CSRFToken': request_header.get('X-CSRFToken', '')
    }

    with open(author_info_file, 'r', encoding='utf-8') as f:
        author_info = json.load(f)
    
    for author in author_info:
        url = f'{host}/api/authors/add'
        response = requests.post(url, headers=header, json=author, verify=False)
        if response.status_code != 200:
            print('Failed to create author:', response.status_code, response.text)
            raise Exception(f'Failed to create author: {response.status_code} {response.text}')
