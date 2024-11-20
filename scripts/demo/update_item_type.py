import json
import pickle
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import desc

from properties.resource_type import resource_type
from properties.property_func import get_select_value

from invenio_db import db
from weko_records.api import ItemTypes, ItemTypeProps 
from weko_records.models import ItemTypeProperty, ItemTypeMapping

# language
lang_key = [
    'subitem_alternative_title_language',
    'bibliographic_titleLang',
    'subitem_conference_name_language',
    'subitem_conference_sponsor_language',
    'subitem_conference_date_language',
    'subitem_conference_venue_language',
    'subitem_conference_place_language',
    'lang',
    'familyNameLang',
    'givenNameLang',
    'contributorAlternativeLang',
    'contributorAffiliationNameLang',
    'creatorAlternativeLang',
    'creatorNameLang',
    'affiliationNameLang',
    'subitem_degreegrantor_language',
    'subitem_degreename_language',
    'subitem_description_language',
    'subitem_distributor_language',
    'alternativeLang',
    'nameLang',
    'subitem_funder_name_language',
    'subitem_award_title_language',
    'subitem_heading_language',
    'subitem_link_language',
    'subitem_publisher_language',
    'subitem_relation_name_language',
    'rightHolderLanguage',
    'subitem_rights_language',
    'subitem_source_title_language',
    'subitem_subject_language',
    'subitem_temporal_language',
    'subitem_text_language',
    'subitem_textarea_language',
    'subitem_title_language',
    'subitem_geographic_coverage_language',
    'subitem_related_publication_title_language',
    'subitem_related_study_title_language',
    'subitem_sampling_procedure_language',
    'subitem_series_language',
    'subitem_study_id_language',
    'subitem_topic_language',
    'subitem_universe_language',
    'subitem_record_name_language',
    'subitem_checkbox_language',
    'subitem_radio_language',
    'subitem_select_language',
    'subitem_1586311767281',
    'subitem_1522650068558',
    'subitem_1592472785698',
    'subitem_1592383877507',
    'subitem_1596609827068',
    'subitem_1586419462229',
    'subitem_1551255710277',
    'subitem_1592369407829',
    'subitem_1592383527694',
    'subitem_1587462183075',
    'subitem_1551255592625',
    'subitem_1551255907416',
    'subitem_1551255964991',
    'subitem_1551256007414',
    'subitem_1551256055588',
    'subitem_1551256259899',
    'subitem_1586228490356',
    'subitem_1551256513476',
    'subitem_1551256657859',
    'subitem_1551256694883',
    'subitem_1551257279831',
    'subitem_1551257316910',
    'subitem_1551257343979',
    'subitem_1551257375939',
    'subitem_1551261546333',
    'subitem_1596610501381',
    'subitem_1596608975087',
    'subitem_1551257257683',
    'subitem_1551256920086',
    'subitem_1551257323812',
    'subitem_1596608609366',
    'subitem_1522399416691',
    'subitem_1522721910626',
    'subitem_1592462961468',
    'subitem_1592367225536',
    'subitem_1602142815328',
    'subitem_1602144578572',
    'subitem_1602213570623',
    'subitem_1602214163661',
    'subitem_1602214559588',
    'subitem_1586316971117',
    'subitem_1522650717957',
    'subitem_1523320867455',
    'subitem_1599711645590',
    'subitem_1599711686511',
    'subitem_1599711745532',
    'subitem_1599711775943',
    'subitem_1599711803382',
    'subitem_1551256350188',
    'subitem_1551256047619',
    'subitem_1522658018441',
    'subitem_1551256129013',
    'subitem_1551257047388',
    'subitem_1522300295150',
    'subitem_1586221269735',
    'subitem_1586253400535',
    'subitem_1588833323804',
    'subitem_1596611020493',
    'subitem_1551255721061',
    'subitem_1551255648112',
    'subitem_1565671149650',
    'subitem_1522299896455',
]
lang_insert_key = 'en'
# resource type
resource_type_key = ['resourcetype']
resource_type_insert_key = 'dataset'
jpcoar_2_resource_type = [
    'aggregated data',
    'clinical trial data',
    'compiled data',
    'encoded data',
    'experimental data',
    'genomic data',
    'geospatial data',
    'laboratory notebook',
    'measurement and test data',
    'observational data',
    'recorded data',
    'simulation data',
    'survey data'
]
# relation
relation_type_key = [
    'subitem_relation_type',
    'subitem_1522306207484',
    'subitem_1551256388439',
    'subitem_1592385010522'
]
relation_type_insert_key = 'isSourceOf'
relation_type = [
    'isCitedBy',
    'Cites'
]
# change text for identifier registration
change_id_reg_text_key = [
    'subitem_system_id_rg_doi_type',
    'subitem_identifier_reg_type'
]
# change text for relation
change_relation_text_key = [
    'subitem_relation_type_select',
    'subitem_1522306382014'
]

