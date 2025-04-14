
CREATE OR REPLACE FUNCTION fix_itemtype_issue_45614()
RETURNS void AS $$
DECLARE
    full_itemtype_id integer := 15;
    target_full_itemtype_id integer := 30002;
    full_itemtype_name_id integer := (SELECT name_id FROM item_type WHERE id = full_itemtype_id);
    full_itemtype_name text := 'デフォルトアイテムタイプ（フル）';
    simple_itemtype_id integer := 16;
    target_simple_itemtype_id integer := 30001;
    simple_itemtype_name_id integer := (SELECT name_id FROM item_type WHERE id = simple_itemtype_id);
    simple_itemtype_name text := 'デフォルトアイテムタイプ（シンプル）';
    full_update_dict jsonb := '{
        "item_1617186331708": "item_30002_title0",
        "item_1617186385884": "item_30002_alternative_title1",
        "item_1617186419668": "item_30002_creator2",
        "item_1617349709064": "item_30002_contributor3",
        "item_1617186476635": "item_30002_access_rights4",
        "item_1617351524846": "item_30002_apc5",
        "item_1617186499011": "item_30002_rights6",
        "item_1617610673286": "item_30002_rights_holder7",
        "item_1617186609386": "item_30002_subject8",
        "item_1617186626617": "item_30002_description9",
        "item_1617186643794": "item_30002_publisher10",
        "item_1617186660861": "item_30002_date11",
        "item_1617186702042": "item_30002_language12",
        "item_1617258105262": "item_30002_resource_type13",
        "item_1617349808926": "item_30002_version14",
        "item_1617265215918": "item_30002_version_type15",
        "item_1617186783814": "item_30002_identifier16",
        "item_1617186819068": "item_30002_identifier_registration17",
        "item_1617353299429": "item_30002_relation18", 
        "item_1617186859717": "item_30002_temporal19", 
        "item_1617186882738": "item_30002_geolocation20",
        "item_1617186901218": "item_30002_funding_reference21",
        "item_1617186920753": "item_30002_source_identifier22",
        "item_1617186941041": "item_30002_source_title23",
        "item_1617186959569": "item_30002_volume_number24",
        "item_1617186981471": "item_30002_issue_number25",
        "item_1617186994930": "item_30002_number_of_pages26",
        "item_1617187024783": "item_30002_page_start27",
        "item_1617187045071": "item_30002_page_end28",
        "item_1617187056579": "item_30002_bibliographic_information29",
        "item_1617187087799": "item_30002_dissertation_number30",
        "item_1617187112279": "item_30002_degree_name31",
        "item_1617187136212": "item_30002_date_granted32",
        "item_1617944105607": "item_30002_degree_grantor33",
        "item_1617187187528": "item_30002_conference34",
        "item_1617605131499": "item_30002_file35",
        "item_1617620223087": "item_30002_heading36",
        "item_1698591601": "item_30002_holding_agent_name37",
        "item_1698591602": "item_30002_original_language43",
        "item_1698591606": "item_30002_catalog39",
        "item_1698591610": "item_30002_dcterms_date38", 
        "item_1698591609": "item_30002_edition41",
        "item_1698591603": "item_30002_dataset_series42",
        "item_1698591607": "item_30002_jpcoar_format40",
        "item_1698591608": "item_30002_volume_title44",
        "item_1698591604": "item_30002_dcterms_extent46",
        "item_1698591605": "item_30002_publisher_information45"
    }';
    simple_update_dict jsonb := '{
        "item_1617186331708": "item_30001_title0",
        "item_1617186385884": "item_30001_alternative_title1",
        "item_1617186419668": "item_30001_creator2",
        "item_1551264340087": "item_30001_creator2",
        "item_1617349709064": "item_30001_contributor3",
        "item_1617186476635": "item_30001_access_rights4",
        "item_1617186499011": "item_30001_rights5",
        "item_1617611018077": "item_30001_rights_holder6", 
        "item_1617186609386": "item_30001_subject7",
        "item_1617186626617": "item_30001_description8",
        "item_1617186643794": "item_30001_publisher9",
        "item_1617186702042": "item_30001_language10",
        "item_1617258105262": "item_30001_resource_type11",
        "item_1617265215918": "item_30001_version_type12",
        "item_1623818042585": "item_30001_identifier_registration13",
        "item_1617353299429": "item_30001_relation14",
        "item_1617186901218": "item_30001_funding_reference15",
        "item_1617186920753": "item_30001_source_identifier16",
        "item_1617187056579": "item_30001_bibliographic_information17",
        "item_1617187087799": "item_30001_dissertation_number18",
        "item_1617187112279": "item_30001_degree_name19",
        "item_1617187136212": "item_30001_date_granted20",
        "item_1617944231687": "item_30001_degree_grantor21",
        "item_1617604990215": "item_30001_file22",
        "item_1617620290792": "item_30001_heading23"
    }';
    key text;
    value text;
    -- スペルミス修正
    spell_miss_update_dict jsonb := '{
        "subitem_degreegrantor_identifie": "subitem_degreegrantor_identifier",
        "holding_agent_name_idenfitier_uri": "holding_agent_name_identifier_uri",
        "holding_agent_name_idenfitier_value": "holding_agent_name_identifier_value",
        "holding_agent_name_idenfitier_scheme": "holding_agent_name_identifier_scheme"
    }';
