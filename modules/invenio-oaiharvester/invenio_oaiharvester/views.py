# -*- coding: utf-8 -*-

"""InvenioOaiHarvester views."""
from flask import Blueprint,current_app
from werkzeug.local import LocalProxy
from invenio_db import db

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'invenio_oaiharvester',
    __name__,
    template_folder='templates',
    static_folder='static',
)

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_oaiharvester dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()