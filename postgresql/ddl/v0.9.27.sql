

DELETE FROM item_type_property WHERE id=121;
DELETE FROM item_type_property WHERE id=122;
DELETE FROM item_type_property WHERE id=124;
DELETE FROM item_type_property WHERE id=132;

-- LINK = '1044'
UPDATE item_type SET render=replace(render::text,'cus_142"','cus_1044"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1587693279322','subitem_link_url')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1587650325204','subitem_link_text')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1587693278490','subitem_link_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1587693278490','subitem_link_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1587693278490','subitem_link_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1587693278490','subitem_link_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1587693278490','subitem_link_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1587693278490','subitem_link_language')::jsonb;

DELETE FROM item_type_property WHERE id=142;

-- TITLE = '1001'
UPDATE item_type SET render=replace(render::text,'cus_67"','cus_1001"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551255647225','subitem_title')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551255647225','subitem_title')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551255647225','subitem_title')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255647225','subitem_title')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551255648112','subitem_title_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551255648112','subitem_title_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551255648112','subitem_title_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255648112','subitem_title_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551255647225','subitem_title')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551255648112','subitem_title_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551255647225','subitem_title')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551255648112','subitem_title_language')::jsonb;

DELETE FROM item_type_property WHERE id=67;

-- TEXT = '1042'
UPDATE item_type SET render=replace(render::text,'cus_137"','cus_1042"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1586228465211','subitem_text_value')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1586228465211','subitem_text_value')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1586228465211','subitem_text_value')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1586228465211','subitem_text_value')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_158622849035','subitem_text_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_158622849035','subitem_text_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_158622849035','subitem_text_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_158622849035','subitem_text_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1586228465211','subitem_text_value')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_158622849035','subitem_text_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1586228465211','subitem_text_value')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_158622849035','subitem_text_language')::jsonb;

DELETE FROM item_type_property WHERE id=137;

-- THUMBNAIL = '1037'
UPDATE item_type SET render=replace(render::text,'cus_120"','cus_1037"')::jsonb;
DELETE FROM item_type_property WHERE id=120;

-- TEXTAREA = '1043'
UPDATE item_type SET render=replace(render::text,'cus_139"','cus_1043"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1586253392325','subitem_textarea_value')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1586253392325','subitem_textarea_value')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1586253392325','subitem_textarea_value')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1586253392325','subitem_textarea_value')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_158625340053','subitem_textarea_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_158625340053','subitem_textarea_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_158625340053','subitem_textarea_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_158625340053','subitem_textarea_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1586253392325','subitem_textarea_value')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_158625340053','subitem_textarea_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1586253392325','subitem_textarea_value')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_158625340053','subitem_textarea_language')::jsonb;

DELETE FROM item_type_property WHERE id=139;

-- APC = '1006'
UPDATE item_type SET render=replace(render::text,'cus_27"','cus_1006"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523260933860','subitem_apc')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523260933860','subitem_apc')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523260933860','subitem_apc')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523260933860','subitem_apc')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1523260933860','subitem_apc')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1523260933860','subitem_apc')::jsonb;

DELETE FROM item_type_property WHERE id=27;

-- IDENTIFIER_REGISTRATION = '1018'
UPDATE item_type SET render=replace(render::text,'cus_16"','cus_1018"')::jsonb;
DELETE FROM item_type_property WHERE id=16;

-- NUMBER_OF_PAGES = '126'
UPDATE item_type SET render=replace(render::text,'cus_85"','cus_126"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb;

DELETE FROM item_type_property WHERE id=85;

-- RESOURCE_TYPE_SIMPLE = '127'
UPDATE item_type SET render=replace(render::text,'cus_177"','cus_127"')::jsonb;
DELETE FROM item_type_property WHERE id=177;

-- S_FILE = '125'  
UPDATE item_type SET render=replace(render::text,'cus_131"','cus_125"')::jsonb;
DELETE FROM item_type_property WHERE id=131;

-- S_IDENTIFIER = '123'
UPDATE item_type SET render=replace(render::text,'cus_130"','cus_123"')::jsonb;
DELETE FROM item_type_property WHERE id=130;

-- SUBJECT = '1009'
UPDATE item_type SET render=replace(render::text,'cus_6"','cus_1009"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523261968819','subitem_subject')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523261968819','subitem_subject')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523261968819','subitem_subject')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523261968819','subitem_subject')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522300048512','subitem_subject_uri')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522300048512','subitem_subject_uri')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522300048512','subitem_subject_uri')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300048512','subitem_subject_uri')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522299896455','subitem_subject_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522299896455','subitem_subject_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522299896455','subitem_subject_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522299896455','subitem_subject_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1523261968819','subitem_subject')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522300048512','subitem_subject_uri')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522299896455','subitem_subject_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1523261968819','subitem_subject')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522300048512','subitem_subject_uri')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522299896455','subitem_subject_language')::jsonb;

