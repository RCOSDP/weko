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
from invenio_db import db
from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.models import OAISet
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
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
        ).yield_per(1000)

    return indexes


def get_delete_records():
    """Get all deleted records.

    Returns:
        [type]: [description]
    """
    pids = db.session.query(
        PersistentIdentifier
    ).filter(
        PersistentIdentifier.pid_type == 'recid',
        PersistentIdentifier.status == PIDStatus.DELETED
    ).yield_per(1000)

    return [item.object_uuid for item in pids]


def update_oai_sets():
    """Update OAI.Sets table.

    Returns:
        [type]: [description]
    """
    logging.info(' STARTED update OAI Sets.')
    oai_sets = OAISet.query.all()
    indexes = get_public_indexes()

    # INIT
    sets_totals = 0
    sets_update = 0
    sets_delete = 0
    sets_create = 0

    index_ids = [item.cid for item in indexes if item]
    sets_missed = list(set(index_ids) - set(
        [item.id for item in oai_sets if item]))
    sets_totals = len(index_ids)

    # Handle for update/delete OAISet
    try:
        with db.session.begin_nested():
            for oaiset in oai_sets:
                if oaiset.id in index_ids:
                    new_set = 'path:"{}"'.format(str(oaiset.id))
                    if oaiset.search_pattern != new_set:
                        oaiset.search_pattern = new_set
                        db.session.merge(oaiset)
                        sets_update += 1
                    else:
                        continue
                else:
                    db.session.delete(oaiset)
                    sets_delete += 1
    except SQLAlchemyError as ex:
        logging.info(' ERROR: {}.'.format(ex))
    # Handle for new OAISet
    try:
        with db.session.begin_nested():
            for index in indexes:
                if index.cid in sets_missed:
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
    except SQLAlchemyError as ex:
        logging.info(' ERROR: {}.'.format(ex))
    # Commit
    db.session.commit()

    logging.info(' FINISHED update OAI Sets.')
    logging.info(' Totals   : {}'.format(sets_totals))
    logging.info(' Created  : {}'.format(sets_create))
    logging.info(' Updated  : {}'.format(sets_update))
    logging.info(' Deleted  : {}'.format(sets_delete))
    logging.info('-' * 60)

    return index_ids


def update_records_metadata(oai_sets: list = []):
    """Update record.json include: _oai and path.

    Args:
        oai_sets (list, optional): [description]. Defaults to [].
    """
    logging.info(' STARTED update Records Metadata.')
    records = db.session.query(RecordMetadata).yield_per(1000)
    rec_totals = 0
    delete_records = get_delete_records()

    try:
        with db.session.begin_nested():
            for rec in records:
                deposit = WekoDeposit(rec.json, rec)
                if deposit.get('path'):
                    deposit['path'] = [item.split("/")[-1] for item
                                       in deposit["path"] if item]
                    if deposit.get('_oai'):
                        deposit['_oai']['sets'] = \
                            [item for item in deposit["path"]
                                if item in oai_sets]
                    deposit.commit()
                    try:
                        is_deleted = False
                        if deposit.id in delete_records:
                            is_deleted = True
                        deposit.indexer.update_path(
                            deposit,
                            update_revision=False,
                            update_oai=True,
                            is_deleted=is_deleted)
                    except TransportError as ex:
                        logging.info(' ERROR-TransportError: {}.'.format(ex))
                        continue
                rec_totals += 1
    except SQLAlchemyError as ex:
        logging.info(' ERROR: {}.'.format(ex))
        db.session.rollback()
    db.session.commit()

    logging.info(' FINISHED update Records Metadata.')
    logging.info(' Totals   : {}'.format(rec_totals))


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
    # Prevent percolator update.
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
