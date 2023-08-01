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

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.models import OAISet
from invenio_communities.config import COMMUNITIES_OAI_FORMAT
from invenio_records.models import RecordMetadata
from elasticsearch.exceptions import TransportError
from weko_deposit.api import WekoDeposit

from datetime import datetime
import os
import sys
import math
import json
import logging
import traceback

# for logging
start_time = datetime.today()

# global connect
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
connection = engine.connect()


def get_public_indexes ():
    sql_get_indexes = '''
    WITH RECURSIVE recursive_t (
        pid, 
        cid, 
        path, 
        name, 
        name_en, 
        public_state, 
        harvest_public_state
        ) AS (
        SELECT 
            index.parent               AS pid, 
            index.id                   AS cid, 
            CAST(index.id AS TEXT)     AS path, 
            index.index_name           AS name, 
            index.index_name_english   AS name_en, 
            index.public_state         AS public_state, 
            index.harvest_public_state AS harvest_public_state 
        FROM index 
        WHERE
            index.parent = 0
        UNION ALL 
           SELECT 
                t.parent                              AS t_parent, 
                t.id                                  AS t_id, 
                rec.path || '/' || CAST(t.id AS TEXT) AS anon_1, 
                CASE WHEN (length(t.index_name) = 0) THEN NULL ELSE rec.name || '-/-' || t.index_name END AS anon_2, 
                rec.name_en || '-/-' || t.index_name_english AS anon_3, 
                t.public_state                               AS t_public_state, 
                t.harvest_public_state                       AS t_harvest_public_state 
           FROM 
               index AS t, recursive_t AS rec 
           WHERE
               t.parent = rec.cid
        )
    SELECT 
        recursive_t.pid                  AS recursive_t_pid, 
        recursive_t.cid                  AS recursive_t_cid, 
        recursive_t.path                 AS recursive_t_path, 
        recursive_t.name                 AS recursive_t_name, 
        recursive_t.name_en              AS recursive_t_name_en, 
        recursive_t.public_state         AS recursive_t_public_state, 
        recursive_t.harvest_public_state AS recursive_t_harvest_public_state 
    FROM
        recursive_t 
    WHERE
        recursive_t.public_state IS true AND 
        recursive_t.harvest_public_state IS true
    '''.strip()

    # with engine.begin() as connection:
    indexes = connection.execute(sql_get_indexes).fetchall()

    return indexes


