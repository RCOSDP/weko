# -*- coding: utf-8 -*-
"""Attach a tiny placeholder file body to the demo item's ObjectVersion.

fixture.sql registers the ObjectVersion row (files_object) but intentionally
ships no file body: file bytes are environment specific (they live under the
``files_location`` of the instance) and do not belong in git.

This script is OPTIONAL. The bug being reproduced is a *button rendering*
bug, and the item detail page renders the button from ``records_metadata``
alone - it never touches the stored bytes. Run this only if you also want the
download endpoint to serve something once the fix is applied.

Usage (inside the web container, after fixture.sql has been loaded)::

    docker compose exec -T web invenio shell \
        /code/scripts/demo/download_button_bug_repro/attach_file.py
"""
from __future__ import print_function

from io import BytesIO

from invenio_db import db
from invenio_files_rest.models import ObjectVersion

BUCKET_ID = '19efee91-8841-4e06-a612-8ec571a9d8b3'
VERSION_ID = '76f234e4-2460-4c86-b9b9-e0c871b381ee'
CONTENT = (
    b"This is a synthetic placeholder file for the WEKO3 "
    b"download-button reproduction fixture.\n"
    b"No real research data. No personal information.\n"
)

obj = ObjectVersion.get(BUCKET_ID, 'sample_restricted_data.txt',
                        version_id=VERSION_ID)
if obj is None:
    raise SystemExit('ObjectVersion not found - load fixture.sql first.')
if obj.file_id is not None:
    print('file body already attached:', obj.file_id)
else:
    obj.set_contents(BytesIO(CONTENT))
    db.session.commit()
    print('file body attached:', obj.file_id)