def main():
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '=== Update item type start. ===')

    s_identifier_dc_data = {
        'identifier': {
            '@value': 'subitem_systemidt_identifier'
        }
    }
    s_identifier_ddi_data = {
        "stdyDscr": {
            "citation": {
                "holdings": {
                    "@attributes": {
                        "URI": "subitem_systemidt_identifier"
                    }
                }
            }
        }
    }
    # item type
    itemtypes = ItemTypes.get_all(True)
    for it in itemtypes:
        try:
            _mapping_update_falg = False
            _update_flag = False
            _schema = it.schema
            _form = it.form
            _render = it.render
            _id = it.id
            # mapping
            try:
                itMapping = ItemTypeMapping.query.filter_by(item_type_id=_id).order_by(desc(ItemTypeMapping.created)).first()
                if itMapping:
                    _mapping = pickle.loads(pickle.dumps(itMapping.mapping, -1))
                    
                    if 'system_identifier_uri' in _mapping:
                        if not _mapping['system_identifier_uri'].get('oai_dc_mapping'):
                            _mapping['system_identifier_uri']['oai_dc_mapping'] = s_identifier_dc_data
                            _mapping_update_falg = True
                        if not _mapping['system_identifier_uri'].get('ddi_mapping'):
                            _mapping['system_identifier_uri']['ddi_mapping'] = s_identifier_ddi_data
                            _mapping_update_falg = True
                    if 'system_identifier_doi' in _mapping:
                        if not _mapping['system_identifier_doi'].get('oai_dc_mapping'):
                            _mapping['system_identifier_doi']['oai_dc_mapping'] = s_identifier_dc_data
                            _mapping_update_falg = True
                        if not _mapping['system_identifier_doi'].get('ddi_mapping'):
                            _mapping['system_identifier_doi']['ddi_mapping'] = s_identifier_ddi_data
                            _mapping_update_falg = True
                    if 'system_identifier_hdl' in _mapping:
                        if not _mapping['system_identifier_hdl'].get('oai_dc_mapping'):
                            _mapping['system_identifier_hdl']['oai_dc_mapping'] = s_identifier_dc_data
                            _mapping_update_falg = True
                        if not _mapping['system_identifier_hdl'].get('ddi_mapping'):
                            _mapping['system_identifier_hdl']['ddi_mapping'] = s_identifier_ddi_data
                            _mapping_update_falg = True
                    if _mapping_update_falg:
                        with db.session.begin_nested():
                            itMapping.mapping = _mapping
                            flag_modified(itMapping, 'mapping')
                            db.session.merge(itMapping)
                        db.session.commit()
                        print(
                            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                            '* Update item type mapping {}({}) to db is success.'.format(it.item_type_name.name, it.id))
            except Exception as e:
                db.session.rollback()
                print(
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    '* Update item type mapping {}({}) to db is fail.'.format(it.item_type_name.name, it.id),
                    e)
            # schema
            if 'properties' in _schema:
                for k, v in _schema['properties'].items():
                    _update_flag = _update_flag | update_schema(v)
            # form
            for item_obj in _form:
                _update_flag = _update_flag | update_form(item_obj)
            # render
            if 'schemaeditor' in _render \
                    and 'schema' in _render['schemaeditor']:
                for k, v in _render['schemaeditor']['schema'].items():
                    _update_flag = _update_flag | update_schema(v)
            if 'table_row_map' in _render:
                if 'schema' in _render['table_row_map'] \
                        and 'properties' in _render['table_row_map']['schema']:
                    for k, v in _render['table_row_map']['schema']['properties'].items():
                        _update_flag = _update_flag | update_schema(v)
                if 'form' in _render['table_row_map']:
                    for item_obj in _render['table_row_map']['form']:
                        _update_flag = _update_flag | update_form(item_obj)
                if 'mapping' in _render['table_row_map']:
                    if 'system_identifier_uri' in _render['table_row_map']['mapping']:
                        if not _render['table_row_map']['mapping']['system_identifier_uri'].get('oai_dc_mapping'):
                            _render['table_row_map']['mapping']['system_identifier_uri']['oai_dc_mapping'] = s_identifier_dc_data
                            _update_flag = True
                        if not _render['table_row_map']['mapping']['system_identifier_uri'].get('ddi_mapping'):
                            _render['table_row_map']['mapping']['system_identifier_uri']['ddi_mapping'] = s_identifier_ddi_data
                            _update_flag = True
                    if 'system_identifier_doi' in _render['table_row_map']['mapping']:
                        if not _render['table_row_map']['mapping']['system_identifier_doi'].get('oai_dc_mapping'):
                            _render['table_row_map']['mapping']['system_identifier_doi']['oai_dc_mapping'] = s_identifier_dc_data
                            _update_flag = True
                        if not _render['table_row_map']['mapping']['system_identifier_doi'].get('ddi_mapping'):
                            _render['table_row_map']['mapping']['system_identifier_doi']['ddi_mapping'] = s_identifier_ddi_data
                            _update_flag = True
                    if 'system_identifier_hdl' in _render['table_row_map']['mapping']:
                        if not _render['table_row_map']['mapping']['system_identifier_hdl'].get('oai_dc_mapping'):
                            _render['table_row_map']['mapping']['system_identifier_hdl']['oai_dc_mapping'] = s_identifier_dc_data
                            _update_flag = True
                        if not _render['table_row_map']['mapping']['system_identifier_hdl'].get('ddi_mapping'):
                            _render['table_row_map']['mapping']['system_identifier_hdl']['ddi_mapping'] = s_identifier_ddi_data
                            _update_flag = True
            if _update_flag:
                try:
                    with db.session.begin_nested():
                        it.schema = _schema
                        it.form = _form
                        it.render = _render
                        flag_modified(it, 'schema')
                        flag_modified(it, 'form')
                        flag_modified(it, 'render')
                        db.session.merge(it)
                    db.session.commit()
                    print(
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'Update item type {}({}) to db is success.'.format(it.item_type_name.name, it.id))
                except Exception as e:
                    db.session.rollback()
                    print(
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'Update item type {}({}) to db is fail.'.format(it.item_type_name.name, it.id),
                        e)
        except Exception as ex:
            print(
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'Change item type {}({}) data is fail.'.format(it.item_type_name.name, it.id),
                ex)
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '=== Update item type end. ===')
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '=== Update property start. ===')
    
    # property
    props = ItemTypeProps.get_records([])
    for prop in props:
        try:
            _update_flag = False
            _schema = prop.schema
            _form = prop.form
            _forms = prop.forms
            _update_flag = _update_flag | update_schema(_schema)
            _update_flag = _update_flag | update_form(_form)
            _update_flag = _update_flag | update_form(_forms)
            if _update_flag:
                try:
                    with db.session.begin_nested():
                        prop.schema = _schema
                        prop.form = _form
                        prop.forms = _forms
                        flag_modified(prop, 'schema')
                        flag_modified(prop, 'form')
                        flag_modified(prop, 'forms')
                        db.session.merge(prop)
                    db.session.commit()
                    print(
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'Update propery {}({}) to db is success.'.format(prop.name, prop.id))
                except Exception as e:
                    db.session.rollback()
                    print(
                        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'Update propery {}({}) to db is fail.'.format(prop.name, prop.id),
                        e)
        except Exception as ex:
            print(
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'Change property {}({}) data is fail.'.format(prop.name, prop.id),
                ex)
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), '=== Update property end. ===')

