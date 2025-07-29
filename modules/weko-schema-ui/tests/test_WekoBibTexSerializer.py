import pytest
from mock import patch

from lxml import etree

# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_WekoBibTexSerializer.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp


    
# class BibTexTypes(Enum):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_WekoBibTexSerializer.py::test_bibtextypes -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_bibtextypes(app,db,db_oaischema):
    from weko_schema_ui.serializers.WekoBibTexSerializer import BibTexTypes
    assert BibTexTypes.ARTICLE.value == 'article'
    assert BibTexTypes.BOOK.value == 'book'
    assert BibTexTypes.BOOKLET.value == 'booklet'
    assert BibTexTypes.CONFERENCE.value == 'conference'
    assert BibTexTypes.INBOOK.value == 'inbook'
    assert BibTexTypes.INCOLLECTION.value == 'incollection'
    assert BibTexTypes.INPROCEEDINGS.value == 'inproceedings'
    assert BibTexTypes.MANUAL.value == 'manual'
    assert BibTexTypes.MASTERSTHESIS.value == 'mastersthesis'
    assert BibTexTypes.MISC.value == 'misc'
    assert BibTexTypes.PHDTHESIS.value == 'phdthesis'
    assert BibTexTypes.PROCEEDINGS.value == 'proceedings'
    assert BibTexTypes.TECHREPORT.value == 'techreport'
    assert BibTexTypes.UNPUBLISHED.value == 'unpublished'
    

# class BibTexFields(Enum):
def test_bibtexfields(app,db,db_oaischema):
    from weko_schema_ui.serializers.WekoBibTexSerializer import BibTexFields
    assert BibTexFields.AUTHOR.value == 'author'
    assert BibTexFields.YOMI.value == 'yomi'
    assert BibTexFields.TITLE.value =='title'
    assert BibTexFields.BOOK_TITLE.value =='book'
    assert BibTexFields.JOURNAL.value =='journal'
    assert BibTexFields.VOLUME.value =='volume'
    assert BibTexFields.NUMBER.value =='issue'
    assert BibTexFields.PAGES.value =='pages'
    assert BibTexFields.PAGE_START.value =='page_start'
    assert BibTexFields.PAGE_END.value =='page_end'
    assert BibTexFields.NOTE.value =='note'
    assert BibTexFields.PUBLISHER.value =='publisher'
    assert BibTexFields.YEAR.value =='year'
    assert BibTexFields.MONTH.value =='month'
    assert BibTexFields.URL.value =='url'
    assert BibTexFields.DOI.value =='doi'
    assert BibTexFields.SCHOOL.value =='school'
    assert BibTexFields.TYPE.value =='type'
    assert BibTexFields.EDITOR.value =='editor'
    assert BibTexFields.EDITION.value =='edition'
    assert BibTexFields.CHAPTER.value =='chapter'
    assert BibTexFields.SERIES.value =='series'
    assert BibTexFields.ADDRESS.value =='address'
    assert BibTexFields.ORGANIZATION.value =='organization'
    assert BibTexFields.KEY.value =='key'
    assert BibTexFields.CROSSREF.value =='crossref'
    assert BibTexFields.ANNOTE.value =='annote'
    assert BibTexFields.INSTITUTION.value =='institution'
    assert BibTexFields.HOW_PUBLISHER.value =='how publisher'

# class WekoBibTexSerializer():
#     def __init__(self):
#     def ____get_bibtex_type_fields(self, bibtex_type):
#     def __get_article_fields():
#     def __get_book_fields():
#     def __get_booklet_fields():
#     def __get_conference_fields():
#     def __get_inbook_fields():
#     def __get_incollection_fields():
#     def __get_inproceedings_fields():
#     def __get_manual_fields():
#     def __get_mastersthesis_fields():
#     def __get_phdthesis_fields():
#     def __get_proceedings_fields():
#     def __get_techreport_fields():
#     def __get_unpublished_fields():
#     def __get_misc_fields():
#     def serialize(self, pid, record, validate_mode=False):
#     def __get_jpcoar_data(pid, record):
#     def __is_empty(self, root):
#     def __get_bibtex_type(self, root):
#     def __validate_fields(self, root, bibtex_type):
#         def validate_by_att(attribute_name, expected_values):
#         def validate_partial_req():
#     def __combine_all_fields(self, bibtex_type):
#     def __get_bibtex_data(self, root, bibtex_type):
#         def process_by_att(att, expected_val, existed_lst):
#         def process_author():
#         def process_url():
#     def __get_item_id(root):
#     def __get_dates(dates):
#     def __get_identifier(identifier_type, identifier_types_data):

# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_WekoBibTexSerializer.py::test_wekobibtexserializer -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
def test_wekobibtexserializer(app, records, db_oaischema, itemtypes, esindex):
    from weko_schema_ui.serializers.WekoBibTexSerializer import WekoBibTexSerializer
    from weko_schema_ui.serializers.wekoxml import WekoXMLSerializer

    app.config['WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME'] = 'jpcoar_mapping'

    jp_dcndl = '{http://ndl.go.jp/dcndl/terms/}'
    jp_datacite = '{https://schema.datacite.org/meta/kernel-4/}'

    indexer, results = records
    record = results[0]['record']
    pid = results[0]['recid']
    serializer = WekoBibTexSerializer()
    assert isinstance(serializer,WekoBibTexSerializer)
    ret = serializer.serialize(pid,record)
    assert ret=='@misc{,\n month = {},\n year = {}\n}\n\n'

    # datetype = Available
    serializer = WekoBibTexSerializer()
    assert isinstance(serializer,WekoBibTexSerializer)
    with patch.dict('weko_schema_ui.config.WEKO_SCHEMA_DATE_DATETYPE_MAPPING', {'dataset': 'Available'}):
        ret = serializer.serialize(pid,record)
        assert ret==(
            '@misc{oai:weko3.example.org:00000001,\n'
            ' author = {情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro},\n'
            ' month = {Jun},\n'
            ' note = {Description\n'
            'Description<br/>Description, 概要\n'
            '概要\n'
            '概要\n'
            '概要},\n'
            ' title = {ja_conference '
            'paperITEM00000009(public_open_access_open_access_simple)},\n'
            ' year = {2021},\n'
            ' yomi = {ジョウホウ, タロウ and ジョウホウ, タロウ and ジョウホウ, タロウ}\n'
            '}\n'
            '\n'
        )

    # set date_priority_mapping
    serializer = WekoBibTexSerializer()
    assert isinstance(serializer,WekoBibTexSerializer)
    serializer.date_priority_mapping = {'dataset': [jp_dcndl + 'dateGranted']}
    ret = serializer.serialize(pid,record)
    assert ret==(
        '@misc{oai:weko3.example.org:00000001,\n'
        ' author = {情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro},\n'
        ' month = {Jun},\n'
        ' note = {Description\n'
        'Description<br/>Description, 概要\n'
        '概要\n'
        '概要\n'
        '概要},\n'
        ' title = {ja_conference '
        'paperITEM00000009(public_open_access_open_access_simple)},\n'
        ' year = {2021},\n'
        ' yomi = {ジョウホウ, タロウ and ジョウホウ, タロウ and ジョウホウ, タロウ}\n'
        '}\n'
        '\n'
    )

    # get pubdate
    serializer = WekoBibTexSerializer()
    assert isinstance(serializer,WekoBibTexSerializer)
    with patch.dict('weko_schema_ui.config.WEKO_SCHEMA_DATE_DATETYPE_MAPPING', {'dataset': 'XXXXX'}):
        ret = serializer.serialize(pid,record)
        assert ret==(
            '@misc{oai:weko3.example.org:00000001,\n'
            ' author = {情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro},\n'
            ' month = {Aug},\n'
            ' note = {Description\n'
            'Description<br/>Description, 概要\n'
            '概要\n'
            '概要\n'
            '概要},\n'
            ' title = {ja_conference '
            'paperITEM00000009(public_open_access_open_access_simple)},\n'
            ' year = {2021},\n'
            ' yomi = {ジョウホウ, タロウ and ジョウホウ, タロウ and ジョウホウ, タロウ}\n'
            '}\n'
            '\n'
        )

    # Duplicate Dates
    serializer = WekoBibTexSerializer()
    assert isinstance(serializer,WekoBibTexSerializer)
    serializer.base_date_priority = [jp_datacite + 'date']
    ret = serializer.serialize(pid,record)
    assert ret==(
        '@misc{oai:weko3.example.org:00000001,\n'
        ' author = {情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro and 情報, 太郎 and Joho, Taro},\n'
        ' month = {Jun, Jun, },\n'
        ' note = {Description\n'
        'Description<br/>Description, 概要\n'
        '概要\n'
        '概要\n'
        '概要},\n'
        ' title = {ja_conference '
        'paperITEM00000009(public_open_access_open_access_simple)},\n'
        ' year = {2021, 2021, 2021},\n'
        ' yomi = {ジョウホウ, タロウ and ジョウホウ, タロウ and ジョウホウ, タロウ}\n'
        '}\n'
        '\n'
    )

    record = results[1]['record']
    pid = results[1]['recid']
    serializer = WekoBibTexSerializer()
    assert isinstance(serializer,WekoBibTexSerializer)
    ret = serializer.serialize(pid,record)
    assert ret=='@inproceedings{,\n month = {},\n year = {}\n}\n\n'

    record.update({'@export_schema_type': 'ddi'})
    serializer = WekoXMLSerializer()
    data = serializer.serialize(pid, record)
    assert b'<metadata>\n        <codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"/>\n      </metadata>' in data

