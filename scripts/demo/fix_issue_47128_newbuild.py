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

def main():
    item_key_data = {
        'item_1551264308487': {'change_subitem_key': False, 'prop_name': 'title'},
        'item_1551264326373': {'change_subitem_key': False, 'prop_name': 'alternative_title'},
        'item_1551265002099': {'change_subitem_key': False, 'prop_name': 'language'},
        'item_1592880868902': {'change_subitem_key': False, 'prop_name': 'text'},
        'item_1593074267803': {'change_subitem_key': False, 'prop_name': 'creator'},
        'item_1600078832557': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1551264340087': {'change_subitem_key': False, 'prop_name': 'creator'},
        'item_1551264418667': {'change_subitem_key': False, 'prop_name': 'contributor'},
        'item_1551264447183': {'change_subitem_key': False, 'prop_name': 'access_rights'},
        'item_1551264605515': {'change_subitem_key': False, 'prop_name': 'apc'},
        'item_1551264629907': {'change_subitem_key': False, 'prop_name': 'rights'},
        'item_1551264767789': {'change_subitem_key': False, 'prop_name': 'rights_holder'},
        'item_1551264822581': {'change_subitem_key': False, 'prop_name': 'subject'},
        'item_1551264846237': {'change_subitem_key': False, 'prop_name': 'description'},
        'item_1551264917614': {'change_subitem_key': False, 'prop_name': 'publisher'},
        'item_1551264974654': {'change_subitem_key': False, 'prop_name': 'date'},
        'item_1551265032053': {'change_subitem_key': False, 'prop_name': 'resource_type'},
        'item_1551265118680': {'change_subitem_key': False, 'prop_name': 'version_type'},
        'item_1551265227803': {'change_subitem_key': False, 'prop_name': 'relation'},
        'item_1551265302120': {'change_subitem_key': False, 'prop_name': 'temporal'},
        'item_1551265409089': {'change_subitem_key': False, 'prop_name': 'source_identifier'},
        'item_1551265438256': {'change_subitem_key': False, 'prop_name': 'source_title'},
        'item_1551265463411': {'change_subitem_key': False, 'prop_name': 'volume_number'},
        'item_1551265520160': {'change_subitem_key': False, 'prop_name': 'issue_number'},
        'item_1551265553273': {'change_subitem_key': False, 'prop_name': 'number_of_pages'},
        'item_1551265569218': {'change_subitem_key': False, 'prop_name': 'page_start'},
        'item_1551265603279': {'change_subitem_key': False, 'prop_name': 'page_end'},
        'item_1551265738931': {'change_subitem_key': False, 'prop_name': 'dissertation_number'},
        'item_1551265790591': {'change_subitem_key': False, 'prop_name': 'degree_name'},
        'item_1551265811989': {'change_subitem_key': False, 'prop_name': 'date_granted'},
        'item_1551265903092': {'change_subitem_key': False, 'prop_name': 'degree_grantor'},
        'item_1570703628633': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1581495656289': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1570704310462': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1581495994272': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1570704547962': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1581496338731': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1570704756060': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1581496403480': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1551266003379': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1581496532660': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1581496606199': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1581496684230': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1581496789900': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1581496994580': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1551265973055': {'change_subitem_key': False, 'prop_name': 'conference'},
        'item_1581497221445': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1551265075370': {'change_subitem_key': False, 'prop_name': 'version'},
        'item_1581497272891': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1570069138259': {'change_subitem_key': False, 'prop_name': 'file'},
        'item_1581495499605': {'change_subitem_key': False, 'prop_name': 'identifier_registration'},
        'item_1551265326081': {'change_subitem_key': True, 'prop_name': 'geolocation'},
        'item_1551265385290': {'change_subitem_key': True, 'prop_name': 'funding_reference'},
        'item_1570705072577': {'change_subitem_key': True, 'prop_name': 'geolocation'},
        'item_1570068313185': {'change_subitem_key': True, 'prop_name': 'geolocation'}
    }
    id_match_key = {}
    prop_id_change = {
        'cus_91': 'cus_1022',
        'cus_93': 'cus_1021'
    }
    print(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'Fix issue 47128 is start. (newbuild)')
    try:
        item_types = db.session.query(ItemType).filter(ItemType.harvesting_type==True).filter(ItemType.id==12).all()
        for item_type in item_types:
            # get/update item key
            try:
                # update property id
                for form in enumerate(item_type.render['table_row_map']['form']):
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
                        item_key_data[item_key]['prop_name'],
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
                print(f"[FIX][fix_issue47128_newbuild.py]item_type:{item_type.id}")
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
                    print(f"[FIX][fix_issue47128_newbuild.py]item_type_mapping:{mapping.id}")
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
                print(
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    'Reload properties of item type ({}) and update item type mapping is success.'.format(item_type.id))
            except Exception as ex:
                db.session.rollback()
                print(
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    'Reload properties of item type ({}) and update item type mapping is fail.'.format(item_type.id))
                print(ex)

        print('IMPORTANT: item key change table: {}'.format(id_match_key))
        item_type_id_list = [str(i.id) for i in item_types]
        item_list = db.session.query(ItemMetadata).filter(ItemMetadata.item_type_id.in_(item_type_id_list)).all()
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
                    else:
                        update_flag = True

                    item.json[new_key] = item.json.pop(old_key)
                    rec.json[new_key] = rec.json.pop(old_key)
                    if item_key_data[old_key]['change_subitem_key']:
                        # geo location
                        if item_key_data[old_key]['prop_name'] == 'geolocation':
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
                        elif item_key_data[old_key]['prop_name'] == 'funding_reference':
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
                if update_flag:
                    flag_modified(item, "json")
                    flag_modified(rec, "json")
                    db.session.merge(item)
                    db.session.merge(rec)
                    db.session.commit()
                    print(f"[FIX][fix_issue47128_newbuild.py]item_metadata:{item.id}")
                    print(f"[FIX][fix_issue47128_newbuild.py]records_metadata:{rec.id}")
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