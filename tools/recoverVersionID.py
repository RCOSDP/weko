import sys
import time

from flask import current_app
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from sqlalchemy.orm.exc import NoResultFound


def recoverVersionID(dryrun=False):
    start = time.time()
    q = PersistentIdentifier.query.filter_by(pid_type='parent', status='R')
    FILE_PROP = 'item_1583103120197'
    count = 0
    for i in q:
        try:
            r = Record.get_record(i.object_uuid)
            if FILE_PROP in r:
                if 'attribute_value_mlt' in r[FILE_PROP]:
                    for prop in r[FILE_PROP]['attribute_value_mlt']:
                        if 'version_id' not in prop:
                            for f in r.files:
                                prop['version_id'] = str(f.version_id)
                            count = count + 1
                            current_app.logger.info(
                                "{0} Process recid: {1}, id: {2}".format(time.time(), r['recid'], i.object_uuid))
                            if not dryrun:
                                r.commit()
        except NoResultFound as e:
            current_app.logger.error("No Record {0}".format(i))
    if not dryrun:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    current_app.logger.info(
        "Processed {0} items, elapsed time: {1}".format(count, time.time()-start))


if __name__ == '__main__':
    args = sys.argv
    dryrun = False
    if args[1] == "--dryrun":
        print(args[1])
    # recoverVersionID(args[1])
