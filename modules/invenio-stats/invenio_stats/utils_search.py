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
    mst, _ = get_permission_filter()

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
    from weko_index_tree.api import Indexes
    is_perm = Permission(action_factory("search-access")).can()
    match = Q("match", publish_status="0")
    version = Q("match", relation_version_is_last="true")
    rng = Q("range", **{"publish_date": {"lte": "now/d"}})
    term_list = []
    mst = []
    is_perm_paths = Indexes.get_browsing_tree_paths()
    is_perm_indexes = [item.split("/")[-1] for item in is_perm_paths]
    search_type = request.values.get("search_type")

    if index_id:
        index_id = str(index_id)
        if search_type == "0":
            should_path = []
            if index_id in is_perm_indexes:
                should_path.append(Q("terms", path=index_id))

            mst.append(match)
            mst.append(rng)
            terms = Q("bool", should=should_path)
        else:  # In case search_type is keyword or index
            if index_id in is_perm_indexes:
                term_list.append(index_id)

            mst.append(match)
            mst.append(rng)
            terms = Q("terms", path=term_list)
    else:
        mst.append(match)
        mst.append(rng)
        terms = Q("terms", path=is_perm_indexes)

    mut = []

    if is_perm:
        user_id, result = check_admin_user()

        if result:
            shuld = [
                Q("match", weko_creator_id=user_id),
                Q("match", weko_shared_id=user_id),
            ]
            shuld.append(Q("bool", must=mst))
            mut.append(Q("bool", should=shuld, must=[terms]))
            mut.append(Q("bool", must=version))
    else:
        mut = mst
        mut.append(terms)
        base_mut = [match, version]
        mut.append(Q("bool", must=base_mut))

    return mut, is_perm_paths

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