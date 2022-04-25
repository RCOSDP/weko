from re import L

import pytest
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import CombinedMultiDict

from weko_search_ui.query import default_search_factory

# def get_item_type_aggs(search_index):
# def get_permission_filter(index_id: str = None):
# def default_search_factory(self, search, query_parser=None, search_type=None):
#     def _get_search_qs_query(qs=None):
#     def _get_detail_keywords_query():
#         def _get_keywords_query(k, v):
#         def _get_object_query(k, v):
#         def _get_nested_query(k, v):
#         def _get_date_query(k, v):
#         def _get_text_query(k, v):
#         def _get_range_query(k, v):
#         def _get_geo_distance_query(k, v):
#         def _get_geo_shape_query(k, v):
#     def _get_simple_search_query(qs=None):
#     def _get_simple_search_community_query(community_id, qs=None):
#     def _get_file_content_query(qstr):
#     def _default_parser(qstr=None):
#     def _default_parser_community(community_id, qstr=None):
# def item_path_search_factory(self, search, index_id=None):
#     def _get_index_earch_query():
# def check_admin_user():
# def opensearch_factory(self, search, query_parser=None):
# def item_search_factory(
#     def _get_query(start_term, end_term, indexes):
# def feedback_email_search_factory(self, search):
#     def _get_query():