def update_schema(value):
    update_flag = False
    if 'properties' in value:
        for k, v in value['properties'].items():
            if 'properties' in v or 'items' in v:
                update_flag = update_flag | update_schema(v)
            if 'enum' in v:
                # lang
                if k in lang_key:
                    for i, d in enumerate(v['enum']):
                        if d == 'ja-Latn':
                            break
                        elif d == lang_insert_key:
                            value['properties'][k]['enum'].insert(i, 'ja-Latn')
                            if 'currentEnum' in v:
                                value['properties'][k]['currentEnum'].insert(i, 'ja-Latn')
                            update_flag = True
                            break
                # resource type
                if k in resource_type_key:
                    if v['enum'].count(jpcoar_2_resource_type[0]) == 0:
                        for i, d in enumerate(v['enum']):
                            if d == resource_type_insert_key:
                                for index, rt in enumerate(jpcoar_2_resource_type):
                                    value['properties'][k]['enum'].insert(i + index, rt)
                                    if 'currentEnum' in v:
                                        value['properties'][k]['currentEnum'].insert(i + index - 1, rt)
                                update_flag = True
                                break
                    if v['enum'].count(jpcoar_2_resource_type[0]) > 1:
                        value['properties'][k]['enum'].reverse()
                        if 'currentEnum' in v:
                            value['properties'][k]['currentEnum'].reverse()
                        for rt in jpcoar_2_resource_type:
                            if value['properties'][k]['enum'].count(rt) > 1:
                                value['properties'][k]['enum'].pop(value['properties'][k]['enum'].index(rt))
                            if 'currentEnum' in v and value['properties'][k]['currentEnum'].count(rt) > 1:
                                value['properties'][k]['currentEnum'].pop(value['properties'][k]['currentEnum'].index(rt))
                        value['properties'][k]['enum'].reverse()
                        if 'currentEnum' in v:
                            value['properties'][k]['currentEnum'].reverse()
                        update_flag = True
                    else:
                        pass
                # relation type
                if k in relation_type_key:
                    for i, d in enumerate(v['enum']):
                        if d == relation_type_insert_key and len(v['enum']) > i + 1:
                            break
                        elif d == relation_type_insert_key and len(v['enum']) == i + 1:
                            for index, ref in enumerate(relation_type):
                                value['properties'][k]['enum'].insert(i + index + 1, ref)
                                if 'currentEnum' in v:
                                    value['properties'][k]['currentEnum'].insert(i + index + 1, ref)
                            update_flag = True
                            break
                # change text
                if k in change_id_reg_text_key:
                    for i, d in enumerate(v['enum']):
                        if d in ['PMID（現在不使用）', 'PMID(現在不使用)', 'PMID']:
                            value['properties'][k]['enum'][i] = 'PMID'
                            update_flag = True
                            break
                if k in change_relation_text_key:
                    for i, d in enumerate(v['enum']):
                        if d in ['ISSN（非推奨）', 'ISSN(非推奨)', 'ISSN']:
                            value['properties'][k]['enum'][i] = 'ISSN【非推奨】'
                            update_flag = True
                            break
        return update_flag
    elif 'items' in value:
        return update_schema(value['items'])
    else:
        return update_flag