DELETE FROM item_type_property WHERE id=6;

-- ALTERNATIVE_TITLE = '1002'
UPDATE item_type SET render=replace(render::text,'cus_69"','cus_1002"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551255720400','subitem_alternative_title')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551255720400','subitem_alternative_title')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551255720400','subitem_alternative_title')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255720400','subitem_alternative_title')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551255720400','subitem_alternative_title')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551255720400','subitem_alternative_title')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb;

DELETE FROM item_type_property WHERE id=69;

-- CONFERENCE = '1034'
UPDATE item_type SET render=replace(render::text,'cus_75"','cus_1034"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711633003','subitem_conference_names')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711633003','subitem_conference_names')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711633003','subitem_conference_names')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711633003','subitem_conference_names')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711636923','subitem_conference_name')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711636923','subitem_conference_name')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711636923','subitem_conference_name')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711636923','subitem_conference_name')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711699392','subitem_conference_date')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711699392','subitem_conference_date')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711699392','subitem_conference_date')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711699392','subitem_conference_date')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711704251','subitem_conference_period')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711704251','subitem_conference_period')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711704251','subitem_conference_period')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711704251','subitem_conference_period')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711758470','subitem_conference_venues')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711758470','subitem_conference_venues')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711758470','subitem_conference_venues')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711758470','subitem_conference_venues')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711769260','subitem_conference_venue')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711769260','subitem_conference_venue')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711769260','subitem_conference_venue')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711769260','subitem_conference_venue')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711788485','subitem_conference_places')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711788485','subitem_conference_places')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711788485','subitem_conference_places')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711788485','subitem_conference_places')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711798761','subitem_conference_place')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711798761','subitem_conference_place')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711798761','subitem_conference_place')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711798761','subitem_conference_place')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1599711813532','subitem_conference_country')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1599711813532','subitem_conference_country')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1599711813532','subitem_conference_country')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711813532','subitem_conference_country')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1599711633003','subitem_conference_names')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711636923','subitem_conference_name')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711699392','subitem_conference_date')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711704251','subitem_conference_period')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711758470','subitem_conference_venues')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711769260','subitem_conference_venue')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711788485','subitem_conference_places')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711798761','subitem_conference_place')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1599711813532','subitem_conference_country')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1599711633003','subitem_conference_names')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711636923','subitem_conference_name')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711699392','subitem_conference_date')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711704251','subitem_conference_period')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711758470','subitem_conference_venues')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711769260','subitem_conference_venue')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711788485','subitem_conference_places')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711798761','subitem_conference_place')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1599711813532','subitem_conference_country')::jsonb;

DELETE FROM item_type_property WHERE id=75;

-- GEOLOCATION = '1021'
UPDATE item_type SET render=replace(render::text,'cus_19"','cus_1021"')::jsonb;

DELETE FROM item_type_property WHERE id=19;

-- CREATOR = '1038'
UPDATE item_type SET render=replace(render::text,'cus_60"','cus_1038"')::jsonb;

DELETE FROM item_type_property WHERE id=60;

-- DESCRIPTION = '1010' 
UPDATE item_type SET render=replace(render::text,'cus_17"','cus_1010"')::jsonb;

DELETE FROM item_type_property WHERE id=17;

-- VERSION_TYPE = '1016'
UPDATE item_type SET render=replace(render::text,'cus_9"','cus_1016"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522305645492','subitem_version_type')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522305645492','subitem_version_type')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522305645492','subitem_version_type')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522305645492','subitem_version_type')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1600292170262','subitem_version_resource')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1600292170262','subitem_version_resource')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1600292170262','subitem_version_resource')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1600292170262','subitem_version_resource')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522305645492','subitem_version_type')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1600292170262','subitem_version_resource')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522305645492','subitem_version_type')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1600292170262','subitem_version_resource')::jsonb;

