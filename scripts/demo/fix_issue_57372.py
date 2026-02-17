import traceback

from sqlalchemy.orm.attributes import flag_modified
from flask import current_app
from invenio_db import db
from weko_admin.models import SearchManagement


def fix_search_conditions(search_condition):
    for condition in search_condition:
        # id
        if 'id' in condition and condition['id'] == 'id':
            if 'mapping' in condition:
                condition['mapping'] = ['identifier', 'URI', 'fullTextURL', 'selfDOI', 'ISBN', 'ISSN', 'NCID', 'PMID', 'DOI', 'NAID', 'ICHUSHI']
            if 'sche_or_attr' in condition:
                condition['sche_or_attr'] = [
                    {'id': 'identifier', 'contents': 'identifier', 'checkStus': False},
                    {'id': 'URI', 'contents': 'URI', 'checkStus': False},
                    {'id': 'fullTextURL', 'contents': 'fullTextURL', 'checkStus': False},
                    {'id': 'selfDOI', 'contents': 'selfDOI', 'checkStus': False},
                    {'id': 'ISBN', 'contents': 'ISBN', 'checkStus': False},
                    {'id': 'ISSN', 'contents': 'ISSN', 'checkStus': False},
                    {'id': 'NCID', 'contents': 'NCID', 'checkStus': False},
                    {'id': 'PMID', 'contents': 'PMID', 'checkStus': False},
                    {'id': 'DOI', 'contents': 'DOI', 'checkStus': False},
                    {'id': 'NAID', 'contents': 'NAID', 'checkStus': False},
                    {'id': 'ICHUSHI', 'contents': 'ICHUSHI', 'checkStus': False},
                ]
        # version
        if 'id' in condition and condition['id'] == 'version':
            if 'options' in condition:
                condition['options'] = [
                    {'id': 'AO', 'contents': 'AO'},
                    {'id': 'SMUR', 'contents': 'SMUR'},
                    {'id': 'AM', 'contents': 'AM'},
                    {'id': 'P', 'contents': 'P'},
                    {'id': 'VoR', 'contents': 'VoR'},
                    {'id': 'CVoR', 'contents': 'CVoR'},
                    {'id': 'EVoR', 'contents': 'EVoR'},
                    {'id': 'NA', 'contents': 'NA'}
                ]


def main():
    res = SearchManagement.get()
    if res:
        try:
            fix_search_conditions(res.search_conditions)
            if 'detail_condition' in res.search_setting_all:
                fix_search_conditions(res.search_setting_all['detail_condition'])
            flag_modified(res, "search_conditions")
            flag_modified(res, "search_setting_all")
            db.session.merge(res)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()