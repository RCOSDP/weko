# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 module docstring."""

import logging
import os
from datetime import datetime

from elasticsearch.exceptions import TransportError
from flask import current_app
from sqlalchemy import create_engine
from weko_deposit.api import WekoDeposit

# for logging
start_time = datetime.today()

# global connect
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
connection = engine.connect()


def get_deleted_meta_records():
    """Get all deleted records."""
    current_app.logger.info('get deleted meta records')
    sql_deleted_meta_records = '''
    SELECT 
        records_metadata.created, 
        records_metadata.updated, 
        records_metadata.id, 
        records_metadata.json, 
        records_metadata.version_id 
    FROM 
        records_metadata
    JOIN 
        pidstore_pid
    ON 
        records_metadata.id = pidstore_pid.object_uuid
    WHERE
        pidstore_pid.pid_type = 'recid' 
        AND pidstore_pid.status = 'D'
        AND pidstore_pid.object_uuid  IS NOT NULL
    '''.strip()

    records = connection.execute(sql_deleted_meta_records).fetchall()
    current_app.logger.info('deleted records count:{}'.format(len(records)))

    return records

def update_elasticsearch_index():
    """Update elasticsearch index: _source.path to empty ."""
    current_app.logger.info('-' * 60)
    current_app.logger.info(' STARTED update elasticsearch index: _source.path.')
    current_app.logger.info('-' * 60)

    deleted_records = get_deleted_meta_records()

    loop = 0
    rec_totals = 0
    ok_count = 0
    transport_error = 0
    for rec in deleted_records:
        loop += 1
        rec_totals += 1
        if loop == 1000:
            job_now = datetime.today()
            current_app.logger.info("{} -> {}".format(job_now, rec_totals))
            loop = 0
        deposit = WekoDeposit(rec.json, rec)
        deposit['path'] = []
        try:
            deposit.indexer.update_es_data(deposit, update_revision=False)
            ok_count += 1
        except TransportError as ex:
            current_app.logger.info(' ERROR-TransportError: {}.'.format(ex))
            transport_error += 1
            continue

    current_app.logger.info(' FINISHED update elasticsearch index: _source.path')
    current_app.logger.info(' total:{} / ok:{} / error:{}'.format(rec_totals, ok_count, transport_error))


def main():
    """Application's main function."""
    # Start logging
    logging.basicConfig(
        level=logging.INFO,
        filename='logging-fix-elasticsearch-deleted-item-path-process' +
                 '{:-%Y%m%d-%s.}'.format(datetime.now()) +
                 str(os.getpid()) + ".log",
        filemode='w',
        format="%(asctime)-15s %(levelname)-5s %(message)s")
    logging.info('*' * 60)

    # Update Elasticsearch index.
    update_elasticsearch_index()

    end_time = datetime.today()

    current_app.logger.info('--> Finished')
    current_app.logger.info('    start time - {}'.format(start_time))
    current_app.logger.info('    end time   - {}'.format(end_time))
    connection.close()
    print(' Finished! ')


if __name__ == '__main__':
    """Main context."""
    main()

