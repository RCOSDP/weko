UPDATE item_type SET schema=replace(schema::text,'subitem_record_name','subitem_source_title')::jsonb WHERE schema::text like '%subitem_record_name%';
UPDATE item_type SET form=replace(form::text,'subitem_record_name','subitem_source_title')::jsonb WHERE form::text like '%subitem_record_name%';
UPDATE item_type SET render=replace(render::text,'subitem_record_name','subitem_source_title')::jsonb WHERE render::text like '%subitem_record_name%';

UPDATE item_type_mapping SET mapping=replace(mapping::text,'subitem_record_name','subitem_source_title')::jsonb WHERE mapping::text like '%subitem_record_name%';
UPDATE records_metadata SET json=replace(json::text,'subitem_record_name','subitem_source_title')::jsonb WHERE json::text like '%subitem_record_name%';
UPDATE item_metadata SET json=replace(json::text,'subitem_record_name','subitem_source_title')::jsonb WHERE json::text like '%subitem_record_name%';