def update_oai_sets ():
    logging.info(' STARTED update OAI Sets.')
    oai_sets = OAISet.query.all()
    indexes = get_public_indexes()

    # INIT
    sets_totals = 0
    sets_update = 0
    sets_delete = 0
    sets_create = 0
    sets_update_error = []
    sets_delete_error = []
    sets_create_error = []

    index_ids = []
    for item in indexes:
        if item[1] > 0:
            index_ids.append(item[1])

    sets_missed = list(set(index_ids) - set([item.id for item in oai_sets if item]))
    sets_totals = len(index_ids)

    current_app.logger.debug("len(sets_missed): {0}".format(len(sets_missed)))
    current_app.logger.debug("sets_totals: {0}".format(sets_totals))

    com_prefix = COMMUNITIES_OAI_FORMAT.replace('{community_id}', '')

    for oaiset in oai_sets:
        if oaiset.id in index_ids:
            new_set = 'path:"{}"'.format(oaiset.id)
            if oaiset.search_pattern != new_set:

                row = []
                # update val
                row.append(new_set)
                # update key
                row.append(oaiset.id)

                # update
                res_error = oai_update (row)
                if res_error == False:
                    sets_update += 1
                else:
                    sets_update_error.append(res_error)
            else:
                continue
        else:
            if (oaiset.spec).startswith(com_prefix):
                # community spec
                continue
            elif (oaiset.spec)[0].isdigit():
                # index spec
                # current_app.logger.info("delete OAISet:{0}".format(oaiset.spec))
                # db.session.delete(oaiset)

                row = []
                # delete key
                row.append(oaiset.id)

                # delete
                res_error = oai_delete (row)
                if res_error == False:
                    sets_delete += 1
                else:
                    sets_delete_error.append(res_error)
            else:
                # other spec
                continue

    # Handle for new OAISet
    for index in indexes:
        if index[1] in sets_missed:
            row = []
            # cid
            row.append(index[1])
            # spec
            row.append(index[2].replace("/", ":"))
            # name
            str = index[3].split("-/-")[-1] if index[3] else index[4].split("-/-")[-1]
            row.append(str)
            # description
            str = index[3].replace("-/-", "->") if index[3] else index[4].replace("-/-", "->")
            row.append(str)
            # search_pattern
            row.append('path:"{}"'.format(index[1]))

            # insert
            res_error = oai_insert(row)
            if res_error == False:
                sets_create += 1
            else:
                sets_create_error.append(res_error)

    current_app.logger.info('-' * 60)
    current_app.logger.info(' FINISHED update OAI Sets.')
    current_app.logger.info(' Totals   : total {}'.format(sets_totals))
    current_app.logger.info(' Created  : ok {} / ng {}'.format(sets_create, len(sets_create_error)))
    current_app.logger.info(' Updated  : ok {} / ng {}'.format(sets_update, len(sets_update_error)))
    current_app.logger.info(' Deleted  : ok {} / ng {}'.format(sets_delete, len(sets_delete_error)))
    current_app.logger.info('-' * 30)

    if len(sets_create_error) > 0:
        current_app.logger.info('sets_create error ids:{}'.format(len(sets_create_error)))
        current_app.logger.info(sets_create_error)
        current_app.logger.info('-' * 30)
    if len(sets_update_error) > 0:
        current_app.logger.info('sets_update error ids:{}'.format(len(sets_update_error)))
        current_app.logger.info(sets_update_error)
        current_app.logger.info('-' * 30)
    if len(sets_delete_error) > 0:
        current_app.logger.info('sets_delete error ids:{}'.format(len(sets_delete_error)))
        current_app.logger.info(sets_delete_error)
        current_app.logger.info('-' * 30)

    # sys.exit()
    return index_ids


def oai_insert (row):
    sql_oai_insert = '''
    INSERT INTO oaiserver_set 
        (
            created, updated, id, spec, name, description, search_pattern 
        ) VALUES ( 
            'now()', 'now()', %s, %s, %s, %s, %s
        )
    '''.strip()
    try:
        with connection.begin():
            connection.execute(sql_oai_insert, row)
    except SQLAlchemyError as ex:
        current_app.logger.info("oai_insert:rollback one -> cid:{}".format(row[0]))
        return row[0]
    #else:
        # current_app.logger.info("oai_insert:commit one -> cid:{}".format(row[0]))

    return False


def oai_update (row):
    sql_oai_update = "UPDATE oaiserver_set SET search_pattern=%s, updated='now()' WHERE id= %s"
    try:
        with connection.begin():
            connection.execute(sql_oai_update, row)
    except SQLAlchemyError as ex:
        current_app.logger.info("oai_update:rollback one -> id:{}".format(row[1]))
        return row[1]
    #else:
        # current_app.logger.info("oai_update:commit one -> id:{}".format(row[1]))

    return False


def oai_delete (row):
    sql_oai_delete = "DELETE FROM oaiserver_set WHERE id= %s"
    try:
        with connection.begin():
            connection.execute(sql_oai_delete, row)
    except SQLAlchemyError as ex:
        current_app.logger.info("oai_delete:rollback one -> id:{}".format(row[0]))
        return row[0]
    #else:
        # current_app.logger.info("oai_delete:commit one -> id:{}".format(row[0]))

    return False


