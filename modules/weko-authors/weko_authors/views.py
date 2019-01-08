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

from flask import (
    Blueprint, current_app, json, jsonify, render_template, request)
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_indexer.api import RecordIndexer

from .permissions import author_permission
from invenio_db import db
from .models import Authors
from weko_records.models import ItemMetadata

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


@blueprint.route("/")
@login_required
@author_permission.require(http_exception=403)
def index():
    """Render a basic view."""
    return render_template(
        current_app.config['WEKO_AUTHORS_LIST_TEMPLATE'])


@blueprint.route("/add", methods=['GET'])
@login_required
@author_permission.require(http_exception=403)
def add():
    """Render an adding author view."""
    return render_template(
        current_app.config['WEKO_AUTHORS_EDIT_TEMPLATE'])


# add by ryuu at 20180808 start
@blueprint.route("/edit", methods=['GET'])
@login_required
@author_permission.require(http_exception=403)
def edit():
    """Render an adding author view."""
    return render_template(
        current_app.config['WEKO_AUTHORS_EDIT_TEMPLATE'])
# add by ryuu at 20180808 end

@blueprint_api.route("/add", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def create():
    """Add an author."""
    if request.headers['Content-Type'] != 'application/json':
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    data["gather_flg"]=0
    indexer = RecordIndexer()
    indexer.client.index(index="authors",
                         doc_type="author",
                         body=data,)

    author_data = dict()

    author_data["id"]= json.loads(json.dumps(data))["pk_id"]
    author_data["json"]= json.dumps(data)

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
        index="authors",
        doc_type="author",
        id=json.loads(json.dumps(data))["id"],
        body=body
    )

    with db.session.begin_nested():
        author_data = Authors.query.filter_by(id=json.loads(json.dumps(data))["pk_id"]).one()
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
    indexer.client.delete(id=json.loads(json.dumps(data))["Id"],
                          index="authors",
                          doc_type="author",)

    with db.session.begin_nested():
        author_data = Authors.query.filter_by(id=json.loads(json.dumps(data))["pk_id"]).one()
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
    query = {"match": {"gather_flg":0}}

    if search_key:
        search_keys = search_key.split(" ")
        match = []
        for key in search_keys:
            if key:
                match.append({"match": {"_all": key}})
        # query = {"bool": {"should": match},"filter":{"term":{"gather_flg":0}}}
        query = {
            "filtered":{
                "filter":{
                    "bool":{
                        "should":match,
                        "must":{
                            "term":{"gather_flg":0}
                        }
                    }
                }
            }
        }


    size = (data.get('numOfPage') or
            current_app.config['WEKO_AUTHORS_NUM_OF_PAGE'])
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
    query_item={
      "size": 0,
      "query": {
          "bool": {
              "must_not": {
                  "match": {
                      "weko_id": "",
                  }
              }
          }
      },"aggs":{
          "item_count": {
              "terms": {
                "field": "weko_id"
               }
          }
       }
    }

    indexer = RecordIndexer()
    result = indexer.client.search(index="authors", body=body)
    result_itemCnt = indexer.client.search(index="weko", body=query_item)

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
    result = indexer.client.search(index="authors", body=body)
    return json.dumps(result)


@blueprint_api.route("/input", methods=['POST'])
@login_required
@author_permission.require(http_exception=403)
def mapping():
    """Transfer the author to JPCOAR format."""
    data = request.get_json()

    # get author data
    author_id = data.get('id') or ''
    indexer = RecordIndexer()
    result = indexer.client.get(index="authors", id=author_id)

    # transfer to JPCOAR format
    res = {'familyNames': [], 'givenNames': [], 'creatorNames': [],
           'nameIdentifiers': []}

    name_info = result.get('_source').get('authorNameInfo')
    for i in name_info:
        if i.get('nameShowFlg') == 'true':
            if i.get('nameFormat') == 'familyNmAndNm':
                tmp = {'familyName': i.get('familyName'),
                       'lang': i.get('language')}
                res['familyNames'].append(tmp)
                tmp = {'givenName': i.get('firstName'),
                       'lang': i.get('language')}
                res['givenNames'].append(tmp)
            else:
                tmp = {'creatorName': i.get('fullName'),
                       'lang': i.get('language')}
                res['creatorNames'].append(tmp)

    id_info = result.get('_source').get('authorIdInfo')
    for j in id_info:
        if j.get('authorIdShowFlg') == 'true':
            tmp = {'nameIdentifier': j.get('authorId'),
                   'nameIdentifierScheme': j.get('idType'),
                   'nameIdentifierURI': ''}
            res['nameIdentifiers'].append(tmp)

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
    """gather author."""
    data = request.get_json()
    gatherFrom = data["idFrom"]
    gatherFromPkId = data["idFromPkId"]
    gatherTo = data["idTo"]

    #update DB of Author
    try:
        with db.session.begin_nested():
            for j in gatherFromPkId :
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
        res = indexer.client.search(index="authors", body=q)
        for h in res.get("hits").get("hits"):
            body = {
                'doc':{
                    'gather_flg':1
                }
            }
            indexer.client.update(
                index="authors",
                doc_type="author",
                id=h.get("_id"),
                body=body
            )

    update_q ={
        "query": {
            "match": {
                "weko_id": "@id"
            }
        }
    }
    indexer = RecordIndexer()
    item_pk_id =[]
    for t in gatherFrom:
        q = json.dumps(update_q).replace("@id", t)
        q = json.loads(q)
        res = indexer.client.search(index="weko", body=q)
        current_app.logger.debug(res.get("hits").get("hits"))
        for h in res.get("hits").get("hits"):
            sub = {"id":h.get("_id"),"weko_id":t}
            item_pk_id.append(sub)
            body = {
                'doc':{
                    "weko_id":gatherTo,
                    "weko_id_hidden":gatherTo
                }
            }
            indexer.client.update(
                index="weko",
                doc_type="item",
                id=h.get("_id"),
                body=body
            )
    current_app.logger.debug(item_pk_id)
    try:
        with db.session.begin_nested():
            for j in item_pk_id:
                itemData = ItemMetadata.query.filter_by(id=j.get("id")).one()
                itemJson = json.dumps(itemData.json)
                itemJson = itemJson.replace(j.get("weko_id"),gatherTo)
                itemData.json = json.loads(itemJson)
                db.session.merge(itemData)
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()
        return jsonify({'code': 204, 'msg': 'Faild'})

    return jsonify({'code': 0, 'msg': 'Success'})






