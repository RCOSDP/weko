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

"""Models for weko-indextree-journal."""

from datetime import datetime

from flask import current_app, flash
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.event import listen
from sqlalchemy_utils.types import JSONType, UUIDType
from weko_index_tree.models import Index
from weko_records.models import Timestamp

# from sqlalchemy_utils.types import UUIDType
# from invenio_records.models import RecordMetadata


class Journal(db.Model, Timestamp):
    """
    Represent an journal.

    The Journal object contains a ``created``, a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'journal'

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """Identifier of the index."""

    index_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            Index.id,
            ondelete='CASCADE'),
        nullable=False)
    # """ID of Index to whom this shib user belongs."""

    index = db.relationship(Index,
                            backref=db.backref('journal', cascade='all'),
                            cascade='all, delete-orphan',
                            single_parent=True)
    """ID of Index to whom this journal belongs."""

    publication_title = db.Column(db.Text, nullable=True, default='')
    """Title of the journal."""

    abstract = db.Column(db.Text, nullable=True, default='')
    """abstract of the journal."""

    code_issnl = db.Column(db.Text, nullable=True, default='')
    """ISSN-L of the journal."""
    """
        varchar(9)
        It complies with the format of ISSN-L.
          ISSN-L:
            "^\\d{4}-?\\d{3}[0-9X]$"
    """

    print_identifier = db.Column(db.Text, nullable=True, default='')
    """Print-format identifier of the journal."""
    """
        varchar(20)
        It complies with the format of ISBN or ISSN.
          ISSN:
            "^\\d{4}-?\\d{3}[0-9X]$"
          ISBN:
            "^\\d{9}[0-9X]$"
            "^\\d+-\\d+-\\d+-[0-9X]$"
            "^97[8-9]\\d{9}[0-9X]$"
            "^97[8-9]-\\d+-\\d+-\\d+-[0-9X]$"
    """

    online_identifier = db.Column(db.Text, nullable=True, default='')
    """Online-format identifier of the journal."""
    """
        varchar(20)
        It complies with the format of ISBN or ISSN.
          ISSN:
            "^\\d{4}-?\\d{3}[0-9X]$"
          ISBN:
            "^\\d{9}[0-9X]$"
            "^\\d+-\\d+-\\d+-[0-9X]$"
            "^97[8-9]\\d{9}[0-9X]$"
            "^97[8-9]-\\d+-\\d+-\\d+-[0-9X]$"
    """

    date_first_issue_online = db.Column(db.Text, nullable=True, default='')
    """Date of first issue available online of the journal."""
    """
        varchar(10)
        It has one of the following format.
        YYYY-MM-DD and current date
        YYYY-MM
        YYYY
        YYYY is can be input only from 1700-2030
    """

    num_first_vol_online = db.Column(db.Text, nullable=True, default='')
    """Number of first volume available online of the journal."""
    """ varchar(255) """

    num_first_issue_online = db.Column(db.Text, nullable=True, default='')
    """Number of first issue available online of the journal."""
    """ varchar(255) """

    date_last_issue_online = db.Column(db.Text, nullable=True, default='')
    """Date of last issue available online of the journal."""
    """ varchar(10)
        It has one of the following format.
            YYYY-MM-DD and current date
            YYYY-MM
            YYYY
            YYYY is can be input only from 1700-2030
    """

    num_last_vol_online = db.Column(db.Text, nullable=True, default='')
    """Number of last volume available online of the journal."""
    """ varchar(255) """

    num_last_issue_online = db.Column(db.Text, nullable=True, default='')
    """Number of last issue available online of the journal."""
    """ varchar(255) """

    title_url = db.Column(db.Text, nullable=True, default='')
    """ varchar(2048)
        WEKO index search result page display URL
        [Top Page URL] /? Action = repository_opensearch & index_id = [title_id]
    """

    first_author = db.Column(db.Text, nullable=True, default='')
    """ first_author """

    title_id = db.Column(db.BigInteger, nullable=True, default=0)
    """ Output the index ID of WEKO. """

    embargo_info = db.Column(db.Text, nullable=True, default='')
    """Embargo information of the journal."""
    """ varchar(255) """

    coverage_depth = db.Column(db.Text, nullable=True, default='')
    """Coverage depth of the journal."""
    """
        varchar(255)
        Select one of the following items:
        Abstract, Fulltext, Selected Articles
    """

    coverage_notes = db.Column(db.Text, nullable=True, default='')
    """Coverage notes of the journal."""
    """ varchar(255) """

    publisher_name = db.Column(db.Text, nullable=True, default='')
    """The Publisher name of the journal."""
    """ varchar(255) """

    publication_type = db.Column(db.Text, nullable=True, default='')
    """Publication type of the journal."""
    """ varchar(255)
        Select the following item: "Serial"
    """

    date_monograph_published_print = db.Column(
        db.Text, nullable=True, default='')
    """" date_monograph_published_print """

    date_monograph_published_online = db.Column(
        db.Text, nullable=True, default='')
    """" date_monograph_published_online """

    monograph_volume = db.Column(db.Text, nullable=True, default='')
    """" monograph_volume """

    monograph_edition = db.Column(db.Text, nullable=True, default='')
    """" monograph_edition """

    first_editor = db.Column(db.Text, nullable=True, default='')
    """" first_editor """

    parent_publication_title_id = db.Column(
        db.BigInteger, nullable=True)
    """Parent publication identifier of the journal."""
    """
        int(11)
        An integer of 1 or larger.
            It's the index ID of index containing journal information
    """

    preceding_publication_title_id = db.Column(
        db.BigInteger, nullable=True)
    """Preceding publication identifier of the journal."""
    """
        int(11)
        An integer of 1 or larger.
            It's the index ID of index containing journal information
    """

    access_type = db.Column(db.Text, nullable=True, default='')
    """Access type of the journal."""
    """
        varchar(1)
        Select 1 of the following items: F, P
        Initial selection is  "F"
        Describe the following in item name of WEKO
        when registering journal information.
         F:Free
         P:Paid
    """

    language = db.Column(db.Text, nullable=True, default='')
    """Language of the journal."""
    """
        varchar(7)
        Select from language code (ISO639-2).
        In the pulldown, show:
        jpn, eng, chi, kor, (the others language by alphabet order).
    """

    title_alternative = db.Column(db.Text, nullable=True, default='')
    """Title alternative of the journal."""
    """ varchar(255) """

    title_transcription = db.Column(db.Text, nullable=True, default='')
    """Title transcription of the journal."""
    """ varchar(255) """

    ncid = db.Column(db.Text, nullable=True, default='')
    """NCID of the journal."""
    """ varchar(10)
        Allow the followoing formats.  "^[AB][ABN][0-9]{7}[0-9X]$"
    """

    ndl_callno = db.Column(db.Text, nullable=True, default='')
    """NDL Call No. of the journal."""
    """ varchar(20)
        Half-size alphanumeric symbol within 20 characters
    """

    ndl_bibid = db.Column(db.Text, nullable=True, default='')
    """NDL Call No. of the journal."""
    """ varchar(20)
        Half-size alphanumeric symbol within 20 characters
        TODO: Need to repair.
    """

    jstage_code = db.Column(db.Text, nullable=True, default='')
    """J-STAGE CDJOURNAL of the journal."""
    """ varchar(20)
        Half-size alphanumeric symbol within 20 characters
    """

    ichushi_code = db.Column(db.Text, nullable=True, default='')
    """Ichushi Code of the journal."""
    """ varchar(6)
        Allow the following input:"^J[0-9]{5}$"
    """

    deleted = db.Column(db.Text, nullable=True, default='')
    """Always output with empty string (character string length = 0)"""

    is_output = db.Column(db.Boolean(name='is_output'),
                          nullable=True,
                          default=lambda: False
                          )

    owner_user_id = db.Column(db.Integer, nullable=True, default=0)
    """Owner user id of the journal."""

    def __iter__(self):
        """Yield distributions for non-duplicate projects in the working set.

        The yield order is the order in which the items' path entries were
        added to the working set.
        """
        for name in dir(Journal):
            if not name.startswith('__') and not name.startswith('_') \
                    and name not in dir(Timestamp):
                value = getattr(self, name)
                if value is None:
                    value = ""
                if isinstance(value, str) or isinstance(value, bool) \
                        or isinstance(value, datetime) \
                        or isinstance(value, int):
                    yield (name, value)

    # format setting for community admin page

    def __str__(self):
        """Representation."""
        return 'Journal <id={0.id}, index_name={0.publication_title}>'.format(
            self)


class Journal_export_processing(db.Model, Timestamp):
    """
    Represent an journal.

    The Journal object contains a ``created``, a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'journal_export_processing'

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """id of the journal export process."""

    start_time = db.Column(db.DateTime, default=datetime.now)
    """start time to export journal."""

    end_time = db.Column(db.DateTime, default=datetime.now)
    """end time to export journal."""

    status = db.Column(db.Boolean(name='status'), nullable=True)
    """status of processing when export journal data."""

    @classmethod
    def save_export_info(cls, data):
        """Save export journal info."""
        try:
            with db.session.begin_nested():
                db.session.add(data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    @classmethod
    def get(cls):
        """Get last process of journal info."""
        return db.session.query(Journal_export_processing).order_by(
            Journal_export_processing.id.desc()
        ).first()


__all__ = ('IndexJournal', 'Journal_export_processing')