def get_delete_records():
    """Get all deleted records.

    Returns:
        [type]: [description]

    # org
    pids = db.session.query(
        PersistentIdentifier
    ).filter(
        PersistentIdentifier.pid_type == 'recid',
        PersistentIdentifier.status == PIDStatus.DELETED
    ).yield_per(1000)
    return [item.object_uuid for item in pids]
    """

    sql_delete_records = '''
    SELECT 
        pidstore_pid.object_uuid  AS pidstore_pid_object_uuid 
    FROM 
        pidstore_pid 
    WHERE 
        pidstore_pid.pid_type = 'recid' 
        AND pidstore_pid.status = 'D'
        AND object_uuid  IS NOT NULL
    '''.strip()

    pids = connection.execute(sql_delete_records).fetchall()

    return [item[0] for item in pids]



def get_meta_records():
    # 全件selectは数秒かかる
    current_app.logger.info('get meta records')
    sql_meta_records = '''
    SELECT 
        -- records_metadata.created    AS records_metadata_created, 
        -- records_metadata.updated    AS records_metadata_updated, 
        -- records_metadata.id         AS records_metadata_id, 
        -- records_metadata.json       AS records_metadata_json, 
        -- records_metadata.version_id AS records_metadata_version_id 
        records_metadata.created, 
        records_metadata.updated, 
        records_metadata.id, 
        records_metadata.json, 
        records_metadata.version_id 
    FROM 
        records_metadata
    -- LIMIT 500
    '''.strip()
    records = connection.execute(sql_meta_records).fetchall()
    current_app.logger.info('records count:{}'.format(len(records)))
    return records


def get_transaction_id_max():
    sql = "SELECT MAX(id) as id FROM transaction"
    res = connection.execute(sql).fetchone()
    return int(res[0])


def insert_transaction():
    # check table alive > transaction_id_seq
    sql = "SELECT * FROM information_schema.tables WHERE table_name = 'transaction_id_seq'"
    res = connection.execute(sql).fetchall()

    if (len(res) == 0):
        # case not seq
        transaction_id = get_transaction_id_max()
        transaction_id += 1
        row = []
        row.append(transaction_id)
        sql_insert_transaction  = '''
            INSERT INTO transaction (
                issued_at, id, remote_addr, user_id
            ) VALUES (
                'now()', %s, NULL, NULL)
        '''.strip()
        connection.execute(sql_insert_transaction, row)
    else:
        # case use seq
        sql_insert_transaction  = '''
            INSERT INTO transaction (
                issued_at, remote_addr, user_id
            ) VALUES (
                'now()', NULL, NULL)
        '''.strip()
        connection.execute(sql_insert_transaction)
        transaction_id = get_transaction_id_max()

    return transaction_id



