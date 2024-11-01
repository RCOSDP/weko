import sys
import os
import json
import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

args = sys.argv
if len(args) == 3:
    user = args[1]
    password = args[2]
    auth = HTTPBasicAuth(user,password)
elif len(args) == 1:
    auth = None
else:
    print("Usage: python update_template_and_policies.py [user] [password]")
    sys.exit(1)

host = os.environ.get('INVENIO_ELASTICSEARCH_HOST','localhost')
prefix = os.environ.get('SEARCH_INDEX_PREFIX')
module_dir = "/code/modules/"
base_url = f"https://{host}:9200/"
template_url = base_url + "_template/{}"
ism_url = base_url + "_plugins/_ism/policies/weko_stats_policy"

verify = False
headers = {"Content-Type":"application/json"}

req_args = {"headers":headers,"verify":verify}
if auth:
    req_args["auth"] = auth

templates_files = {
    "tenant1-events-v1": "invenio-stats/invenio_stats/contrib/events/os-v2/events-v1.json",
    "tenant1-aggregation-v1": "invenio-stats/invenio_stats/contrib/aggregations/os-v2/aggregation-v1.json",
}

templates = {}
print("# get template from json files")
for index, path in templates_files.items():
    file_path = os.path.join(module_dir, path)
    if not os.path.isfile(file_path):
        print("## not exist file: {}".format(file_path))
        continue
    with open(file_path, "r") as json_file:
        templates[index] = json.loads(
            json_file.read().\
                replace("__SEARCH_INDEX_PREFIX__",prefix+"-")
        )

try:
    print("# put templates")
    print("## put events template")
    res = requests.put(template_url.format(f"{prefix}-events-v1"), json=templates[f"{prefix}-events-v1"],**req_args)
    if res.status_code!=200:
        raise Exception(res.text)
    print("## put aggregations template")
    res = requests.put(template_url.format(f"{prefix}-aggregation-v1"), json=templates[f"{prefix}-aggregation-v1"],**req_args)
    if res.status_code!=200:
        raise Exception(res.text)

    ism_body = {
    "policy": {
        "description": "Rollover policy based on max size",
        "default_state": "hot",
        "states": [
        {
            "name": "hot",
            "actions": [
            {
                "rollover": {
                "min_size": "50gb"
                }
            }
            ]
        }
        ]
    }
    }
    policy_name="weko_stats_policy"
    print("# put ism policy")
    res = requests.put(ism_url, json=ism_body,**req_args)
    if res.status_code!=201:
        raise Exception(res.text)
except Exception as e:
    import traceback
    print("## raise error")
    print(traceback.format_exc())