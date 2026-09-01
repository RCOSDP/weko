#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_profile.json を shell の eval 用に展開する。"""
import hashlib
import json
import shlex
import sys

def main():
    path = sys.argv[1]
    raw = open(path, 'rb').read()
    c = json.loads(raw)
    out = {
        'WRITES': '--allow-writes' if c.get('allow_writes') else '',
        'REFRESH': str(c.get('refresh_fixtures', 40)),
        'WEB_CONTAINER': c.get('web_container', 'weko-web-1'),
        'BASE': c.get('base_url', 'https://localhost:8443'),
        'HOSTHDR': c.get('host_header', 'weko3.example.org'),
        'PROFILE_HASH': hashlib.sha256(raw).hexdigest()[:12],
    }
    for k, v in out.items():
        print(f'{k}={shlex.quote(v)}')

if __name__ == '__main__':
    main()
