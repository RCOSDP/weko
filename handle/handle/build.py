#!/usr/bin/env python3

""" This script takes the configuration templates and creates new ones for the
handle server based upon environment variables """

import sys
import os
import subprocess
import string
import encodings
import base64

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__)) + '/config/'
HANDLE_BIN = sys.argv[1]
OUT_DIR = sys.argv[2]

# Config options
config = {
    'SERVER_ADMIN_FULL_ACCESS': os.getenv('SERVER_ADMIN_FULL_ACCESS', 'yes'),
    'CASE_SENSITIVE': os.getenv('CASE_SENSITIVE', 'no'),
    'MAX_SESSION_TIME': os.getenv('MAX_SESSION_TIME', 86400000),
    'MAX_AUTH_TIME': os.getenv('MAX_AUTH_TIME', 60000),
    'THIS_SERVER_ID': os.getenv('THIS_SERVER_ID', 1),
    'TRACE_RESOLUTION': os.getenv('TRACE_RESOLUTION', 'no'),
    'ALLOW_LIST_HDLS': os.getenv('ALLOW_LIST_HDLS', 'yes'),
    'ALLOW_RECURSION': os.getenv('ALLOW_RECURSION', 'no'),
    'SERVER_ADMINS': ' '.join(['"%s"'%s for s in os.getenv('SERVER_ADMINS', "").split(" ")]),
    'REPLICATION_ADMINS': ' '.join(['"%s"'%s for s in os.getenv('REPLICATION_ADMINS', "").split(" ")]),
    'HANDLE_HOST_IP': os.getenv('HANDLE_HOST_IP', '0.0.0.0'),
    'SERVER_PRIVATE_KEY_PEM': os.getenv('SERVER_PRIVATE_KEY_PEM', '').encode('ASCII'), # Explict convert to byte string
    'SERVER_PUBLIC_KEY_PEM': os.getenv('SERVER_PUBLIC_KEY_PEM', '').encode('ASCII'), # Explict convert to byte string
    'STORAGE_TYPE': os.getenv('STORAGE_TYPE', ''),
    'SQL_URL': os.getenv('SQL_URL', ''),
    'SQL_DRIVER': os.getenv('SQL_DRIVER', 'com.mysql.jdbc.Driver'),
    'SQL_LOGIN': os.getenv('SQL_LOGIN', 'root'),
    'SQL_PASSWD': os.getenv('SQL_PASSWD', ''),
    'SQL_READ_ONLY': os.getenv('SQL_READ_ONLY', 'no'),
    'ALLOW_NA_ADMINS': os.getenv('ALLOW_NA_ADMINS', 'yes'),
    'TEMPLATE_NS_OVERRIDE': os.getenv('TEMPLATE_NS_OVERRIDE', 'no'),
    'HOME_PREFIX' = os.getenv('HOME_PREFIX', '0.NA/YOUR_PREFIX'),
    'DESC' = os.getenv('DESC', 'YOUR DESCRIPTION'),
    'CONTACT_EMAIL' = os.getenv('CONTACT_EMAIL', 'YOUR EMAIL'),
    'ORG_NAME' = os.getenv('ORG_NAME', 'YOUR ORG')
}

# Create private / public keys based on config using hdl-convert-key tool
# The handle server works with DSA format, not PEM formats.
handle_convert_cmd = os.path.join(HANDLE_BIN, "hdl-convert-key")
with subprocess.Popen([handle_convert_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
    private_key_dsa = p.communicate(input=config['SERVER_PRIVATE_KEY_PEM'])[0]
    with open(os.path.join(OUT_DIR, "privkey.bin"), 'wb') as f:
        f.write(private_key_dsa)

public_key_dsa = None
with subprocess.Popen([handle_convert_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as p:
    public_key_dsa = p.communicate(input=config['SERVER_PUBLIC_KEY_PEM'])[0]
    with open(os.path.join(OUT_DIR, "pubkey.bin"), 'wb') as f:
        f.write(public_key_dsa)

# Build a base64 version of key for the siteinfo file
config['SERVER_PUBLIC_KEY_DSA_BASE64'] = base64.b64encode(public_key_dsa).decode('ASCII')

# Build the templates
def generate_template(template, out_file, config):
    """Generate a output file from a config"""
    with open(template, 'r') as f:
        template = string.Template(f.read())
        s = template.substitute(config)

        with open(out_file, 'w') as f:
            f.write(s)

generate_template(os.path.join(CONFIG_DIR, 'config.dct.template'), os.path.join(OUT_DIR, 'config.dct'), config)
generate_template(os.path.join(CONFIG_DIR, 'siteinfo.json.template'), os.path.join(OUT_DIR,'siteinfo.json'), config)
generate_template(os.path.join(CONFIG_DIR, 'contactdata.dct.template'), os.path.join(OUT_DIR,'siteinfo.json'), config)
