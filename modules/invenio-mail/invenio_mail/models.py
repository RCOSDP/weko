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

"""Database models for mail."""

import pickle
from invenio_db import db


class MailConfig(db.Model):
    """Mail Config."""

    id = db.Column(db.Integer, primary_key=True)
    mail_server = db.Column(db.String(255), default='localhost')
    mail_port = db.Column(db.Integer, default=25)
    mail_use_tls = db.Column(db.Boolean(name='use_tls'), default=False)
    mail_use_ssl = db.Column(db.Boolean(name='use_ssl'), default=False)
    mail_username = db.Column(db.String(255), default='')
    mail_password = db.Column(db.String(255), default='')
    mail_default_sender = db.Column(db.String(255), default='')

    @classmethod
    def get_config(cls):
        """Get mail Config."""
        if len(cls.query.all()) < 1:
            db.session.add(cls())
            db.session.commit()
        cfg = pickle.loads(pickle.dumps(cls.query.get(1).__dict__))
        cfg.pop('id')
        cfg.pop('_sa_instance_state')
        return cfg

    @classmethod
    def set_config(cls, new_config):
        """Set mail Config."""
        cfg = cls.query.get(1)
        cfg.mail_server = new_config['mail_server']
        cfg.mail_port = int(new_config['mail_port'])
        cfg.mail_use_tls = new_config['mail_use_tls']
        cfg.mail_use_ssl = new_config['mail_use_ssl']
        cfg.mail_username = new_config['mail_username']
        cfg.mail_password = new_config['mail_password']
        cfg.mail_default_sender = new_config['mail_default_sender']
        db.session.commit()
