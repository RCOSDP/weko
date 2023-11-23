
CREATE OR REPLACE FUNCTION update_if_condition()
RETURNS void AS $$
BEGIN
    IF (SELECT COUNT(id) FROM item_type_property)>53 THEN
        DELETE FROM item_type_property WHERE id=121;
        DELETE FROM item_type_property WHERE id=122;
        DELETE FROM item_type_property WHERE id=124;
        DELETE FROM item_type_property WHERE id=132;
        -- LINK = '1044'
        RAISE NOTICE 'Property ID being processed: 1044';
        UPDATE item_type SET render=replace(render::text,'cus_142"','cus_1044"')::jsonb WHERE render::text like '%cus_142"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1587693279322','subitem_link_url')::jsonb WHERE schema::text like '%subitem_1587693279322%';
        UPDATE item_type SET form=replace(form::text,'subitem_1587693279322','subitem_link_url')::jsonb WHERE form::text like '%subitem_1587693279322%';
        UPDATE item_type SET render=replace(render::text,'subitem_1587693279322','subitem_link_url')::jsonb WHERE render::text like '%subitem_1587693279322%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1587693279322','subitem_link_url')::jsonb WHERE mapping::text like '%subitem_1587693279322%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1587650325204','subitem_link_text')::jsonb WHERE schema::text like '%subitem_1587650325204%';
        UPDATE item_type SET form=replace(form::text,'subitem_1587650325204','subitem_link_text')::jsonb WHERE form::text like '%subitem_1587650325204%';
        UPDATE item_type SET render=replace(render::text,'subitem_1587650325204','subitem_link_text')::jsonb WHERE render::text like '%subitem_1587650325204%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1587650325204','subitem_link_text')::jsonb WHERE mapping::text like '%subitem_1587650325204%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1587693278490','subitem_link_language')::jsonb WHERE schema::text like '%subitem_1587693278490%';
        UPDATE item_type SET form=replace(form::text,'subitem_1587693278490','subitem_link_language')::jsonb WHERE form::text like '%subitem_1587693278490%';
        UPDATE item_type SET render=replace(render::text,'subitem_1587693278490','subitem_link_language')::jsonb WHERE render::text like '%subitem_1587693278490%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1587693278490','subitem_link_language')::jsonb WHERE mapping::text like '%subitem_1587693278490%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1587693279322','subitem_link_url')::jsonb WHERE json::text like '%subitem_1587693279322%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1587650325204','subitem_link_text')::jsonb WHERE json::text like '%subitem_1587650325204%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1587693278490','subitem_link_language')::jsonb WHERE json::text like '%subitem_1587693278490%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1587693279322','subitem_link_url')::jsonb WHERE json::text like '%subitem_1587693279322%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1587650325204','subitem_link_text')::jsonb WHERE json::text like '%subitem_1587650325204%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1587693278490','subitem_link_language')::jsonb WHERE json::text like '%subitem_1587693278490%';

        DELETE FROM item_type_property WHERE id=142;

        -- TITLE = '1001'
        RAISE NOTICE 'Property ID being processed: 1001';
        UPDATE item_type SET render=replace(render::text,'cus_67"','cus_1001"')::jsonb WHERE render::text like '%cus_67"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255647225','subitem_title')::jsonb WHERE schema::text like '%subitem_1551255647225%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255647225','subitem_title')::jsonb WHERE form::text like '%subitem_1551255647225%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255647225','subitem_title')::jsonb WHERE render::text like '%subitem_1551255647225%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255647225','subitem_title')::jsonb WHERE mapping::text like '%subitem_1551255647225%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255648112','subitem_title_language')::jsonb WHERE schema::text like '%subitem_1551255648112%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255648112','subitem_title_language')::jsonb WHERE form::text like '%subitem_1551255648112%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255648112','subitem_title_language')::jsonb WHERE render::text like '%subitem_1551255648112%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255648112','subitem_title_language')::jsonb WHERE mapping::text like '%subitem_1551255648112%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255647225','subitem_title')::jsonb WHERE json::text like '%subitem_1551255647225%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255648112','subitem_title_language')::jsonb WHERE json::text like '%subitem_1551255648112%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255647225','subitem_title')::jsonb WHERE json::text like '%subitem_1551255647225%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255648112','subitem_title_language')::jsonb WHERE json::text like '%subitem_1551255648112%';

        DELETE FROM item_type_property WHERE id=67;

        -- TEXT = '1042'
        RAISE NOTICE 'Property ID being processed: 1042';
        UPDATE item_type SET render=replace(render::text,'cus_137"','cus_1042"')::jsonb WHERE render::text like '%cus_137"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1586228465211','subitem_text_value')::jsonb WHERE schema::text like '%subitem_1586228465211%';
        UPDATE item_type SET form=replace(form::text,'subitem_1586228465211','subitem_text_value')::jsonb WHERE form::text like '%subitem_1586228465211%';
        UPDATE item_type SET render=replace(render::text,'subitem_1586228465211','subitem_text_value')::jsonb WHERE render::text like '%subitem_1586228465211%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1586228465211','subitem_text_value')::jsonb WHERE mapping::text like '%subitem_1586228465211%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_158622849035','subitem_text_language')::jsonb WHERE schema::text like '%subitem_158622849035%';
        UPDATE item_type SET form=replace(form::text,'subitem_158622849035','subitem_text_language')::jsonb WHERE form::text like '%subitem_158622849035%';
        UPDATE item_type SET render=replace(render::text,'subitem_158622849035','subitem_text_language')::jsonb WHERE render::text like '%subitem_158622849035%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_158622849035','subitem_text_language')::jsonb WHERE mapping::text like '%subitem_158622849035%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1586228465211','subitem_text_value')::jsonb WHERE json::text like '%subitem_1586228465211%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_158622849035','subitem_text_language')::jsonb WHERE json::text like '%subitem_158622849035%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1586228465211','subitem_text_value')::jsonb WHERE json::text like '%subitem_1586228465211%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_158622849035','subitem_text_language')::jsonb WHERE json::text like '%subitem_158622849035%';

        DELETE FROM item_type_property WHERE id=137;

        -- THUMBNAIL = '1037'
        RAISE NOTICE 'Property ID being processed: 1037';
        UPDATE item_type SET render=replace(render::text,'cus_120"','cus_1037"')::jsonb WHERE render::text like '%cus_120"%';
        DELETE FROM item_type_property WHERE id=120;

        -- TEXTAREA = '1043'
        RAISE NOTICE 'Property ID being processed: 1043';
        UPDATE item_type SET render=replace(render::text,'cus_139"','cus_1043"')::jsonb WHERE render::text like '%cus_139"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1586253392325','subitem_textarea_value')::jsonb WHERE schema::text like '%subitem_1586253392325%';
        UPDATE item_type SET form=replace(form::text,'subitem_1586253392325','subitem_textarea_value')::jsonb WHERE form::text like '%subitem_1586253392325%';
        UPDATE item_type SET render=replace(render::text,'subitem_1586253392325','subitem_textarea_value')::jsonb WHERE render::text like '%subitem_1586253392325%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1586253392325','subitem_textarea_value')::jsonb WHERE mapping::text like '%subitem_1586253392325%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_158625340053','subitem_textarea_language')::jsonb WHERE schema::text like '%subitem_158625340053%';
        UPDATE item_type SET form=replace(form::text,'subitem_158625340053','subitem_textarea_language')::jsonb WHERE form::text like '%subitem_158625340053%';
        UPDATE item_type SET render=replace(render::text,'subitem_158625340053','subitem_textarea_language')::jsonb WHERE render::text like '%subitem_158625340053%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_158625340053','subitem_textarea_language')::jsonb WHERE mapping::text like '%subitem_158625340053%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1586253392325','subitem_textarea_value')::jsonb WHERE json::text like '%subitem_1586253392325%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_158625340053','subitem_textarea_language')::jsonb WHERE json::text like '%subitem_158625340053%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1586253392325','subitem_textarea_value')::jsonb WHERE json::text like '%subitem_1586253392325%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_158625340053','subitem_textarea_language')::jsonb WHERE json::text like '%subitem_158625340053%';

        DELETE FROM item_type_property WHERE id=139;

        -- APC = '1006'
        RAISE NOTICE 'Property ID being processed: 1006';
        UPDATE item_type SET render=replace(render::text,'cus_27"','cus_1006"')::jsonb WHERE render::text like '%cus_27"%';
        UPDATE item_type SET render=replace(render::text,'cus_100"','cus_1006"')::jsonb WHERE render::text like '%cus_100"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523260933860','subitem_apc')::jsonb WHERE schema::text like '%subitem_1523260933860%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523260933860','subitem_apc')::jsonb WHERE form::text like '%subitem_1523260933860%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523260933860','subitem_apc')::jsonb WHERE render::text like '%subitem_1523260933860%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523260933860','subitem_apc')::jsonb WHERE mapping::text like '%subitem_1523260933860%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1523260933860','subitem_apc')::jsonb WHERE json::text like '%subitem_1523260933860%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1523260933860','subitem_apc')::jsonb WHERE json::text like '%subitem_1523260933860%';

        DELETE FROM item_type_property WHERE id=27;

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551257776901','subitem_apc')::jsonb WHERE schema::text like '%subitem_1551257776901%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551257776901','subitem_apc')::jsonb WHERE form::text like '%subitem_1551257776901%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551257776901','subitem_apc')::jsonb WHERE render::text like '%subitem_1551257776901%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551257776901','subitem_apc')::jsonb WHERE mapping::text like '%subitem_1551257776901%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551257776901','subitem_apc')::jsonb WHERE json::text like '%subitem_1551257776901%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551257776901','subitem_apc')::jsonb WHERE json::text like '%subitem_1551257776901%';

        DELETE FROM item_type_property WHERE id=100;

        -- IDENTIFIER_REGISTRATION = '1018'
        RAISE NOTICE 'Property ID being processed: 1018';
        UPDATE item_type SET render=replace(render::text,'cus_16"','cus_1018"')::jsonb WHERE render::text like '%cus_16"%';
        DELETE FROM item_type_property WHERE id=16;

        UPDATE item_type SET render=replace(render::text,'cus_86"','cus_1018"')::jsonb WHERE render::text like '%cus_86"%';
        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256250276','subitem_identifier_reg_text')::jsonb WHERE schema::text like '%subitem_1551256250276%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256250276','subitem_identifier_reg_text')::jsonb WHERE form::text like '%subitem_1551256250276%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256250276','subitem_identifier_reg_text')::jsonb WHERE render::text like '%subitem_1551256250276%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256250276','subitem_identifier_reg_text')::jsonb WHERE mapping::text like '%subitem_1551256250276%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256259586','subitem_identifier_reg_type')::jsonb WHERE schema::text like '%subitem_1551256259586%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256259586','subitem_identifier_reg_type')::jsonb WHERE form::text like '%subitem_1551256259586%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256259586','subitem_identifier_reg_type')::jsonb WHERE render::text like '%subitem_1551256259586%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256259586','subitem_identifier_reg_type')::jsonb WHERE mapping::text like '%subitem_1551256259586%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256250276','subitem_identifier_reg_text')::jsonb WHERE json::text like '%subitem_1551256250276%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256259586','subitem_identifier_reg_type')::jsonb WHERE json::text like '%subitem_1551256259586%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256250276','subitem_identifier_reg_text')::jsonb WHERE json::text like '%subitem_1551256250276%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256259586','subitem_identifier_reg_type')::jsonb WHERE json::text like '%subitem_1551256259586%';

        DELETE FROM item_type_property WHERE id=86;

        -- NUMBER_OF_PAGES = '126'
        RAISE NOTICE 'Property ID being processed: 126';
        UPDATE item_type SET render=replace(render::text,'cus_85"','cus_126"')::jsonb WHERE render::text like '%cus_85"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb WHERE schema::text like '%subitem_1551256248092%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb WHERE form::text like '%subitem_1551256248092%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb WHERE render::text like '%subitem_1551256248092%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb WHERE mapping::text like '%subitem_1551256248092%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb WHERE json::text like '%subitem_1551256248092%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256248092','subitem_number_of_pages')::jsonb WHERE json::text like '%subitem_1551256248092%';

        DELETE FROM item_type_property WHERE id=85;

        -- RESOURCE_TYPE_SIMPLE = '127'
        RAISE NOTICE 'Property ID being processed: 127';
        UPDATE item_type SET render=replace(render::text,'cus_177"','cus_127"')::jsonb WHERE render::text like '%cus_177"%';
        DELETE FROM item_type_property WHERE id=177;

        -- S_FILE = '125'  
        RAISE NOTICE 'Property ID being processed: 125';
        UPDATE item_type SET render=replace(render::text,'cus_131"','cus_125"')::jsonb WHERE render::text like '%cus_131"%';
        DELETE FROM item_type_property WHERE id=131;

        -- S_IDENTIFIER = '123'
        RAISE NOTICE 'Property ID being processed: 123';
        UPDATE item_type SET render=replace(render::text,'cus_130"','cus_123"')::jsonb WHERE render::text like '%cus_130"%';
        DELETE FROM item_type_property WHERE id=123;
        UPDATE item_type_property SET id=123 WHERE id=130;

        -- SUBJECT = '1009'
        RAISE NOTICE 'Property ID being processed: 1009';
        UPDATE item_type SET render=replace(render::text,'cus_6"','cus_1009"')::jsonb WHERE render::text like '%cus_6"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523261968819','subitem_subject')::jsonb WHERE schema::text like '%subitem_1523261968819%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523261968819','subitem_subject')::jsonb WHERE form::text like '%subitem_1523261968819%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523261968819','subitem_subject')::jsonb WHERE render::text like '%subitem_1523261968819%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523261968819','subitem_subject')::jsonb WHERE mapping::text like '%subitem_1523261968819%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522300048512','subitem_subject_uri')::jsonb WHERE schema::text like '%subitem_1522300048512%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522300048512','subitem_subject_uri')::jsonb WHERE form::text like '%subitem_1522300048512%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522300048512','subitem_subject_uri')::jsonb WHERE render::text like '%subitem_1522300048512%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300048512','subitem_subject_uri')::jsonb WHERE mapping::text like '%subitem_1522300048512%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb WHERE schema::text like '%subitem_1522300014469%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb WHERE form::text like '%subitem_1522300014469%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb WHERE render::text like '%subitem_1522300014469%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb WHERE mapping::text like '%subitem_1522300014469%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522299896455','subitem_subject_language')::jsonb WHERE schema::text like '%subitem_1522299896455%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522299896455','subitem_subject_language')::jsonb WHERE form::text like '%subitem_1522299896455%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522299896455','subitem_subject_language')::jsonb WHERE render::text like '%subitem_1522299896455%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522299896455','subitem_subject_language')::jsonb WHERE mapping::text like '%subitem_1522299896455%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1523261968819','subitem_subject')::jsonb WHERE json::text like '%subitem_1523261968819%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522300048512','subitem_subject_uri')::jsonb WHERE json::text like '%subitem_1522300048512%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb WHERE json::text like '%subitem_1522300014469%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522299896455','subitem_subject_language')::jsonb WHERE json::text like '%subitem_1522299896455%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1523261968819','subitem_subject')::jsonb WHERE json::text like '%subitem_1523261968819%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522300048512','subitem_subject_uri')::jsonb WHERE json::text like '%subitem_1522300048512%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522300014469','subitem_subject_scheme')::jsonb WHERE json::text like '%subitem_1522300014469%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522299896455','subitem_subject_language')::jsonb WHERE json::text like '%subitem_1522299896455%';

        DELETE FROM item_type_property WHERE id=6;

        -- ALTERNATIVE_TITLE = '1002'
        RAISE NOTICE 'Property ID being processed: 1002';
        UPDATE item_type SET render=replace(render::text,'cus_69"','cus_1002"')::jsonb WHERE render::text like '%cus_69"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255720400','subitem_alternative_title')::jsonb WHERE schema::text like '%subitem_1551255720400%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255720400','subitem_alternative_title')::jsonb WHERE form::text like '%subitem_1551255720400%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255720400','subitem_alternative_title')::jsonb WHERE render::text like '%subitem_1551255720400%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255720400','subitem_alternative_title')::jsonb WHERE mapping::text like '%subitem_1551255720400%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb WHERE schema::text like '%subitem_1551255721061%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb WHERE form::text like '%subitem_1551255721061%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb WHERE render::text like '%subitem_1551255721061%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb WHERE mapping::text like '%subitem_1551255721061%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255720400','subitem_alternative_title')::jsonb WHERE json::text like '%subitem_1551255720400%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb WHERE json::text like '%subitem_1551255721061%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255720400','subitem_alternative_title')::jsonb WHERE json::text like '%subitem_1551255720400%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255721061','subitem_alternative_title_language')::jsonb WHERE json::text like '%subitem_1551255721061%';

        DELETE FROM item_type_property WHERE id=69;

        -- CONFERENCE = '1034'
        RAISE NOTICE 'Property ID being processed: 1034';
        UPDATE item_type SET render=replace(render::text,'cus_75"','cus_1034"')::jsonb WHERE render::text like '%cus_75"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711633003','subitem_conference_names')::jsonb WHERE schema::text like '%subitem_1599711633003%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711633003','subitem_conference_names')::jsonb WHERE form::text like '%subitem_1599711633003%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711633003','subitem_conference_names')::jsonb WHERE render::text like '%subitem_1599711633003%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711633003','subitem_conference_names')::jsonb WHERE mapping::text like '%subitem_1599711633003%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711636923','subitem_conference_name')::jsonb WHERE schema::text like '%subitem_1599711636923%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711636923','subitem_conference_name')::jsonb WHERE form::text like '%subitem_1599711636923%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711636923','subitem_conference_name')::jsonb WHERE render::text like '%subitem_1599711636923%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711636923','subitem_conference_name')::jsonb WHERE mapping::text like '%subitem_1599711636923%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb WHERE schema::text like '%subitem_1599711645590%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb WHERE form::text like '%subitem_1599711645590%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb WHERE render::text like '%subitem_1599711645590%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb WHERE mapping::text like '%subitem_1599711645590%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb WHERE schema::text like '%subitem_1599711655652%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb WHERE form::text like '%subitem_1599711655652%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb WHERE render::text like '%subitem_1599711655652%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb WHERE mapping::text like '%subitem_1599711655652%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb WHERE schema::text like '%subitem_1599711660052%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb WHERE form::text like '%subitem_1599711660052%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb WHERE render::text like '%subitem_1599711660052%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb WHERE mapping::text like '%subitem_1599711660052%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb WHERE schema::text like '%subitem_1599711680082%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb WHERE form::text like '%subitem_1599711680082%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb WHERE render::text like '%subitem_1599711680082%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb WHERE mapping::text like '%subitem_1599711680082%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb WHERE schema::text like '%subitem_1599711686511%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb WHERE form::text like '%subitem_1599711686511%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb WHERE render::text like '%subitem_1599711686511%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb WHERE mapping::text like '%subitem_1599711686511%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711699392','subitem_conference_date')::jsonb WHERE schema::text like '%subitem_1599711699392%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711699392','subitem_conference_date')::jsonb WHERE form::text like '%subitem_1599711699392%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711699392','subitem_conference_date')::jsonb WHERE render::text like '%subitem_1599711699392%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711699392','subitem_conference_date')::jsonb WHERE mapping::text like '%subitem_1599711699392%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711704251','subitem_conference_period')::jsonb WHERE schema::text like '%subitem_1599711704251%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711704251','subitem_conference_period')::jsonb WHERE form::text like '%subitem_1599711704251%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711704251','subitem_conference_period')::jsonb WHERE render::text like '%subitem_1599711704251%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711704251','subitem_conference_period')::jsonb WHERE mapping::text like '%subitem_1599711704251%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb WHERE schema::text like '%subitem_1599711712451%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb WHERE form::text like '%subitem_1599711712451%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb WHERE render::text like '%subitem_1599711712451%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb WHERE mapping::text like '%subitem_1599711712451%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb WHERE schema::text like '%subitem_1599711727603%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb WHERE form::text like '%subitem_1599711727603%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb WHERE render::text like '%subitem_1599711727603%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb WHERE mapping::text like '%subitem_1599711727603%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb WHERE schema::text like '%subitem_1599711731891%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb WHERE form::text like '%subitem_1599711731891%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb WHERE render::text like '%subitem_1599711731891%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb WHERE mapping::text like '%subitem_1599711731891%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb WHERE schema::text like '%subitem_1599711735410%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb WHERE form::text like '%subitem_1599711735410%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb WHERE render::text like '%subitem_1599711735410%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb WHERE mapping::text like '%subitem_1599711735410%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb WHERE schema::text like '%subitem_1599711739022%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb WHERE form::text like '%subitem_1599711739022%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb WHERE render::text like '%subitem_1599711739022%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb WHERE mapping::text like '%subitem_1599711739022%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb WHERE schema::text like '%subitem_1599711743722%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb WHERE form::text like '%subitem_1599711743722%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb WHERE render::text like '%subitem_1599711743722%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb WHERE mapping::text like '%subitem_1599711743722%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb WHERE schema::text like '%subitem_1599711745532%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb WHERE form::text like '%subitem_1599711745532%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb WHERE render::text like '%subitem_1599711745532%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb WHERE mapping::text like '%subitem_1599711745532%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711758470','subitem_conference_venues')::jsonb WHERE schema::text like '%subitem_1599711758470%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711758470','subitem_conference_venues')::jsonb WHERE form::text like '%subitem_1599711758470%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711758470','subitem_conference_venues')::jsonb WHERE render::text like '%subitem_1599711758470%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711758470','subitem_conference_venues')::jsonb WHERE mapping::text like '%subitem_1599711758470%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711769260','subitem_conference_venue')::jsonb WHERE schema::text like '%subitem_1599711769260%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711769260','subitem_conference_venue')::jsonb WHERE form::text like '%subitem_1599711769260%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711769260','subitem_conference_venue')::jsonb WHERE render::text like '%subitem_1599711769260%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711769260','subitem_conference_venue')::jsonb WHERE mapping::text like '%subitem_1599711769260%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb WHERE schema::text like '%subitem_1599711775943%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb WHERE form::text like '%subitem_1599711775943%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb WHERE render::text like '%subitem_1599711775943%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb WHERE mapping::text like '%subitem_1599711775943%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711788485','subitem_conference_places')::jsonb WHERE schema::text like '%subitem_1599711788485%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711788485','subitem_conference_places')::jsonb WHERE form::text like '%subitem_1599711788485%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711788485','subitem_conference_places')::jsonb WHERE render::text like '%subitem_1599711788485%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711788485','subitem_conference_places')::jsonb WHERE mapping::text like '%subitem_1599711788485%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711798761','subitem_conference_place')::jsonb WHERE schema::text like '%subitem_1599711798761%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711798761','subitem_conference_place')::jsonb WHERE form::text like '%subitem_1599711798761%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711798761','subitem_conference_place')::jsonb WHERE render::text like '%subitem_1599711798761%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711798761','subitem_conference_place')::jsonb WHERE mapping::text like '%subitem_1599711798761%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb WHERE schema::text like '%subitem_1599711803382%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb WHERE form::text like '%subitem_1599711803382%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb WHERE render::text like '%subitem_1599711803382%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb WHERE mapping::text like '%subitem_1599711803382%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1599711813532','subitem_conference_country')::jsonb WHERE schema::text like '%subitem_1599711813532%';
        UPDATE item_type SET form=replace(form::text,'subitem_1599711813532','subitem_conference_country')::jsonb WHERE form::text like '%subitem_1599711813532%';
        UPDATE item_type SET render=replace(render::text,'subitem_1599711813532','subitem_conference_country')::jsonb WHERE render::text like '%subitem_1599711813532%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1599711813532','subitem_conference_country')::jsonb WHERE mapping::text like '%subitem_1599711813532%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711633003','subitem_conference_names')::jsonb WHERE json::text like '%subitem_1599711633003%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711636923','subitem_conference_name')::jsonb WHERE json::text like '%subitem_1599711636923%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb WHERE json::text like '%subitem_1599711645590%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb WHERE json::text like '%subitem_1599711655652%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb WHERE json::text like '%subitem_1599711660052%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb WHERE json::text like '%subitem_1599711680082%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb WHERE json::text like '%subitem_1599711686511%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711699392','subitem_conference_date')::jsonb WHERE json::text like '%subitem_1599711699392%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711704251','subitem_conference_period')::jsonb WHERE json::text like '%subitem_1599711704251%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb WHERE json::text like '%subitem_1599711712451%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb WHERE json::text like '%subitem_1599711727603%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb WHERE json::text like '%subitem_1599711731891%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb WHERE json::text like '%subitem_1599711735410%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb WHERE json::text like '%subitem_1599711739022%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb WHERE json::text like '%subitem_1599711743722%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb WHERE json::text like '%subitem_1599711745532%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711758470','subitem_conference_venues')::jsonb WHERE json::text like '%subitem_1599711758470%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711769260','subitem_conference_venue')::jsonb WHERE json::text like '%subitem_1599711769260%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb WHERE json::text like '%subitem_1599711775943%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711788485','subitem_conference_places')::jsonb WHERE json::text like '%subitem_1599711788485%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711798761','subitem_conference_place')::jsonb WHERE json::text like '%subitem_1599711798761%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb WHERE json::text like '%subitem_1599711803382%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1599711813532','subitem_conference_country')::jsonb WHERE json::text like '%subitem_1599711813532%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711633003','subitem_conference_names')::jsonb WHERE json::text like '%subitem_1599711633003%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711636923','subitem_conference_name')::jsonb WHERE json::text like '%subitem_1599711636923%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711645590','subitem_conference_name_language')::jsonb WHERE json::text like '%subitem_1599711645590%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711655652','subitem_conference_sequence')::jsonb WHERE json::text like '%subitem_1599711655652%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711660052','subitem_conference_sponsors')::jsonb WHERE json::text like '%subitem_1599711660052%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711680082','subitem_conference_sponsor')::jsonb WHERE json::text like '%subitem_1599711680082%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711686511','subitem_conference_sponsor_language')::jsonb WHERE json::text like '%subitem_1599711686511%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711699392','subitem_conference_date')::jsonb WHERE json::text like '%subitem_1599711699392%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711704251','subitem_conference_period')::jsonb WHERE json::text like '%subitem_1599711704251%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711712451','subitem_conference_start_day')::jsonb WHERE json::text like '%subitem_1599711712451%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711727603','subitem_conference_start_month')::jsonb WHERE json::text like '%subitem_1599711727603%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711731891','subitem_conference_start_year')::jsonb WHERE json::text like '%subitem_1599711731891%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711735410','subitem_conference_end_day')::jsonb WHERE json::text like '%subitem_1599711735410%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711739022','subitem_conference_end_month')::jsonb WHERE json::text like '%subitem_1599711739022%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711743722','subitem_conference_end_year')::jsonb WHERE json::text like '%subitem_1599711743722%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711745532','subitem_conference_date_language')::jsonb WHERE json::text like '%subitem_1599711745532%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711758470','subitem_conference_venues')::jsonb WHERE json::text like '%subitem_1599711758470%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711769260','subitem_conference_venue')::jsonb WHERE json::text like '%subitem_1599711769260%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711775943','subitem_conference_venue_language')::jsonb WHERE json::text like '%subitem_1599711775943%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711788485','subitem_conference_places')::jsonb WHERE json::text like '%subitem_1599711788485%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711798761','subitem_conference_place')::jsonb WHERE json::text like '%subitem_1599711798761%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711803382','subitem_conference_place_language')::jsonb WHERE json::text like '%subitem_1599711803382%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1599711813532','subitem_conference_country')::jsonb WHERE json::text like '%subitem_1599711813532%';

        DELETE FROM item_type_property WHERE id=75;

        -- GEOLOCATION = '1021'
        RAISE NOTICE 'Property ID being processed: 1021';
        UPDATE item_type SET render=replace(render::text,'cus_19"','cus_1021"')::jsonb WHERE render::text like '%cus_19"%';

        DELETE FROM item_type_property WHERE id=19;

        -- CREATOR = '1038'
        RAISE NOTICE 'Property ID being processed: 1038';
        UPDATE item_type SET render=replace(render::text,'cus_60"','cus_1038"')::jsonb WHERE render::text like '%cus_60"%';

        DELETE FROM item_type_property WHERE id=60;

        -- DESCRIPTION = '1010'
        RAISE NOTICE 'Property ID being processed: 1010'; 
        UPDATE item_type SET render=replace(render::text,'cus_17"','cus_1010"')::jsonb WHERE render::text like '%cus_17"%';

        DELETE FROM item_type_property WHERE id=17;

        -- VERSION_TYPE = '1016'
        RAISE NOTICE 'Property ID being processed: 1016'; 
        UPDATE item_type SET render=replace(render::text,'cus_9"','cus_1016"')::jsonb WHERE render::text like '%cus_9"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522305645492','subitem_version_type')::jsonb WHERE schema::text like '%subitem_1522305645492%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522305645492','subitem_version_type')::jsonb WHERE form::text like '%subitem_1522305645492%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522305645492','subitem_version_type')::jsonb WHERE render::text like '%subitem_1522305645492%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522305645492','subitem_version_type')::jsonb WHERE mapping::text like '%subitem_1522305645492%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1600292170262','subitem_version_resource')::jsonb WHERE schema::text like '%subitem_1600292170262%';
        UPDATE item_type SET form=replace(form::text,'subitem_1600292170262','subitem_version_resource')::jsonb WHERE form::text like '%subitem_1600292170262%';
        UPDATE item_type SET render=replace(render::text,'subitem_1600292170262','subitem_version_resource')::jsonb WHERE render::text like '%subitem_1600292170262%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1600292170262','subitem_version_resource')::jsonb WHERE mapping::text like '%subitem_1600292170262%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522305645492','subitem_version_type')::jsonb WHERE json::text like '%subitem_1522305645492%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1600292170262','subitem_version_resource')::jsonb WHERE json::text like '%subitem_1600292170262%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522305645492','subitem_version_type')::jsonb WHERE json::text like '%subitem_1522305645492%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1600292170262','subitem_version_resource')::jsonb WHERE json::text like '%subitem_1600292170262%';

        DELETE FROM item_type_property WHERE id=9;

        -- PUBLISHER = '1011' 
        RAISE NOTICE 'Property ID being processed: 1011';
        UPDATE item_type SET render=replace(render::text,'cus_5"','cus_1011"')::jsonb WHERE render::text like '%cus_5"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522300295150','subitem_publisher')::jsonb WHERE schema::text like '%subitem_1522300295150%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522300295150','subitem_publisher')::jsonb WHERE form::text like '%subitem_1522300295150%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522300295150','subitem_publisher')::jsonb WHERE render::text like '%subitem_1522300295150%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300295150','subitem_publisher')::jsonb WHERE mapping::text like '%subitem_1522300295150%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb WHERE schema::text like '%subitem_1522300316516%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb WHERE form::text like '%subitem_1522300316516%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb WHERE render::text like '%subitem_1522300316516%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb WHERE mapping::text like '%subitem_1522300316516%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522300295150','subitem_publisher')::jsonb WHERE json::text like '%subitem_1522300295150%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb WHERE json::text like '%subitem_1522300316516%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522300295150','subitem_publisher')::jsonb WHERE json::text like '%subitem_1522300295150%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522300316516','subitem_publisher_languag')::jsonb WHERE json::text like '%subitem_1522300295150%';

        DELETE FROM item_type_property WHERE id=5;

        -- FUNDING_REFERENCE = '1022'
        RAISE NOTICE 'Property ID being processed: 1022';
        UPDATE item_type SET render=replace(render::text,'cus_21"','cus_1022"')::jsonb WHERE render::text like '%cus_21"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb WHERE schema::text like '%subitem_1522399143519%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb WHERE form::text like '%subitem_1522399143519%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb WHERE render::text like '%subitem_1522399143519%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb WHERE mapping::text like '%subitem_1522399143519%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb WHERE schema::text like '%subitem_1522399281603%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb WHERE form::text like '%subitem_1522399281603%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb WHERE render::text like '%subitem_1522399281603%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb WHERE mapping::text like '%subitem_1522399281603%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb WHERE schema::text like '%subitem_1522399333375%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb WHERE form::text like '%subitem_1522399333375%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb WHERE render::text like '%subitem_1522399333375%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb WHERE mapping::text like '%subitem_1522399333375%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399412622','subitem_funder_names')::jsonb WHERE schema::text like '%subitem_1522399412622%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399412622','subitem_funder_names')::jsonb WHERE form::text like '%subitem_1522399412622%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399412622','subitem_funder_names')::jsonb WHERE render::text like '%subitem_1522399412622%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399412622','subitem_funder_names')::jsonb WHERE mapping::text like '%subitem_1522399412622%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb WHERE schema::text like '%subitem_1522399416691%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb WHERE form::text like '%subitem_1522399416691%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb WHERE render::text like '%subitem_1522399416691%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb WHERE mapping::text like '%subitem_1522399416691%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522737543681','subitem_funder_name')::jsonb WHERE schema::text like '%subitem_1522737543681%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522737543681','subitem_funder_name')::jsonb WHERE form::text like '%subitem_1522737543681%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522737543681','subitem_funder_name')::jsonb WHERE render::text like '%subitem_1522737543681%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522737543681','subitem_funder_name')::jsonb WHERE mapping::text like '%subitem_1522737543681%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399571623','subitem_award_numbers')::jsonb WHERE schema::text like '%subitem_1522399571623%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399571623','subitem_award_numbers')::jsonb WHERE form::text like '%subitem_1522399571623%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399571623','subitem_award_numbers')::jsonb WHERE render::text like '%subitem_1522399571623%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399571623','subitem_award_numbers')::jsonb WHERE mapping::text like '%subitem_1522399571623%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399585738','subitem_award_uri')::jsonb WHERE schema::text like '%subitem_1522399585738%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399585738','subitem_award_uri')::jsonb WHERE form::text like '%subitem_1522399585738%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399585738','subitem_award_uri')::jsonb WHERE render::text like '%cusubitem_1522399585738s_27%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399585738','subitem_award_uri')::jsonb WHERE mapping::text like '%subitem_1522399585738%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399628911','subitem_award_number')::jsonb WHERE schema::text like '%subitem_1522399628911%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399628911','subitem_award_number')::jsonb WHERE form::text like '%subitem_1522399628911%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399628911','subitem_award_number')::jsonb WHERE render::text like '%subitem_1522399628911%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399628911','subitem_award_number')::jsonb WHERE mapping::text like '%subitem_1522399628911%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522399651758','subitem_award_titles')::jsonb WHERE schema::text like '%subitem_1522399651758%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522399651758','subitem_award_titles')::jsonb WHERE form::text like '%subitem_1522399651758%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522399651758','subitem_award_titles')::jsonb WHERE render::text like '%subitem_1522399651758%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522399651758','subitem_award_titles')::jsonb WHERE mapping::text like '%subitem_1522399651758%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522721910626','subitem_award_title_language')::jsonb WHERE schema::text like '%subitem_1522721910626%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522721910626','subitem_award_title_language')::jsonb WHERE form::text like '%subitem_1522721910626%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522721910626','subitem_award_title_language')::jsonb WHERE render::text like '%subitem_1522721910626%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522721910626','subitem_award_title_language')::jsonb WHERE mapping::text like '%subitem_1522721910626%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522721929892','subitem_award_title')::jsonb WHERE schema::text like '%subitem_1522721929892%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522721929892','subitem_award_title')::jsonb WHERE form::text like '%subitem_1522721929892%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522721929892','subitem_award_title')::jsonb WHERE render::text like '%subitem_1522721929892%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522721929892','subitem_award_title')::jsonb WHERE mapping::text like '%subitem_1522721929892%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb WHERE json::text like '%subitem_1522399143519%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb WHERE json::text like '%subitem_1522399281603%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb WHERE json::text like '%subitem_1522399333375%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399412622','subitem_funder_names')::jsonb WHERE json::text like '%subitem_1522399412622%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb WHERE json::text like '%subitem_1522399416691%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522737543681','subitem_funder_name')::jsonb WHERE json::text like '%subitem_1522737543681%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399571623','subitem_award_numbers')::jsonb WHERE json::text like '%subitem_1522399571623%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399585738','subitem_award_uri')::jsonb WHERE json::text like '%subitem_1522399585738%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399628911','subitem_award_number')::jsonb WHERE json::text like '%subitem_1522399628911%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522399651758','subitem_award_titles')::jsonb WHERE json::text like '%subitem_1522399651758%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522721910626','subitem_award_title_language')::jsonb WHERE json::text like '%subitem_1522721910626%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522721929892','subitem_award_title')::jsonb WHERE json::text like '%subitem_1522721929892%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399143519','subitem_funder_identifiers')::jsonb WHERE json::text like '%subitem_1522399143519%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399281603','subitem_funder_identifier_type')::jsonb WHERE json::text like '%subitem_1522399281603%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399333375','subitem_funder_identifier')::jsonb WHERE json::text like '%subitem_1522399333375%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399412622','subitem_funder_names')::jsonb WHERE json::text like '%subitem_1522399412622%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399416691','subitem_funder_name_language')::jsonb WHERE json::text like '%subitem_1522399416691%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522737543681','subitem_funder_name')::jsonb WHERE json::text like '%subitem_1522737543681%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399571623','subitem_award_numbers')::jsonb WHERE json::text like '%subitem_1522399571623%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399585738','subitem_award_uri')::jsonb WHERE json::text like '%subitem_1522399585738%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399628911','subitem_award_number')::jsonb WHERE json::text like '%subitem_1522399628911%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522399651758','subitem_award_titles')::jsonb WHERE json::text like '%subitem_1522399651758%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522721910626','subitem_award_title_language')::jsonb WHERE json::text like '%subitem_1522721910626%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522721929892','subitem_award_title')::jsonb WHERE json::text like '%subitem_1522721929892%';

        DELETE FROM item_type_property WHERE id=21;

        -- SOURCE_TITLE = '1024'
        RAISE NOTICE 'Property ID being processed: 1024';
        UPDATE item_type SET render=replace(render::text,'cus_13"','cus_1024"')::jsonb WHERE render::text like '%cus_13"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb WHERE schema::text like '%subitem_1522650068558%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb WHERE form::text like '%subitem_1522650068558%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb WHERE render::text like '%subitem_1522650068558%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb WHERE mapping::text like '%subitem_1522650068558%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522650091861','subitem_record_name')::jsonb WHERE schema::text like '%subitem_1522650091861%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522650091861','subitem_record_name')::jsonb WHERE form::text like '%subitem_1522650091861%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522650091861','subitem_record_name')::jsonb WHERE render::text like '%subitem_1522650091861%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650091861','subitem_record_name')::jsonb WHERE mapping::text like '%subitem_1522650091861%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb WHERE json::text like '%subitem_1522650068558%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522650091861','subitem_record_name')::jsonb WHERE json::text like '%subitem_1522650091861%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522650068558','subitem_record_name_languag')::jsonb WHERE json::text like '%subitem_1522650068558%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522650091861','subitem_record_name')::jsonb WHERE json::text like '%subitem_1522650091861%';

        DELETE FROM item_type_property WHERE id=13;

        -- SOURCE_ID = '1023'
        RAISE NOTICE 'Property ID being processed: 1023';
        UPDATE item_type SET render=replace(render::text,'cus_10"','cus_1023"')::jsonb WHERE render::text like '%cus_10"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb WHERE schema::text like '%subitem_1522646500366%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb WHERE form::text like '%subitem_1522646500366%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb WHERE render::text like '%subitem_1522646500366%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb WHERE mapping::text like '%subitem_1522646500366%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522646572813','subitem_source_identifier')::jsonb WHERE schema::text like '%subitem_1522646572813%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522646572813','subitem_source_identifier')::jsonb WHERE form::text like '%subitem_1522646572813%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522646572813','subitem_source_identifier')::jsonb WHERE render::text like '%subitem_1522646572813%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522646572813','subitem_source_identifier')::jsonb WHERE mapping::text like '%subitem_1522646572813%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb WHERE json::text like '%subitem_1522646500366%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522646572813','subitem_source_identifier')::jsonb WHERE json::text like '%subitem_1522646572813%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522646500366','subitem_source_identifier_type')::jsonb WHERE json::text like '%subitem_1522646500366%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522646572813','subitem_source_identifier')::jsonb WHERE json::text like '%subitem_1522646572813%';

        DELETE FROM item_type_property WHERE id=10;

        -- ISSUE = '1026' 
        RAISE NOTICE 'Property ID being processed: 1026';
        UPDATE item_type SET render=replace(render::text,'cus_87"','cus_1026"')::jsonb WHERE render::text like '%cus_87"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256294723','subitem_issue')::jsonb WHERE schema::text like '%subitem_1551256294723%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256294723','subitem_issue')::jsonb WHERE form::text like '%subitem_1551256294723%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256294723','subitem_issue')::jsonb WHERE render::text like '%subitem_1551256294723%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256294723','subitem_issue')::jsonb WHERE mapping::text like '%subitem_1551256294723%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256294723','subitem_issue')::jsonb WHERE json::text like '%subitem_1551256294723%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256294723','subitem_issue')::jsonb WHERE json::text like '%subitem_1551256294723%';

        DELETE FROM item_type_property WHERE id=87;

        -- DEGREE_NAME = '1031' 
        RAISE NOTICE 'Property ID being processed: 1031';
        UPDATE item_type SET render=replace(render::text,'cus_80"','cus_1031"')::jsonb WHERE render::text like '%cus_80"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256126428','subitem_degreename')::jsonb WHERE schema::text like '%subitem_1551256126428%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256126428','subitem_degreename')::jsonb WHERE form::text like '%subitem_1551256126428%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256126428','subitem_degreename')::jsonb WHERE render::text like '%subitem_1551256126428%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256126428','subitem_degreename')::jsonb WHERE mapping::text like '%subitem_1551256126428%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256129013','subitem_degreename_language')::jsonb WHERE schema::text like '%subitem_1551256129013%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256129013','subitem_degreename_language')::jsonb WHERE form::text like '%subitem_1551256129013%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256129013','subitem_degreename_language')::jsonb WHERE render::text like '%subitem_1551256129013%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256129013','subitem_degreename_language')::jsonb WHERE mapping::text like '%subitem_1551256129013%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256126428','subitem_issue')::jsonb WHERE json::text like '%subitem_1551256126428%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256129013','subitem_degreename')::jsonb WHERE json::text like '%subitem_1551256129013%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256126428','subitem_issue')::jsonb WHERE json::text like '%subitem_1551256126428%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256129013','subitem_degreename')::jsonb WHERE json::text like '%subitem_1551256129013%';

        DELETE FROM item_type_property WHERE id=80;

        -- DATE_GRANTED = '1032'   
        RAISE NOTICE 'Property ID being processed: 1032';
        UPDATE item_type SET render=replace(render::text,'cus_79"','cus_1032"')::jsonb WHERE render::text like '%cus_79"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256096004','subitem_dategranted')::jsonb WHERE schema::text like '%subitem_1551256096004%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256096004','subitem_dategranted')::jsonb WHERE form::text like '%subitem_1551256096004%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256096004','subitem_dategranted')::jsonb WHERE render::text like '%subitem_1551256096004%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256096004','subitem_dategranted')::jsonb WHERE mapping::text like '%subitem_1551256096004%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256096004','subitem_dategranted')::jsonb WHERE json::text like '%subitem_1551256096004%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256096004','subitem_dategranted')::jsonb WHERE json::text like '%subitem_1551256096004%';

        DELETE FROM item_type_property WHERE id=79;

        -- DEGREE_GRANTOR = '1033'
        RAISE NOTICE 'Property ID being processed: 1033';
        UPDATE item_type SET render=replace(render::text,'cus_78"','cus_1033"')::jsonb WHERE render::text like '%cus_78"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb WHERE schema::text like '%subitem_1551256015892%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb WHERE form::text like '%subitem_1551256015892%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb WHERE render::text like '%subitem_1551256015892%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb WHERE mapping::text like '%subitem_1551256015892%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb WHERE schema::text like '%subitem_1551256027296%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb WHERE form::text like '%subitem_1551256027296%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb WHERE render::text like '%subitem_1551256027296%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb WHERE mapping::text like '%subitem_1551256027296%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb WHERE schema::text like '%subitem_1551256029891%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb WHERE form::text like '%subitem_1551256029891%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb WHERE render::text like '%subitem_1551256029891%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb WHERE mapping::text like '%subitem_1551256029891%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb WHERE schema::text like '%subitem_1551256037922%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb WHERE form::text like '%subitem_1551256037922%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb WHERE render::text like '%subitem_1551256037922%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb WHERE mapping::text like '%subitem_1551256037922%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb WHERE schema::text like '%subitem_1551256042287%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb WHERE form::text like '%subitem_1551256042287%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb WHERE render::text like '%subitem_1551256042287%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb WHERE mapping::text like '%subitem_1551256042287%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb WHERE schema::text like '%subitem_1551256047619%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb WHERE form::text like '%subitem_1551256047619%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb WHERE render::text like '%subitem_1551256047619%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb WHERE mapping::text like '%subitem_1551256047619%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb WHERE json::text like '%subitem_1551256015892%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb WHERE json::text like '%subitem_1551256027296%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb WHERE json::text like '%subitem_1551256029891%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb WHERE json::text like '%subitem_1551256037922%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb WHERE json::text like '%subitem_1551256042287%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb WHERE json::text like '%subitem_1551256047619%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256015892','subitem_degreegrantor_identifie')::jsonb WHERE json::text like '%subitem_1551256015892%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256027296','subitem_degreegrantor_identifier_name')::jsonb WHERE json::text like '%subitem_1551256027296%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256029891','subitem_degreegrantor_identifier_scheme')::jsonb WHERE json::text like '%subitem_1551256029891%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256037922','subitem_degreegrantor')::jsonb WHERE json::text like '%subitem_1551256037922%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256042287','subitem_degreegrantor_name')::jsonb WHERE json::text like '%subitem_1551256042287%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256047619','subitem_degreegrantor_language')::jsonb WHERE json::text like '%subitem_1551256047619%';

        DELETE FROM item_type_property WHERE id=78;

        -- DISSERTATION_NUMBER = '1030'
        RAISE NOTICE 'Property ID being processed: 1030';
        UPDATE item_type SET render=replace(render::text,'cus_82"','cus_1030"')::jsonb WHERE render::text like '%cus_82"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb WHERE schema::text like '%subitem_1551256171004%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb WHERE form::text like '%subitem_1551256171004%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb WHERE render::text like '%subitem_1551256171004%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb WHERE mapping::text like '%subitem_1551256171004%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb WHERE json::text like '%subitem_1551256171004%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256171004','subitem_dissertationnumber')::jsonb WHERE json::text like '%subitem_1551256171004%';
        DELETE FROM item_type_property WHERE id=82;

        -- CONTRIBUTOR = '1039'
        RAISE NOTICE 'Property ID being processed: 1039';
        UPDATE item_type SET render=replace(render::text,'cus_62"','cus_1039"')::jsonb WHERE render::text like '%cus_62"%';
        DELETE FROM item_type_property WHERE id=62;

        -- VOLUME = '1025'
        RAISE NOTICE 'Property ID being processed: 1025';
        UPDATE item_type SET render=replace(render::text,'cus_88"','cus_1025"')::jsonb WHERE render::text like '%cus_88"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256328147','subitem_volume')::jsonb WHERE schema::text like '%subitem_1551256328147%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256328147','subitem_volume')::jsonb WHERE form::text like '%subitem_1551256328147%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256328147','subitem_volume')::jsonb WHERE render::text like '%subitem_1551256328147%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256328147','subitem_volume')::jsonb WHERE mapping::text like '%subitem_1551256328147%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256328147','subitem_volume')::jsonb WHERE json::text like '%subitem_1551256328147%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256328147','subitem_volume')::jsonb WHERE json::text like '%subitem_1551256328147%';
        DELETE FROM item_type_property WHERE id=88;

        -- FILE = '1035'
        RAISE NOTICE 'Property ID being processed: 1035';
        UPDATE item_type SET render=replace(render::text,'cus_20"','cus_1035"')::jsonb WHERE render::text like '%cus_20"%';
        
        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652546580','url')::jsonb WHERE schema::text like '%subitem_1522652546580%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652546580','url')::jsonb WHERE form::text like '%subitem_1522652546580%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652546580','url')::jsonb WHERE render::text like '%subitem_1522652546580%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652546580','url')::jsonb WHERE mapping::text like '%subitem_1522652546580%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652548920','objectType')::jsonb WHERE schema::text like '%subitem_1522652548920%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652548920','objectType')::jsonb WHERE form::text like '%subitem_1522652548920%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652548920','objectType')::jsonb WHERE render::text like '%subitem_1522652548920%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652548920','objectType')::jsonb WHERE mapping::text like '%subitem_1522652548920%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652672693','label')::jsonb WHERE schema::text like '%subitem_1522652672693%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652672693','label')::jsonb WHERE form::text like '%subitem_1522652672693%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652672693','label')::jsonb WHERE render::text like '%subitem_1522652672693%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652672693','label')::jsonb WHERE mapping::text like '%subitem_1522652672693%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652685531','url')::jsonb WHERE schema::text like '%subitem_1522652685531%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652685531','url')::jsonb WHERE form::text like '%subitem_1522652685531%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652685531','url')::jsonb WHERE render::text like '%subitem_1522652685531%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652685531','url')::jsonb WHERE mapping::text like '%subitem_1522652685531%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652734962','format')::jsonb WHERE schema::text like '%subitem_1522652734962%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652734962','format')::jsonb WHERE form::text like '%subitem_1522652734962%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652734962','format')::jsonb WHERE render::text like '%subitem_1522652734962%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652734962','format')::jsonb WHERE mapping::text like '%subitem_1522652734962%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652740098','filesize')::jsonb WHERE schema::text like '%subitem_1522652740098%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652740098','filesize')::jsonb WHERE form::text like '%subitem_1522652740098%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652740098','filesize')::jsonb WHERE render::text like '%subitem_1522652740098%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652740098','filesize')::jsonb WHERE mapping::text like '%subitem_1522652740098%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522722119299','value')::jsonb WHERE schema::text like '%subitem_1522722119299%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522722119299','value')::jsonb WHERE form::text like '%subitem_1522722119299%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522722119299','value')::jsonb WHERE render::text like '%subitem_1522722119299%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522722119299','value')::jsonb WHERE mapping::text like '%subitem_1522722119299%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652747880','fileDate')::jsonb WHERE schema::text like '%subitem_1522652747880%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652747880','fileDate')::jsonb WHERE form::text like '%subitem_1522652747880%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652747880','fileDate')::jsonb WHERE render::text like '%subitem_1522652747880%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652747880','fileDate')::jsonb WHERE mapping::text like '%subitem_1522652747880%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522722132466','fileDateType')::jsonb WHERE schema::text like '%subitem_1522722132466%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522722132466','fileDateType')::jsonb WHERE form::text like '%subitem_1522722132466%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522722132466','fileDateType')::jsonb WHERE render::text like '%subitem_1522722132466%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522722132466','fileDateType')::jsonb WHERE mapping::text like '%subitem_1522722132466%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522739295711','fileDateValue')::jsonb WHERE schema::text like '%subitem_1522739295711%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522739295711','fileDateValue')::jsonb WHERE form::text like '%subitem_1522739295711%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522739295711','fileDateValue')::jsonb WHERE render::text like '%subitem_1522739295711%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522739295711','fileDateValue')::jsonb WHERE mapping::text like '%subitem_1522739295711%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523325300505','version')::jsonb WHERE schema::text like '%subitem_1523325300505%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523325300505','version')::jsonb WHERE form::text like '%subitem_1523325300505%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523325300505','version')::jsonb WHERE render::text like '%subitem_1523325300505%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523325300505','version')::jsonb WHERE mapping::text like '%subitem_1523325300505%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652546580','url')::jsonb WHERE json::text like '%subitem_1522652546580%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652548920','objectType')::jsonb WHERE json::text like '%subitem_1522652548920%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652672693','label')::jsonb WHERE json::text like '%subitem_1522652672693%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652685531','url')::jsonb WHERE json::text like '%subitem_1522652685531%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652734962','format')::jsonb WHERE json::text like '%subitem_1522652734962%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652740098','filesize')::jsonb WHERE json::text like '%subitem_1522652740098%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522722119299','value')::jsonb WHERE json::text like '%subitem_1522722119299%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652747880','fileDate')::jsonb WHERE json::text like '%subitem_1522652747880%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522722132466','fileDateType')::jsonb WHERE json::text like '%subitem_1522722132466%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522739295711','fileDateValue')::jsonb WHERE json::text like '%subitem_1522739295711%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1523325300505','version')::jsonb WHERE json::text like '%subitem_1523325300505%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652546580','url')::jsonb WHERE json::text like '%subitem_1522652546580%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652548920','objectType')::jsonb WHERE json::text like '%subitem_1522652548920%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652672693','label')::jsonb WHERE json::text like '%subitem_1522652672693%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652685531','url')::jsonb WHERE json::text like '%subitem_1522652685531%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652734962','format')::jsonb WHERE json::text like '%subitem_1522652734962%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652740098','filesize')::jsonb WHERE json::text like '%subitem_1522652740098%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522722119299','value')::jsonb WHERE json::text like '%subitem_1522722119299%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652747880','fileDate')::jsonb WHERE json::text like '%subitem_1522652747880%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522722132466','fileDateType')::jsonb WHERE json::text like '%subitem_1522722132466%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522739295711','fileDateValue')::jsonb WHERE json::text like '%subitem_1522739295711%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1523325300505','version')::jsonb WHERE json::text like '%subitem_1523325300505%';

        DELETE FROM item_type_property WHERE id=20;

        UPDATE item_type SET render=replace(render::text,'cus_65"','cus_1035"')::jsonb WHERE render::text like '%cus_65"%';
        DELETE FROM item_type_property WHERE id=65;

        UPDATE item_type SET render=replace(render::text,'cus_72"','cus_1035"')::jsonb WHERE render::text like '%cus_72"%';
        
        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255558587','url')::jsonb WHERE schema::text like '%subitem_1551255558587%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255558587','url')::jsonb WHERE form::text like '%subitem_1551255558587%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255558587','url')::jsonb WHERE render::text like '%subitem_1551255558587%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255558587','url')::jsonb WHERE mapping::text like '%subitem_1551255558587%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255581435','objectType')::jsonb WHERE schema::text like '%subitem_1551255581435%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255581435','objectType')::jsonb WHERE form::text like '%subitem_1551255581435%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255581435','objectType')::jsonb WHERE render::text like '%subitem_1551255581435%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255581435','objectType')::jsonb WHERE mapping::text like '%subitem_1551255581435%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255628842','label')::jsonb WHERE schema::text like '%subitem_1551255628842%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255628842','label')::jsonb WHERE form::text like '%subitem_1551255628842%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255628842','label')::jsonb WHERE render::text like '%subitem_1551255628842%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255628842','label')::jsonb WHERE mapping::text like '%subitem_1551255628842%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255570271','url')::jsonb WHERE schema::text like '%subitem_1551255570271%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255570271','url')::jsonb WHERE form::text like '%subitem_1551255570271%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255570271','url')::jsonb WHERE render::text like '%subitem_1551255570271%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255570271','url')::jsonb WHERE mapping::text like '%subitem_1551255570271%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255750794','format')::jsonb WHERE schema::text like '%subitem_1551255750794%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255750794','format')::jsonb WHERE form::text like '%subitem_1551255750794%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255750794','format')::jsonb WHERE render::text like '%subitem_1551255750794%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255750794','format')::jsonb WHERE mapping::text like '%subitem_1551255750794%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255788530','filesize')::jsonb WHERE schema::text like '%subitem_1551255788530%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255788530','filesize')::jsonb WHERE form::text like '%subitem_1551255788530%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255788530','filesize')::jsonb WHERE render::text like '%subitem_1551255788530%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255788530','filesize')::jsonb WHERE mapping::text like '%subitem_1551255788530%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1570068579439','value')::jsonb WHERE schema::text like '%subitem_1570068579439%';
        UPDATE item_type SET form=replace(form::text,'subitem_1570068579439','value')::jsonb WHERE form::text like '%subitem_1570068579439%';
        UPDATE item_type SET render=replace(render::text,'subitem_1570068579439','value')::jsonb WHERE render::text like '%subitem_1570068579439%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1570068579439','value')::jsonb WHERE mapping::text like '%subitem_1570068579439%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522652747880','fileDate')::jsonb WHERE schema::text like '%subitem_1522652747880%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522652747880','fileDate')::jsonb WHERE form::text like '%subitem_1522652747880%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522652747880','fileDate')::jsonb WHERE render::text like '%subitem_1522652747880%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522652747880','fileDate')::jsonb WHERE mapping::text like '%subitem_1522652747880%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255833133','fileDateType')::jsonb WHERE schema::text like '%subitem_1551255833133%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255833133','fileDateType')::jsonb WHERE form::text like '%subitem_1551255833133%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255833133','fileDateType')::jsonb WHERE render::text like '%subitem_1551255833133%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255833133','fileDateType')::jsonb WHERE mapping::text like '%subitem_1551255833133%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255828320','fileDateValue')::jsonb WHERE schema::text like '%subitem_1551255828320%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255828320','fileDateValue')::jsonb WHERE form::text like '%subitem_1551255828320%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255828320','fileDateValue')::jsonb WHERE render::text like '%subitem_1551255828320%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255828320','fileDateValue')::jsonb WHERE mapping::text like '%subitem_1551255828320%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255854908','version')::jsonb WHERE schema::text like '%subitem_1551255854908%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255854908','version')::jsonb WHERE form::text like '%subitem_1551255854908%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255854908','version')::jsonb WHERE render::text like '%subitem_1551255854908%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255854908','version')::jsonb WHERE mapping::text like '%subitem_1551255854908%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255558587','url')::jsonb WHERE json::text like '%subitem_1551255558587%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255581435','objectType')::jsonb WHERE json::text like '%subitem_1551255581435%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255628842','label')::jsonb WHERE json::text like '%subitem_1551255628842%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255570271','url')::jsonb WHERE json::text like '%subitem_1551255570271%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255750794','format')::jsonb WHERE json::text like '%subitem_1551255750794%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255788530','filesize')::jsonb WHERE json::text like '%subitem_1551255788530%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1570068579439','value')::jsonb WHERE json::text like '%subitem_1570068579439%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522652747880','fileDate')::jsonb WHERE json::text like '%subitem_1522652747880%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255833133','fileDateType')::jsonb WHERE json::text like '%subitem_1551255833133%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255828320','fileDateValue')::jsonb WHERE json::text like '%subitem_1551255828320%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255854908','version')::jsonb WHERE json::text like '%subitem_1551255854908%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255558587','url')::jsonb WHERE json::text like '%subitem_1551255558587%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255581435','objectType')::jsonb WHERE json::text like '%subitem_1551255581435%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255628842','label')::jsonb WHERE json::text like '%subitem_1551255628842%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255570271','url')::jsonb WHERE json::text like '%subitem_1551255570271%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255750794','format')::jsonb WHERE json::text like '%subitem_1551255750794%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255788530','filesize')::jsonb WHERE json::text like '%subitem_1551255788530%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1570068579439','value')::jsonb WHERE json::text like '%subitem_1570068579439%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522652747880','fileDate')::jsonb WHERE json::text like '%subitem_1522652747880%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255833133','fileDateType')::jsonb WHERE json::text like '%subitem_1551255833133%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255828320','fileDateValue')::jsonb WHERE json::text like '%subitem_1551255828320%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255854908','version')::jsonb WHERE json::text like '%subitem_1551255854908%';
        DELETE FROM item_type_property WHERE id=72;

        UPDATE item_type SET render=replace(render::text,'cus_101"','cus_1035"')::jsonb WHERE render::text like '%cus_101"%';
        
        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259623304','url')::jsonb WHERE schema::text like '%subitem_1551259623304%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259623304','url')::jsonb WHERE form::text like '%subitem_1551259623304%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259623304','url')::jsonb WHERE render::text like '%subitem_1551259623304%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259623304','url')::jsonb WHERE mapping::text like '%subitem_1551259623304%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259670908','objectType')::jsonb WHERE schema::text like '%subitem_1551259670908%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259670908','objectType')::jsonb WHERE form::text like '%subitem_1551259670908%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259670908','objectType')::jsonb WHERE render::text like '%subitem_1551259670908%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259670908','objectType')::jsonb WHERE mapping::text like '%subitem_1551259670908%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259762549','label')::jsonb WHERE schema::text like '%subitem_1551259762549%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259762549','label')::jsonb WHERE form::text like '%subitem_1551259762549%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259762549','label')::jsonb WHERE render::text like '%subitem_1551259762549%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259762549','label')::jsonb WHERE mapping::text like '%subitem_1551259762549%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259665538','url')::jsonb WHERE schema::text like '%subitem_1551259665538%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259665538','url')::jsonb WHERE form::text like '%subitem_1551259665538%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259665538','url')::jsonb WHERE render::text like '%subitem_1551259665538%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259665538','url')::jsonb WHERE mapping::text like '%subitem_1551259665538%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259906932','format')::jsonb WHERE schema::text like '%subitem_1551259906932%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259906932','format')::jsonb WHERE form::text like '%subitem_1551259906932%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259906932','format')::jsonb WHERE render::text like '%subitem_1551259906932%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259906932','format')::jsonb WHERE mapping::text like '%subitem_1551259906932%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259960284','filesize')::jsonb WHERE schema::text like '%subitem_1551259960284%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259960284','filesize')::jsonb WHERE form::text like '%subitem_1551259960284%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259960284','filesize')::jsonb WHERE render::text like '%subitem_1551259960284%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259960284','filesize')::jsonb WHERE mapping::text like '%subitem_1551259960284%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1570697598267','value')::jsonb WHERE schema::text like '%subitem_1570697598267%';
        UPDATE item_type SET form=replace(form::text,'subitem_1570697598267','value')::jsonb WHERE form::text like '%subitem_1570697598267%';
        UPDATE item_type SET render=replace(render::text,'subitem_1570697598267','value')::jsonb WHERE render::text like '%subitem_1570697598267%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1570697598267','value')::jsonb WHERE mapping::text like '%subitem_1570697598267%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259970148','fileDate')::jsonb WHERE schema::text like '%subitem_1551259970148%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259970148','fileDate')::jsonb WHERE form::text like '%subitem_1551259970148%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259970148','fileDate')::jsonb WHERE render::text like '%subitem_1551259970148%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259970148','fileDate')::jsonb WHERE mapping::text like '%subitem_1551259970148%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259979542','fileDateType')::jsonb WHERE schema::text like '%subitem_1551259979542%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259979542','fileDateType')::jsonb WHERE form::text like '%subitem_1551259979542%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259979542','fileDateType')::jsonb WHERE render::text like '%subitem_1551259979542%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259979542','fileDateType')::jsonb WHERE mapping::text like '%subitem_1551259979542%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551259972522','fileDateValue')::jsonb WHERE schema::text like '%subitem_1551259972522%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551259972522','fileDateValue')::jsonb WHERE form::text like '%subitem_1551259972522%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551259972522','fileDateValue')::jsonb WHERE render::text like '%subitem_1551259972522%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551259972522','fileDateValue')::jsonb WHERE mapping::text like '%subitem_1551259972522%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259623304','url')::jsonb WHERE json::text like '%subitem_1551259623304%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259670908','objectType')::jsonb WHERE json::text like '%subitem_1551259670908%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259762549','label')::jsonb WHERE json::text like '%subitem_1551259762549%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259665538','url')::jsonb WHERE json::text like '%subitem_1551259665538%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259906932','format')::jsonb WHERE json::text like '%subitem_1551259906932%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259960284','filesize')::jsonb WHERE json::text like '%subitem_1551259960284%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1570697598267','value')::jsonb WHERE json::text like '%subitem_1570697598267%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259970148','fileDate')::jsonb WHERE json::text like '%subitem_1551259970148%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259979542','fileDateType')::jsonb WHERE json::text like '%subitem_1551259979542%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551259972522','fileDateValue')::jsonb WHERE json::text like '%subitem_1551259972522%';
        
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259623304','url')::jsonb WHERE json::text like '%subitem_1551259623304%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259670908','objectType')::jsonb WHERE json::text like '%subitem_1551259670908%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259762549','label')::jsonb WHERE json::text like '%subitem_1551259762549%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259665538','url')::jsonb WHERE json::text like '%subitem_1551259665538%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259906932','format')::jsonb WHERE json::text like '%subitem_1551259906932%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259960284','filesize')::jsonb WHERE json::text like '%subitem_1551259960284%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1570697598267','value')::jsonb WHERE json::text like '%subitem_1570697598267%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259970148','fileDate')::jsonb WHERE json::text like '%subitem_1551259970148%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259979542','fileDateType')::jsonb WHERE json::text like '%subitem_1551259979542%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551259972522','fileDateValue')::jsonb WHERE json::text like '%subitem_1551259972522%';
        DELETE FROM item_type_property WHERE id=101;

        -- VERSION = '1015' 
        RAISE NOTICE 'Property ID being processed: 1015';
        UPDATE item_type SET render=replace(render::text,'cus_28"','cus_1015"')::jsonb WHERE render::text like '%cus_28"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523263171732','subitem_version')::jsonb WHERE schema::text like '%subitem_1523263171732%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523263171732','subitem_version')::jsonb WHERE form::text like '%subitem_1523263171732%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523263171732','subitem_version')::jsonb WHERE render::text like '%subitem_1523263171732%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523263171732','subitem_version')::jsonb WHERE mapping::text like '%subitem_1523263171732%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1523263171732','subitem_version')::jsonb WHERE json::text like '%subitem_1523263171732%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1523263171732','subitem_version')::jsonb WHERE json::text like '%subitem_1523263171732%';

        DELETE FROM item_type_property WHERE id=28;

        -- DATE = '1012'   
        RAISE NOTICE 'Property ID being processed: 1012';
        UPDATE item_type SET render=replace(render::text,'cus_11"','cus_1012"')::jsonb WHERE render::text like '%cus_11"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb WHERE schema::text like '%subitem_1522300695726%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb WHERE form::text like '%subitem_1522300695726%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb WHERE render::text like '%subitem_1522300695726%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb WHERE mapping::text like '%subitem_1522300695726%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb WHERE schema::text like '%subitem_1522300722591%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb WHERE form::text like '%subitem_1522300722591%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb WHERE render::text like '%subitem_1522300722591%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb WHERE mapping::text like '%subitem_1522300722591%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb WHERE json::text like '%subitem_1522300695726%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb WHERE json::text like '%subitem_1522300722591%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522300695726','subitem_date_issued_type')::jsonb WHERE json::text like '%subitem_1522300695726%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522300722591','subitem_date_issued_datetime')::jsonb WHERE json::text like '%subitem_1522300722591%';


        DELETE FROM item_type_property WHERE id=11;

        -- TEMPORAL = '1020'
        RAISE NOTICE 'Property ID being processed: 1020';
        UPDATE item_type SET render=replace(render::text,'cus_18"','cus_1020"')::jsonb WHERE render::text like '%cus_18"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb WHERE schema::text like '%subitem_1522658018441%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb WHERE form::text like '%subitem_1522658018441%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb WHERE render::text like '%subitem_1522658018441%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb WHERE mapping::text like '%subitem_1522658018441%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522658031721','subitem_temporal_text')::jsonb WHERE schema::text like '%subitem_1522658031721%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522658031721','subitem_temporal_text')::jsonb WHERE form::text like '%subitem_1522658031721%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522658031721','subitem_temporal_text')::jsonb WHERE render::text like '%subitem_1522658031721%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522658031721','subitem_temporal_text')::jsonb WHERE mapping::text like '%subitem_1522658031721%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb WHERE json::text like '%subitem_1522658018441%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522658031721','subitem_temporal_text')::jsonb WHERE json::text like '%subitem_1522658031721%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522658018441','subitem_temporal_languag')::jsonb WHERE json::text like '%subitem_1522658018441%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522658031721','subitem_temporal_text')::jsonb WHERE json::text like '%subitem_1522658031721%';


        DELETE FROM item_type_property WHERE id=18;

        -- BIBLIO_INFO = '1027'
        RAISE NOTICE 'Property ID being processed: 1027';
        UPDATE item_type SET render=replace(render::text,'cus_102"','cus_1027"')::jsonb WHERE render::text like '%cus_102"%';
        DELETE FROM item_type_property WHERE id=102;

        -- ACCESS_RIGHT = '1005'
        RAISE NOTICE 'Property ID being processed: 1005';
        UPDATE item_type SET render=replace(render::text,'cus_4"','cus_1005"')::jsonb WHERE render::text like '%cus_4"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522299639480','subitem_access_right')::jsonb WHERE schema::text like '%subitem_1522299639480%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522299639480','subitem_access_right')::jsonb WHERE form::text like '%subitem_1522299639480%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522299639480','subitem_access_right')::jsonb WHERE render::text like '%subitem_1522299639480%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522299639480','subitem_access_right')::jsonb WHERE mapping::text like '%subitem_1522299639480%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb WHERE schema::text like '%subitem_1600958577026%';
        UPDATE item_type SET form=replace(form::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb WHERE form::text like '%subitem_1600958577026%';
        UPDATE item_type SET render=replace(render::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb WHERE render::text like '%subitem_1600958577026%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb WHERE mapping::text like '%subitem_1600958577026%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522299639480','subitem_access_right')::jsonb WHERE json::text like '%subitem_1522299639480%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb WHERE json::text like '%subitem_1600958577026%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522299639480','subitem_access_right')::jsonb WHERE json::text like '%subitem_1522299639480%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1600958577026','subitem_access_right_uri')::jsonb WHERE json::text like '%subitem_1600958577026%';

        DELETE FROM item_type_property WHERE id=4;

        -- RIGHTS = '1007' 
        RAISE NOTICE 'Property ID being processed: 1007';
        UPDATE item_type SET render=replace(render::text,'cus_14"','cus_1007"')::jsonb WHERE render::text like '%cus_14"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522650717957','subitem_rights_language')::jsonb WHERE schema::text like '%subitem_1522650717957%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522650717957','subitem_rights_language')::jsonb WHERE form::text like '%subitem_1522650717957%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522650717957','subitem_rights_language')::jsonb WHERE render::text like '%subitem_1522650717957%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650717957','subitem_rights_language')::jsonb WHERE mapping::text like '%subitem_1522650717957%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522650727486','subitem_rights_resource')::jsonb WHERE schema::text like '%subitem_1522650727486%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522650727486','subitem_rights_resource')::jsonb WHERE form::text like '%subitem_1522650727486%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522650727486','subitem_rights_resource')::jsonb WHERE render::text like '%subitem_1522650727486%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522650727486','subitem_rights_resource')::jsonb WHERE mapping::text like '%subitem_1522650727486%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522651041219','subitem_rights')::jsonb WHERE schema::text like '%subitem_1522651041219%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522651041219','subitem_rights')::jsonb WHERE form::text like '%subitem_1522651041219%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522651041219','subitem_rights')::jsonb WHERE render::text like '%subitem_1522651041219%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522651041219','subitem_rights')::jsonb WHERE mapping::text like '%subitem_1522651041219%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522650717957','subitem_rights_language')::jsonb WHERE json::text like '%subitem_1522650717957%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522650727486','subitem_rights_resource')::jsonb WHERE json::text like '%subitem_1522650727486%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522651041219','subitem_rights')::jsonb WHERE json::text like '%subitem_1522651041219%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522650717957','subitem_rights_language')::jsonb WHERE json::text like '%subitem_1522650717957%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522650727486','subitem_rights_resource')::jsonb WHERE json::text like '%subitem_1522650727486%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522651041219','subitem_rights')::jsonb WHERE json::text like '%subitem_1522651041219%';

        DELETE FROM item_type_property WHERE id=14;


        UPDATE item_type SET render=replace(render::text,'cus_95"','cus_1007"')::jsonb WHERE render::text like '%cus_95"%';
        -- subitem_1551257025236　の置き換え対象なし
        UPDATE item_type SET schema=replace(schema::text,'.subitem_1551257047388','subitem_rights_language')::jsonb WHERE schema::text like '%.subitem_1551257047388%';
        UPDATE item_type SET form=replace(form::text,'.subitem_1551257047388','subitem_rights_language')::jsonb WHERE form::text like '%.subitem_1551257047388%';
        UPDATE item_type SET render=replace(render::text,'.subitem_1551257047388','subitem_rights_language')::jsonb WHERE render::text like '%.subitem_1551257047388%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'.subitem_1551257047388','subitem_rights_language')::jsonb WHERE mapping::text like '%.subitem_1551257047388%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551257030435','subitem_rights_resource')::jsonb WHERE schema::text like '%subitem_1551257030435%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551257030435','subitem_rights_resource')::jsonb WHERE form::text like '%subitem_1551257030435%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551257030435','subitem_rights_resource')::jsonb WHERE render::text like '%subitem_1551257030435%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551257030435','subitem_rights_resource')::jsonb WHERE mapping::text like '%subitem_1551257030435%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551257043769','subitem_rights')::jsonb WHERE schema::text like '%subitem_1551257043769%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551257043769','subitem_rights')::jsonb WHERE form::text like '%subitem_1551257043769%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551257043769','subitem_rights')::jsonb WHERE render::text like '%subitem_1551257043769%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551257043769','subitem_rights')::jsonb WHERE mapping::text like '%subitem_1551257043769%';

        UPDATE records_metadata SET json=replace(json::text,'.subitem_1551257047388','subitem_rights_language')::jsonb WHERE json::text like '%.subitem_1551257047388%';
        UPDATE records_metadata SET json=replace(json::text,'.subitem_1551257043769','subitem_rights_resource')::jsonb WHERE json::text like '%subitem_1551257030435%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551257043769','subitem_rights')::jsonb WHERE json::text like '%subitem_1551257043769%';

        UPDATE item_metadata SET json=replace(json::text,'.subitem_1551257047388','subitem_rights_language')::jsonb WHERE json::text like '%.subitem_1551257047388%';
        UPDATE item_metadata SET json=replace(json::text,'.subitem_1551257043769','subitem_rights_resource')::jsonb WHERE json::text like '%subitem_1551257030435%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551257043769','subitem_rights')::jsonb WHERE json::text like '%subitem_1551257043769%';

        DELETE FROM item_type_property WHERE id=95;

        -- RIGHTS_HOLDER = '1008'
        RAISE NOTICE 'Property ID being processed: 1008';
        UPDATE item_type SET render=replace(render::text,'cus_3"','cus_1008"')::jsonb WHERE render::text like '%cus_3"%';
        DELETE FROM item_type_property WHERE id=3;

        -- END_PAGE = '1029'  
        RAISE NOTICE 'Property ID being processed: 1029';
        UPDATE item_type SET render=replace(render::text,'cus_83"','cus_1029"')::jsonb WHERE render::text like '%cus_83"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256185532','subitem_end_page')::jsonb WHERE schema::text like '%subitem_1551256185532%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256185532','subitem_end_page')::jsonb WHERE form::text like '%subitem_1551256185532%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256185532','subitem_end_page')::jsonb WHERE render::text like '%subitem_1551256185532%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256185532','subitem_end_page')::jsonb WHERE mapping::text like '%subitem_1551256185532%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256185532','subitem_end_page')::jsonb WHERE json::text like '%subitem_1551256185532%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256185532','subitem_end_page')::jsonb WHERE json::text like '%subitem_1551256185532%';

        DELETE FROM item_type_property WHERE id=83;

        -- HEADING = '1041'
        RAISE NOTICE 'Property ID being processed: 1041';
        UPDATE item_type SET render=replace(render::text,'cus_175"','cus_1041"')::jsonb WHERE render::text like '%cus_175"%';

        DELETE FROM item_type_property WHERE id=175;

        UPDATE item_type SET render=replace(render::text,'cus_119"','cus_1041"')::jsonb WHERE render::text like '%cus_119"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1565671149650','subitem_heading_language')::jsonb WHERE schema::text like '%subitem_1565671149650%';
        UPDATE item_type SET form=replace(form::text,'subitem_1565671149650','subitem_heading_language')::jsonb WHERE form::text like '%subitem_1565671149650%';
        UPDATE item_type SET render=replace(render::text,'subitem_1565671149650','subitem_heading_language')::jsonb WHERE render::text like '%subitem_1565671149650%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1565671149650','subitem_heading_language')::jsonb WHERE mapping::text like '%subitem_1565671149650%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb WHERE schema::text like '%subitem_1565671169640%';
        UPDATE item_type SET form=replace(form::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb WHERE form::text like '%subitem_1565671169640%';
        UPDATE item_type SET render=replace(render::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb WHERE render::text like '%subitem_1565671169640%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb WHERE mapping::text like '%subitem_1565671169640%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1565671178623','subitem_heading_headline')::jsonb WHERE schema::text like '%subitem_1565671178623%';
        UPDATE item_type SET form=replace(form::text,'subitem_1565671178623','subitem_heading_headline')::jsonb WHERE form::text like '%subitem_1565671178623%';
        UPDATE item_type SET render=replace(render::text,'subitem_1565671178623','subitem_heading_headline')::jsonb WHERE render::text like '%subitem_1565671178623%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1565671178623','subitem_heading_headline')::jsonb WHERE mapping::text like '%subitem_1565671178623%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1565671149650','subitem_heading_language')::jsonb WHERE json::text like '%subitem_1565671149650%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb WHERE json::text like '%subitem_1565671169640%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1565671178623','subitem_heading_headline')::jsonb WHERE json::text like '%subitem_1565671178623%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1565671149650','subitem_heading_language')::jsonb WHERE json::text like '%subitem_1565671149650%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1565671169640','subitem_heading_banner_headline')::jsonb WHERE json::text like '%subitem_1565671169640%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1565671178623','subitem_heading_headline')::jsonb WHERE json::text like '%subitem_1565671178623%';

        DELETE FROM item_type_property WHERE id=119;
        -- LANGUAGE = '1003' 
        RAISE NOTICE 'Property ID being processed: 1003';
        UPDATE item_type SET render=replace(render::text,'cus_71"','cus_1003"')::jsonb WHERE render::text like '%cus_71"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551255818386','subitem_language')::jsonb WHERE schema::text like '%subitem_1551255818386%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551255818386','subitem_language')::jsonb WHERE form::text like '%subitem_1551255818386%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551255818386','subitem_language')::jsonb WHERE render::text like '%subitem_1551255818386%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551255818386','subitem_language')::jsonb WHERE mapping::text like '%subitem_1551255818386%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551255818386','subitem_language')::jsonb WHERE json::text like '%subitem_1551255818386%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551255818386','subitem_language')::jsonb WHERE json::text like '%subitem_1551255818386%';

        DELETE FROM item_type_property WHERE id=71;

        -- FILE_PRICE = '1036'
        RAISE NOTICE 'Property ID being processed: 1036';
        UPDATE item_type SET render=replace(render::text,'cus_103"','cus_1036"')::jsonb WHERE render::text like '%cus_103"%';
        DELETE FROM item_type_property WHERE id=103;

        -- IDENTIFIER = '1017' 
        RAISE NOTICE 'Property ID being processed: 1017';
        UPDATE item_type SET render=replace(render::text,'cus_176"','cus_1017"')::jsonb WHERE render::text like '%cus_176"%';
        DELETE FROM item_type_property WHERE id=176;

        -- RESOURCE_TYPE = '1014'
        RAISE NOTICE 'Property ID being processed: 1014';
        UPDATE item_type SET render=replace(render::text,'cus_8"','cus_1014"')::jsonb WHERE render::text like '%cus_8"%';
        DELETE FROM item_type_property WHERE id=8;

        UPDATE item_type SET render=replace(render::text,'cus_74"','cus_1014"')::jsonb WHERE render::text like '%cus_74"%';
        DELETE FROM item_type_property WHERE id=74;

        UPDATE item_type SET render=replace(render::text,'cus_104"','cus_1014"')::jsonb WHERE render::text like '%cus_104"%';
        DELETE FROM item_type_property WHERE id=104;

        UPDATE item_type SET render=replace(render::text,'cus_105"','cus_1014"')::jsonb WHERE render::text like '%cus_105"%';
        DELETE FROM item_type_property WHERE id=105;

        UPDATE item_type SET render=replace(render::text,'cus_106"','cus_1014"')::jsonb WHERE render::text like '%cus_106"%';
        DELETE FROM item_type_property WHERE id=106;

        UPDATE item_type SET render=replace(render::text,'cus_109"','cus_1014"')::jsonb WHERE render::text like '%cus_109"%';
        DELETE FROM item_type_property WHERE id=109;   

        UPDATE item_type SET render=replace(render::text,'cus_112"','cus_1014"')::jsonb WHERE render::text like '%cus_112"%';
        DELETE FROM item_type_property WHERE id=112;  

        UPDATE item_type SET render=replace(render::text,'cus_113"','cus_1014"')::jsonb WHERE render::text like '%cus_113"%';
        DELETE FROM item_type_property WHERE id=113;  

        UPDATE item_type SET render=replace(render::text,'cus_114"','cus_1014"')::jsonb WHERE render::text like '%cus_114"%';
        DELETE FROM item_type_property WHERE id=114;  

        UPDATE item_type SET render=replace(render::text,'cus_115"','cus_1014"')::jsonb WHERE render::text like '%cus_115"%';
        DELETE FROM item_type_property WHERE id=115;  

        UPDATE item_type SET render=replace(render::text,'cus_116"','cus_1014"')::jsonb WHERE render::text like '%cus_116"%';
        DELETE FROM item_type_property WHERE id=116;  

        UPDATE item_type SET render=replace(render::text,'cus_117"','cus_1014"')::jsonb WHERE render::text like '%cus_117"%';
        DELETE FROM item_type_property WHERE id=117;  

        UPDATE item_type SET render=replace(render::text,'cus_118"','cus_1014"')::jsonb WHERE render::text like '%cus_118"%';
        DELETE FROM item_type_property WHERE id=118;  

        -- START_PAGE = '1028'
        RAISE NOTICE 'Property ID being processed: 1028';
        UPDATE item_type SET render=replace(render::text,'cus_84"','cus_1028"')::jsonb WHERE render::text like '%cus_84"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256198917','subitem_start_page')::jsonb WHERE schema::text like '%subitem_1551256198917%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256198917','subitem_start_page')::jsonb WHERE form::text like '%subitem_1551256198917%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256198917','subitem_start_page')::jsonb WHERE render::text like '%subitem_1551256198917%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256198917','subitem_start_page')::jsonb WHERE mapping::text like '%subitem_1551256198917%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256198917','subitem_start_page')::jsonb WHERE json::text like '%subitem_1551256198917%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256198917','subitem_start_page')::jsonb WHERE json::text like '%subitem_1551256198917%';

        DELETE FROM item_type_property WHERE id=84;

        -- RELATION = '1019'
        RAISE NOTICE 'Property ID being processed: 1019';
        UPDATE item_type SET render=replace(render::text,'cus_12"','cus_1019"')::jsonb WHERE render::text like '%cus_12"%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522306207484','subitem_relation_type')::jsonb WHERE schema::text like '%subitem_1522306207484%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522306207484','subitem_relation_type')::jsonb WHERE form::text like '%subitem_1522306207484%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522306207484','subitem_relation_type')::jsonb WHERE render::text like '%subitem_1522306207484%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306207484','subitem_relation_type')::jsonb WHERE mapping::text like '%subitem_1522306207484%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb WHERE schema::text like '%subitem_1522306287251%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb WHERE form::text like '%subitem_1522306287251%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb WHERE render::text like '%subitem_1522306287251%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb WHERE mapping::text like '%subitem_1522306287251%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb WHERE schema::text like '%subitem_1522306382014%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb WHERE form::text like '%subitem_1522306382014%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb WHERE render::text like '%subitem_1522306382014%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb WHERE mapping::text like '%subitem_1522306382014%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb WHERE schema::text like '%subitem_1522306436033%';
        UPDATE item_type SET form=replace(form::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb WHERE form::text like '%subitem_1522306436033%';
        UPDATE item_type SET render=replace(render::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb WHERE render::text like '%subitem_1522306436033%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb WHERE mapping::text like '%subitem_1522306436033%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523320863692','subitem_relation_name')::jsonb WHERE schema::text like '%subitem_1523320863692%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523320863692','subitem_relation_name')::jsonb WHERE form::text like '%subitem_1523320863692%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523320863692','subitem_relation_name')::jsonb WHERE render::text like '%subitem_1523320863692%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523320863692','subitem_relation_name')::jsonb WHERE mapping::text like '%subitem_1523320863692%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb WHERE schema::text like '%subitem_1523320867455%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb WHERE form::text like '%subitem_1523320867455%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb WHERE render::text like '%subitem_1523320867455%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb WHERE mapping::text like '%subitem_1523320867455%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb WHERE schema::text like '%subitem_1523320909613%';
        UPDATE item_type SET form=replace(form::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb WHERE form::text like '%subitem_1523320909613%';
        UPDATE item_type SET render=replace(render::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb WHERE render::text like '%subitem_1523320909613%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb WHERE mapping::text like '%subitem_1523320909613%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1522306207484','subitem_relation_type')::jsonb WHERE json::text like '%subitem_1522306207484%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb WHERE json::text like '%subitem_1522306287251%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb WHERE json::text like '%subitem_1522306382014%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb WHERE json::text like '%subitem_1522306436033%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1523320863692','subitem_relation_name')::jsonb WHERE json::text like '%subitem_1523320863692%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb WHERE json::text like '%subitem_1523320867455%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb WHERE json::text like '%subitem_1523320909613%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1522306207484','subitem_relation_type')::jsonb WHERE json::text like '%subitem_1522306207484%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522306287251','subitem_relation_type_id')::jsonb WHERE json::text like '%subitem_1522306287251%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522306382014','subitem_relation_type_select')::jsonb WHERE json::text like '%subitem_1522306382014%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1522306436033','subitem_relation_type_id_text')::jsonb WHERE json::text like '%subitem_1522306436033%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1523320863692','subitem_relation_name')::jsonb WHERE json::text like '%subitem_1523320863692%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1523320867455','subitem_relation_name_language')::jsonb WHERE json::text like '%subitem_1523320867455%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1523320909613','subitem_relation_name_text')::jsonb WHERE json::text like '%subitem_1523320909613%';

        DELETE FROM item_type_property WHERE id=12;
        
        UPDATE item_type SET render=replace(render::text,'cus_92"','cus_1019"')::jsonb WHERE render::text like '%cus_92"%';
        -- subitem_1551256387752 の置換先はなし

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256388439','subitem_relation_type')::jsonb WHERE schema::text like '%subitem_1551256388439%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256388439','subitem_relation_type')::jsonb WHERE form::text like '%subitem_1551256388439%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256388439','subitem_relation_type')::jsonb WHERE render::text like '%subitem_1551256388439%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256388439','subitem_relation_type')::jsonb WHERE mapping::text like '%subitem_1551256388439%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256465077','subitem_relation_type_id')::jsonb WHERE schema::text like '%subitem_1551256465077%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256465077','subitem_relation_type_id')::jsonb WHERE form::text like '%subitem_1551256465077%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256465077','subitem_relation_type_id')::jsonb WHERE render::text like '%subitem_1551256465077%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256465077','subitem_relation_type_id')::jsonb WHERE mapping::text like '%subitem_1551256465077%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256629524','subitem_relation_type_select')::jsonb WHERE schema::text like '%subitem_1551256629524%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256629524','subitem_relation_type_select')::jsonb WHERE form::text like '%subitem_1551256629524%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256629524','subitem_relation_type_select')::jsonb WHERE render::text like '%subitem_1551256629524%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256629524','subitem_relation_type_select')::jsonb WHERE mapping::text like '%subitem_1551256629524%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256478339','subitem_relation_type_id_text')::jsonb WHERE schema::text like '%subitem_1551256478339%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256478339','subitem_relation_type_id_text')::jsonb WHERE form::text like '%subitem_1551256478339%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256478339','subitem_relation_type_id_text')::jsonb WHERE render::text like '%subitem_1551256478339%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256478339','subitem_relation_type_id_text')::jsonb WHERE mapping::text like '%subitem_1551256478339%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256480278','subitem_relation_name')::jsonb WHERE schema::text like '%subitem_1551256480278%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256480278','subitem_relation_name')::jsonb WHERE form::text like '%subitem_1551256480278%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256480278','subitem_relation_name')::jsonb WHERE render::text like '%subitem_1551256480278%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256480278','subitem_relation_name')::jsonb WHERE mapping::text like '%subitem_1551256480278%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256513476','subitem_relation_name_language')::jsonb WHERE schema::text like '%subitem_1551256513476%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256513476','subitem_relation_name_language')::jsonb WHERE form::text like '%subitem_1551256513476%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256513476','subitem_relation_name_language')::jsonb WHERE render::text like '%subitem_1551256513476%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256513476','subitem_relation_name_language')::jsonb WHERE mapping::text like '%subitem_1551256513476%';

        UPDATE item_type SET schema=replace(schema::text,'subitem_1551256498531','subitem_relation_name_text')::jsonb WHERE schema::text like '%subitem_1551256498531%';
        UPDATE item_type SET form=replace(form::text,'subitem_1551256498531','subitem_relation_name_text')::jsonb WHERE form::text like '%subitem_1551256498531%';
        UPDATE item_type SET render=replace(render::text,'subitem_1551256498531','subitem_relation_name_text')::jsonb WHERE render::text like '%subitem_1551256498531%';
        UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_1551256498531','subitem_relation_name_text')::jsonb WHERE mapping::text like '%subitem_1551256498531%';

        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256388439','subitem_relation_type')::jsonb WHERE json::text like '%subitem_1551256388439%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256465077','subitem_relation_type_id')::jsonb WHERE json::text like '%subitem_1551256465077%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256629524','subitem_relation_type_select')::jsonb WHERE json::text like '%subitem_1551256629524%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256478339','subitem_relation_type_id_text')::jsonb WHERE json::text like '%subitem_1551256478339%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256480278','subitem_relation_name')::jsonb WHERE json::text like '%subitem_1551256480278%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256513476','subitem_relation_name_language')::jsonb WHERE json::text like '%subitem_1551256513476%';
        UPDATE records_metadata SET json=replace(json::text,'subitem_1551256498531','subitem_relation_name_text')::jsonb WHERE json::text like '%subitem_1551256498531%';

        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256388439','subitem_relation_type')::jsonb WHERE json::text like '%subitem_1551256388439%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256465077','subitem_relation_type_id')::jsonb WHERE json::text like '%subitem_1551256465077%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256629524','subitem_relation_type_select')::jsonb WHERE json::text like '%subitem_1551256629524%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256478339','subitem_relation_type_id_text')::jsonb WHERE json::text like '%subitem_1551256478339%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256480278','subitem_relation_name')::jsonb WHERE json::text like '%subitem_1551256480278%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256513476','subitem_relation_name_language')::jsonb WHERE json::text like '%subitem_1551256513476%';
        UPDATE item_metadata SET json=replace(json::text,'subitem_1551256498531','subitem_relation_name_text')::jsonb WHERE json::text like '%subitem_1551256498531%';

        DELETE FROM item_type_property WHERE id=92;

        -- Upgrade all record version_id
        RAISE NOTICE 'Upgrade all record version_id';
        UPDATE records_metadata SET version_id=version_id+1 ;

    END IF;
END;
$$ LANGUAGE plpgsql;
