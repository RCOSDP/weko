#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Seed dummy WEKO records for performance measurement.

Clones an existing published record (its records_metadata rows, the 7
pidstore_pid rows, the 4 pidrelations rows and the 2 Elasticsearch docs)
N times, assigning fresh recid values. Each cloned record keeps the same
WEKO versioning shape (parent / recid / recid.1) so the item landing page
(default_view_method -> PIDVersioning) renders, and gets an ES doc with
relation_version_is_last=True so it shows up in the search list.

Run inside the web container's app context, e.g.:

    docker compose -f docker-compose.arm64.yml -p weko exec web \
        bash -lc 'source /home/invenio/.virtualenvs/invenio/bin/activate && \
        python /code/test/perf_measure/seed_records.py <template_recid> <start> <count> [batch]'

Example: seed 3000 records starting at recid 3000001, cloning template 2000001:

    python /code/test/perf_measure/seed_records.py 2000001 3000001 3000 200
"""
from __future__ import print_function

import copy
import json
import sys
import uuid


def main():
    template_recid = sys.argv[1] if len(sys.argv) > 1 else '2000001'
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 3000001
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
    batch = int(sys.argv[4]) if len(sys.argv) > 4 else 200

    from invenio_app.factory import create_app
    app = create_app()
    with app.app_context():
        from invenio_db import db
        from invenio_search import current_search_client
        from sqlalchemy import text

        # --- Resolve the item ES index name (…-weko-item-…) ---
        prefix = app.config.get('SEARCH_INDEX_PREFIX', '')
        idx_names = [i for i in current_search_client.indices.get_alias().keys()
                     if 'weko-item' in i]
        if not idx_names:
            raise SystemExit('item index not found (prefix=%r)' % prefix)
        item_index = sorted(idx_names)[0]
        doc_type = 'item-v1.0.0'
        print('item index:', item_index)

        # --- Load template DB rows ---
        def one(q, **kw):
            return db.session.execute(text(q), kw).fetchone()

        def allrows(q, **kw):
            return db.session.execute(text(q), kw).fetchall()

        base_pid = one(
            "SELECT object_uuid FROM pidstore_pid "
            "WHERE pid_type='recid' AND pid_value=:v", v=template_recid)
        ver_pid = one(
            "SELECT object_uuid FROM pidstore_pid "
            "WHERE pid_type='recid' AND pid_value=:v", v=template_recid + '.1')
        if not base_pid or not ver_pid:
            raise SystemExit('template recid %s (and .1) not found' % template_recid)
        base_uuid = str(base_pid[0])
        ver_uuid = str(ver_pid[0])

        base_json = one("SELECT json FROM records_metadata WHERE id=:i", i=base_uuid)[0]
        ver_json = one("SELECT json FROM records_metadata WHERE id=:i", i=ver_uuid)[0]
        if isinstance(base_json, str):
            base_json = json.loads(base_json)
        if isinstance(ver_json, str):
            ver_json = json.loads(ver_json)

        # ES template docs (by _id = uuid)
        base_es = current_search_client.get(
            index=item_index, doc_type=doc_type, id=base_uuid)['_source']
        ver_es = current_search_client.get(
            index=item_index, doc_type=doc_type, id=ver_uuid)['_source']

        host = app.config.get('THEME_SITEURL', '')
        oai_prefix = 'oai:%s:' % app.config.get(
            'OAISERVER_ID_PREFIX', 'weko3.example.org').replace('oai:', '')

        def clone_json(src, recid, title):
            j = copy.deepcopy(src)
            j['recid'] = recid
            j['control_number'] = recid
            j['_oai'] = {'id': '%s%08d' % (oai_prefix, int(float(recid)))
                         if '.' not in recid else '%s%08d.1' % (
                             oai_prefix, int(float(recid)))}
            if '_deposit' in j:
                j['_deposit']['id'] = recid
                if isinstance(j['_deposit'].get('pid'), dict):
                    j['_deposit']['pid']['value'] = recid
            j['title'] = [title]
            j['item_title'] = title
            # update the visible title subitem for item type 30002 if present
            for k, v in list(j.items()):
                if k.endswith('_title0') and isinstance(v, dict):
                    mlt = v.get('attribute_value_mlt')
                    if isinstance(mlt, list) and mlt and isinstance(mlt[0], dict):
                        mlt[0]['subitem_title'] = title
            return j

        def clone_es(src, recid, title, is_last, item_meta):
            e = copy.deepcopy(src)
            e['control_number'] = recid
            e['relation_version_is_last'] = is_last
            e['title'] = [title]
            e['_item_metadata'] = item_meta
            if isinstance(e.get('_oai'), dict):
                e['_oai']['id'] = item_meta['_oai']['id']
            return e

        # Sequences used by pidstore_pid.id
        def next_pid_ids(n):
            row = db.session.execute(text(
                "SELECT nextval('pidstore_pid_id_seq') FROM generate_series(1, :n)"),
                {'n': n}).fetchall()
            return [r[0] for r in row]

        insert_pid = text(
            "INSERT INTO pidstore_pid (id, pid_type, pid_value, status, "
            "object_type, object_uuid, created, updated) VALUES "
            "(:id, :pt, :pv, 'R', 'rec', :uuid, now(), now())")
        insert_rel = text(
            "INSERT INTO pidrelations_pidrelation (parent_id, child_id, "
            "relation_type, index, created, updated) VALUES "
            "(:p, :c, :rt, :idx, now(), now())")
        insert_rec = text(
            "INSERT INTO records_metadata (id, json, version_id, created, updated) "
            "VALUES (:id, :j, 1, now(), now())")

        made = 0
        for base in range(start, start + count):
            recid = str(base)
            vrecid = '%s.1' % base
            title = 'Perf Test Record %d' % base
            new_base_uuid = str(uuid.uuid4())
            new_ver_uuid = str(uuid.uuid4())

            j_base = clone_json(base_json, recid, title)
            j_ver = clone_json(ver_json, vrecid, title)

            # records_metadata (base + version)
            db.session.execute(insert_rec, {'id': new_base_uuid,
                                            'j': json.dumps(j_base)})
            db.session.execute(insert_rec, {'id': new_ver_uuid,
                                            'j': json.dumps(j_ver)})

            # 7 PIDs: recid, recid.1, depid, depid.1, oai, oai.1, parent
            ids = next_pid_ids(7)
            pid_recid, pid_recidv, pid_depid, pid_depidv, pid_oai, pid_oaiv, pid_parent = ids
            db.session.execute(insert_pid, {'id': pid_recid, 'pt': 'recid',
                                            'pv': recid, 'uuid': new_base_uuid})
            db.session.execute(insert_pid, {'id': pid_recidv, 'pt': 'recid',
                                            'pv': vrecid, 'uuid': new_ver_uuid})
            db.session.execute(insert_pid, {'id': pid_depid, 'pt': 'depid',
                                            'pv': recid, 'uuid': new_base_uuid})
            db.session.execute(insert_pid, {'id': pid_depidv, 'pt': 'depid',
                                            'pv': vrecid, 'uuid': new_ver_uuid})
            db.session.execute(insert_pid, {'id': pid_oai, 'pt': 'oai',
                                            'pv': j_base['_oai']['id'],
                                            'uuid': new_base_uuid})
            db.session.execute(insert_pid, {'id': pid_oaiv, 'pt': 'oai',
                                            'pv': j_ver['_oai']['id'],
                                            'uuid': new_ver_uuid})
            db.session.execute(insert_pid, {'id': pid_parent, 'pt': 'parent',
                                            'pv': 'parent:%s' % recid,
                                            'uuid': new_base_uuid})

            # relations mirroring the template:
            #   parent -> recid (VERSION, idx 0)
            #   parent -> recid.1 (VERSION, idx 1)
            #   recid  -> depid (RECORD)
            #   recid.1-> depid.1 (RECORD)
            db.session.execute(insert_rel, {'p': pid_parent, 'c': pid_recid,
                                            'rt': 2, 'idx': 0})
            db.session.execute(insert_rel, {'p': pid_parent, 'c': pid_recidv,
                                            'rt': 2, 'idx': 1})
            db.session.execute(insert_rel, {'p': pid_recid, 'c': pid_depid,
                                            'rt': 3, 'idx': None})
            db.session.execute(insert_rel, {'p': pid_recidv, 'c': pid_depidv,
                                            'rt': 3, 'idx': None})

            # ES docs (base = last version shown in search; version = not last)
            current_search_client.index(
                index=item_index, doc_type=doc_type, id=new_base_uuid,
                body=clone_es(base_es, recid, title, True, j_base))
            current_search_client.index(
                index=item_index, doc_type=doc_type, id=new_ver_uuid,
                body=clone_es(ver_es, vrecid, title, False, j_ver))

            made += 1
            if made % batch == 0:
                db.session.commit()
                print('committed %d / %d (recid up to %s)' % (made, count, recid))

        db.session.commit()
        current_search_client.indices.refresh(index=item_index)
        print('DONE: seeded %d records (%d..%d)' % (made, start, start + count - 1))


if __name__ == '__main__':
    main()