DELETE FROM item_type_property WHERE id=9;

-- PUBLISHER = '1011'  
UPDATE item_type SET render=replace(render::text,'cus_5"','cus_1011"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522300295150','subitem_publisher')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522300295150','subitem_publisher')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522300295150','subitem_publisher')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300295150','subitem_publisher')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522300295150','subitem_publisher')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522300295150','subitem_publisher')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb;

DELETE FROM item_type_property WHERE id=5;

-- FUNDING_REFERENCE = '1022'
UPDATE item_type SET render=replace(render::text,'cus_21"','cus_1022"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399412622','subitem_funder_names')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399412622','subitem_funder_names')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399412622','subitem_funder_names')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399412622','subitem_funder_names')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522737543681','subitem_funder_name')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522737543681','subitem_funder_name')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522737543681','subitem_funder_name')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522737543681','subitem_funder_name')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399571623','subitem_award_numbers')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399571623','subitem_award_numbers')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399571623','subitem_award_numbers')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399571623','subitem_award_numbers')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399585738','subitem_award_uri')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399585738','subitem_award_uri')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399585738','subitem_award_uri')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399585738','subitem_award_uri')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399628911','subitem_award_number')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399628911','subitem_award_number')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399628911','subitem_award_number')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399628911','subitem_award_number')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522399651758','subitem_award_titles')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522399651758','subitem_award_titles')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522399651758','subitem_award_titles')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399651758','subitem_award_titles')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522721910626','subitem_award_title_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522721910626','subitem_award_title_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522721910626','subitem_award_title_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522721910626','subitem_award_title_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522721929892','subitem_award_title')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522721929892','subitem_award_title')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522721929892','subitem_award_title')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522721929892','subitem_award_title')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399412622','subitem_funder_names')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522737543681','subitem_funder_name')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399571623','subitem_award_numbers')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399585738','subitem_award_uri')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399628911','subitem_award_number')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522399651758','subitem_award_titles')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522721910626','subitem_award_title_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522721929892','subitem_award_title')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399412622','subitem_funder_names')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522737543681','subitem_funder_name')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399571623','subitem_award_numbers')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399585738','subitem_award_uri')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399628911','subitem_award_number')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522399651758','subitem_award_titles')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522721910626','subitem_award_title_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522721929892','subitem_award_title')::jsonb;

DELETE FROM item_type_property WHERE id=21;

-- SOURCE_TITLE = '1024'   
UPDATE item_type SET render=replace(render::text,'cus_13"','cus_1024"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522650091861','subitem_record_name')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522650091861','subitem_record_name')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522650091861','subitem_record_name')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650091861','subitem_record_name')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522650091861','subitem_record_name')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522650091861','subitem_record_name')::jsonb;

DELETE FROM item_type_property WHERE id=13;

-- SOURCE_ID = '1023'
UPDATE item_type SET render=replace(render::text,'cus_10"','cus_1023"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522646572813','subitem_source_identifier')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522646572813','subitem_source_identifier')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522646572813','subitem_source_identifier')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522646572813','subitem_source_identifier')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522646572813','subitem_source_identifier')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522646572813','subitem_source_identifier')::jsonb;

DELETE FROM item_type_property WHERE id=10;

-- ISSUE = '1026' 
UPDATE item_type SET render=replace(render::text,'cus_87"','cus_1026"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256294723','subitem_issue')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256294723','subitem_issue')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256294723','subitem_issue')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256294723','subitem_issue')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256294723','subitem_issue')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551256294723','subitem_issue')::jsonb;

DELETE FROM item_type_property WHERE id=87;

-- DEGREE_NAME = '1031'    
UPDATE item_type SET render=replace(render::text,'cus_80"','cus_1031"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256126428','subitem_degreename')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256126428','subitem_degreename')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256126428','subitem_degreename')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256126428','subitem_degreename')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256129013','subitem_degreename_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256129013','subitem_degreename_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256129013','subitem_degreename_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256129013','subitem_degreename_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256126428','subitem_issue')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256129013','subitem_degreename')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551256126428','subitem_issue')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256129013','subitem_degreename')::jsonb;

DELETE FROM item_type_property WHERE id=80;

