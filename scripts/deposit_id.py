# -*- coding: utf-8 -*-

import argparse
import sys
from invenio_db import db
from weko_deposit.api import WekoDeposit

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('filename')
try:
    args = parser.parse_args()
except:
    sys.exit(0)

try:
    with open(args.filename) as f:
        for line in f:
            rid = line[:-1]
            try:
                WekoDeposit.create({}, recid=rid)
                db.session.commit()
                app.logger.info('Deposit id: %s created.' % rid)
            except Exception as ex:
                app.logger.error(
                    'Error occurred during creating deposit id: %s' % rid)
                app.logger.info(str(ex))
                db.session.rollback()
except:
    print('Cannot open file: %s' % args.filename)

