#!/usr/bin/python3
import json
import os
from urllib import parse

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

# Set the base URL
base_url = os.environ.get('REQUEST_SCHEME', 'https') + '://' \
    + os.environ.get('SERVER_NAME', '')
if not os.environ.get('HTTP_WEKOSOCIETYAFFILIATION') \
        and os.environ.get('NO_CHECK_WEKOSOCIETYAFFILIATION') != 'TRUE':
    # Alert and redirect to the base URL if the permission is invalid
    print('Content-Type: text/html; charset=utf-8')
    print('')
    print('<script type="text/javascript">'
          'window.alert("Permission is invalid");'
          'window.location.href={};</script>'.format(json.dumps(base_url)))
else:
    # Get the next URL
    qs = parse.parse_qs(os.environ.get('QUERY_STRING', ''))
    next_url = qs['next'][0] if 'next' in qs else '/'
    url = base_url + '/weko/shib/login?next=' + parse.quote(next_url, safe='')

    # Create the form data in the same format as login.php
    data = {
        'SHIB_ATTR_USER_NAME': os.environ.get('HTTP_WEKOID', ''),
        'SHIB_ATTR_EPPN': os.environ.get('Remote-User', ''),
        'SHIB_ATTR_MAIL': os.environ.get('mail', ''),
        'SHIB_ATTR_SESSION_ID': os.environ.get('Shib-Session-ID', ''),
        'SHIB_ATTR_ROLE_AUTHORITY_NAME':
            os.environ.get('HTTP_WEKOSOCIETYAFFILIATION', ''),
    }

    # Request to the Shibboleth login
    response = requests.post(url, data=data, verify=False)
    response.raise_for_status()
    redirect = response.text

    if redirect.startswith('/'):
        # Redirect to the Shibboleth login
        print('Status: 302 Found')
        print('Content-Type: text/html')
        print('Location: ' + base_url + redirect)
        print('')
    else:
        # Display the login page or the page before login processing
        print('Status: 200 OK')
        print('Content-Type: text/html; charset=utf-8')
        print('')
        print(redirect)
