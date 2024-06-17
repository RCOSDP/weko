# -*- coding: utf-8 -*-

"""InvenioMail views."""
from flask import Blueprint,current_app
from werkzeug.local import LocalProxy
from invenio_db import db

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'invenio_mail',
    __name__,
    template_folder='templates',
    static_folder='static',
)

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_mail dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()