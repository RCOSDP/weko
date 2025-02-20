#!/usr/bin/python3
from http import cookiejar
import os
import requests
import requests.cookies
import tempfile
from urllib import parse

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

    # Get the fastcgi_params
    fastcgi_params = []
    with open('/etc/nginx/shib_fastcgi_params', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('fastcgi_param'):
                fastcgi_params.append(line.split(' ')[1])

    # Create the data for setting to form data
    data = {}
    for param in fastcgi_params:
        if os.environ.get(param):
            data[param] = os.environ.get(param)

    headers = {
        'HTTP_WEKOID': os.environ.get('HTTP_WEKOID'),
        'HTTP_WEKOSOCIETYAFFILIATION': os.environ.get('HTTP_WEKOSOCIETYAFFILIATION'),
    }

    # Create the cookie jar
    with tempfile.NamedTemporaryFile(prefix='cookie_', delete=False) as f:
        temp_path = f.name
    cookie_jar = cookiejar.LWPCookieJar(temp_path)

    # Request to the Shibboleth login
    response = requests.post(url, data=data, headers=headers, verify=False, cookies=cookie_jar)
    response.raise_for_status()
    redirect_url = response.text

    # Redirect to the Shibboleth login
    print('HTTP:/1.1 302 Found')
    print("Content-Type: text/html")
    print('Location: ' + base_url + redirect_url)
    print('')
