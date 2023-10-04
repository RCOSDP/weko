from datetime import datetime
from jpcoar2_add_properties import (
    jpcoar_publisher_schema,
    jpcoar_publisher_form,
    dcterms_date_schema,
    dcterms_date_form,
    dcndl_edition_schema,
    dcndl_edition_form,
    dcndl_volume_title_schema,
    dcndl_volume_title_form,
    dcndl_original_language_schema,
    dcndl_original_language_form,
    dcterms_extent_schema,
    dcterms_extent_form,
    jpcoar_format_schema,
    jpcoar_format_form,
    jpcoar_holding_agent_schema,
    jpcoar_holding_agent_form,
    jpcoar_dataset_series_schema,
    jpcoar_dataset_series_form,
    jpcoar_catalog_schema,
    jpcoar_catalog_form
)
from jpcoar2_add_mapping import (
    jpcoar_publisher_mapping,
    dcterms_date_mapping,
    dcndl_edition_mapping,
    dcndl_volume_title_mapping,
    dcndl_original_language_mapping,
    dcterms_extent_mapping,
    jpcoar_format_mapping,
    jpcoar_holding_agent_mapping,
    jpcoar_dataset_series_mapping,
    jpcoar_catalog_mapping
)

from weko_records.api import ItemTypes, ItemTypeProps
from weko_records.models import ItemType, ItemTypeMapping

from invenio_db import db
from sqlalchemy.orm.attributes import flag_modified


#* Terminal command
#* sudo docker compose exec web invenio shell scripts/demo/jpcoar2_add_prop_to_metadata.py


#* Function for updating the target item type
def update_full_or_simple_item_type(
        item_type: ItemType = None,
        item_type_mapping: ItemTypeMapping = None,
        item_key: str = None,
        metadata_title: str = None,
        prop_title_i18n_en: str = None,
        prop_title_i18n_ja: str = None,
        prop_schema_properties: dict = None,
        prop_schema_type: str = None,
        prop_form: [dict] = None,
        prop_mapping: dict = None,
        prop_max_items: int = 0,
        prop_id_input_type: int = None,
        prop_option: dict = None,
        ) -> None:
    
    if item_type.schema["properties"].get(item_key):
        print(f"{metadata_title} already added to {item_type.item_type_name.name}.")
    else:
        if metadata_title \
        and prop_schema_properties \
        and prop_schema_type \
        and prop_form \
        and prop_mapping \
        and item_key:
            property_schema = {
                "items": prop_schema_properties,
                "maxItems": prop_max_items,
                "minItems": 0,
                "title": metadata_title,
                "type": prop_schema_type,
            }

            property_form = {
                "add": "New",
                "items": prop_form,
                "key": item_key,
                "style": {"add": "btn-success"},
                "title": metadata_title,
                "title_i18n": {"en": prop_title_i18n_en, "ja": prop_title_i18n_ja},
            }

            property_render_meta_list = {
                "input_maxItems": str(prop_max_items),
                "input_minItems": "1",
                "input_type": f'cus_{str(prop_id_input_type)}',
                "input_value": "",
                "option": prop_option,
                "title": metadata_title,
                "title_i18n": {"en": prop_title_i18n_en, "ja": prop_title_i18n_ja},
            }

            #* Modify target item type
            item_type.schema["properties"][item_key] = property_schema
            item_type.form.append(property_form)
            item_type.render["schemaeditor"]["schema"][item_key] = property_schema
            item_type.render["table_row_map"]["schema"]["properties"][item_key] = property_schema
            item_type.render["table_row_map"]["form"].append(property_form)
            item_type.render["meta_list"][item_key] = property_render_meta_list
            item_type.render["table_row"].append(item_key)
            item_type.render["table_row_map"]["mapping"][item_key] = prop_mapping
            item_type_mapping.mapping[item_key] = prop_mapping

            #* Update target item type using update() method from ItemTypes
            ItemTypes.update(
                id_=item_type.id,
                name=item_type.item_type_name.name,
                schema=item_type.schema,
                form=item_type.form,
                render=item_type.render,
            )

            try:
                #* Save changes to DB
                with db.session.begin_nested():
                    flag_modified(item_type, "schema")
                    flag_modified(item_type, "form")
                    flag_modified(item_type, "render")
                    flag_modified(item_type_mapping, "mapping")
                    db.session.merge(item_type)
                    db.session.merge(item_type_mapping)
                db.session.commit()
                print(
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    f'Successfully added {metadata_title} to {item_type.item_type_name.name}'
                )

            except Exception as e:
                db.session.rollback()
                print(
                    datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    f'Failed to add {metadata_title} to {item_type.item_type_name.name}'
                )

    return


