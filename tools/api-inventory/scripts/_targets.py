#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測定対象の no を1行1件で出す。profile の skip_category_tags を除外する。"""
import json
import sys

def main():
    full, profile = sys.argv[1], sys.argv[2]
    skip = json.load(open(profile, encoding='utf-8')).get('skip_category_tags', [])
    rows = [l.rstrip('\n').split('\t') for l in open(full, encoding='utf-8')]
    head = {n: i for i, n in enumerate(rows[0])}
    i = head.get('category_tags')
    for r in rows[1:]:
        tags = r[i] if i is not None and len(r) > i else ''
        if any(t and t in tags for t in skip):
            continue
        print(r[0])

if __name__ == '__main__':
    main()
