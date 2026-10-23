#!/usr/bin/python3
from http import cookiejar
import os
import requests
import tempfile
from urllib import parse
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

# Set the base URL
base_url = os.environ.get('REQUEST_SCHEME') + '://' + os.environ.get('HTTP_HOST')
if not os.environ.get('HTTP_WEKOSOCIETYAFFILIATION') \
    and os.environ.get('NO_CHECK_WEKOSOCIETYAFFILIATION') != 'TRUE':
    # Alert and redirect to the base URL if the permission is invalid
    print('Content-Type: text/html; charset=utf-8\n\n')
    print('<script type="text/javascript">window.alert("Permission is invalid");window.location.href="{}";</script>'.format(base_url))
else:
    # Get the next URL
    qs = parse.parse_qs(os.environ.get('QUERY_STRING'))
    if 'next' in qs:
        next = qs['next'][0]
    else:
        next = '%2F'
    url = base_url + '/weko/shib/login?next=' + next

    # Create the data for setting to form data
    data = {}
    data['SHIB_ATTR_USER_NAME'] = os.environ.get('HTTP_WEKOID')
    data['SHIB_ATTR_EPPN'] = os.environ.get('Remote-User')
    data['SHIB_ATTR_MAIL'] = os.environ.get('mail')
    data['SHIB_ATTR_SESSION_ID'] = os.environ.get('Shib-Session-ID')
    data['SHIB_ATTR_ROLE_AUTHORITY_NAME'] = os.environ.get('HTTP_WEKOSOCIETYAFFILIATION')
    data['SHIB_ATTR_PAGE_NAME'] = os.environ.get('HTTP_WEKOSOCIETYSUBGROUP')
    data['SHIB_ATTR_ACTIVE_FLAG'] = os.environ.get('HTTP_WEKOACTIVEUSER')
    data['SHIB_ATTR_SITE_USER_WITHIN_IP_RANGE_FLAG'] = os.environ.get('HTTP_WEKOSITEUSERWITHINIPRANGE')
    data['SHIB_ATTR_ORGANIZATION'] = os.environ.get('HTTP_UIDPDOMAINNAME')
    data['SHIB_ATTR_HANDLE'] = os.environ.get('HTTP_DISPLAYNAME')

    # Create the cookie jar
    with tempfile.NamedTemporaryFile(prefix='cookie_', delete=False) as f:
        temp_path = f.name
    cookie_jar = cookiejar.LWPCookieJar(temp_path)

    # Request to the Shibboleth login
    response = requests.post(url, data=data, verify=False, cookies=cookie_jar)
    response.raise_for_status()
    redirect = response.text

    if redirect.startswith('/'):
        # Redirect to the Shibboleth login
        print('HTTP/1.1 302 Found')
        print('Content-Type: text/html')
        print('Location: ' + base_url + redirect)
        print('')
    else:
        # Display the login page or the page before login processing with flash message
        print('HTTP/1.1 200 OK')
        print('Content-Type: text/html')
        print('')
        print(redirect)