#* Get Full and Simple Item Types as well as their respective Item Type Mapping
#* デフォルトアイテムタイプ（フル）Item Type
item_type_full: [ItemType or None] = [
    itemtype
    for itemtype
    in ItemTypes.get_all(True)
    if itemtype.item_type_name.name == "デフォルトアイテムタイプ（フル）"
]

#* デフォルトアイテムタイプ（シンプル）Item Type
item_type_simple: [ItemType or None] = [
    itemtype
    for itemtype
    in ItemTypes.get_all(True)
    if itemtype.item_type_name.name == "デフォルトアイテムタイプ（シンプル）"
]

#* デフォルトアイテムタイプ（フル）Item Type Mapping
item_type_full_mapping: [ItemTypeMapping or None] = [
    item_type
    for item_type
    in ItemTypeMapping.query.all()
    if item_type.item_type_id == item_type_full[0].id
]

#* デフォルトアイテムタイプ（シンプル）Item Type Mapping
item_type_simple_mapping: [ItemTypeMapping or None] = [
    item_type
    for item_type
    in ItemTypeMapping.query.all()
    if item_type.item_type_id == item_type_simple[0].id
]

#* All existing properties
all_item_type_properties = ItemTypeProps.get_records([])

#* JPCOAR - PUBLISHER
jpcoar_publisher_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "jpcoar_publisher"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(jpcoar_publisher_mapping.keys())[0],
    metadata_title = "JPCOAR PUBLISHER",
    prop_title_i18n_en = "JPCOAR PUBLISHER",
    prop_title_i18n_ja = "JPCOAR PUBLISHER",
    prop_schema_properties = jpcoar_publisher_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_publisher_form,
    prop_mapping = jpcoar_publisher_mapping,
    prop_max_items = 9999,
    prop_id_input_type = jpcoar_publisher_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(jpcoar_publisher_mapping.keys())[0],
    metadata_title = "JPCOAR PUBLISHER",
    prop_title_i18n_en = "JPCOAR PUBLISHER",
    prop_title_i18n_ja = "JPCOAR PUBLISHER",
    prop_schema_properties = jpcoar_publisher_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_publisher_form,
    prop_mapping = jpcoar_publisher_mapping,
    prop_max_items = 9999,
    prop_id_input_type = jpcoar_publisher_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* DCTERMS - DATE
dcterms_date_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "dcterms_date"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(dcterms_date_mapping.keys())[0],
    metadata_title = "DCTERMS DATE",
    prop_title_i18n_en = "DCTERMS DATE",
    prop_title_i18n_ja = "DCTERMS DATE",
    prop_schema_properties = dcterms_date_schema,
    prop_schema_type = "object",
    prop_form = dcterms_date_form,
    prop_mapping = dcterms_date_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcterms_date_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(dcterms_date_mapping.keys())[0],
    metadata_title = "DCTERMS DATE",
    prop_title_i18n_en = "DCTERMS DATE",
    prop_title_i18n_ja = "DCTERMS DATE",
    prop_schema_properties = dcterms_date_schema,
    prop_schema_type = "object",
    prop_form = dcterms_date_form,
    prop_mapping = dcterms_date_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcterms_date_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* DCNDL - EDITION
dcndl_edition_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "dcndl_edition"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(dcndl_edition_mapping.keys())[0],
    metadata_title = "DCNDL EDITION",
    prop_title_i18n_en = "DCNDL EDITION",
    prop_title_i18n_ja = "DCNDL EDITION",
    prop_schema_properties = dcndl_edition_schema,
    prop_schema_type = "object",
    prop_form = dcndl_edition_form,
    prop_mapping = dcndl_edition_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcndl_edition_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(dcndl_edition_mapping.keys())[0],
    metadata_title = "DCNDL EDITION",
    prop_title_i18n_en = "DCNDL EDITION",
    prop_title_i18n_ja = "DCNDL EDITION",
    prop_schema_properties = dcndl_edition_schema,
    prop_schema_type = "object",
    prop_form = dcndl_edition_form,
    prop_mapping = dcndl_edition_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcndl_edition_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* DCNDL - VOLUME TITLE
