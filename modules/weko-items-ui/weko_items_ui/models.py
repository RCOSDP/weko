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

from datetime import datetime
from copy import deepcopy
import math
from flask import current_app
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types.choice import ChoiceType
from invenio_db.shared import db
from invenio_pidstore.models import RecordIdentifier
from sqlalchemy_utils.types import UUIDType
from invenio_pidstore.models import PersistentIdentifier
from weko_records.models import ItemMetadata
from weko_authors.models import Authors

class CRIS_Institutions(object):

    """ INSTITUTION TYPES START"""


    RM = 'researchmap'


    """ INSTITUTION TYPES END """


class CRISLinkageResult(db.Model, Timestamp):

    __tablename__ = 'cris_linkage_result'

    """ record id """
    recid = db.Column(
        db.Integer,
        db.ForeignKey(RecordIdentifier.recid),
        primary_key=True,
    )

    cris_institution = db.Column(
        db.Text,
        primary_key=True,
        nullable = False,
    )

    last_linked_date = db.Column(
        db.DateTime,
        nullable= True,
    )

    last_linked_item = db.Column(
        UUIDType,
        db.ForeignKey(ItemMetadata.id),
        nullable= True,
    )
    
    succeed = db.Column(
        db.Boolean,
        nullable= True
    )

    failed_log = db.Column(
        db.Text,
        nullable = False,
        default = ''
    )

    def get_last(self ,recid ,cris_institution):
        return self.query.filter_by(recid=recid , cris_institution=cris_institution).one_or_none()
    
    def register_linkage_result(self ,recid ,cris_institution ,result ,item_uuid ,failed_log):
        with db.session.begin_nested():
            lresult:CRISLinkageResult = self.get_last(recid ,cris_institution)
            if not lresult:
                lresult = CRISLinkageResult()
                lresult.recid = recid
                lresult.cris_institution = cris_institution
            
            lresult.succeed = result
            if not result:
                lresult.failed_log = failed_log
            else :
                lresult.failed_log = ''
                lresult.last_linked_date = datetime.utcnow()
                lresult.last_linked_item = item_uuid

            db.session.add(lresult)
        db.session.commit()
        return True
    
    def set_running(self, item_uuid ,cris_institution):
        with db.session.begin_nested():
            recid = PersistentIdentifier.get_by_object(pid_type='recid',
                                            object_type='rec',
                                            object_uuid=item_uuid)
            recid = math.floor(float(recid.pid_value))
            lresult =  self.get_last(recid ,cris_institution)
            if lresult :
                lresult.succeed = None

            if not lresult :
                lresult = CRISLinkageResult()
                lresult.recid = recid
                lresult.cris_institution = cris_institution
                lresult.succeed = None
                lresult.last_linked_item = item_uuid

        db.session.add(lresult)
        db.session.commit()
        return 