-- DATE_GRANTED = '1032'   
UPDATE item_type SET render=replace(render::text,'cus_79"','cus_1032"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256096004','subitem_dategranted')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256096004','subitem_dategranted')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256096004','subitem_dategranted')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256096004','subitem_dategranted')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256096004','subitem_dategranted')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551256096004','subitem_dategranted')::jsonb;

DELETE FROM item_type_property WHERE id=79;

-- DEGREE_GRANTOR = '1033'  
UPDATE item_type SET render=replace(render::text,'cus_78"','cus_1033"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb;

DELETE FROM item_type_property WHERE id=78;

-- DISSERTATION_NUMBER = '1030'    
UPDATE item_type SET render=replace(render::text,'cus_82"','cus_1030"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb;
DELETE FROM item_type_property WHERE id=82;

-- CONTRIBUTOR = '1039'   
UPDATE item_type SET render=replace(render::text,'cus_62"','cus_1039"')::jsonb;
DELETE FROM item_type_property WHERE id=62;

-- VOLUME = '1025'  
UPDATE item_type SET render=replace(render::text,'cus_88"','cus_1025"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256328147','subitem_volume')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256328147','subitem_volume')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256328147','subitem_volume')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256328147','subitem_volume')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256328147','subitem_volume')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256328147','subitem_volume')::jsonb;
DELETE FROM item_type_property WHERE id=88;

-- FILE = '1035'   
UPDATE item_type SET render=replace(render::text,'cus_20"','cus_1035"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652546580','url')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652546580','url')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652546580','url')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652546580','url')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652548920','objectType')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652548920','objectType')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652548920','objectType')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652548920','objectType')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652672693','label')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652672693','label')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652672693','label')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652672693','label')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652685531','url')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652685531','url')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652685531','url')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652685531','url')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652734962','format')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652734962','format')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652734962','format')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652734962','format')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652740098','filesize')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652740098','filesize')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652740098','filesize')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652740098','filesize')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522722119299','value')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522722119299','value')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522722119299','value')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522722119299','value')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522652747880','fileDate')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522652747880','fileDate')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522652747880','fileDate')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652747880','fileDate')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522722132466','fileDateType')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522722132466','fileDateType')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522722132466','fileDateType')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522722132466','fileDateType')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522739295711','type')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522739295711','type')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522739295711','type')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522739295711','type')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523325300505','version')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523325300505','version')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523325300505','version')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523325300505','version')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522652546580','url')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522652548920','objectType')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522652672693','label')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522652685531','url')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522652734962','format')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522652740098','filesize')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522722119299','value')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522652747880','fileDate')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522722132466','fileDateType')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522739295711','type')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1523325300505','version')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522652546580','url')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522652548920','objectType')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522652672693','label')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522652685531','url')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522652734962','format')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522652740098','filesize')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522722119299','value')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522652747880','fileDate')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522722132466','fileDateType')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522739295711','type')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1523325300505','version')::jsonb;

DELETE FROM item_type_property WHERE id=20;

-- VERSION = '1015'   
UPDATE item_type SET render=replace(render::text,'cus_28"','cus_1015"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523263171732','subitem_version')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523263171732','subitem_version')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523263171732','subitem_version')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523263171732','subitem_version')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1523263171732','subitem_version')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1523263171732','subitem_version')::jsonb;

DELETE FROM item_type_property WHERE id=28;

-- DATE = '1012'      
UPDATE item_type SET render=replace(render::text,'cus_11"','cus_1012"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb;


DELETE FROM item_type_property WHERE id=11;

-- TEMPORAL = '1020'
UPDATE item_type SET render=replace(render::text,'cus_18"','cus_1020"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522658031721','subitem_temporal_text')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522658031721','subitem_temporal_text')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522658031721','subitem_temporal_text')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522658031721','subitem_temporal_text')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522658031721','subitem_temporal_text')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522658031721','subitem_temporal_text')::jsonb;


DELETE FROM item_type_property WHERE id=18;

-- BIBLIO_INFO = '1027'
UPDATE item_type SET render=replace(render::text,'cus_102"','cus_1027"')::jsonb;
DELETE FROM item_type_property WHERE id=102;

-- ACCESS_RIGHT = '1005'
UPDATE item_type SET render=replace(render::text,'cus_4"','cus_1005"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522299639480','subitem_access_right')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522299639480','subitem_access_right')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522299639480','subitem_access_right')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522299639480','subitem_access_right')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522299639480','subitem_access_right')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522299639480','subitem_access_right')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb;

