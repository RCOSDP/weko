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

"""Views for weko-authors."""

import re

from flask import Blueprint, current_app, json, jsonify, request
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from weko_records.models import ItemMetadata

from .models import Authors, AuthorsPrefixSettings
from .permissions import author_permission
from .utils import get_author_setting_obj

blueprint = Blueprint(
    'weko_authors',
    __name__,
    url_prefix='/authors',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_authors',
    __name__,
    url_prefix='/authors',
    template_folder='templates',
    static_folder='static',
)


@blueprint_api.route("/add", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def create():
    """Add an author."""
    if request.headers['Content-Type'] != 'application/json':
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    data["gather_flg"] = 0
    indexer = RecordIndexer()
    indexer.client.index(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=data,
    )

    author_data = dict()

    author_data["id"] = json.loads(json.dumps(data))["pk_id"]
    author_data["json"] = json.dumps(data)

    with db.session.begin_nested():
        author = Authors(**author_data)
        db.session.add(author)
    db.session.commit()
    return jsonify(msg=_('Success'))


# add by ryuu. at 20180820 start
@blueprint_api.route("/edit", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def update_author():
    """Add an author."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    indexer = RecordIndexer()
    body = {'doc': data}
    indexer.client.update(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        id=json.loads(json.dumps(data))["id"],
        body=body
    )

    with db.session.begin_nested():
        author_data = Authors.query.filter_by(
            id=json.loads(json.dumps(data))["pk_id"]).one()
        author_data.json = json.dumps(data)
        db.session.merge(author_data)
    db.session.commit()

    return jsonify(msg=_('Success'))


@blueprint_api.route("/delete", methods=['post'])
@login_required
@author_permission.require(http_exception=403)
def delete_author():
    """Add an author."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    indexer = RecordIndexer()
    indexer.client.delete(
        id=json.loads(json.dumps(data))["Id"],
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],)

    with db.session.begin_nested():
        author_data = Authors.query.filter_by(
            id=json.loads(json.dumps(data))["pk_id"]).one()
        db.session.delete(author_data)
    db.session.commit()

    return jsonify(msg=_('Success'))

# add by ryuu. at 20180820 end


@blueprint_api.route("/search", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def get():
    """Get all authors."""
    data = request.get_json()

    search_key = data.get('searchKey') or ''
    match = [{"term": {"gather_flg": 0}}]

    if search_key:
        match.append({"multi_match": {"query": search_key, "type": "phrase"}})
    query = {"bool": {"must": match}}
    size = int(data.get('numOfPage')
               or current_app.config['WEKO_AUTHORS_NUM_OF_PAGE'])
    num = data.get('pageNumber') or 1
    offset = (int(num) - 1) * size if int(num) > 1 else 0

    sort_key = data.get('sortKey') or ''
    sort_order = data.get('sortOrder') or ''
    sort = {}
    if sort_key and sort_order:
        sort = {sort_key + '.raw': {"order": sort_order, "mode": "min"}}

    body = {
        "query": query,
        "from": offset,
        "size": size,
        "sort": sort
    }
    query_item = {
        "size": 0,
        "query": {
            "bool": {
                "must_not": {
                    "match": {
                        "weko_id": "",
                    }
                }
            }
        }, "aggs": {
            "item_count": {
                "terms": {
                    "field": "weko_id"
                }
            }
        }
    }

    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=body
    )
    result_itemCnt = indexer.client.search(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=query_item
    )

    result['item_cnt'] = result_itemCnt

    return jsonify(result)


@blueprint_api.route("/search_edit", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def getById():
    """Get all authors."""
    data = request.get_json()
    search_key = data.get('Id') or ''

    if search_key:
        match = []
        match.append({"match": {"_id": search_key}})
        query = {"bool": {"must": match}}

    body = {
        "query": query
    }

    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=body
    )
    return json.dumps(result)


@blueprint_api.route("/input", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def mapping():
    """Transfer the author to JPCOAR format."""
    def get_name_creator(res, _source):
        name_info = _source.get('authorNameInfo')
        for i in name_info:
            if i.get('nameShowFlg') == 'true':
                if i.get('nameFormat') == 'familyNmAndNm':
                    tmp = {'familyName': i.get('familyName'),
                           'familyNameLang': i.get('language')}
                    res['familyNames'].append(tmp)
                    tmp = {'givenName': i.get('firstName'),
                           'givenNameLang': i.get('language')}
                    res['givenNames'].append(tmp)
                else:
                    tmp = {'creatorName': i.get('fullName'),
                           'creatorNameLang': i.get('language')}
                    res['creatorNames'].append(tmp)

    def get_identifier_creator(res, _source):
        def get_info_author_id(idTtype):
            prefix_settings = AuthorsPrefixSettings.query.all()
            scheme = uri = ''
            for prefix in prefix_settings:
                if prefix.id == idTtype:
                    scheme = prefix.name
                    if scheme == 'KAKEN2':
                        scheme = 'kakenhi'
                    uri = prefix.url
                    return scheme, uri
            return scheme, uri

        id_info = _source.get('authorIdInfo')
        for j in id_info:
            if j.get('authorIdShowFlg') == 'true':
                scheme, uri = get_info_author_id(int(j['idType']))
                _author_id = j.get('authorId')
                if _author_id and uri:
                    uri = re.sub("#+$", _author_id, uri, 1)
                tmp = {
                    'nameIdentifier': _author_id,
                    'nameIdentifierScheme': scheme,
                    'nameIdentifierURI': uri
                }
                res['nameIdentifiers'].append(tmp)

    def get_email_creator(res, _source):
        email_info = _source.get('emailInfo')
        for item in email_info:
            email = item.get('email')
            email_json = {'creatorMail': email}
            res['creatorMails'].append(email_json)

    data = request.get_json()

    # get author data
    author_id = data.get('id', '')
    indexer = RecordIndexer()
    result = indexer.client.get(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        id=author_id
    )
    _source = result.get('_source')

    # transfer to JPCOAR format
    res = {'familyNames': [], 'givenNames': [], 'creatorNames': [],
           'nameIdentifiers': [], 'creatorAlternative': [], 'creatorMails': []}

    get_name_creator(res, _source)
    get_identifier_creator(res, _source)
    get_email_creator(res, _source)

    # remove empty element
    last = {}
    for k, v in res.items():
        if v:
            last[k] = v

    current_app.logger.debug([last])

    return json.dumps([last])


@blueprint_api.route("/gather", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def gatherById():
    """Gather author."""
    data = request.get_json()
    gatherFrom = data["idFrom"]
    gatherFromPkId = data["idFromPkId"]
    gatherTo = data["idTo"]

    # update DB of Author
    try:
        with db.session.begin_nested():
            for j in gatherFromPkId:
                author_data = Authors.query.filter_by(id=j).one()
                author_data.gather_flg = 1
                db.session.merge(author_data)
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()
        return jsonify({'code': 204, 'msg': 'Faild'})

    update_author_q = {
        "query": {
            "match": {
                "_id": "@id"
            }
        }
    }

    indexer = RecordIndexer()
    for t in gatherFrom:
        q = json.dumps(update_author_q).replace("@id", t)
        q = json.loads(q)
        res = indexer.client.search(
            index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
            body=q
        )
        for h in res.get("hits").get("hits"):
            body = {
                'doc': {
                    'gather_flg': 1
                }
            }
            indexer.client.update(
                index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
                doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
                id=h.get("_id"),
                body=body
            )

    update_q = {
        "query": {
            "match": {
                "weko_id": "@id"
            }
        }
    }
    indexer = RecordIndexer()
    item_pk_id = []
    for t in gatherFrom:
        q = json.dumps(update_q).replace("@id", t)
        q = json.loads(q)
        res = indexer.client.search(
            index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
            body=q
        )
        current_app.logger.debug(res.get("hits").get("hits"))
        for h in res.get("hits").get("hits"):
            sub = {"id": h.get("_id"), "weko_id": t}
            item_pk_id.append(sub)
            body = {
                'doc': {
                    "weko_id": gatherTo,
                    "weko_id_hidden": gatherTo
                }
            }
            indexer.client.update(
                index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
                doc_type=current_app.config['INDEXER_DEFAULT_DOCTYPE'],
                id=h.get("_id"),
                body=body
            )
    current_app.logger.debug(item_pk_id)
    try:
        with db.session.begin_nested():
            for j in item_pk_id:
                itemData = ItemMetadata.query.filter_by(id=j.get("id")).one()
                itemJson = json.dumps(itemData.json)
                itemJson = itemJson.replace(j.get("weko_id"), gatherTo)
                itemData.json = json.loads(itemJson)
                db.session.merge(itemData)
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()
        return jsonify({'code': 204, 'msg': 'Faild'})

    return jsonify({'code': 0, 'msg': 'Success'})


@blueprint_api.route("/search_prefix", methods=['get'])
@login_required
@author_permission.require(http_exception=403)
def get_prefix_list():
    """Get all authors prefix settings."""
    settings = AuthorsPrefixSettings.query.order_by(
        AuthorsPrefixSettings.id).all()
    data = []
    if settings:
        for s in settings:
            tmp = s.__dict__
            if '_sa_instance_state' in tmp:
                tmp.pop('_sa_instance_state')
            data.append(tmp)
    return jsonify(data)


@blueprint_api.route("/list_vocabulary", methods=['get'])
@login_required
@author_permission.require(http_exception=403)
def get_list_schema():
    """Get all scheme items config.py."""
    data = {
        "list": current_app.config['WEKO_AUTHORS_LIST_SCHEME'],
        "index": current_app.config['WEKO_AUTHORS_INDEX_ITEM_OTHER']
    }
    return jsonify(data)


@blueprint_api.route("/edit_prefix", methods=['post'])
@login_required
@author_permission.require(http_exception=403)
def update_prefix():
    """Update authors prefix settings."""
    try:
        data = request.get_json()
        check = get_author_setting_obj(data['scheme'])
        if check is None or check.id == data['id']:
            AuthorsPrefixSettings.update(**data)
            return jsonify({'code': 200, 'msg': 'Success'})
        else:
            return jsonify(
                {'code': 400, 'msg': 'Specified scheme is already exist.'})
    except Exception:
        return jsonify({'code': 204, 'msg': 'Failed'})


@blueprint_api.route("/delete_prefix/<id>", methods=['delete'])
@login_required
@author_permission.require(http_exception=403)
def delete_prefix(id):
    """Delete authors prefix settings."""
    AuthorsPrefixSettings.delete(id)
    return jsonify(msg=_('Success'))


@blueprint_api.route("/add_prefix", methods=['put'])
@login_required
@author_permission.require(http_exception=403)
def create_prefix():
    """Add new authors prefix settings."""
    try:
        data = request.get_json()
        check = get_author_setting_obj(data['scheme'])
        if check is None:
            AuthorsPrefixSettings.create(**data)
            return jsonify({'code': 200, 'msg': 'Success'})
        else:
            return jsonify(
                {'code': 400, 'msg': 'Specified scheme is already exist.'})
    except Exception:
        return jsonify({'code': 204, 'msg': 'Failed'})