def update_records_metadata(oai_sets: list = []):
    """Update record.json include: _oai and path.

    Args:
        oai_sets (list, optional): [description]. Defaults to [].
    """
    current_app.logger.info('-' * 60)
    current_app.logger.info(' STARTED update Records Metadata.')
    current_app.logger.info('-' * 60)

    # records = db.session.query(RecordMetadata).yield_per(1000)
    records = get_meta_records()
    delete_records = get_delete_records()
    transaction_id = insert_transaction()

    loop = 0
    rec_totals = 0
    ok_count = 0
    ng_count = 0
    transport_error = 0
    for rec in records:
        error_flag = False
        metadata_id = rec.id
        deposit = WekoDeposit(rec.json, rec)
        if deposit.get('path'):
            loop += 1
            rec_totals += 1
            if loop == 1000:
                job_now = datetime.today()
                current_app.logger.info("{} -> {}".format(job_now, rec_totals))
                loop = 0
            deposit['path'] = [item.split("/")[-1] for item in deposit["path"] if item]
            if deposit.get('_oai'):
                _sets = []
                if (deposit['_oai']).get('sets'):
                    for i in (deposit['_oai']).get('sets'):
                        if not i[0].isdigit():
                            _sets.append(i)

                deposit['_oai']['sets'] = [item for item in deposit["path"] if int(item) in oai_sets]
                deposit['_oai']['sets'].extend(_sets)
                # current_app.logger.debug("replaced _oai.sets:{}".format(deposit['_oai']['sets']))

                json_str = json.dumps(deposit)
                version_id = int(rec.version_id)
                version_id_next = int(version_id) +1

                with connection.begin():
                    row = []
                    row.append(json_str)
                    row.append(version_id_next)
                    row.append(metadata_id)
                    row.append(version_id)
                    sql = """
                    UPDATE records_metadata SET 
                        updated='now()', 
                        json= %s, 
                        version_id= %s 
                    WHERE 
                        records_metadata.id = %s 
                        AND records_metadata.version_id = %s
                    """.strip()
                    try:
                        connection.execute(sql, row)
                    except SQLAlchemyError as ex:
                        current_app.logger.info("update records_metadata:error -> {} -> {}".format(metadata_id, version_id))
                        error_flag = True

                    row = []
                    row.append(metadata_id)
                    row.append(json_str)
                    row.append(version_id_next)
                    row.append(transaction_id)
                    sql = """
                    INSERT INTO records_metadata_version (
                        created, updated, id, json, version_id, transaction_id, end_transaction_id, operation_type
                    ) VALUES (
                        'now()', 'now()', %s, %s, %s, %s, NULL, 1
                    )
                    """.strip()
                    try:
                        connection.execute(sql, row)
                    except SQLAlchemyError as ex:
                        current_app.logger.info("insert records_metadata_version:error -> {} -> {}".format(metadata_id, version_id))
                        error_flag = True

                    row = []
                    row.append(transaction_id)
                    row.append(transaction_id)
                    row.append(metadata_id)
                    row.append(metadata_id)
                    sql = """
                    UPDATE records_metadata_version SET 
                        end_transaction_id= %s 
                    WHERE 
                    records_metadata_version.transaction_id = 
                        (
                        SELECT 
                            max(records_metadata_version_1.transaction_id) AS max_1 
                        FROM 
                            records_metadata_version AS records_metadata_version_1 
                        WHERE 
                            records_metadata_version_1.transaction_id < %s 
                            AND records_metadata_version_1.id = %s
                        ) 
                    AND records_metadata_version.id = %s
                    """.strip()
                    try:
                        connection.execute(sql, row)
                    except SQLAlchemyError as ex:
                        current_app.logger.info("update records_metadata_version:error -> {} -> {}".format(metadata_id, version_id))
                        error_flag = True

                if error_flag == False:
                    ok_count += 1
                    try:
                        is_deleted = False
                        if metadata_id in delete_records:
                            is_deleted = True
                        deposit.indexer.update_es_data(
                            deposit,
                            update_revision=False,
                            update_oai=True,
                            is_deleted=is_deleted)
                    except TransportError as ex:
                        current_app.logger.info(' ERROR-TransportError: {}.'.format(ex))
                        transport_error+=1
                        continue
                else:
                    ng_count += 1
            # sys.exit()

    current_app.logger.info(' FINISHED update Records Metadata. - transaction_id:{}'.format(transaction_id))
    current_app.logger.info(' total:{} / ok:{} / ng:{}'.format(rec_totals, ok_count, ng_count))
    current_app.logger.info(' TransportError:{}'.format(transport_error))


def main():
    """Application's main function."""
    # Start logging
    logging.basicConfig(
        level=logging.INFO,
        filename='logging-replace-index-id-process' +
                 '{:-%Y%m%d-%s.}'.format(datetime.now()) +
                 str(os.getpid()) + ".log",
        filemode='w',
        format="%(asctime)-15s %(levelname)-5s %(message)s")
    logging.info('*' * 60)

    indexes = []

    # Update OAISets
    indexes = update_oai_sets()
    # sys.exit()


    # Temporary disable oaiset signals.
    # Prevent percolator update.
    current_oaiserver.unregister_signals()
    # Update Record Metadata.
    # current_app.logger.debug("indexes: {}".format(indexes))
    update_records_metadata(indexes)
    current_oaiserver.register_signals()

    end_time = datetime.today()

    current_app.logger.info('--> Finished')
    current_app.logger.info('    start time - {}'.format(start_time))
    current_app.logger.info('    end time   - {}'.format(end_time))
    connection.close()
    print(' Finished! ')


if __name__ == '__main__':
    """Main context."""
    main()