dcndl_volume_title_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "dcndl_volume_title"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(dcndl_volume_title_mapping.keys())[0],
    metadata_title = "DCNDL VOLUME TITLE",
    prop_title_i18n_en = "DCNDL VOLUME TITLE",
    prop_title_i18n_ja = "DCNDL VOLUME TITLE",
    prop_schema_properties = dcndl_volume_title_schema,
    prop_schema_type = "object",
    prop_form = dcndl_volume_title_form,
    prop_mapping = dcndl_volume_title_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcndl_volume_title_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(dcndl_volume_title_mapping.keys())[0],
    metadata_title = "DCNDL VOLUME TITLE",
    prop_title_i18n_en = "DCNDL VOLUME TITLE",
    prop_title_i18n_ja = "DCNDL VOLUME TITLE",
    prop_schema_properties = dcndl_volume_title_schema,
    prop_schema_type = "object",
    prop_form = dcndl_volume_title_form,
    prop_mapping = dcndl_volume_title_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcndl_volume_title_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* DCNDL - ORIGINAL LANGUAGE
dcndl_original_language_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "dcndl_original_language"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(dcndl_original_language_mapping.keys())[0],
    metadata_title = "DCNDL ORIGINAL LANGUAGE",
    prop_title_i18n_en = "DCNDL ORIGINAL LANGUAGE",
    prop_title_i18n_ja = "DCNDL ORIGINAL LANGUAGE",
    prop_schema_properties = dcndl_original_language_schema,
    prop_schema_type = "object",
    prop_form = dcndl_original_language_form,
    prop_mapping = dcndl_original_language_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcndl_original_language_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(dcndl_original_language_mapping.keys())[0],
    metadata_title = "DCNDL ORIGINAL LANGUAGE",
    prop_title_i18n_en = "DCNDL ORIGINAL LANGUAGE",
    prop_title_i18n_ja = "DCNDL ORIGINAL LANGUAGE",
    prop_schema_properties = dcndl_original_language_schema,
    prop_schema_type = "object",
    prop_form = dcndl_original_language_form,
    prop_mapping = dcndl_original_language_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcndl_original_language_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* DCTERMS - EXTENT
dcterms_extent_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "dcterms_extent"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(dcterms_extent_mapping.keys())[0],
    metadata_title = "DCTERMS EXTENT",
    prop_title_i18n_en = "DCTERMS EXTENT",
    prop_title_i18n_ja = "DCTERMS EXTENT",
    prop_schema_properties = dcterms_extent_schema,
    prop_schema_type = "object",
    prop_form = dcterms_extent_form,
    prop_mapping = dcterms_extent_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcterms_extent_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(dcterms_extent_mapping.keys())[0],
    metadata_title = "DCTERMS EXTENT",
    prop_title_i18n_en = "DCTERMS EXTENT",
    prop_title_i18n_ja = "DCTERMS EXTENT",
    prop_schema_properties = dcterms_extent_schema,
    prop_schema_type = "object",
    prop_form = dcterms_extent_form,
    prop_mapping = dcterms_extent_mapping,
    prop_max_items = 9999,
    prop_id_input_type = dcterms_extent_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* JPCOAR - FORMAT
jpcoar_format_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "jpcoar_format"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(jpcoar_format_mapping.keys())[0],
    metadata_title = "JPCOAR FORMAT",
    prop_title_i18n_en = "JPCOAR FORMAT",
    prop_title_i18n_ja = "JPCOAR FORMAT",
    prop_schema_properties = jpcoar_format_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_format_form,
    prop_mapping = jpcoar_format_mapping,
    prop_max_items = 9999,
    prop_id_input_type = jpcoar_format_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(jpcoar_format_mapping.keys())[0],
    metadata_title = "JPCOAR FORMAT",
    prop_title_i18n_en = "JPCOAR FORMAT",
    prop_title_i18n_ja = "JPCOAR FORMAT",
    prop_schema_properties = jpcoar_format_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_format_form,
    prop_mapping = jpcoar_format_mapping,
    prop_max_items = 9999,
    prop_id_input_type = jpcoar_format_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* JPCOAR - HOLDING AGENT