BEGIN
    -- デフォルトアイテムタイプ（フル）
    IF (SELECT COUNT(id) FROM item_type WHERE id = target_full_itemtype_id)=0 THEN
        RAISE NOTICE 'processing item type: %', full_itemtype_name;
        RAISE NOTICE 'start: %', timeofday();
        FOR key, value IN SELECT * FROM jsonb_each_text(full_update_dict)
        LOOP
            RAISE NOTICE 'fix property key: % > %', key, value;
            UPDATE item_type SET schema=replace(schema::text, key, value)::jsonb WHERE id = full_itemtype_id AND schema::text like '%' || key || '"%';
            UPDATE item_type SET form=replace(form::text, key, value)::jsonb WHERE id = full_itemtype_id AND form::text like '%' || key || '"%';
            UPDATE item_type SET form=replace(form::text, key, value)::jsonb WHERE id = full_itemtype_id AND form::text like '%' || key || '[%';
            UPDATE item_type SET form=replace(form::text, key, value)::jsonb WHERE id = full_itemtype_id AND form::text like '%' || key || '.%';
            UPDATE item_type SET render=replace(render::text, key, value)::jsonb WHERE id = full_itemtype_id AND render::text like '%' || key || '"%';
            UPDATE item_type SET render=replace(render::text, key, value)::jsonb WHERE id = full_itemtype_id AND render::text like '%' || key || '[%';
            UPDATE item_type SET render=replace(render::text, key, value)::jsonb WHERE id = full_itemtype_id AND render::text like '%' || key || '.%';
            UPDATE item_type_mapping SET mapping=replace(mapping::text, key, value)::jsonb WHERE item_type_id=full_itemtype_id AND mapping::text like '%' || key || '"%';
            UPDATE records_metadata SET json=replace(json::text, key, value)::jsonb WHERE json->>'item_type_id'=CAST(full_itemtype_id as text) AND json::text like '%' || key || '%';
            UPDATE item_metadata SET json=replace(json::text, key, value)::jsonb WHERE item_type_id=full_itemtype_id AND json::text like '%' || key || '%';
        END LOOP;
        RAISE NOTICE 'end: %', timeofday();
    END IF;

    -- デフォルトアイテムタイプ（シンプル）
    IF (SELECT COUNT(id) FROM item_type WHERE id = target_simple_itemtype_id)=0 THEN
        RAISE NOTICE 'processing item type: %', simple_itemtype_name;
        RAISE NOTICE 'start: %', timeofday();
        FOR key, value IN SELECT * FROM jsonb_each_text(simple_update_dict)
        LOOP
            RAISE NOTICE 'fix property key: % > %', key, value;
            UPDATE item_type SET schema=replace(schema::text, key, value)::jsonb WHERE id = simple_itemtype_id AND schema::text like '%' || key || '"%';
            UPDATE item_type SET form=replace(form::text, key, value)::jsonb WHERE id = simple_itemtype_id AND form::text like '%' || key || '"%';
            UPDATE item_type SET form=replace(form::text, key, value)::jsonb WHERE id = simple_itemtype_id AND form::text like '%' || key || '[%';
            UPDATE item_type SET form=replace(form::text, key, value)::jsonb WHERE id = simple_itemtype_id AND form::text like '%' || key || '.%';
            UPDATE item_type SET render=replace(render::text, key, value)::jsonb WHERE id = simple_itemtype_id AND render::text like '%' || key || '"%';
            UPDATE item_type SET render=replace(render::text, key, value)::jsonb WHERE id = simple_itemtype_id AND render::text like '%' || key || '[%';
            UPDATE item_type SET render=replace(render::text, key, value)::jsonb WHERE id = simple_itemtype_id AND render::text like '%' || key || '.%';
            UPDATE item_type_mapping SET mapping=replace(mapping::text, key, value)::jsonb WHERE item_type_id = simple_itemtype_id AND mapping::text like '%' || key || '"%';
            UPDATE records_metadata SET json=replace(json::text, key, value)::jsonb WHERE json->>'item_type_id'=CAST(simple_itemtype_id as text) AND json::text like '%' || key || '%';
            UPDATE item_metadata SET json=replace(json::text, key, value)::jsonb WHERE item_type_id=simple_itemtype_id AND json::text like '%' || key || '%';
        END LOOP;
        RAISE NOTICE 'end: %', timeofday();
    END IF;

    IF (SELECT COUNT(id) FROM item_type WHERE id = target_full_itemtype_id)=0 AND (SELECT COUNT(id) FROM item_type WHERE id = target_simple_itemtype_id)=0 THEN
        RAISE NOTICE 'fix item_type_id';
        RAISE NOTICE 'start: %', timeofday();
        CREATE TEMPORARY TABLE tmp_item_type AS SELECT * FROM item_type where id in (full_itemtype_id,simple_itemtype_id);
        CREATE TEMPORARY TABLE tmp_item_type_name  AS SELECT * FROM item_type_name where id in (full_itemtype_name_id,simple_itemtype_name_id);
        UPDATE tmp_item_type_name SET id = target_full_itemtype_id WHERE id = full_itemtype_name_id;
        UPDATE tmp_item_type_name SET id = target_simple_itemtype_id WHERE id = simple_itemtype_name_id;
        UPDATE item_type_name SET name = concat('backup_',name) WHERE id = full_itemtype_name_id;
        UPDATE item_type_name SET name = concat('backup_',name) WHERE id = simple_itemtype_name_id;
        INSERT INTO item_type_name SELECT * FROM tmp_item_type_name where id in (target_simple_itemtype_id,target_full_itemtype_id);

        UPDATE tmp_item_type SET id = target_full_itemtype_id,name_id=target_full_itemtype_id WHERE id = full_itemtype_id;
        UPDATE tmp_item_type SET id = target_simple_itemtype_id,name_id=target_simple_itemtype_id WHERE id = simple_itemtype_id;
        INSERT INTO item_type SELECT * FROM tmp_item_type where id in (target_simple_itemtype_id,target_full_itemtype_id);
        DROP TABLE tmp_item_type_name;
        DROP TABLE tmp_item_type;

        UPDATE item_type_edit_history SET item_type_id = target_full_itemtype_id WHERE item_type_id = full_itemtype_id;
        UPDATE item_type_edit_history SET item_type_id = target_simple_itemtype_id WHERE item_type_id = simple_itemtype_id;
        UPDATE workflow_workflow SET itemtype_id = target_full_itemtype_id WHERE itemtype_id = full_itemtype_id;
        UPDATE workflow_workflow SET itemtype_id = target_simple_itemtype_id WHERE itemtype_id = simple_itemtype_id;
        UPDATE item_metadata SET item_type_id = target_full_itemtype_id WHERE item_type_id = full_itemtype_id;
        UPDATE item_metadata SET item_type_id = target_simple_itemtype_id WHERE item_type_id = simple_itemtype_id;
        UPDATE item_type_mapping SET item_type_id = target_full_itemtype_id WHERE item_type_id = full_itemtype_id;
        UPDATE item_type_mapping SET item_type_id = target_simple_itemtype_id WHERE item_type_id = simple_itemtype_id;

        DELETE FROM item_type WHERE id in (full_itemtype_id,simple_itemtype_id) ;
        DELETE FROM item_type_name WHERE id in (full_itemtype_name_id,simple_itemtype_name_id);
        
        UPDATE item_metadata SET json=replace(json::text,format('/items/jsonschema/%s"',full_itemtype_id),format('/items/jsonschema/%s"',target_full_itemtype_id))::jsonb WHERE item_type_id=full_itemtype_id AND json::text like format('%%/items/jsonschema/%s"%%',full_itemtype_id);
        UPDATE item_metadata SET json=replace(json::text,format('/items/jsonschema/%s"',simple_itemtype_id),format('/items/jsonschema/%s"',target_simple_itemtype_id))::jsonb WHERE item_type_id=simple_itemtype_id AND json::text like format('%%/items/jsonschema/%s"%%',simple_itemtype_id);
        UPDATE item_metadata SET json=replace(json::text,format('"$schema": "%s"',full_itemtype_id),format('"$schema": "/items/jsonschema/%s"',target_full_itemtype_id))::jsonb WHERE item_type_id=full_itemtype_id AND json::text like format('%%"$schema": "%s"%%',full_itemtype_id);
        UPDATE item_metadata SET json=replace(json::text,format('"$schema": "%s"',simple_itemtype_id),format('"$schema": "/items/jsonschema/%s"',target_simple_itemtype_id))::jsonb WHERE item_type_id=simple_itemtype_id AND json::text like format('%%"$schema": "%s"%%',simple_itemtype_id);

        UPDATE records_metadata SET json=replace(json::text,format('"item_type_id": "%s"',full_itemtype_id),format('"item_type_id": "%s"',target_full_itemtype_id))::jsonb WHERE json->>'item_type_id'=CAST(full_itemtype_id as text) AND json::text like format('%%"item_type_id": "%s"%%',full_itemtype_id);
        UPDATE records_metadata SET json=replace(json::text,format('"item_type_id": "%s"',simple_itemtype_id),format('"item_type_id": "%s"',target_simple_itemtype_id))::jsonb WHERE json->>'item_type_id'=CAST(simple_itemtype_id as text) AND json::text like format('%%"item_type_id": "%s"%%',simple_itemtype_id);
        RAISE NOTICE 'end: %', timeofday();
    END IF;

    -- スペルミス修正
    RAISE NOTICE 'fix spell miss';
    RAISE NOTICE 'start: %', timeofday();
    FOR key, value IN SELECT * FROM jsonb_each_text(spell_miss_update_dict)
    LOOP
        IF (SELECT COUNT(id) FROM item_type WHERE schema::text like '%' || key || '"%')>0 THEN
            RAISE NOTICE 'fix spell miss: % > %', key, value;
            RAISE NOTICE 'start: %', timeofday();
            UPDATE item_type SET schema=replace(schema::text, key || '"', value || '"')::jsonb WHERE schema::text like '%' || key || '"%';
            UPDATE item_type SET form=replace(form::text, key || '"', value || '"')::jsonb WHERE form::text like '%' || key || '"%';
            UPDATE item_type SET form=replace(form::text, key || '[', value || '[')::jsonb WHERE form::text like '%' || key || '[%';
            UPDATE item_type SET form=replace(form::text, key || '.', value || '.')::jsonb WHERE form::text like '%' || key || '.%';
            UPDATE item_type SET render=replace(render::text, key || '"', value || '"')::jsonb WHERE render::text like '%' || key || '"%';
            UPDATE item_type SET render=replace(render::text, key || '[', value || '[')::jsonb WHERE render::text like '%' || key || '[%';
            UPDATE item_type SET render=replace(render::text, key || '.', value || '.')::jsonb WHERE render::text like '%' || key || '.%';

            UPDATE item_type_mapping SET mapping=replace(mapping::text, key || '"', value || '"')::jsonb WHERE mapping::text like '%' || key || '"%';

            UPDATE item_type_property SET schema=replace(schema::text, key || '"', value || '"')::jsonb WHERE schema::text like '%' || key || '"%';
            UPDATE item_type_property SET form=replace(form::text, key || '"', value || '"')::jsonb WHERE form::text like '%' || key || '"%';
            UPDATE item_type_property SET form=replace(form::text, key || '[', value || '[')::jsonb WHERE form::text like '%' || key || '[%';
            UPDATE item_type_property SET form=replace(form::text, key || '.', value || '.')::jsonb WHERE form::text like '%' || key || '.%';
            UPDATE item_type_property SET forms=replace(forms::text, key || '"', value || '"')::jsonb WHERE forms::text like '%' || key || '"%';
            UPDATE item_type_property SET forms=replace(forms::text, key || '[', value || '[')::jsonb WHERE forms::text like '%' || key || '[%';
            UPDATE item_type_property SET forms=replace(forms::text, key || '.', value || '.')::jsonb WHERE forms::text like '%' || key || '.%';

            UPDATE records_metadata SET json=replace(json::text, key || '"', value || '"')::jsonb WHERE json::text like '%' || key || '"%';
            UPDATE item_metadata SET json=replace(json::text, key || '"', value || '"')::jsonb WHERE json::text like '%' || key || '"%';
            RAISE NOTICE 'end: %', timeofday();
        END IF;
    END LOOP;
    RAISE NOTICE 'end: %', timeofday();
END;
$$ LANGUAGE plpgsql;
