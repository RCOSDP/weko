# -*- coding: utf-8 -*-

import argparse
import sys
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('filename')
parser.add_argument('root_path', nargs='?', default='.')
try:
    args = parser.parse_args()
except:
    sys.exit(0)

try:
    with open(args.filename, 'r') as contents:
        for line in contents:
            content = eval(line[:-1])
            try:
                print(content)
                with open(args.root_path + '/' + content['file_name'], 'rb') as file:
                    pid = PersistentIdentifier.query.filter_by(
                        pid_type='recid', pid_value=content['item_id']).first()
                    rec = RecordMetadata.query.filter_by(id=pid.object_uuid).first()
                    bucket = rec.json['_buckets']['deposit']
                    obj = ObjectVersion.create(bucket, content['upload_name'])
                    obj.set_contents(file)
                    db.session.commit()
            except Exception as ex:
                app.logger.info(str(ex))
                db.session.rollback()
except:
    print('Cannot open file: %s' % args.filename)