DELETE FROM item_type_property WHERE id=4;

-- RIGHTS = '1007' 
UPDATE item_type SET render=replace(render::text,'cus_14"','cus_1007"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522650717957','subitem_rights_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522650717957','subitem_rights_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522650717957','subitem_rights_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650717957','subitem_rights_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522650727486','subitem_rights_resource')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522650727486','subitem_rights_resource')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522650727486','subitem_rights_resource')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650727486','subitem_rights_resource')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522651041219','subitem_rights')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522651041219','subitem_rights')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522651041219','subitem_rights')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522651041219','subitem_rights')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522650717957','subitem_rights_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522650727486','subitem_rights_resource')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522651041219','subitem_rights')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522650717957','subitem_rights_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522650727486','subitem_rights_resource')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522651041219','subitem_rights')::jsonb;

DELETE FROM item_type_property WHERE id=14;

-- RIGHTS_HOLDER = '1008'    
UPDATE item_type SET render=replace(render::text,'cus_3"','cus_1008"')::jsonb;
DELETE FROM item_type_property WHERE id=3;

-- END_PAGE = '1029'   
UPDATE item_type SET render=replace(render::text,'cus_83"','cus_1029"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256185532','subitem_end_page')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256185532','subitem_end_page')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256185532','subitem_end_page')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256185532','subitem_end_page')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256185532','subitem_end_page')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551256185532','subitem_end_page')::jsonb;

DELETE FROM item_type_property WHERE id=83;

-- HEADING = '1041' 
UPDATE item_type SET render=replace(render::text,'cus_175"','cus_1041"')::jsonb;

DELETE FROM item_type_property WHERE id=175;

UPDATE item_type SET render=replace(render::text,'cus_119"','cus_1041"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1565671149650','subitem_heading_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1565671149650','subitem_heading_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1565671149650','subitem_heading_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1565671149650','subitem_heading_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1565671178623','subitem_heading_headline')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1565671178623','subitem_heading_headline')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1565671178623','subitem_heading_headline')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1565671178623','subitem_heading_headline')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1565671149650','subitem_heading_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1565671178623','subitem_heading_headline')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1565671149650','subitem_heading_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1565671178623','subitem_heading_headline')::jsonb;

DELETE FROM item_type_property WHERE id=119;
-- LANGUAGE = '1003' 
UPDATE item_type SET render=replace(render::text,'cus_71"','cus_1003"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551255818386','subitem_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551255818386','subitem_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551255818386','subitem_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255818386','subitem_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551255818386','subitem_language')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551255818386','subitem_language')::jsonb;

DELETE FROM item_type_property WHERE id=71;

-- FILE_PRICE = '1036'
UPDATE item_type SET render=replace(render::text,'cus_103"','cus_1036"')::jsonb;
DELETE FROM item_type_property WHERE id=103;

-- IDENTIFIER = '1017'       
UPDATE item_type SET render=replace(render::text,'cus_176"','cus_1017"')::jsonb;
DELETE FROM item_type_property WHERE id=176;

-- RESOURCE_TYPE = '1014'
UPDATE item_type SET render=replace(render::text,'cus_8"','cus_1014"')::jsonb;
DELETE FROM item_type_property WHERE id=8;

-- START_PAGE = '1028'  
UPDATE item_type SET render=replace(render::text,'cus_84"','cus_1028"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1551256198917','subitem_start_page')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256198917','subitem_start_page')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256198917','subitem_start_page')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256198917','subitem_start_page')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1551256198917','subitem_start_page')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1551256198917','subitem_start_page')::jsonb;

DELETE FROM item_type_property WHERE id=84;

-- RELATION = '1019'  
UPDATE item_type SET render=replace(render::text,'cus_12"','cus_1019"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522306207484','subitem_relation_type')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522306207484','subitem_relation_type')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522306207484','subitem_relation_type')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306207484','subitem_relation_type')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523320863692','subitem_relation_name')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523320863692','subitem_relation_name')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523320863692','subitem_relation_name')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523320863692','subitem_relation_name')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb;
UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1522306207484','subitem_relation_type')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1523320863692','subitem_relation_name')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb;

UPDATE item_metadata SET json=replace(json::text,'subitem_1522306207484','subitem_relation_type')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1523320863692','subitem_relation_name')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb;

DELETE FROM item_type_property WHERE id=12;