def update_form(form_data):
    update_flag = False
    if isinstance(form_data, list):
        for i, value in enumerate(form_data):
            if 'titleMap' in value:
                if 'key' in value:
                    subitem_key = value['key'].split('.')[-1]
                    # lang
                    if subitem_key in lang_key:
                        for map_index, d in enumerate(value['titleMap']):
                            if d['name'] == 'ja-Latn':
                                break
                            elif d['name'] == lang_insert_key:
                                form_data[i]['titleMap'].insert(map_index, {'name': 'ja-Latn', 'value': 'ja-Latn'})
                                update_flag = True
                                break
                    # resource type
                    if subitem_key in resource_type_key:
                        rt0 = jpcoar_2_resource_type[0]
                        if value['titleMap'].count({'name': rt0, 'value': rt0}) == 0:
                            for map_index, d in enumerate(value['titleMap']):
                                if d['name'] in jpcoar_2_resource_type:
                                    break
                                elif d['name'] == resource_type_insert_key:
                                    for jpcoar_index, rt in enumerate(jpcoar_2_resource_type):
                                        form_data[i]['titleMap'].insert(map_index + jpcoar_index, {'name': rt, 'value': rt})
                                    update_flag = True
                                    break
                        if value['titleMap'].count({'name': rt0, 'value': rt0}) > 1:
                            form_data[i]['titleMap'].reverse()
                            for rt in jpcoar_2_resource_type:
                                if form_data[i]['titleMap'].count({'name': rt, 'value': rt}) > 1:
                                    form_data[i]['titleMap'].pop(form_data[i]['titleMap'].index({'name': rt, 'value': rt}))
                            form_data[i]['titleMap'].reverse()
                            update_flag = True
                        else:
                            pass
                    # relation type
                    if subitem_key in relation_type_key:
                        for map_index, d in enumerate(value['titleMap']):
                            if d['name'] == relation_type_insert_key and len(value['titleMap']) > map_index + 1:
                                break
                            elif d['name'] == relation_type_insert_key and len(value['titleMap']) == map_index + 1:
                                for ref_index, ref in enumerate(relation_type):
                                    form_data[i]['titleMap'].insert(map_index + ref_index + 1, {'name': ref, 'value': ref})
                                update_flag = True
                                break
                    # change text
                    if subitem_key in change_id_reg_text_key:
                        for map_index, d in enumerate(value['titleMap']):
                            if d['name'] in ['PMID（現在不使用）', 'PMID(現在不使用)', 'PMID']:
                                form_data[i]['titleMap'][map_index] = {'name': 'PMID', 'value': 'PMID'}
                                update_flag = True
                                break
                    if subitem_key in change_relation_text_key:
                        for map_index, d in enumerate(value['titleMap']):
                            if d['name'] in ['ISSN（非推奨）', 'ISSN(非推奨)', 'ISSN']:
                                form_data[i]['titleMap'][map_index] = {'name': 'ISSN【非推奨】', 'value': 'ISSN【非推奨】'}
                                update_flag = True
                                break
                if 'accessrole' in value['key']:
                    if 'type' in value:
                        if value['type'] == "radios":
                            form_data[i]['onChange'] = "accessRoleChange()"
                            update_flag = True
                            break
            elif 'items' in value:
                update_flag = update_flag | update_form(form_data[i]['items'])
    elif isinstance(form_data, dict) and 'items' in form_data:
        update_flag = update_flag | update_form(form_data['items'])
    return update_flag

if __name__ == '__main__':
    main()