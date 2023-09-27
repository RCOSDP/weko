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

"""API for weko-indextree-journal."""

from flask import current_app, request
from flask_login import current_user
from invenio_db import db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from weko_index_tree.api import Indexes

from .models import Journal


class Journals(object):
    """Define API for journal creation and update."""

    @classmethod
    def create(cls, journals=None):
        """
        Create the journals. Delete all journals before creation.

        :param journals: the journal information (dictinary).
        :returns: The :class:`Journal` instance lists or None.
        """
        def _add_journal(data):
            with db.session.begin_nested():
                journal = Journal(**data)
                db.session.add(journal)
            db.session.commit()

        if not isinstance(journals, dict):
            return

        data = dict()
        is_ok = True
        try:
            cid = journals.get('id')
            if not cid:
                return
            data["id"] = cid

            # check index id.
            index_id = journals.get('index_id')
            if not index_id:
                return

            index_info = Indexes.get_index(index_id=index_id, with_count=True)

            if index_info:
                data["index_id"] = index_id
            else:
                return

            data["publication_title"] = journals.get('publication_title')
            data["print_identifier"] = journals.get('print_identifier')
            data["online_identifier"] = journals.get('online_identifier')
            data["date_first_issue_online"] = journals.get(
                'date_first_issue_online')
            data["num_first_vol_online"] = journals.get('num_first_vol_online')
            data["num_first_issue_online"] = journals.get(
                'num_first_issue_online')
            data["date_last_issue_online"] = journals.get(
                'date_last_issue_online')
            data["num_last_vol_online"] = journals.get('num_last_vol_online')
            data["num_last_issue_online"] = journals.get(
                'num_last_issue_online')
            data["embargo_info"] = journals.get('embargo_info')
            data["coverage_depth"] = journals.get('coverage_depth')
            data["coverage_notes"] = journals.get('coverage_notes')
            data["publisher_name"] = journals.get('publisher_name')
            data["publication_type"] = journals.get('publication_type')
            data["parent_publication_title_id"] = journals.get(
                'parent_publication_title_id')
            data["preceding_publication_title_id"] = journals.get(
                'preceding_publication_title_id')
            data["access_type"] = journals.get('access_type')
            data["language"] = journals.get('language')
            data["title_alternative"] = journals.get('title_alternative')
            data["title_transcription"] = journals.get('title_transcription')
            data["ncid"] = journals.get('ncid')
            data["ndl_callno"] = journals.get('ndl_callno')
            data["ndl_bibid"] = journals.get('ndl_bibid')
            data["jstage_code"] = journals.get('jstage_code')
            data["ichushi_code"] = journals.get('ichushi_code')
            data["is_output"] = journals.get('is_output')
            # real url: '?action=' +
            # current_app.config['WEKO_INDEXTREE_JOURNAL_OPENSEARCH_URI'] +
            # '&index_id='
            data["title_url"] = 'search?search_type=2&q={}'.\
                format(index_id)
            data["title_id"] = index_id

            # get current user logged id.
            data["owner_user_id"] = current_user.get_id()

            _add_journal(data)
        except IntegrityError as ie:
            is_ok = False
            current_app.logger.debug(ie)
            db.session.rollback()
        except Exception as ex:
            is_ok = False
            current_app.logger.debug(ex)
            db.session.rollback()
        finally:
            del data
        return is_ok

    @classmethod
    def update(cls, journal_id, **data):
        """
        Update the journal detail info.

        :param journal_id: Identifier of the journal.
        :param detail: new journal info for update.
        :return: Updated journal info
        """
        try:
            with db.session.begin_nested():
                journal = db.session.query(Journal).\
                    filter_by(index_id=journal_id).one_or_none()
                if not journal:
                    return

                for k, v in data.items():
                    setattr(journal, k, v)
                journal.owner_user_id = current_user.get_id()
                db.session.merge(journal)
            db.session.commit()
            return journal
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def delete(cls, journal_id):
        """
        Delete the journal by journal_id.

        :param journal_id: Identifier of the journal.
        :return: bool True: Delete success None: Delete failed
        """
        try:
            with db.session.begin_nested():
                slf = cls.get_journal(journal_id)
                if not slf:
                    return
                slf = Journal.query.filter_by(id=journal_id).one()
                db.session.delete(slf)
            db.session.commit()
            return True
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None

    @classmethod
    def get_journal(cls, journal_id):
        """
        Get journal information by journal_id.

        :param journal_id: Identifier of the journal.
        :return: A journal object.
        """
        try:
            obj = db.session.query(Journal).filter_by(
                id=journal_id).one_or_none()

            if obj is None:
                return []

            return dict(obj)
        except SQLAlchemyError as e:
            current_app.logger.error(
                '[{0}] Data acquisition error (DB error). Error: {1}'.format(
                    100, e
                )
            )
            current_app.logger.error(
                '[{0}] [{1} {2}] End with error.'.format(
                    100, 'Get Journal By ID ', journal_id
                )
            )
            db.session.rollback()
        except Exception as ex:
            current_app.logger. \
                error('[{0}] End with unknown error. Error:{1}'.format(1, ex))
            db.session.rollback()
            return None

    @classmethod
    def get_journal_by_index_id(cls, index_id):
        """
        Get journal information by index_id.

        :param index_id: Identifier of the journal.
        :return: A journal object.
        """
        try:
            current_app.logger.info('[{0}] [{1} {2}] START'.format(
                0, 'Get Journal By Index ID ', index_id))
            obj = db.session.query(Journal).filter_by(index_id=index_id)\
                .one_or_none()
            current_app.logger.info('[{0}] [{1} {2}] END'.format(
                0, 'Get Journal By Index ID ', index_id))

            if obj is None:
                current_app.logger.info(
                    '[{0}] Return {1} when get by index ID {2}.'.format(
                        0, obj, index_id
                    )
                )
                return {}

            return dict(obj)
        except SQLAlchemyError as e:
            current_app.logger.error(
                '[{0}] Data acquisition error (DB error). Error: {1}'.format(
                    100, e)
            )
            current_app.logger.error(
                '[{0}] [{1} {2}] End with error.'.format(
                    100, 'Get Journal By Index ID ', index_id
                )
            )
            db.session.rollback()
        except Exception as ex:
            current_app.logger. \
                error('[{0}] End with unknown error. Error:{1}'.format(1, ex))
            db.session.rollback()
            return None

    @classmethod
    def get_all_journals(cls):
        """
        Get all journals in journal table.

        :return: List of journal object.
        """
        try:
            journals = db.session.query(Journal).all()

            #if journals is None:
            if journals == []:
                current_app.logger.info(
                    '[{0}] Return {1} when get all journal.'.format(
                        0, journals)
                )
                return None

            return journals
        except SQLAlchemyError as e:
            current_app.logger.error(
                '[{0}] Data acquisition error (DB error). Error: {1}'.format(
                    100, e
                )
            )
            current_app.logger.error(
                '[{0}] [{1}] End with error.'.format(
                    100, 'Get all journal'
                )
            )
            db.session.rollback()
        except Exception as ex:
            current_app.logger.error(
                '[{0}] End with unknown error. Error:{1}'.format(
                    1, ex
                )
            )
            db.session.rollback()
            return None