jpcoar_holding_agent_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "jpcoar_holding_agent"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(jpcoar_holding_agent_mapping.keys())[0],
    metadata_title = "JPCOAR HOLDING AGENT",
    prop_title_i18n_en = "JPCOAR HOLDING AGENT",
    prop_title_i18n_ja = "JPCOAR HOLDING AGENT",
    prop_schema_properties = jpcoar_holding_agent_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_holding_agent_form,
    prop_mapping = jpcoar_holding_agent_mapping,
    prop_max_items = 1,
    prop_id_input_type = jpcoar_holding_agent_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": False,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(jpcoar_holding_agent_mapping.keys())[0],
    metadata_title = "JPCOAR HOLDING AGENT",
    prop_title_i18n_en = "JPCOAR HOLDING AGENT",
    prop_title_i18n_ja = "JPCOAR HOLDING AGENT",
    prop_schema_properties = jpcoar_holding_agent_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_holding_agent_form,
    prop_mapping = jpcoar_holding_agent_mapping,
    prop_max_items = 1,
    prop_id_input_type = jpcoar_holding_agent_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": False,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* JPCOAR - DATASET SERIES
jpcoar_dataset_series_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "jpcoar_dataset_series"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(jpcoar_dataset_series_mapping.keys())[0],
    metadata_title = "JPCOAR DATASET SERIES",
    prop_title_i18n_en = "JPCOAR DATASET SERIES",
    prop_title_i18n_ja = "JPCOAR DATASET SERIES",
    prop_schema_properties = jpcoar_dataset_series_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_dataset_series_form,
    prop_mapping = jpcoar_dataset_series_mapping,
    prop_max_items = 1,
    prop_id_input_type = jpcoar_dataset_series_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": False,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(jpcoar_dataset_series_mapping.keys())[0],
    metadata_title = "JPCOAR DATASET SERIES",
    prop_title_i18n_en = "JPCOAR DATASET SERIES",
    prop_title_i18n_ja = "JPCOAR DATASET SERIES",
    prop_schema_properties = jpcoar_dataset_series_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_dataset_series_form,
    prop_mapping = jpcoar_dataset_series_mapping,
    prop_max_items = 1,
    prop_id_input_type = jpcoar_dataset_series_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": False,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)

#* JPCOAR - CATALOG
jpcoar_catalog_property_id = [
    prop.id 
    for prop
    in all_item_type_properties
    if prop.name == "jpcoar_catalog"
]
#? デフォルトアイテムタイプ（フル）
update_full_or_simple_item_type(
    item_type = item_type_full[0],
    item_type_mapping = item_type_full_mapping[0],
    item_key = list(jpcoar_catalog_mapping.keys())[0],
    metadata_title = "JPCOAR CATALOG",
    prop_title_i18n_en = "JPCOAR CATALOG",
    prop_title_i18n_ja = "JPCOAR CATALOG",
    prop_schema_properties = jpcoar_catalog_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_catalog_form,
    prop_mapping = jpcoar_catalog_mapping,
    prop_max_items = 9999,
    prop_id_input_type = jpcoar_catalog_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)
#? デフォルトアイテムタイプ（シンプル）
update_full_or_simple_item_type(
    item_type = item_type_simple[0],
    item_type_mapping = item_type_simple_mapping[0],
    item_key = list(jpcoar_catalog_mapping.keys())[0],
    metadata_title = "JPCOAR CATALOG",
    prop_title_i18n_en = "JPCOAR CATALOG",
    prop_title_i18n_ja = "JPCOAR CATALOG",
    prop_schema_properties = jpcoar_catalog_schema,
    prop_schema_type = "object",
    prop_form = jpcoar_catalog_form,
    prop_mapping = jpcoar_catalog_mapping,
    prop_max_items = 9999,
    prop_id_input_type = jpcoar_catalog_property_id[0],
    prop_option = {
        # "crtf": True,
        # "hidden": False,
        "multiple": True,
        # "oneline": False,
        # "required": False,
        # "showlist": True,
    },
)