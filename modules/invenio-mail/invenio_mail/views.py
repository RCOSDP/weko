# -*- coding: utf-8 -*-

"""InvenioMail views."""
from flask import Blueprint
from werkzeug.local import LocalProxy

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'invenio_mail',
    __name__,
    template_folder='templates',
    static_folder='static',
)
