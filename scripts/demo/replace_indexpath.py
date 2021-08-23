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
from time import sleep

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.models import OAISet
from invenio_records.models import RecordMetadata
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import case, func
from weko_deposit.api import WekoDeposit
from weko_index_tree.models import Index


def get_public_indexes():
    """Get all indexes allowing create OAI.Set.

    Returns:
        [type]: [description]
    """
    recursive_t = db.session.query(
        Index.parent.label("pid"),
        Index.id.label("cid"),
        func.cast(Index.id, db.Text).label("path"),
        Index.index_name.label("name"),
        Index.index_name_english.label("name_en"),
        Index.public_state.label("public_state"),
        Index.harvest_public_state.label("harvest_public_state")
    ).filter(
        Index.parent == 0,
    ).cte(name="recursive_t", recursive=True)

    rec_alias = aliased(recursive_t, name="rec")
    test_alias = aliased(Index, name="t")
    recursive_t = recursive_t.union_all(
        db.session.query(
            test_alias.parent,
            test_alias.id,
            rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
            case([(func.length(test_alias.index_name) == 0, None)],
                 else_=rec_alias.c.name + '-/-' + test_alias.index_name),
            rec_alias.c.name_en + '-/-' + test_alias.index_name_english,
            test_alias.public_state,
            test_alias.harvest_public_state,
        ).filter(
            test_alias.parent == rec_alias.c.cid,
        )
    )

    with db.session.begin_nested():
        indexes = db.session.query(
            recursive_t
        ).filter(
            recursive_t.c.public_state.is_(True),
            recursive_t.c.harvest_public_state.is_(True)
        ).all()

    return indexes


def update_oai_sets():
    """Update OAI.Sets table.

    Returns:
        [type]: [description]
    """
    logging.info(' START update OAI Sets.')
    oai_sets = OAISet.query.all()
    indexes = get_public_indexes()

    # INIT
    sets_totals = 0
    sets_errors = 0
    sets_update = 0
    sets_delete = 0
    sets_create = 0

    index_ids = [item.cid for item in indexes if item]
    sets_missed = list(set(index_ids) - set(
        [item.id for item in oai_sets if item]))
    sets_totals = len(index_ids)

    # Handle for update/delete OAISet
    for oaiset in oai_sets:
        update = False
        try:
            with db.session.begin_nested():
                if oaiset.id in index_ids:
                    new_set = 'path:"{}"'.format(str(oaiset.id))
                    if oaiset.search_pattern != new_set:
                        oaiset.search_pattern = new_set
                        db.session.merge(oaiset)
                        update = True
                    else:
                        continue
                else:
                    db.session.delete(oaiset)
            if update:
                sets_update += 1
            else:
                sets_delete += 1
        except Exception as ex:
            logging.info(' ERROR!: When handle Set'
                         ': {}/ detail: {}.'.format(oaiset.id, ex))
            sets_errors += 1
            continue

    # Handle for new OAISet
    for index in indexes:
        if index.cid in sets_missed:
            try:
                with db.session.begin_nested():
                    oaiset = OAISet(
                        id=index.cid,
                        spec=index.path.replace("/", ":"),
                        name=index.name.split("-/-")[-1]
                        if index.name else index.name_en.split("-/-")[-1],
                        description=index.name.replace("-/-", "->")
                        if index.name else index.name_en.replace("-/-", "->"),
                        search_pattern='path:"{}"'.format(index.cid)
                    )
                    db.session.add(oaiset)
                sets_create += 1
            except Exception as ex:
                logging.info(' ERROR!: When create Set'
                             ': {}/ detail: {}.'.format(oaiset.id, ex))
                sets_errors += 1
                continue

    # Commit
    db.session.commit()
    logging.info(' FINISH update OAI Sets.')
    logging.info(' Total    : {}'.format(sets_totals))
    logging.info(' Created  : {}'.format(sets_create))
    logging.info(' Updated  : {}'.format(sets_update))
    logging.info(' Deleted  : {}'.format(sets_delete))
    logging.info(' Errored  : {}'.format(sets_errors))
    if sets_totals != (sets_create + sets_update + sets_delete + sets_errors):
        logging.info(' The remains not had been changed.')
    logging.info('-' * 60)

    return index_ids


def update_records_metadata(oai_sets: list = []):
    """Update record.json include: _oai and path.

    Args:
        oai_sets (list, optional): [description]. Defaults to [].
    """
    logging.info(' START update Records Metadata.')
    records = db.session.query(RecordMetadata).yield_per(1000)

    rec_totals = 0
    rec_errors = 0

    for rec in records:
        rec_totals += 1
        try:
            with db.session.begin_nested():
                deposit = WekoDeposit(rec.json, rec)
                if deposit.get('path'):
                    deposit['path'] = [item.split("/")[-1] for item
                                       in deposit["path"] if item]
                    if deposit.get('_oai'):
                        deposit['_oai']['sets'] = \
                            [item for item in deposit["path"]
                                if item in oai_sets]
                deposit.update_item_by_task()
        except SQLAlchemyError as ex:
            logging.info(' ERROR!: When update Record'
                         ': {}/ detail: {}.'.format(rec.id, ex))
            rec_errors += 1
            continue

    db.session.commit()

    # Update record to ES
    sleep(20)
    query = (item.id for item in records if item)
    logging.info(' REINDEX Records Metadata on ES.')

    RecordIndexer().bulk_index(query)
    RecordIndexer().process_bulk_queue(
        es_bulk_kwargs={'raise_on_error': True})

    logging.info(' FINISH update Records Metadata.')
    logging.info(' Total    : {}'.format(rec_totals))
    logging.info(' Errored  : {}'.format(rec_errors))


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

    # Temporary disable oaiset signals.
    current_oaiserver.unregister_signals()
    indexes = []

    # Update OAISets
    indexes = update_oai_sets()
    # Update Record Metadata.
    update_records_metadata(indexes)

    current_oaiserver.register_signals()

    logging.info(' FINISHED ')
    logging.info('*' * 60)
    print(' Finished! ')


if __name__ == '__main__':
    """Main context."""
    main()
