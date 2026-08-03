import orjson
from flask import current_app, request
from elasticsearch_dsl import Q
from flask_login import current_user
from invenio_access import Permission, action_factory
from invenio_records_rest.errors import InvalidQueryRESTError
from werkzeug.datastructures import MultiDict

def billing_file_search_factory(search):
    """Create billing file searcher."""
    from invenio_records_rest.sorter import default_sorter_factory

    # add  Permission filter by publish date and status
    mst = get_permission_filter()

    # billing file search filter
    query = Q('bool', must=[{'terms': {'content.billing.raw': ['billing_file']}}])
    should = [Q('nested', path='content', query=query)]
    mkq = [Q('bool', should=should)]
    mst.extend(mkq)

    query_q = Q("bool", must=mst) if mst else Q()

    search = search.source(includes=['path', 'content.filename', '_item_metadata.owner', '_oai.id'])

    try:
        search = search.filter(query_q)
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(request.values.get("q", "")),
            exc_info=True,
        )
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    urlkwargs = MultiDict()
    search, sortkwargs = default_sorter_factory(search, search_index)

    urlkwargs.add("q", query_q)
    # debug elastic search query
    current_app.logger.debug("query: {}".format(orjson.dumps((search.query()).to_dict()).decode()))
    current_app.logger.debug("urlkwargs: {}".format(urlkwargs))

    return search, urlkwargs

def get_permission_filter(index_id: str = None):
    """Check permission.

    Args:
        index_id (str, optional): Index Identifier Number. Defaults to None.

    Returns:
        List: Query command.

    """
    match = Q("match", publish_status="0")
    version = Q("match", relation_version_is_last="true")
    rng = Q("range", **{"publish_date": {"lte": "now/d"}})
    mst = []

    mst.append(match)
    mst.append(rng)

    mut = []
    shuld= []

    shuld.append(Q("bool", must=mst))
    mut.append(Q("bool", should=shuld))
    mut.append(Q("bool", must=version))

    return mut

def check_admin_user():
    """
    Check administrator role user.

    :return: result
    """
    result = True
    user_id = (
        current_user.get_id()
        if current_user and current_user.is_authenticated
        else None
    )

    if user_id:
        users = current_app.config["WEKO_PERMISSION_ROLE_USER"]

        for lst in list(current_user.roles or []):

            # if is administrator
            if lst.name == users[2]:
                result = True

    return user_id, result