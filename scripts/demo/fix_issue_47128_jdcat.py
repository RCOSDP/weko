import properties
import json
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from invenio_db import db
from invenio_records.models import RecordMetadata
from weko_records.api import ItemTypes
from weko_records.models import ItemMetadata, ItemType, ItemTypeMapping

def get_properties_mapping():
    mapping = {}
    for i in dir(properties):
        prop = getattr(properties, i)
        if getattr(prop, 'property_id', None) and prop.property_id:
            mapping[int(prop.property_id)] = prop.mapping
    return mapping

def change_subitem_key(data, copy, subitem_change_table):
    for subitem_key in copy.copy().keys():
        if subitem_key in subitem_change_table:
            temp = data.pop(subitem_key)
            if subitem_change_table[subitem_key] is not None:
                data[subitem_change_table[subitem_key]] = temp
                if isinstance(temp, dict):
                    change_subitem_key(data[subitem_change_table[subitem_key]], temp, subitem_change_table)
                elif isinstance(temp, list):
                    for index, child_data in enumerate(temp):
                        if isinstance(child_data, dict):
                            change_subitem_key(data[subitem_change_table[subitem_key]][index], child_data, subitem_change_table)
                        else:
                            break
                else:
                    continue

def main():
    ITEM_ID_CHANGE_FILE_NAME = 'item_id_change_{}'.format(datetime.utcnow().strftime('%Y%m%d%H%M'))
    item_key_data = {
        'resourcetype': {'change_key_20': False, 'prop_name_20': 'resourceType'},
        'item_1551264308487': {'change_key_12': True, 'change_key_20': True, 'prop_name_12': 'title', 'prop_name_20': 'title'},
        'item_1551264326373': {'change_key_12': True, 'change_key_20': True, 'prop_name_12': 'alternative_title', 'prop_name_20': 'alternative_title'},
        'item_1551264340087': {'change_key_12': True, 'prop_name_12': 'creator'},
        'item_1593074267803': {'change_key_20': False, 'prop_name_20': 'author'},
        'item_1551264418667': {'change_key_12': True, 'prop_name_12': 'contributor'},
        'item_1551264447183': {'change_key_12': True, 'prop_name_12': 'access_rights'},
        'item_1551264605515': {'change_key_12': True, 'prop_name_12': 'apc'},
        'item_1551264629907': {'change_key_12': True, 'change_key_20': True, 'prop_name_12': 'rights', 'prop_name_20': 'lisence'},
        'item_1551264767789': {'change_key_12': True, 'prop_name_12': 'rights_holder'},
        'item_1551264822581': {'change_key_12': True, 'change_key_20': False, 'prop_name_12': 'subject', 'prop_name_20': 'topic'},
        'item_1551264917614': {'change_key_12': True, 'change_key_20': True, 'prop_name_12': 'publisher', 'prop_name_20': 'publisher'},
        'item_1551264974654': {'change_key_12': True, 'prop_name_12': 'date'},
        'item_1551265002099': {'change_key_12': True, 'change_key_20': True, 'prop_name_12': 'language', 'prop_name_20': 'language'},
        'item_1551265032053': {'change_key_12': False, 'prop_name_12': 'resource_type'},
        'item_1551265075370': {'change_key_12': True, 'change_key_20': False, 'prop_name_12': 'version', 'prop_name_20': 'version'},
        'item_1551265118680': {'change_key_12': True, 'prop_name_12': 'version_type'},
        'item_1551265227803': {'change_key_12': True, 'prop_name_12': 'relation'},
        'item_1551265302120': {'change_key_12': True, 'prop_name_12': 'temporal'},
        'item_1551265385290': {'change_key_12': True, 'prop_name_12': 'funding_reference'},
        'item_1551265409089': {'change_key_12': True, 'prop_name_12': 'source_identifier'},
        'item_1551265438256': {'change_key_12': True, 'prop_name_12': 'source_title'},
        'item_1551265463411': {'change_key_12': True, 'prop_name_12': 'volume_number'},
        'item_1551265520160': {'change_key_12': True, 'prop_name_12': 'issue_number'},
        'item_1551265553273': {'change_key_12': True, 'prop_name_12': 'number_of_pages'},
        'item_1551265569218': {'change_key_12': True, 'prop_name_12': 'page_start'},
        'item_1551265603279': {'change_key_12': True, 'prop_name_12': 'page_end'},
        'item_1551265738931': {'change_key_12': True, 'prop_name_12': 'dissertation_number'},
        'item_1551265790591': {'change_key_12': True, 'prop_name_12': 'degree_name'},
        'item_1551265811989': {'change_key_12': True, 'prop_name_12': 'date_granted'},
        'item_1551265903092': {'change_key_12': True, 'prop_name_12': 'degree_grantor'},
        'item_1551265973055': {'change_key_12': True, 'prop_name_12': 'conference'},
        'item_1570068313185': {'change_key_12': True, 'change_key_20': True, 'prop_name_12': 'geolocation', 'prop_name_20': 'geo'},
        'item_1570069138259': {'change_key_12': True, 'prop_name_12': 'file'},
        'item_1600078832557': {'change_key_20': False, 'prop_name_20': 'file'},
        'item_1581495499605': {'change_key_12': True, 'prop_name_12': 'identifier_registration'},
        'item_1636457801246': {'change_key_12': False, 'prop_name_12': 'identifier'},
        'item_1636460428217': {'change_key_12': True, 'prop_name_12': 'description'},
        'item_1551264846237': {'change_key_20': True, 'prop_name_20': 'description'},
        'item_1588254290498': {'change_key_20': True, 'prop_name_20': 'series'},
        'item_1592880868902': {'change_key_20': True, 'prop_name_20': 'bib'},
        'item_1602145007095': {'change_key_20': True, 'prop_name_20': 'uri'},
        'item_1602145817646': {'change_key_20': True, 'prop_name_20': 'fund'},
        'item_1602146041055': {'change_key_20': True, 'prop_name_20': 'datafile'},
        'item_1586157591881': {'change_key_20': False, 'prop_name_20': 'study_id'},
		'item_1586253152753': {'change_key_20': False, 'prop_name_20': 'date_of_c'},
		'item_1586253224033': {'change_key_20': False, 'prop_name_20': 'unit_of_analysis'},
		'item_1586253249552': {'change_key_20': False, 'prop_name_20': 'universe'},
		'item_1586253334588': {'change_key_20': False, 'prop_name_20': 'sampling_procedure'},
		'item_1586253349308': {'change_key_20': False, 'prop_name_20': 'collection_method'},
		'item_1586253589529': {'change_key_20': False, 'prop_name_20': 'sampling_rate'},
		'item_1588260046718': {'change_key_20': False, 'prop_name_20': 'data_k'},
		'item_1588260178185': {'change_key_20': False, 'prop_name_20': 'access_e'},
		'item_1592405734122': {'change_key_20': False, 'prop_name_20': 'distributor'},
		'item_1592405735401': {'change_key_20': False, 'prop_name_20': 'related_publications'},
		'item_1592405736602': {'change_key_20': False, 'prop_name_20': 'related_studies'},
		'item_1602145192334': {'change_key_20': False, 'prop_name_20': 'time_period'},
		'item_1602145850035': {'change_key_20': False, 'prop_name_20': 'grand_id'},
		'item_1602147887655': {'change_key_20': False, 'prop_name_20': 'provider'}
    }
    subitem_change_table = {
        'subitem_1551255647225': 'subitem_title',
        'subitem_1551255648112': 'subitem_title_language',
        'subitem_1551255720400': 'subitem_alternative_title',
        'subitem_1551255721061': 'subitem_alternative_title_language',
        'subitem_1551255789000': 'nameIdentifiers',
        'subitem_1551255793478': 'nameIdentifier',
        'subitem_1551255794292': 'nameIdentifierScheme',
        'subitem_1551255795486': 'nameIdentifierURI',
        'subitem_1551255898956': 'creatorNames',
        'subitem_1551255905565': 'creatorName',
        'subitem_1551255907416': 'creatorNameLang',
        'subitem_1551255929209': 'familyNames',
        'subitem_1551255938498': 'familyName',
        'subitem_1551255964991': 'familyNameLang',
        'subitem_1551255991424': 'givenNames',
        'subitem_1551256006332': 'givenName',
        'subitem_1551256007414': 'givenNameLang',
        'subitem_1551256025394': 'creatorAlternatives',
        'subitem_1551256035730': 'creatorAlternative',
        'subitem_1551256055588': 'creatorAlternativeLang',
        'subitem_1551256087090': 'creatorAffiliations',
        'subitem_1551257036415': 'contributorType',
        'subitem_1551257150927': 'nameIdentifiers',
        'subitem_1551257152742': 'nameIdentifier',
        'subitem_1551257172531': 'nameIdentifierScheme',
        'subitem_1551257228080': 'nameIdentifierURI',
        'subitem_1551257245638': 'contributorNames',
        'subitem_1551257276108': 'contributorName',
        'subitem_1551257279831': 'lang',
        'subitem_1551257272214': 'familyNames',
        'subitem_1551257314588': 'familyName',
        'subitem_1551257316910': 'familyNameLang',
        'subitem_1551257339190': 'givenNames',
        'subitem_1551257342360': 'givenName',
        'subitem_1551257343979': 'givenNameLang',
        'subitem_1551257372442': 'contributorAlternatives',
        'subitem_1551257374288': 'contributorAlternative',
        'subitem_1551257375939': 'contributorAlternativeLang',
        'subitem_1551257419251': 'contributorAffiliations',
        'subitem_1551257421633': 'contributorAffiliationNameIdentifiers',
        'subitem_1551261472867': 'contributorAffiliationNameIdentifier',
        'subitem_1551261485670': 'contributorAffiliationScheme',
        'subitem_1551261493409': 'contributorAffiliationURI',
        'subitem_1551261534334': 'contributorAffiliationNames',
        'subitem_1551261542403': 'contributorAffiliationName',
        'subitem_1551261546333': 'contributorAffiliationNameLang',
        'subitem_1551256089084': 'affiliationNameIdentifiers',
        'subitem_1551256097891': 'affiliationNameIdentifier',
        'subitem_1551256145018': 'affiliationNameIdentifierScheme',
        'subitem_1551256147368': 'affiliationNameIdentifierURI',
        'subitem_1551256229037': 'affiliationNames',
        'subitem_1551256259183': 'affiliationName',
        'subitem_1551256259899': 'affiliationNameLang',
        'subitem_1551257553743': 'subitem_access_right',
        'subitem_1551257578398': 'subitem_access_right_uri',
        'subitem_1551257776901': 'subitem_apc',
        'subitem_1602213569986': 'subitem_text_value',
        'subitem_1602213570623': 'subitem_text_language',
        'subitem_1551257138324': None,
        'subitem_1551257143244': 'nameIdentifiers',
        'subitem_1551257145912': 'nameIdentifier',
        'subitem_1551257156244': 'nameIdentifierScheme',
        'subitem_1551257232980': 'nameIdentifierURI',
        'subitem_1551257249371': 'rightHolderNames',
        'subitem_1551257255641': 'rightHolderName',
        'subitem_1551257257683': 'rightHolderLanguage',
        'subitem_1551257315453': 'subitem_subject',
        'subitem_1551257323812': 'subitem_subject_language',
        'subitem_1551257329877': 'subitem_subject_scheme',
        'subitem_1551257343002': 'subitem_subject_uri',
        'subitem_1551255702686': 'subitem_publisher',
        'subitem_1551255710277': 'subitem_publisher_language',
        'subitem_1551255753471': 'subitem_date_issued_datetime',
        'subitem_1551255775519': 'subitem_date_issued_type',
        'subitem_1551255818386': 'subitem_language',
        'subitem_1551255975405': 'subitem_version',
        'subitem_1551256387752': None,
        'subitem_1551256388439': 'subitem_relation_type',
        'subitem_1551256465077': 'subitem_relation_type_id',
        'subitem_1551256478339': 'subitem_relation_type_select',
        'subitem_1551256629524': 'subitem_relation_type_id_text',
        'subitem_1551256480278': 'subitem_relation_name',
        'subitem_1551256498531': 'subitem_relation_name_text',
        'subitem_1551256513476': 'subitem_relation_name_language',
        'subitem_1551256918211': 'subitem_temporal_text',
        'subitem_1551256920086': 'subitem_temporal_language',
        'subitem_1551256405981': 'subitem_source_identifier',
        'subitem_1551256409644': 'subitem_source_identifier_type',
        'subitem_1551256349044': 'subitem_source_title',
        'subitem_1551256350188': 'subitem_source_title_language',
        'subitem_1551256328147': 'subitem_volume',
        'subitem_1551256294723': 'subitem_issue',
        'subitem_1551256248092': 'subitem_number_of_pages',
        'subitem_1551256198917': 'subitem_start_page',
        'subitem_1551256185532': 'subitem_end_page',
        'subitem_1551256171004': 'subitem_dissertationnumber',
        'subitem_1551256126428': 'subitem_degreename',
        'subitem_1551256129013': 'subitem_degreename_language',
        'subitem_1551256096004': 'subitem_dategranted',
        'subitem_1551256015892': 'subitem_degreegrantor_identifier',
        'subitem_1551256027296': 'subitem_degreegrantor_identifier_name',
        'subitem_1551256029891': 'subitem_degreegrantor_identifier_scheme',
        'subitem_1551256037922': 'subitem_degreegrantor',
        'subitem_1551256042287': 'subitem_degreegrantor_name',
        'subitem_1551256047619': 'subitem_degreegrantor_language',
        'subitem_1599711633003': 'subitem_conference_names',
        'subitem_1599711636923': 'subitem_conference_name',
        'subitem_1599711645590': 'subitem_conference_name_language',
        'subitem_1599711655652': 'subitem_conference_sequence',
        'subitem_1599711660052': 'subitem_conference_sponsors',
        'subitem_1599711680082': 'subitem_conference_sponsor',
        'subitem_1599711686511': 'subitem_conference_sponsor_language',
        'subitem_1599711699392': 'subitem_conference_date',
        'subitem_1599711704251': 'subitem_conference_period',
        'subitem_1599711712451': 'subitem_conference_start_day',
        'subitem_1599711727603': 'subitem_conference_start_month',
        'subitem_1599711731891': 'subitem_conference_start_year',
        'subitem_1599711735410': 'subitem_conference_end_day',
        'subitem_1599711739022': 'subitem_conference_end_month',
        'subitem_1599711743722': 'subitem_conference_end_year',
        'subitem_1599711745532': 'subitem_conference_date_language',
        'subitem_1599711758470': 'subitem_conference_venues',
        'subitem_1599711769260': 'subitem_conference_venue',
        'subitem_1599711775943': 'subitem_conference_venue_language',
        'subitem_1599711788485': 'subitem_conference_places',
        'subitem_1599711798761': 'subitem_conference_place',
        'subitem_1599711803382': 'subitem_conference_place_language',
        'subitem_1599711813532': 'subitem_conference_country',
        'subitem_1586419454219': 'subitem_text_value',
        'subitem_1586419462229': 'subitem_text_language',
        'subitem_1551256250276': 'subitem_identifier_reg_text',
        'subitem_1551256259586': 'subitem_identifier_reg_type',
        'subitem_1522657647525': 'subitem_description_type',
        'subitem_1522657697257': 'subitem_description',
        'subitem_1523262169140': 'subitem_description_language',
        'subitem_1551255637472': 'subitem_description_type',
        'subitem_1551255577890': 'subitem_description',
        'subitem_1551255592625': 'subitem_description_language',
        'subitem_1587462181884': 'subitem_text_value',
        'subitem_1587462183075': 'subitem_text_language',
        'subitem_1586228465211': 'subitem_text_value',
        'subitem_1586228490356': 'subitem_text_language',
        'subitem_1602144759036': 'subitem_uri_value',
        'subitem_1602142814330': 'subitem_text_value',
        'subitem_1602142815328': 'subitem_text_language',
        'subitem_1602143181822': 'subitem_uri_value'
    }
    version_type_resource = {
        'AO': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce',
        'SMUR': 'http://purl.org/coar/version/c_71e4c1898caa6e32',
        'AM': 'http://purl.org/coar/version/c_ab4af688f83e57aa',
        'P': 'http://purl.org/coar/version/c_fa2ee174bc00049f',
        'VoR': 'http://purl.org/coar/version/c_970fb48d4fbd8a85',
        'CVoR': 'http://purl.org/coar/version/c_e19f295774971610',
        'EVoR': 'http://purl.org/coar/version/c_dc82b40f9837b551',
        'NA': 'http://purl.org/coar/version/c_be7fb7dd8ff6fe43'
    }
    id_match_key = {}
    prop_id_change = {
        'cus_8': 'cus_1014',
        'cus_17': 'cus_1010',
        'cus_60': 'cus_1038',
        'cus_65': 'cus_1035',
        'cus_67': 'cus_1001',
        'cus_68': 'cus_1011',
        'cus_69': 'cus_1002',
        'cus_70': 'cus_1012',
        'cus_71': 'cus_1003',
        'cus_72': 'cus_1035',
        'cus_73': 'cus_1038',
        'cus_74': 'cus_1014',
        'cus_75': 'cus_1034',
        'cus_76': 'cus_1015',
        'cus_77': 'cus_1016',
        'cus_78': 'cus_1033',
        'cus_79': 'cus_1032',
        'cus_80': 'cus_1031',
        'cus_82': 'cus_1030',
        'cus_83': 'cus_1029',
        'cus_84': 'cus_1028',
        'cus_85': 'cus_126',
        'cus_86': 'cus_1018',
        'cus_87': 'cus_1026',
        'cus_88': 'cus_1025',
        'cus_89': 'cus_1024',
        'cus_90': 'cus_1023',
        'cus_91': 'cus_1022',
        'cus_92': 'cus_1019',
        'cus_93': 'cus_1021',
        'cus_94': 'cus_1020',
        'cus_95': 'cus_1007',
        'cus_96': 'cus_1008',
        'cus_97': 'cus_1009',
        'cus_98': 'cus_1039',
        'cus_99': 'cus_1005',
        'cus_100': 'cus_1006',
        'cus_137': 'cus_1042',
        'cus_141': 'cus_1042',
        'cus_162': 'cus_1042',
        'cus_165': 'cus_1042',
        'cus_166': 'cus_305',
        'cus_169': 'cus_305',
        'cus_170': 'cus_1042',
        'cus_176': 'cus_1017',
        'cus_10003': 'cus_1010'
    }
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Fix issue 47128 is start (jdcat).')
    try:
        item_types = db.session.query(ItemType).filter(ItemType.id.in_([12, 20])).all()
        for item_type in item_types:
            # get/update item key
            try:
                # update property id
                for form in item_type.render['table_row_map']['form']:
                    if isinstance(form, dict) and 'key' in form:
                        item_key = form['key']
                        if item_key.startswith('item_'):
                            prop_id = item_type.render['meta_list'][item_key]['input_type']
                            if prop_id in prop_id_change.keys():
                                item_type.render['meta_list'][item_key]['input_type'] = prop_id_change[prop_id]
                # get new item key
                count = 1
                id_match_key[item_type.id] = {}
                item_key_list = item_type.render['table_row']
                
                for item_key in item_key_list:
                    if item_key not in item_key_data:
                        continue
                    new_key = 'item_{}_{}_{}'.format(
                        item_type.id,
                        item_key_data[item_key]['prop_name_{}'.format(item_type.id)],
                        count
                    )
                    id_match_key[item_type.id][item_key] = new_key
                    count += 1
                
                # update item key
                item_type_schema = json.dumps(item_type.schema)
                item_type_form = json.dumps(item_type.form)
                item_type_render = json.dumps(item_type.render)
                for old_key, new_key in id_match_key[item_type.id].items():
                    item_type_schema = item_type_schema.replace(old_key, new_key)
                    item_type_form = item_type_form.replace(old_key, new_key)
                    item_type_render = item_type_render.replace(old_key, new_key)
                item_type.schema = json.loads(item_type_schema)
                item_type.form = json.loads(item_type_form)
                item_type.render = json.loads(item_type_render)
                flag_modified(item_type, "schema")
                flag_modified(item_type, "form")
                flag_modified(item_type, "render")
                db.session.merge(item_type)
                db.session.commit()
                print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Update item key of item type ({}) is success.'.format(item_type.id))
            except Exception as ex:
                db.session.rollback()
                print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Update item key of item type ({}) is fail.'.format(item_type.id))
                print(ex)

            # update item key of item type mapping
            mappings = db.session.query(ItemTypeMapping).filter(ItemTypeMapping.id==item_type.id).all()
            for mapping in mappings:
                try:
                    mapping_data = json.dumps(mapping.mapping)
                    for old_key, new_key in id_match_key[item_type.id].items():
                        mapping_data = mapping_data.replace(old_key, new_key)
                    mapping.mapping = json.loads(mapping_data)
                    flag_modified(mapping, "mapping")
                    db.session.merge(mapping)
                    db.session.commit()
                    print(
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'Update item key of item type mapping (item_type_id: {}, version_id: {}) is success.'.format(mapping.item_type_id, mapping.version_id))
                except Exception as ex:
                    db.session.rollback()
                    print(
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'Update item key of item type mapping (item_type_id: {}, version_id: {}) is fail.'.format(mapping.item_type_id, mapping.version_id))
                    print(ex)

            # reload property and update mapping
            try:
                mapping = get_properties_mapping()
                ItemTypes.reload(item_type.id, mapping, [], 'ALL')
                db.session.commit()
                print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Reload properties of item type ({}) is success.'.format(item_type.id))
            except Exception as ex:
                db.session.rollback()
                print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Reload properties of item type ({}) is fail.'.format(item_type.id))
                print(ex)

        print('IMPORTANT: item key change table: {}'.format(id_match_key))
        # 12: Multiple, 20: Harvesting DDI
        item_list = db.session.query(ItemMetadata).filter(ItemMetadata.item_type_id.in_([12, 20])).all()
        success_count = 0
        skip_count = 0
        update_flag = False
        print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Update metadata start.')
        for item in item_list:
            try:
                rec = db.session.query(RecordMetadata).filter(RecordMetadata.id==item.id).one_or_none()
                for old_key, new_key in id_match_key[item_type.id].items():
                    if old_key not in item.json:
                        continue

                    name_key = ''
                    if 'prop_name_{}'.format(item.item_type_id) in item_key_data[old_key]:
                        name_key = 'prop_name_{}'.format(item.item_type_id)
                    else:
                        continue

                    chang_key = ''
                    if 'change_key_{}'.format(item.item_type_id) in item_key_data[old_key]:
                        chang_key = 'change_key_{}'.format(item.item_type_id)
                    else:
                        continue

                    update_flag = True
                    item.json[new_key] = item.json.pop(old_key)
                    rec.json[new_key] = rec.json.pop(old_key)
                    if item_key_data[old_key][chang_key]:
                        # rights
                        if item_key_data[old_key][name_key] == 'rights':
                            # item_metadata
                            for i, subitem in enumerate(item.json[new_key]):
                                if 'subitem_1551257030435' in subitem:
                                    item.json[new_key][i]['subitem_version_type'] = item.json[new_key][i].pop('subitem_1551257030435')
                                if 'subitem_1551257025236' in subitem:
                                    value = item.json[new_key][i].pop('subitem_1551257025236')
                                    if isinstance(value, list) and len(value) > 0:
                                        if 'subitem_1551257043769' in value[0]:
                                            item.json[new_key][i]['subitem_rights'] = value[0]['subitem_1551257043769']
                                        if 'subitem_1551257047388' in value[0]:
                                            item.json[new_key][i]['subitem_rights_language'] = value[0]['subitem_1551257047388']
                            # records_metadata
                            for i, subitem in enumerate(rec.json[new_key]['attribute_value_mlt']):
                                if 'subitem_1551257030435' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_version_type'] = \
                                            rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551257030435')
                                if 'subitem_1551257025236' in subitem:
                                    value = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551257025236')
                                    if isinstance(value, list) and len(value) > 0:
                                        if 'subitem_1551257043769' in value[0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_rights'] = value[0]['subitem_1551257043769']
                                        if 'subitem_1551257047388' in value[0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_rights_language'] = value[0]['subitem_1551257047388']
                        # version type
                        if item_key_data[old_key][name_key] == 'version_type':
                            # item_metadata
                            for i, subitem in enumerate(item.json[new_key]):
                                if 'subitem_1551256025676' in subitem:
                                    value = item.json[new_key][i].pop('subitem_1551256025676')
                                    item.json[new_key][i]['subitem_version_type'] = value
                                    if version_type_resource.get(value, ''):
                                        item.json[new_key][i]['subitem_version_resource'] = version_type_resource[value]
                            # records_metadata
                            for i, subitem in enumerate(rec.json[new_key]['attribute_value_mlt']):
                                if 'subitem_1551256025676' in subitem:
                                    value = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256025676')
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_version_type'] = value
                                    if version_type_resource.get(value, ''):
                                        rec.json[new_key]['attribute_value_mlt'][i]['subitem_version_resource'] = version_type_resource[value]
                        # file
                        if item_key_data[old_key][name_key] == 'file':
                            # item_metadata
                            for i, subitem in enumerate(item.json[new_key]):
                                if 'subitem_1551255558587' in subitem and \
                                        isinstance(subitem['subitem_1551255558587'], list) and \
                                        len(subitem['subitem_1551255558587']) > 0:
                                    value = item.json[new_key][i].pop('subitem_1551255558587')
                                    item.json[new_key][i]['url'] = {}
                                    if 'subitem_1551255570271' in value[0]:
                                        item.json[new_key][i]['url']['url'] = value[0]['subitem_1551255570271']
                                    if 'subitem_1551255581435' in value[0]:
                                        item.json[new_key][i]['url']['objectType'] = value[0]['subitem_1551255581435']
                                    if 'subitem_1551255628842' in value[0]:
                                        item.json[new_key][i]['url']['label'] = value[0]['subitem_1551255628842']
                                if 'subitem_1551255750794' in subitem:
                                    item.json[new_key][i]['format'] = item.json[new_key][i].pop('subitem_1551255750794')
                                if 'subitem_1551255788530' in subitem:
                                    value = item.json[new_key][i].pop('subitem_1551255788530')
                                    item.json[new_key][i]['filesize'] = []
                                    for v in value:
                                        if 'subitem_1570068579439' in v:
                                            item.json[new_key][i]['filesize'].append({'value': v['subitem_1570068579439']})
                                if 'subitem_1551255820788' in subitem:
                                    value = item.json[new_key][i].pop('subitem_1551255820788')
                                    item.json[new_key][i]['date'] = []
                                    for v in value:
                                        tmp = {}
                                        if 'subitem_1551255828320' in v:
                                            tmp['dateValue'] = v['subitem_1551255828320']
                                        if 'subitem_1551255833133' in v:
                                            tmp['dateType'] = v['subitem_1551255833133']
                                        if tmp:
                                            item.json[new_key][i]['date'].append(tmp)
                                if 'subitem_1551255854908' in subitem:
                                    item.json[new_key][i]['version'] = item.json[new_key][i].pop('subitem_1551255854908')
                            # records_metadata
                            for i, subitem in enumerate(rec.json[new_key]['attribute_value_mlt']):
                                if 'subitem_1551255558587' in subitem and \
                                        isinstance(subitem['subitem_1551255558587'], list) and \
                                        len(subitem['subitem_1551255558587']) > 0:
                                    value = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551255558587')
                                    rec.json[new_key]['attribute_value_mlt'][i]['url'] = {}
                                    if 'subitem_1551255570271' in value[0]:
                                        rec.json[new_key]['attribute_value_mlt'][i]['url']['url'] = value[0]['subitem_1551255570271']
                                    if 'subitem_1551255581435' in value[0]:
                                        rec.json[new_key]['attribute_value_mlt'][i]['url']['objectType'] = value[0]['subitem_1551255581435']
                                    if 'subitem_1551255628842' in value[0]:
                                        rec.json[new_key]['attribute_value_mlt'][i]['url']['label'] = value[0]['subitem_1551255628842']
                                if 'subitem_1551255750794' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['format'] = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551255750794')
                                if 'subitem_1551255788530' in subitem:
                                    value = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551255788530')
                                    rec.json[new_key]['attribute_value_mlt'][i]['filesize'] = []
                                    for v in value:
                                        if 'subitem_1570068579439' in v:
                                            rec.json[new_key]['attribute_value_mlt'][i]['filesize'].append({'value': v['subitem_1570068579439']})
                                if 'subitem_1551255820788' in subitem:
                                    value = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551255820788')
                                    rec.json[new_key]['attribute_value_mlt'][i]['date'] = []
                                    for v in value:
                                        tmp = {}
                                        if 'subitem_1551255828320' in v:
                                            tmp['dateValue'] = v['subitem_1551255828320']
                                        if 'subitem_1551255833133' in v:
                                            tmp['dateType'] = v['subitem_1551255833133']
                                        if tmp:
                                            rec.json[new_key]['attribute_value_mlt'][i]['date'].append(tmp)
                                if 'subitem_1551255854908' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['version'] = rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551255854908')
                        # geo location
                        if item_key_data[old_key][name_key] == 'geolocation':
                            # item_metadata
                            for i, subitem in enumerate(item.json[new_key]):
                                # geolocation place
                                if 'subitem_1551256842196' in subitem:
                                    item.json[new_key][i]['subitem_geolocation_place'] = item.json[new_key][i].pop('subitem_1551256842196')
                                    for j, subplace in enumerate(item.json[new_key][i]['subitem_geolocation_place']):
                                        if 'subitem_1570008213846' in subplace:
                                            item.json[new_key][i]['subitem_geolocation_place'][j]['subitem_geolocation_place_text'] = \
                                                    item.json[new_key][i]['subitem_geolocation_place'][j].pop('subitem_1570008213846')
                                if 'subitem_1551256775293' in subitem:
                                    if 'subitem_geolocation_place' in item.json[new_key][i]:
                                        item.json[new_key][i]['subitem_geolocation_place'].append(
                                            {'subitem_geolocation_place_text': item.json[new_key][i].pop('subitem_1551256775293')})
                                    else:
                                        item.json[new_key][i]['subitem_geolocation_place'] = \
                                                [{'subitem_geolocation_place_text': item.json[new_key][i].pop('subitem_1551256775293')}]
                                # geolocation point
                                if 'subitem_1551256778926' in subitem:
                                    item.json[new_key][i]['subitem_geolocation_point'] = {}
                                    if len(item.json[new_key][i]['subitem_1551256778926']) > 0:
                                        if 'subitem_1551256783928' in subitem['subitem_1551256778926'][0]:
                                            item.json[new_key][i]['subitem_geolocation_point']['subitem_point_longitude'] = \
                                                    item.json[new_key][i]['subitem_1551256778926'][0].pop('subitem_1551256783928')
                                        if 'subitem_1551256814806' in subitem['subitem_1551256778926'][0]:
                                            item.json[new_key][i]['subitem_geolocation_point']['subitem_point_latitude'] = \
                                                    item.json[new_key][i]['subitem_1551256778926'][0].pop('subitem_1551256814806')
                                    item.json[new_key][i].pop('subitem_1551256778926')
                                # geolocation box
                                if 'subitem_1551256822219' in subitem:
                                    item.json[new_key][i]['subitem_geolocation_box'] = {}
                                    if len(item.json[new_key][i]['subitem_1551256822219']) > 0:
                                        if 'subitem_1551256824945' in subitem['subitem_1551256822219'][0]:
                                            item.json[new_key][i]['subitem_geolocation_box']['subitem_west_longitude'] = \
                                                    item.json[new_key][i]['subitem_1551256822219'][0].pop('subitem_1551256824945')
                                        if 'subitem_1551256831892' in subitem['subitem_1551256822219'][0]:
                                            item.json[new_key][i]['subitem_geolocation_box']['subitem_east_longitude'] = \
                                                    item.json[new_key][i]['subitem_1551256822219'][0].pop('subitem_1551256831892')
                                        if 'subitem_1551256834732' in subitem['subitem_1551256822219'][0]:
                                            item.json[new_key][i]['subitem_geolocation_box']['subitem_south_latitude'] = \
                                                    item.json[new_key][i]['subitem_1551256822219'][0].pop('subitem_1551256834732')
                                        if 'subitem_1551256840435' in subitem['subitem_1551256822219'][0]:
                                            item.json[new_key][i]['subitem_geolocation_box']['subitem_north_latitude'] = \
                                                    item.json[new_key][i]['subitem_1551256822219'][0].pop('subitem_1551256840435')
                                    item.json[new_key][i].pop('subitem_1551256822219')
                            # records_metadata
                            for i, subitem in enumerate(rec.json[new_key]['attribute_value_mlt']):
                                # geolocation place
                                if 'subitem_1551256842196' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_place'] = \
                                            rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256842196')
                                    for j, subplace in enumerate(rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_place']):
                                        if 'subitem_1570008213846' in subplace:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_place'][j]['subitem_geolocation_place_text'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_place'][j].pop('subitem_1570008213846')
                                if 'subitem_1551256775293' in subitem:
                                    if 'subitem_geolocation_place' in rec.json[new_key]['attribute_value_mlt'][i]:
                                        rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_place'].append(
                                            {'subitem_geolocation_place_text': rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256775293')})
                                    else:
                                        rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_place'] = \
                                                [{'subitem_geolocation_place_text': rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256775293')}]
                                # geolocation point
                                if 'subitem_1551256778926' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_point'] = {}
                                    if len(rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256778926']) > 0:
                                        if 'subitem_1551256783928' in subitem['subitem_1551256778926'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_point']['subitem_point_longitude'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256778926'][0].pop('subitem_1551256783928')
                                        if 'subitem_1551256814806' in subitem['subitem_1551256778926'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_point']['subitem_point_latitude'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256778926'][0].pop('subitem_1551256814806')
                                    rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256778926')
                                # geolocation box
                                if 'subitem_1551256822219' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_box'] = {}
                                    if len(rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256822219']) > 0:
                                        if 'subitem_1551256824945' in subitem['subitem_1551256822219'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_box']['subitem_west_longitude'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256822219'][0].pop('subitem_1551256824945')
                                        if 'subitem_1551256831892' in subitem['subitem_1551256822219'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_box']['subitem_east_longitude'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256822219'][0].pop('subitem_1551256831892')
                                        if 'subitem_1551256834732' in subitem['subitem_1551256822219'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_box']['subitem_south_latitude'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256822219'][0].pop('subitem_1551256834732')
                                        if 'subitem_1551256840435' in subitem['subitem_1551256822219'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_geolocation_box']['subitem_north_latitude'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256822219'][0].pop('subitem_1551256840435')
                                    rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256822219')
                        # funding reference
                        elif item_key_data[old_key][name_key] == 'funding_reference':
                            # item_metadata
                            for i, subitem in enumerate(item.json[new_key]):
                                # funder identifiers
                                if 'subitem_1551256454316' in subitem:
                                    item.json[new_key][i]['subitem_funder_identifiers'] = {}
                                    if len(subitem['subitem_1551256454316']) > 0:
                                        if 'subitem_1551256614960' in subitem['subitem_1551256454316'][0]:
                                            item.json[new_key][i]['subitem_funder_identifiers']['subitem_funder_identifier'] = \
                                                    item.json[new_key][i]['subitem_1551256454316'][0].pop('subitem_1551256614960')
                                        if 'subitem_1551256619706' in subitem['subitem_1551256454316'][0]:
                                            item.json[new_key][i]['subitem_funder_identifiers']['subitem_funder_identifier_type'] = \
                                                    item.json[new_key][i]['subitem_1551256454316'][0].pop('subitem_1551256619706')
                                    item.json[new_key][i].pop('subitem_1551256454316')
                                # funder names
                                if 'subitem_1551256462220' in subitem:
                                    item.json[new_key][i]['subitem_funder_names'] = []
                                    for subname in item.json[new_key][i]['subitem_1551256462220']:
                                        temp = {}
                                        if 'subitem_1551256653656' in subname:
                                            temp['subitem_funder_name'] = subname['subitem_1551256653656']
                                        if 'subitem_1551256657859' in subname:
                                            temp['subitem_funder_name_language'] = subname['subitem_1551256657859']
                                        item.json[new_key][i]['subitem_funder_names'].append(temp)
                                    item.json[new_key][i].pop('subitem_1551256462220')
                                # award numbers
                                if 'subitem_1551256665850' in subitem:
                                    item.json[new_key][i]['subitem_award_numbers'] = {}
                                    if len(subitem['subitem_1551256665850']) > 0:
                                        if 'subitem_1551256671920' in subitem['subitem_1551256665850'][0]:
                                            item.json[new_key][i]['subitem_award_numbers']['subitem_award_number'] = \
                                                    item.json[new_key][i]['subitem_1551256665850'][0].pop('subitem_1551256671920')
                                        if 'subitem_1551256679403' in subitem['subitem_1551256665850'][0]:
                                            item.json[new_key][i]['subitem_award_numbers']['subitem_award_uri'] = \
                                                    item.json[new_key][i]['subitem_1551256665850'][0].pop('subitem_1551256679403')
                                    item.json[new_key][i].pop('subitem_1551256665850')
                                # funder titles
                                if 'subitem_1551256688098' in subitem:
                                    item.json[new_key][i]['subitem_award_titles'] = []
                                    for subname in item.json[new_key][i]['subitem_1551256688098']:
                                        temp = {}
                                        if 'subitem_1551256691232' in subname:
                                            temp['subitem_award_title'] = subname['subitem_1551256691232']
                                        if 'subitem_1551256694883' in subname:
                                            temp['subitem_award_title_language'] = subname['subitem_1551256694883']
                                        item.json[new_key][i]['subitem_award_titles'].append(temp)
                                    item.json[new_key][i].pop('subitem_1551256688098')
                            # records_metadata
                            for i, subitem in enumerate(rec.json[new_key]['attribute_value_mlt']):
                                # funder identifiers
                                if 'subitem_1551256454316' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_funder_identifiers'] = {}
                                    if len(subitem['subitem_1551256454316']) > 0:
                                        if 'subitem_1551256614960' in subitem['subitem_1551256454316'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_funder_identifiers']['subitem_funder_identifier'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256454316'][0].pop('subitem_1551256614960')
                                        if 'subitem_1551256619706' in subitem['subitem_1551256454316'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_funder_identifiers']['subitem_funder_identifier_type'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256454316'][0].pop('subitem_1551256619706')
                                    rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256454316')
                                # funder names
                                if 'subitem_1551256462220' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_funder_names'] = []
                                    for subname in rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256462220']:
                                        temp = {}
                                        if 'subitem_1551256653656' in subname:
                                            temp['subitem_funder_name'] = subname['subitem_1551256653656']
                                        if 'subitem_1551256657859' in subname:
                                            temp['subitem_funder_name_language'] = subname['subitem_1551256657859']
                                        rec.json[new_key]['attribute_value_mlt'][i]['subitem_funder_names'].append(temp)
                                    rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256462220')
                                # award numbers
                                if 'subitem_1551256665850' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_award_numbers'] = {}
                                    if len(subitem['subitem_1551256665850']) > 0:
                                        if 'subitem_1551256671920' in subitem['subitem_1551256665850'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_award_numbers']['subitem_award_number'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256665850'][0].pop('subitem_1551256671920')
                                        if 'subitem_1551256679403' in subitem['subitem_1551256665850'][0]:
                                            rec.json[new_key]['attribute_value_mlt'][i]['subitem_award_numbers']['subitem_award_uri'] = \
                                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256665850'][0].pop('subitem_1551256679403')
                                    rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256665850')
                                # funder titles
                                if 'subitem_1551256688098' in subitem:
                                    rec.json[new_key]['attribute_value_mlt'][i]['subitem_award_titles'] = []
                                    for subname in rec.json[new_key]['attribute_value_mlt'][i]['subitem_1551256688098']:
                                        temp = {}
                                        if 'subitem_1551256691232' in subname:
                                            temp['subitem_award_title'] = subname['subitem_1551256691232']
                                        if 'subitem_1551256694883' in subname:
                                            temp['subitem_award_title_language'] = subname['subitem_1551256694883']
                                        rec.json[new_key]['attribute_value_mlt'][i]['subitem_award_titles'].append(temp)
                                    rec.json[new_key]['attribute_value_mlt'][i].pop('subitem_1551256688098')
                        else:
                            # item_metadata
                            for i, subitem in enumerate(item.json[new_key]):
                                change_subitem_key(item.json[new_key][i], subitem, subitem_change_table)
                            # records_metadata
                            for i, subitem in enumerate(rec.json[new_key]['attribute_value_mlt']):
                                change_subitem_key(rec.json[new_key]['attribute_value_mlt'][i], subitem, subitem_change_table)
                if update_flag:
                    flag_modified(item, "json")
                    flag_modified(rec, "json")
                    db.session.merge(item)
                    db.session.merge(rec)
                    db.session.commit()
                    success_count += 1
                else:
                    skip_count += 1
            except Exception as ex:
                print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Update {} is fail.'.format(item.id))
                print(ex)
                db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'Update metadata finish. Updated {} items. Skipped {} items.'.format(success_count, skip_count))
        print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Fix issue 47128 is success.')
    except Exception as e:
        print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Fix issue 47128 is fail.')
        print(e)

if __name__ == '__main__':
    main()