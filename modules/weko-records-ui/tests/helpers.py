import copy


def fill_oauth2_headers(json_headers, token):
    """Create authentication headers (with a valid oauth2 token)."""
    headers = copy.deepcopy(json_headers)
    headers.append(
        ('Authorization', 'Bearer {0}'.format(token.access_token))
    )
    return headers
