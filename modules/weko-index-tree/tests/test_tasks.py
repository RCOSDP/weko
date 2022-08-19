import json
import pytest

from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_oaiserver.models import OAISet


# def update_oaiset_setting(index_info, data):
def test_update_oaiset_setting(index_info, data):
    """Create/Update oai set setting."""
    try:
        pub_state = data["public_state"] and data["harvest_public_state"]
        if int(data["parent"]) == 0:
            spec = str(data["id"])
            description = data["index_name"]
        else:
            spec = index_info[2].replace("/", ":")
            description = index_info[4].replace("-/-", "->")
        with db.session.begin_nested():
            current_app.logger.debug("data[id]:{}".format(data["id"]))
            oaiset = OAISet.query.filter_by(id=data["id"]).one_or_none()
            if oaiset:
                if pub_state:
                    oaiset.spec = spec
                    oaiset.name = data["index_name"]
                    oaiset.search_pattern = 'path:"{}"'.format(data["id"])
                    #oaiset.search_pattern = '_oai.sets:"{}"'.format(spec)
                    oaiset.description = description
                    db.session.merge(oaiset)
                else:
                    db.session.delete(oaiset)
            elif pub_state:
                oaiset = OAISet(
                    id=data["id"],
                    spec=spec,
                    name=data["index_name"],
                    description=description)
                oaiset.search_pattern = 'path:"{}"'.format(data["id"])
                #oaiset.search_pattern = '_oai.sets:"{}"'.format(spec)
                db.session.add(oaiset)
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()

# def delete_oaiset_setting(id_list):
