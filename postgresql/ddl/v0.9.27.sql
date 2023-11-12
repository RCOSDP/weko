

DELETE FROM item_type_property WHERE id=121;
DELETE FROM item_type_property WHERE id=122;
DELETE FROM item_type_property WHERE id=124;

DELETE FROM item_type_property WHERE id=103;
DELETE FROM item_type_property WHERE id=120;
DELETE FROM item_type_property WHERE id=132;
DELETE FROM item_type_property WHERE id=139;
DELETE FROM item_type_property WHERE id=142;
DELETE FROM item_type_property WHERE id=175;

-- LINK = '1044'
UPDATE item_type SET render=replace(render::text,'cus_142"','cus_1044"')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1587693279322','subitem_link_url')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1587693279322','subitem_link_url')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1587650325204','subitem_link_text')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1587650325204','subitem_link_text')::jsonb;

UPDATE item_type SET schema=replace(schema::text,'subitem_1587693278490','subitem_link_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1587693278490','subitem_link_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1587693278490','subitem_link_language')::jsonb;

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

UPDATE item_type SET schema=replace(schema::text,'subitem_1551255648112','subitem_title_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551255648112','subitem_title_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551255648112','subitem_title_language')::jsonb;

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

UPDATE item_type SET schema=replace(schema::text,'subitem_158622849035','subitem_text_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_158622849035','subitem_text_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_158622849035','subitem_text_language')::jsonb;

UPDATE records_metadata SET json=replace(json::text,'subitem_1586228465211','subitem_text_value')::jsonb;
UPDATE records_metadata SET json=replace(json::text,'"subitem_158622849035','subitem_text_language')::jsonb;

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

UPDATE item_type SET schema=replace(schema::text,'"subitem_158625340053','subitem_textarea_language')::jsonb;
UPDATE item_type SET form=replace(form::text,'"subitem_158625340053','subitem_textarea_language')::jsonb;
UPDATE item_type SET render=replace(render::text,'"subitem_158625340053','subitem_textarea_language')::jsonb;

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


-- START_PAGE = '1028'
UPDATE records_metadata SET json=replace(json::text,'subitem_1551256198917','subitem_start_page')::jsonb;
UPDATE item_metadata SET json=replace(json::text,'subitem_1551256198917','subitem_start_page')::jsonb;

UPDATE item_type SET render=replace(render::text,'cus_84"','cus_1028"')::jsonb;
UPDATE item_type SET schema=replace(schema::text,'subitem_1551256198917','subitem_start_page')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1551256198917','subitem_start_page')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1551256198917','subitem_start_page')::jsonb;



-- APC = '1006'
UPDATE records_metadata SET json=replace(json::text,'subitem_1523260933860','subitem_apc')::jsonb;
UPDATE item_type SET render=replace(render::text,'cus_27"','cus_1006"')::jsonb;
UPDATE item_type SET schema=replace(schema::text,'subitem_1523260933860','subitem_apc')::jsonb;
UPDATE item_type SET render=replace(render::text,'subitem_1523260933860','subitem_apc')::jsonb;

-- 値を引き継ぐことができない
-- UPDATE records_metadata SET json=replace(json::text,'subitem_1551255818386','subitem_language')::jsonb;
-- UPDATE item_type SET render=replace(render::text,'cus_71"','cus_1003"')::jsonb;


-- UPDATE records_metadata SET json=replace(json::text,'subitem_1551255647225','subitem_title')::jsonb;
-- UPDATE records_metadata SET json=replace(json::text,'subitem_1551255648112','subitem_title_language')::jsonb;

-- UPDATE item_type SET render=replace(render::text,'cus_67"','cus_1001"')::jsonb;
UPDATE item_type SET form=replace(form::text,'subitem_1523260933860','subitem_apc')::jsonb;
