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

from flask import Blueprint, current_app, json, jsonify, make_response, request
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_db import db
from invenio_indexer.api import RecordIndexer

from .config import WEKO_AUTHORS_IMPORT_KEY
from .models import Authors, AuthorsAffiliationSettings, AuthorsPrefixSettings
from .permissions import author_permission
from .utils import get_author_prefix_obj, get_author_affiliation_obj, get_count_item_link

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

    session = db.session
    new_id = Authors.get_sequence(session)

    data = request.get_json()
    data["gather_flg"] = 0
    data["is_deleted"] = "false"
    data["pk_id"] = str(new_id)
    data["authorIdInfo"].insert(0,
                                {
                                    "idType": "1",
                                    "authorId": str(new_id),
                                    "authorIdShowFlg": "true"
                                })
    indexer = RecordIndexer()
    es_id = indexer.client.index(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=data,
    )
    data['id'] = es_id

    author_data = dict()

    author_data["id"] = new_id
    author_data["json"] = json.dumps(data)

    with session.begin_nested():
        author = Authors(**author_data)
        session.add(author)
    session.commit()
    return jsonify(msg=_('Success'))


# add by ryuu. at 20180820 start
@blueprint_api.route("/edit", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def update_author():
    """Update an author."""
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

    from weko_deposit.tasks import update_items_by_authorInfo
    update_items_by_authorInfo.delay(
        [json.loads(json.dumps(data))["pk_id"]], data)

    return jsonify(msg=_('Success'))


@blueprint_api.route("/delete", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def delete_author():
    """Delete an author."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    if get_count_item_link(data['pk_id']):
        return make_response(
            _('The author is linked to items and cannot be deleted.'),
            500)

    try:
        with db.session.begin_nested():
            author_data = Authors.query.filter_by(
                id=json.loads(json.dumps(data))["pk_id"]).one()
            author_data.is_deleted = True
            json_data = json.loads(author_data.json)
            json_data['is_deleted'] = 'true'
            author_data.json = json.dumps(json_data)
            db.session.merge(author_data)

            RecordIndexer().client.update(
                id=json.loads(json.dumps(data))["Id"],
                index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
                doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
                body={'doc': {'is_deleted': 'true'}}
            )
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(ex)

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
    should = [
        {"bool": {"must": [{"term": {"is_deleted": {"value": "false"}}}]}},
        {"bool": {"must_not": {"exists": {"field": "is_deleted"}}}}
    ]
    match = [{"term": {"gather_flg": 0}}, {"bool": {"should": should}}]

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
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=body
    )

    query_item = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "publish_status": 0
                        }
                    },
                    {
                        "match": {
                            "relation_version_is_last": "true"
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "term": {
                                        "author_link.raw":
                                        "@author_id"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
    item_cnt_list = []
    for es_hit in result['hits']['hits']:
        author_id_info = es_hit['_source']['authorIdInfo']
        if author_id_info:
            author_id = author_id_info[0]['authorId']
            temp_str = json.dumps(query_item).replace(
                "@author_id", author_id)
            result_itemCnt = indexer.client.search(
                index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
                body=json.loads(temp_str)
            )
            if result_itemCnt \
                    and result_itemCnt['hits'] \
                    and result_itemCnt['hits']['total']:
                item_cnt_list.append(
                    {'key': author_id,
                     'doc_count': result_itemCnt['hits']['total']})

    result['item_cnt'] = {'aggregations':
                          {'item_count': {'buckets': item_cnt_list}}}

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
    else:
        should = [
            {"bool": {"must": [{"term": {"is_deleted": {"value": "false"}}}]}},
            {"bool": {"must_not": {"exists": {"field": "is_deleted"}}}}
        ]
        match = [{"term": {"gather_flg": 0}}, {"bool": {"should": should}}]
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
                    scheme = prefix.scheme
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

    def get_affiliation(res, _source):
        def get_affiliation_name_identifier(affiliationIdType):
            affiliation_settings = AuthorsAffiliationSettings.query.all()
            affiliation_scheme = affiliation_uri = ''
            for affiliation in affiliation_settings:
                if affiliation.id == affiliationIdType:
                    affiliation_scheme = affiliation.scheme
                    affiliation_uri = affiliation.url
                    return affiliation_scheme, affiliation_uri
            return affiliation_scheme, affiliation_uri

        affiliation_info = _source.get('affiliationInfo')
        if affiliation_info:
            for affiliation_data in affiliation_info:
                identifier_info = affiliation_data.get('identifierInfo')
                affiliation_name_info = affiliation_data.get('affiliationNameInfo')
                affiliation_tmp = {
                    'affiliationNameIdentifiers': [], 'affiliationNames': []}

                for identifier_data in identifier_info:
                    if identifier_data.get('affiliationId'):
                        if identifier_data.get('identifierShowFlg') == 'true':
                            scheme, uri = get_affiliation_name_identifier(
                                int(identifier_data['affiliationIdType']))
                            _affiliation_id = identifier_data.get('affiliationId')
                            if _affiliation_id and uri:
                                uri = re.sub(
                                    "#+$", _affiliation_id, uri, 1)
                            identifier_tmp = {
                                'affiliationNameIdentifier': _affiliation_id,
                                'affiliationNameIdentifierScheme': scheme,
                                'affiliationNameIdentifierURI': uri
                            }
                            affiliation_tmp['affiliationNameIdentifiers'].append(
                                identifier_tmp)

                for af_name_data in affiliation_name_info:
                    if af_name_data.get('affiliationName'):
                        if af_name_data.get('affiliationNameShowFlg') == 'true':
                            affiliation_name = af_name_data.get('affiliationName')
                            af_name_lang = af_name_data.get('affiliationNameLang')
                            af_name_tmp = {'affiliationName': affiliation_name,
                                        'affiliationNameLang': af_name_lang}
                            affiliation_tmp['affiliationNames'].append(af_name_tmp)
                res['creatorAffiliations'].append(affiliation_tmp)

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
           'nameIdentifiers': [], 'creatorAlternative': [],
           'creatorMails': [], 'creatorAffiliations': []
           }

    get_name_creator(res, _source)
    get_identifier_creator(res, _source)
    get_email_creator(res, _source)
    get_affiliation(res, _source)

    # remove empty element
    last = {}
    for k, v in res.items():
        if v:
            last[k] = v

    last['author_name'] = WEKO_AUTHORS_IMPORT_KEY.get('author_name')
    last['author_mail'] = WEKO_AUTHORS_IMPORT_KEY.get('author_mail')
    last['author_affiliation'] = WEKO_AUTHORS_IMPORT_KEY.get(
        'author_affiliation')
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

    # Remove the target from the gatherFrom list
    if gatherTo in gatherFrom:
        target_index = gatherFrom.index(gatherTo)
        gatherFrom.pop(target_index)
        gatherFromPkId.pop(target_index)

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
        return jsonify({'code': 204, 'msg': 'Failed'})

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

    target_author_q = {
        "query": {
            "match": {
                "_id": "@id"
            }
        }
    }
    q = json.dumps(target_author_q).replace("@id", gatherTo)
    q = json.loads(q)
    res = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        body=q
    )
    target_data = res.get("hits").get("hits")[0].get("_source")

    from weko_deposit.tasks import update_items_by_authorInfo
    update_items_by_authorInfo.delay(gatherFromPkId, target_data)

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
            tmp.pop('_sa_instance_state', None)
            data.append(tmp)
    return jsonify(data)


@blueprint_api.route("/search_affiliation", methods=['get'])
@login_required
@author_permission.require(http_exception=403)
def get_affiliation_list():
    """Get all authors affiliation settings."""
    settings = AuthorsAffiliationSettings.query.order_by(
        AuthorsAffiliationSettings.id).all()
    data = []
    if settings:
        for s in settings:
            tmp = s.__dict__
            tmp.pop('_sa_instance_state', None)
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


@blueprint_api.route("/list_affiliation_scheme", methods=['get'])
@login_required
@author_permission.require(http_exception=403)
def get_list_affiliation_schema():
    """Get all affiliation scheme items config.py."""
    data = {
        "list": current_app.config['WEKO_AUTHORS_LIST_SCHEME_AFFILIATION'],
        "index": current_app.config[
            'WEKO_AUTHORS_AFFILIATION_IDENTIFIER_ITEM_OTHER']
    }
    return jsonify(data)


@blueprint_api.route("/edit_prefix", methods=['post'])
@login_required
@author_permission.require(http_exception=403)
def update_prefix():
    """Update authors prefix settings."""
    try:
        data = request.get_json()
        check = get_author_prefix_obj(data['scheme'])
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
        check = get_author_prefix_obj(data['scheme'])
        if check is None:
            AuthorsPrefixSettings.create(**data)
            return jsonify({'code': 200, 'msg': 'Success'})
        else:
            return jsonify(
                {'code': 400, 'msg': 'Specified scheme is already exist.'})
    except Exception:
        return jsonify({'code': 204, 'msg': 'Failed'})


@blueprint_api.route("/edit_affiliation", methods=['post'])
@login_required
@author_permission.require(http_exception=403)
def update_affiliation():
    """Update authors affiliation settings."""
    try:
        data = request.get_json()
        check = get_author_affiliation_obj(data['scheme'])
        if check is None or check.id == data['id']:
            AuthorsAffiliationSettings.update(**data)
            return jsonify({'code': 200, 'msg': 'Success'})
        else:
            return jsonify(
                {'code': 400, 'msg': 'Specified scheme is already exist.'})
    except Exception:
        return jsonify({'code': 204, 'msg': 'Failed'})


@blueprint_api.route("/delete_affiliation/<id>", methods=['delete'])
@login_required
@author_permission.require(http_exception=403)
def delete_affiliation(id):
    """Delete authors affiliation settings."""
    AuthorsAffiliationSettings.delete(id)
    return jsonify(msg=_('Success'))


@blueprint_api.route("/add_affiliation", methods=['put'])
@login_required
@author_permission.require(http_exception=403)
def create_affiliation():
    """Add new authors affiliation settings."""
    try:
        data = request.get_json()
        check = get_author_affiliation_obj(data['scheme'])
        if check is None:
            AuthorsAffiliationSettings.create(**data)
            return jsonify({'code': 200, 'msg': 'Success'})
        else:
            return jsonify(
                {'code': 400, 'msg': 'Specified scheme is already exist.'})
    except Exception:
        return jsonify({'code': 204, 'msg': 'Failed'})


@blueprint.teardown_request
@blueprint_api.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko-authors dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()