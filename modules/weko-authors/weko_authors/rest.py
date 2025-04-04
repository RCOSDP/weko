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

"""Blueprint for schema rest."""

import json
import traceback
import inspect
import pdb

from flask import Blueprint, current_app, Response, jsonify
from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from .scopes import author_search_scope,author_create_scope,author_update_scope,author_delete_scope
from invenio_records_rest.utils import obj_or_import_string
from werkzeug.exceptions import InternalServerError, NotFound
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from weko_accounts.utils import roles_required, limiter
from .errors import VersionNotFoundRESTError
from weko_authors.api import WekoAuthors
from weko_authors.utils import validate_weko_id, check_period_date

from flask import request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from invenio_search import current_search_client

WEKO_ADMIN_PERMISSION_ROLE_SYSTEM = "System Administrator"
WEKO_ADMIN_PERMISSION_ROLE_REPO = "Repository Administrator"

def create_blueprint(endpoints):
    """Create Weko-Authors-REST blueprint.

    See: :data:`weko_authors.config.WEKO_AUTHORS_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_authors_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug('weko_authors dbsession_clean: {}'.format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        record_serializers ={'application/json':jsonify}
        if endpoint == 'authors':
            authors = Authors.as_view(
                Authors.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            author_api = AuthorDBManagementAPI.as_view(
                AuthorDBManagementAPI.view_name.format(endpoint),
                record_serializers=record_serializers,
                default_media_type=options.get('default_media_type'),
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=authors,
                methods=['GET']
            )
            blueprint.add_url_rule(
                options.get('api_route'),
                view_func=author_api,
                methods=['GET','POST','PUT','DELETE']
            )

    return blueprint


class Authors(ContentNegotiatedMethodView):
    """Authors Resource."""
    view_name = '{0}'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(Authors, self).__init__(
            *args,
            **kwargs
        )

    def get(self, **kwargs):
        """Count authors."""
        version = kwargs.get('version')
        from .config import WEKO_AUTHORS_COUNT_API_VERSION
        func = WEKO_AUTHORS_COUNT_API_VERSION.get(f'get-{version}')

        if func:
            return func(self, **kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):

        # Execute count.
        try:
            from .utils import count_authors
            count_result = count_authors()

            # Create Response
            res = Response(
                response=json.dumps(count_result),
                status=200,
                content_type='application/json'
            )

            # Response header setting
            res.headers['Cache-Control'] = 'no-store'
            res.headers['Pragma'] = 'no-cache'
            res.headers['Expires'] = 0

            return res

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()

class AuthorDBManagementAPI(ContentNegotiatedMethodView):
    """Author Database Management API."""
    view_name = '{0}_db_management_API'
    def __init__(self, record_serializers=None, 
                default_media_type=None, **kwargs):
        """Constructor."""
        super(AuthorDBManagementAPI, self).__init__(
            method_serializers={
                'GET': record_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
                'DELETE': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
                'DELETE': default_media_type,
            },
            default_media_type=default_media_type,        
            **kwargs
        )

    @require_api_auth(allow_anonymous=False)
    @require_oauth_scopes(author_search_scope.id)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @limiter.limit('')
    def get(self, **kwargs):
        """Handle GET request."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if hasattr(self, func_name):
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()
        
    @require_api_auth(allow_anonymous=False)
    @require_oauth_scopes(author_create_scope.id)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @limiter.limit('')
    def post(self, **kwargs):
        """Handle GET request."""
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if hasattr(self, func_name):
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()
    
    @require_api_auth(allow_anonymous=False)
    @require_oauth_scopes(author_update_scope.id)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @limiter.limit('')
    def put(self, **kwargs):
        """Handle GET request."""
        version = kwargs.get('version')
        func_name = f'put_{version}'
        if hasattr(self, func_name):
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()
    
    @require_api_auth(allow_anonymous=False)
    @require_oauth_scopes(author_delete_scope.id)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @limiter.limit('')
    def delete(self, **kwargs):
        """Handle GET request."""
        version = kwargs.get('version')
        func_name = f'delete_{version}'
        if hasattr(self, func_name):
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        """Handle GET request for v1."""
        from weko_authors.utils import get_author_prefix_obj,get_author_affiliation_obj,get_author_prefix_obj_by_id,get_author_affiliation_obj_by_id
        try:
            fullname = request.args.get("fullname")
            firstname = request.args.get("firstname")
            familyname = request.args.get("familyname")
            idtype = request.args.get("idtype")
            authorid = request.args.get("authorid")

            if (idtype and not authorid) or (authorid and not idtype):
                raise BadRequest("Both 'idtype' and 'authorid' must be specified together or omitted.")

            # idtype (scheme -> id)
            idtype_id = None
            if idtype:
                prefix_obj = get_author_prefix_obj(idtype)
                if not prefix_obj:
                    raise BadRequest(f"Invalid idtype '{idtype}'.")
                idtype_id = prefix_obj.id

            search_query = \
            {"query": 
                {"bool": 
                    {"must": [
                        {"term": {"gather_flg": {"value": 0}}}
                        ], 
                    "must_not": [{ "term": { "is_deleted": True}}]}
                }
            }

            if fullname:
                parts = fullname.split(" ", 1)
                firstname_ = parts[0]
                familyname_ = parts[1] if len(parts) > 1 else None

                if firstname_ and familyname_:
                    search_query["query"]["bool"]["must"].append({"match": {"authorNameInfo.firstName": firstname_}})
                    search_query["query"]["bool"]["must"].append({"match": {"authorNameInfo.familyName": familyname_}})

            if firstname:
                search_query["query"]["bool"]["must"].append({"match": {"authorNameInfo.firstName": firstname}})
            if familyname:
                search_query["query"]["bool"]["must"].append({"match": {"authorNameInfo.familyName": familyname}})

            if idtype and authorid:
                search_query["query"]["bool"]["must"].append({
                    "function_score": {
                        "query": { "match_all": {} },
                        "script_score": {
                            "script": {
                                "lang": "painless",
                                "source": f"for (def author : params._source.authorIdInfo) {{ if (author.idType == '{idtype_id}' && author.authorId == '{authorid}') return 100; }} return 0;"
                            }
                        }
                    }
                })
                search_query["min_score"] = 100
                
            search_index = current_app.config.get("WEKO_AUTHORS_ES_INDEX_NAME")
            search_results = current_search_client.search(index=search_index, body=search_query)
            if search_results["hits"]["total"]> 0:
                search_results = [author.get("_source", {}) for author in search_results.get("hits", {}).get("hits", [])]
            else:
                search_results = {}
                
            search_results = [self.remove_filed_no_need(author) for author in search_results]
            search_results = [self.process_authors_data_after(author) for author in search_results]

            return Response(
                response=json.dumps({"authors": search_results}),
                status=200,
                content_type='application/json'
            )

        except BadRequest as e:
            raise BadRequest(str(e))
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            raise InternalServerError("Internal server error.")
        
    def process_authors_data_before(self, author_data):
        from weko_authors.utils import get_author_prefix_obj,get_author_affiliation_obj
        # `authorIdInfo` (scheme -> id)
        for auth_id in author_data.get("authorIdInfo", []):
            prefix_obj = get_author_prefix_obj(auth_id.get("idType"))
            if prefix_obj:
                auth_id["idType"] = prefix_obj.id
        # `affiliationIdType` (scheme -> id)
        for affiliation in author_data.get("affiliationInfo", []):
            for identifier in affiliation.get("identifierInfo", []):
                aff_obj = get_author_affiliation_obj(identifier.get("affiliationIdType"))
                if aff_obj:
                    identifier["affiliationIdType"] = aff_obj.id
        return author_data

    def process_authors_data_after(self, author_data):
        from weko_authors.utils import get_author_prefix_obj_by_id,get_author_affiliation_obj_by_id
        # `authorIdInfo` (id -> scheme)
        for auth_id in author_data.get("authorIdInfo", []):
            prefix_obj = get_author_prefix_obj_by_id(auth_id.get("idType"))
            if prefix_obj:
                auth_id["idType"] = prefix_obj.scheme  # 用 scheme 替换 idType
        # `affiliationIdType` (id -> scheme)
        for affiliation in author_data.get("affiliationInfo", []):
            for identifier in affiliation.get("identifierInfo", []):
                aff_obj = get_author_affiliation_obj_by_id(identifier.get("affiliationIdType"))
                if aff_obj:
                    identifier["affiliationIdType"] = aff_obj.scheme
        return author_data
    
    def remove_filed_no_need(self,data):
        keys_to_keep = {"emailInfo", "authorIdInfo", "authorNameInfo", "affiliationInfo"}
        return {k: v for k, v in data.items() if k in keys_to_keep}


    def post_v1(self, **kwargs):
        """Handle POST request for author registration."""
        import uuid
        from weko_authors.models import Authors
        lang_options_list = [
                "ja", "ja-Kana", "en", "fr", "it", "de", "es",
                "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar",
                "el", "ko"
            ]
        try:
            data = request.get_json()

            if not data:
                raise BadRequest("Request body cannot be empty.")
            author_data = data.get("author")
            if not author_data:
                raise BadRequest("author can not be null.")
            
            prefix_schemes,affiliation_schemes = self.get_all_schemes()
            if not self.validate_request_data(self.extract_data(author_data), lang_options_list, prefix_schemes, affiliation_schemes):
                raise BadRequest("Invalid Author Data, 'idtype' or 'language' Not Allowed.")

            self.validate_author_data(author_data,author_data.get("pk_id"))
            
            author_data = self.process_authors_data_before(author_data)

            self.handle_weko_id(author_data)

            es_id = str(uuid.uuid4())
            author_data["id"] = es_id

            with db.session.begin_nested():
                new_id = Authors.get_sequence(db.session)
                author_data["pk_id"] = str(new_id)
                author_record = Authors(id=new_id, json=author_data, is_deleted=False)
                db.session.add(author_record)
                
            author_data["gather_flg"] = 0
            author_data["is_deleted"] = False
            author_data.pop("id")

            search_index = current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"]
            current_search_client.index(index=search_index, id=es_id, body=author_data, doc_type="_doc")
            return Response(
                            response=json.dumps({"message": "Author successfully registered.", "author": self.process_authors_data_after(author_data)}),
                            status=200,
                            content_type='application/json'
                        )

        except BadRequest as e:
            raise BadRequest(str(e))
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("Database error.")
        except Exception:
            current_app.logger.error(traceback.format_exc())
            raise InternalServerError("Internal server error.")

    def validate_author_data(self, author_data, pk_id=None, is_update=False): 
        have_weko_id = False
        for auth_id in author_data.get("authorIdInfo", []):
            id_type = auth_id.get("idType")
            author_id = auth_id.get("authorId")

            if bool(id_type) ^ bool(author_id):
                raise BadRequest("Both 'idType' and 'authorId' must be provided together.")

            if id_type == "WEKO":
                have_weko_id = True
                is_valid, error_msg = validate_weko_id(author_id, pk_id)
                if not is_valid and error_msg == "not half digit":
                    raise BadRequest("The WEKO ID must be numeric characters only.")
                if not is_valid and error_msg == "already exists":
                    raise BadRequest("The value is already in use as WEKO ID.")
        if not have_weko_id and is_update:
            raise BadRequest(f"idType: WEKO (weko id) must be provided.")

        for name_info in author_data.get("authorNameInfo", []):
            first_name = name_info.get("firstName")
            family_name = name_info.get("familyName")
            language = name_info.get("language")

            if (first_name or family_name) and not language:
                raise BadRequest("If 'firstName' or 'familyName' is provided, 'language' must also be specified.")

            if language and first_name and family_name and not name_info.get("nameFormat"):
                name_info["nameFormat"] = "familyNmAndNm"

        if not isinstance(author_data.get("affiliationInfo", []), list):
            raise BadRequest("'affiliationInfo' should be a list.")

        for affiliation in author_data.get("affiliationInfo", []):
            if not isinstance(affiliation, dict):
                raise BadRequest("Invalid format in 'affiliationInfo'.")

            for identifier in affiliation.get("identifierInfo", []):
                id_type = identifier.get("affiliationIdType")
                aff_id = identifier.get("affiliationId")

                if bool(id_type) ^ bool(aff_id):
                    raise BadRequest("Both 'affiliationIdType' and 'affiliationId' must be provided together.")

            for name_info in affiliation.get("affiliationNameInfo", []):
                aff_name = name_info.get("affiliationName")
                aff_lang = name_info.get("affiliationNameLang")

                if bool(aff_name) ^ bool(aff_lang):
                    raise BadRequest("Both 'affiliationName' and 'affiliationNameLang' must be provided together.")

        is_valid, error_msg = check_period_date(author_data)
        if not is_valid:
            raise BadRequest(f"affiliationPeriodInfo error: {error_msg}")

    def handle_weko_id(self, author_data):
        author_id_info = author_data.get("authorIdInfo", [])
        has_weko_id = any(auth_id.get("idType") == "1" for auth_id in author_id_info)

        if not has_weko_id:
            search_index = current_app.config.get("WEKO_AUTHORS_ES_INDEX_NAME")

            query = {
                "size": 0,
                "aggs": {
                    "max_weko_id": {
                        "max": {
                            "script": {
                                "source": """
                                    int maxId = 0;
                                    for (def entry : params._source.authorIdInfo) {
                                        if (entry.idType == '1') {
                                            try {
                                                int id = Integer.parseInt(entry.authorId);
                                                if (id > maxId) maxId = id;
                                            } catch (Exception e) {
                                                // Ignore non-numeric values
                                            }
                                        }
                                    }
                                    return maxId;
                                """,
                                "lang": "painless"
                            }
                        }
                    }
                }
            }

            search_results = current_search_client.search(index=search_index, body=query)
            max_weko_id = search_results["aggregations"]["max_weko_id"]["value"] or 0

            new_weko_id = str(int(max_weko_id) + 1)

            author_id_info.append({
                "idType": "1",
                "authorId": new_weko_id,
                "authorIdShowFlg": "true"
            })

        author_data["authorIdInfo"] = author_id_info
        
    def put_v1(self, **kwargs):
        """Handle PUT request for author update."""
        from weko_authors.models import Authors
        from weko_deposit.tasks import update_items_by_authorInfo
        from flask_login import current_user
        
        search_index = current_app.config["WEKO_AUTHORS_ES_INDEX_NAME"]
        lang_options_list = [
                "ja", "ja-Kana", "en", "fr", "it", "de", "es",
                "zh-cn", "zh-tw", "ru", "la", "ms", "eo", "ar",
                "el", "ko"
            ]

        try:
            data = request.get_json()

            if not data:
                raise BadRequest("Request body cannot be empty.")
            author_data = data.get("author")
            if not author_data:
                raise BadRequest("author can not be null.")

            es_id = data.get("id")
            pk_id = data.get("pk_id")
            
            if pk_id:
                if not pk_id.isdigit():
                    raise BadRequest("Invalid author ID.")
            
            for data_filed in ["emailInfo","authorIdInfo","authorNameInfo","affiliationInfo"]:
                if not author_data.get(data_filed,False):
                    author_data[data_filed] = []
            
            prefix_schemes,affiliation_schemes = self.get_all_schemes()
            if not self.validate_request_data(self.extract_data(author_data), lang_options_list, prefix_schemes, affiliation_schemes):
                raise BadRequest("Invalid Author Data, 'idtype' or 'language' Not Allowed.")

            if not es_id and not pk_id:
                raise BadRequest("Either 'id' or 'pk_id' must be specified.")

            author_by_pk = None
            author_by_es = None

            if pk_id:
                author_by_pk = Authors.query.filter_by(id=pk_id).first()

            if es_id:
                search_results = current_search_client.search(
                    index=search_index,
                    body={"query": {"term": {"_id": es_id}}},
                    size=1
                )
                if search_results["hits"]["total"] > 0:
                    author_by_es = search_results["hits"]["hits"][0]["_source"]

            if not author_by_pk and not author_by_es:
                raise NotFound("Specified author does not exist.")
            
            if pk_id and es_id and (bool(author_by_pk) ^ bool(author_by_es)):
                raise BadRequest("Parameters 'id' and 'pk_id' refer to different users.")


            if author_by_pk and author_by_es and str(author_by_pk.id) != str(author_by_es.get("pk_id")):
                raise BadRequest("Parameters 'id' and 'pk_id' refer to different users.")
            
            if author_by_pk and not es_id:
                es_id = author_by_pk.json.get("id")
            if author_by_es and not pk_id:
                pk_id = author_by_es.get("pk_id")

            self.validate_author_data(author_data, pk_id, is_update=True)
            
            # scheme -> id
            author_data = self.process_authors_data_before(author_data) 
            
            # author_data['id'] = es_id
            author_data['pk_id'] = pk_id
            author_data['gather_flg'] = 0
            
            WekoAuthors.update(pk_id,author_data,data.get("force_change",False))
            
            doc = current_search_client.get(index=search_index, id=es_id, doc_type="_doc")
            result = doc.get("_source", {})

            # id -> scheme
            author_data = self.process_authors_data_after(result)

            return Response(
                response=json.dumps({
                    "message": "Author successfully updated.",
                    "author": self.remove_filed_no_need(author_data)
                }),
                status=200,
                content_type='application/json'
            )

        except BadRequest as e:
            raise BadRequest(str(e))
        except NotFound as e:
            raise NotFound(str(e))
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.error(traceback.format_exc())
            raise InternalServerError("Database error.")
        except Exception:
            current_app.logger.error(traceback.format_exc())
            raise InternalServerError("Internal server error.")
        
    def extract_data(self, data):
        result = {
            "authorIdInfo_idType": [item["idType"] for item in data.get("authorIdInfo", []) if "idType" in item],
            "authorNameInfo_language": [item["language"] for item in data.get("authorNameInfo", []) if "language" in item],
            "affiliationInfo_affiliationIdType": [
                identifier["affiliationIdType"]
                for aff in data.get("affiliationInfo", [])
                for identifier in aff.get("identifierInfo", [])
                if "affiliationIdType" in identifier
            ],
            "affiliationInfo_affiliationNameLang": [
                name_info["affiliationNameLang"]
                for aff in data.get("affiliationInfo", [])
                for name_info in aff.get("affiliationNameInfo", [])
                if "affiliationNameLang" in name_info
            ]
        }
        print(f"extract_data:{result}")
        return result
    
    def get_all_schemes(self):
        from .models import AuthorsPrefixSettings, AuthorsAffiliationSettings
        prefix_schemes = db.session.query(AuthorsPrefixSettings.scheme).distinct().all()
        affiliation_schemes = db.session.query(AuthorsAffiliationSettings.scheme).distinct().all()
        prefix_schemes = [scheme[0] for scheme in prefix_schemes]
        affiliation_schemes = [scheme[0] for scheme in affiliation_schemes]
        print(f"prefix_schemes:{prefix_schemes}")
        print(f"affiliation_schemes:{affiliation_schemes}")
        return prefix_schemes,affiliation_schemes
        
        
    def validate_request_data(self, extracted_data, lang_options_list, prefix_schemes, affiliation_schemes):
        if not all(lang in lang_options_list for lang in extracted_data["authorNameInfo_language"]):
            print("authorNameInfo_language")
            return False
        if not all(lang in lang_options_list for lang in extracted_data["affiliationInfo_affiliationNameLang"]):
            print("affiliationInfo_affiliationNameLang")
            return False
        if not all(scheme in prefix_schemes for scheme in extracted_data["authorIdInfo_idType"]):
            print("authorIdInfo_idType")
            return False
        if not all(scheme in affiliation_schemes for scheme in extracted_data["affiliationInfo_affiliationIdType"]):
            print("affiliationInfo_affiliationIdType")
            return False
        return True


    def delete_v1(self, **kwargs):
        """Handle DELETE request for author deletion."""
        from weko_authors.models import Authors
        try:
            data = request.get_json()

            if not data:
                raise BadRequest("Request body cannot be empty.")

            es_id = data.get("id")
            pk_id = data.get("pk_id")

            if not es_id and not pk_id:
                raise BadRequest("Either 'id' or 'pk_id' must be specified.")
            
            author_by_pk = None
            author_by_es = None
            search_index = current_app.config.get("WEKO_AUTHORS_ES_INDEX_NAME")

            if pk_id:
                author_by_pk = Authors.query.filter_by(id=pk_id).first()

            if es_id:
                search_results = current_search_client.search(
                    index=search_index,
                    body={"query": {"term": {"_id": es_id}}},
                    size=1
                )
                if search_results["hits"]["total"]> 0:
                    author_by_es = search_results["hits"]["hits"][0]["_source"]
            
            if not author_by_pk and not author_by_es:
                raise NotFound("Specified author does not exist.")

            if author_by_pk and not es_id:
                es_id = author_by_pk.json.get("id")
                search_results = current_search_client.search(
                    index=search_index,
                    body={"query": {"term": {"_id": es_id}}},
                    size=1
                )
                if search_results["hits"]["total"]> 0:
                    author_by_es = search_results["hits"]["hits"][0]["_source"]

            if author_by_es and not pk_id:
                pk_id = author_by_es.get("pk_id")
                author_by_pk = Authors.query.filter_by(id=pk_id).first()
                
            if author_by_pk and author_by_es and str(author_by_pk.id) != str(author_by_es.get("pk_id")):
                raise BadRequest("Parameters 'id' and 'pk_id' refer to different users.")

            if author_by_pk:
                author_by_pk.is_deleted = True
                db.session.commit()

            if author_by_es:
                current_search_client.update(
                    index=search_index,
                    id=es_id,
                    body={"doc": {"is_deleted": True}},
                    doc_type="_doc"
                )
            return self.make_response(200)

        except BadRequest as e:
            raise BadRequest(str(e))
        except NotFound as e:
            raise NotFound(str(e))
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("Database error.")
        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            raise InternalServerError("Internal server error.")
