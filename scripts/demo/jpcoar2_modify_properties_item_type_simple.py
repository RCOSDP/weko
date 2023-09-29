from datetime import datetime

from weko_records.api import ItemTypes, ItemTypeProps
from weko_records.models import ItemType, ItemTypeProperty, ItemTypeMapping, ItemMetadata, FileMetadata

from invenio_db import db
from sqlalchemy.orm.attributes import flag_modified


"""
(8) Add attributes to the following elements according to JPCOAR2.0 specifications.
• jpcoar:creator@creatorType
• jpcoar:creator > jpcoar:creatorName@nameType
• jpcoar:contributor > jpcoar:contributorName@nameType
• jpcoar:fundingReference > jpcoar:funderIdentifier@funderIdentifierTypeURI
• jpcoar:fundingReference > jpcoar:awardNumber@awardNumberType
"""

#* Terminal command
#* sudo docker compose exec web invenio shell scripts/demo/jpcoar2_modify_properties_item_type_simple.py


def update_simple_item_type(
        item_type: ItemType = None,
        item_type_mapping: ItemTypeMapping = None,
        item_type_target_form: list = None,
        item_type_target_render_form: list = None,
        item_type_property: ItemTypeProperty = None,
        item_key: str = None,
        add_to_schema: dict = None,
        add_to_form: dict = None,
        add_to_form_singular: dict = None,
        add_to_mapping: dict = None,
        ) -> None:
    
    schema_key = list(add_to_schema.keys())[0]
    mapping_key = list(add_to_mapping.keys())[0]

    if add_to_schema is not None \
            and add_to_form is not None \
            and add_to_form_singular is not None \
            and add_to_mapping is not None :

        #* Modify target ITEM TYPE
        item_type.schema["properties"][item_key][schema_key] = add_to_schema[schema_key]
        item_type_target_form[0]["items"].append(add_to_form)
        item_type.render["schemaeditor"]["schema"][item_key] = add_to_schema[schema_key]
        item_type.render["table_row_map"]["schema"]["properties"][item_key] = add_to_schema[schema_key]
        item_type_target_render_form[0]["items"].append(add_to_form)
        item_type.render["table_row_map"]["mapping"][item_key][mapping_key] = add_to_mapping[mapping_key]

        #* Modify target ITEM TYPE PROPERTY
        item_type_property.schema["properties"][schema_key] = add_to_schema[schema_key]
        item_type_property.form["items"].append(add_to_form_singular)
        item_type_property.forms["items"].append(add_to_form)

        #* Modify target ITEM TYPE MAPPING
        for mapping in item_type_mapping:
            if mapping.mapping.get(item_key) is not None:
                mapping.mapping[item_key][mapping_key] = add_to_mapping[mapping_key]
            else:
                print(mapping)

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
                flag_modified(item_type_property, "schema")
                flag_modified(item_type_property, "form")
                flag_modified(item_type_property, "forms")
                for mapping in item_type_mapping:
                    flag_modified(mapping, "mapping")
                    db.session.merge(mapping)
                db.session.merge(item_type)
                db.session.merge(item_type_property)
            db.session.commit()
            print(
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                f'Successfully modified {item_type.item_type_name.name} for CREATOR TYPE'
            )

        except Exception as err:
            db.session.rollback()
            print(
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                err,
                f'Failed to modify {item_type.item_type_name.name} for CREATOR TYPE'
            )

    return


#* Get Simple Item Type as well as Simple Item Type Mapping
#* デフォルトアイテムタイプ（シンプル）Item Type
item_type_simple: [ItemType or None] = [
    itemtype
    for itemtype
    in ItemTypes.get_all(True)
    if itemtype.item_type_name.name == "デフォルトアイテムタイプ（シンプル）"
]

#* デフォルトアイテムタイプ（シンプル）Item Type Mapping
item_type_simple_mapping: [ItemTypeMapping or None] = [
    item_type
    for item_type
    in ItemTypeMapping.query.all()
    if item_type.item_type_id == item_type_simple[0].id
]
item_type_simple_mapping_keys: [str] or None = None
if len(item_type_simple_mapping) > 0:
    item_type_simple_mapping_keys = [key for key in item_type_simple_mapping[0].mapping.keys()]

#* All existing properties
all_item_type_properties = ItemTypeProps.get_records([])
schema_keys = list(item_type_simple[0].schema["properties"].keys())

#* ========================================== CREATOR TYPE
#? Parent key for Creator Item
creator_item_key: [str] = [
    creator
    for creator
    in list(item_type_simple[0].schema["properties"].keys())
    if item_type_simple[0].schema["properties"][creator].get("items", {}).get("properties", {}).get("creatorAffiliations")
    or item_type_simple[0].schema["properties"][creator].get("properties", {}).get("creatorAffiliations")
]

#? Element of Creator from itemtype.form
creator_form_list: list = [
    creator_form
    for creator_form
    in item_type_simple[0].form
    if creator_form.get("title", {}) == "Creator"
]

#? Element of Creator from itemtype.render["table_row_map"]["form"] 
creator_render_form_list: list = [
    creator_form
    for creator_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if creator_form.get("title", {}) == "Creator"
]

#? Creator Property for Creator Type
creator_property: ItemTypeProperty or None = None
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for creator_schema_key in schema_keys:
        if schema.get(creator_schema_key, {}).get('title'):
            if "作成者名" == schema.get(creator_schema_key, {}).get('title') \
                    or "Creator" == schema.get(creator_schema_key, {}).get('title'):
                creator_property = prop

#? Creator Type schema data
add_to_schema_creator_type = {
    "creatorType": {
        "type": "string",
        "format": "text",
        "title": "作成者タイプ"
    }
}

#? Creator Type form data
add_to_form_creator_type = {
    "key": "parentkey[].creatorType",
    "type": "text",
    "title": "作成者タイプ",
    "title_i18n": {"en": "Creator Type", "ja": "作成者タイプ"}
}

#? Creator Type form data for singular form use
add_to_form_singular_creator_type = {
    "key": "parentkey.creatorType",
    "type": "text",
    "title": "作成者タイプ",
    "title_i18n": {"en": "Creator Type", "ja": "作成者タイプ"}
}

#? Creator Type mapping data
add_to_mapping_creator_type = {
    "creatorType": {
        "@value": "creatorType",
    }
}

###! UPDATE CHANGES IN ITEM TYPE Simple FOR CREATOR TYPE ~ START
if creator_item_key:
    #* ITEM TYPE SIMPLE
    update_simple_item_type(
        item_type = item_type_simple[0],
        item_type_mapping = item_type_simple_mapping,
        item_type_target_form = creator_form_list,
        item_type_target_render_form = creator_form_list,
        item_type_property = creator_property,
        item_key = creator_item_key[0],
        add_to_schema = add_to_schema_creator_type,
        add_to_form = add_to_form_creator_type,
        add_to_form_singular = add_to_form_singular_creator_type,
        add_to_mapping = add_to_mapping_creator_type,
    )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR CREATOR TYPE ~ END


#* ========================================== CREATOR NAME TYPE
#? Parent key for Creator Item
creator_item_key: [str] = [
    creator
    for creator
    in list(item_type_simple[0].schema["properties"].keys())
    if item_type_simple[0].schema["properties"][creator].get("items", {}).get("properties", {}).get("creatorAffiliations")
    or item_type_simple[0].schema["properties"][creator].get("properties", {}).get("creatorAffiliations")
]

#? Element of Creator from itemtype.form
creator_form_list: list = [
    creator_form
    for creator_form
    in item_type_simple[0].form
    if creator_form.get("title", {}) == "Creator"
]

#? Get Creator Name form
creator_name_form: list = [
    creator_form
    for creator_form
    in creator_form_list[0]["items"]
    if "creatorName"
    in creator_form["key"]
]

#? Get Creator Name prefix
creator_name_type_key_prefix: str or None = None
creator_name_type_key_singular_prefix: str or None = None
if creator_name_form:
    creator_name_form = creator_name_form[0].get("items", [])
if creator_name_form:
    creator_name_type_key_prefix = (".").join(creator_name_form[0]["key"].split(".")[0:-1])
    creator_name_type_key_singular_prefix = creator_name_type_key_prefix.replace("[", "").replace("]", "")

#? Element of Creator from itemtype.render["table_row_map"]["form"]
creator_render_form_list: list = [
    creator_form
    for creator_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if creator_form.get("title", {}) == "Creator"
]

#? Get Creator Name form from itemtype.render["table_row_map"]["form"]
creator_name_render_form: list = [a for a in creator_render_form_list[0]["items"] if "creatorName" in a["key"]]

#? Creator Property for Creator Name Type
creator_property: ItemTypeProperty or None = None
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for creator_schema_key in schema_keys:
        if schema.get(creator_schema_key, {}).get('title'):
            if "作成者名" == schema.get(creator_schema_key, {}).get('title'):
                creator_property = prop

#? Get Creator Name schema from Creator Property
creator_name_property_schema_property: dict or None = None
if len(creator_property.schema.get("properties", {})) > 0:
    for schema_prop_key in list(creator_property.schema["properties"].keys()):
        if len(creator_property.schema["properties"][schema_prop_key].get("items", {})) > 0:
            if len(creator_property.schema["properties"][schema_prop_key]["items"].get("properties", {})) > 0:
                if len(creator_property.schema["properties"][schema_prop_key]["items"]["properties"].get("creatorName", {})) > 0:
                    creator_name_property_schema_property = creator_property.schema["properties"][schema_prop_key]["items"]["properties"]

#? Get Creator Name form from Creator Property
creator_name_property_form: dict or None = None
if len(creator_property.form.get("items")) > 0:
    for creator_prop_form in creator_property.form["items"]:
        if creator_prop_form.get("items") is not None:
            for creator_prop_form_sublevel in creator_prop_form.get("items"):
                if "creatorNames" in creator_prop_form_sublevel["key"]:
                    creator_name_property_form = creator_prop_form["items"]

#? Get Creator Name forms from Creator Property
creator_name_property_forms: dict or None = None
if len(creator_property.forms.get("items")) > 0:
    for creator_prop_form in creator_property.forms["items"]:
        if creator_prop_form.get("items") is not None:
            for creator_prop_form_sublevel in creator_prop_form.get("items"):
                if "creatorNames" in creator_prop_form_sublevel["key"]:
                    creator_name_property_forms = creator_prop_form["items"]

#? Creator Name Type schema data
add_to_schema_creator_name_type = {
    "creatorNameType": {
        "type": "string",
        "format": "select",
        "enum": ["Organizational", "Personal"],
        "currentEnum": ["Organizational", "Personal"],
        "title": "作成者名タイプ",
    }
}

#? Creator Name Type form data
add_to_form_creator_name_type = {
    "key": creator_name_type_key_prefix + ".creatorNameType",
    "type": "select",
    "title": "作成者名タイプ",
    "title_i18n": {"en": "Creator Name Type", "ja": "作成者名タイプ"},
    "titleMap": [
        {
            "value": "Organizational",
            "name": "Organizational"
        },
        {
            "value": "Personal",
            "name": "Personal"
        }
    ],
}

#? Creator Name Type form data for singular form use
add_to_form_singular_creator_name_type = {
    "key": creator_name_type_key_singular_prefix + ".creatorNameType",
    "type": "text",
    "title": "作成者名タイプ",
    "title_i18n": {"en": "Creator Name Type", "ja": "作成者名タイプ"}
}

###! UPDATE CHANGES IN ITEM TYPE Simple FOR CREATOR NAME TYPE ~ START
if creator_item_key:
    #* Modify ITEM TYPE Simple for Creator Name Type
    item_type_simple[0].schema["properties"][creator_item_key[0]]["creatorNameType"] = add_to_schema_creator_name_type["creatorNameType"]
    creator_name_form.append(add_to_form_creator_name_type)
    item_type_simple[0].render["schemaeditor"]["schema"][creator_item_key[0]] = add_to_schema_creator_name_type["creatorNameType"]
    item_type_simple[0].render["table_row_map"]["schema"]["properties"][creator_item_key[0]] = add_to_schema_creator_name_type["creatorNameType"]
    creator_name_render_form[0]["items"].append(add_to_form_creator_name_type)
    if len(item_type_simple[0].render["table_row_map"]["mapping"][creator_item_key[0]]["jpcoar_mapping"].get("creator")) > 0:
        if len(item_type_simple[0].render["table_row_map"]["mapping"][creator_item_key[0]]["jpcoar_mapping"]["creator"].get("creatorName")) > 0:
            if len(item_type_simple[0].render["table_row_map"]["mapping"][creator_item_key[0]]["jpcoar_mapping"]["creator"]["creatorName"].get("@attributes")) > 0:
                item_type_simple[0].render["table_row_map"]["mapping"][creator_item_key[0]]["jpcoar_mapping"]["creator"]["creatorName"]["@attributes"]["nameType"] = "creatorNames.creatorNameType"

    #* Modify CREATOR ITEM TYPE PROPERTY for Creator Name Type
    if len(creator_name_property_schema_property):
        creator_name_property_schema_property["creatorNameType"] = add_to_schema_creator_name_type["creatorNameType"]
        creator_name_property_form.append(add_to_form_singular_creator_name_type)
        creator_name_property_forms.append(add_to_form_creator_name_type)

    #* Modify ITEM TYPE Simple MAPPING for Creator Name Type
    creator_item_type_mapping = None
    for itm in item_type_simple_mapping:
        for key in item_type_simple_mapping_keys:
            try:
                if isinstance(itm.mapping[key]["jpcoar_mapping"], dict):
                    if itm.mapping[key]["jpcoar_mapping"].get("creator", {}) is not None \
                            or len(itm.mapping[key]["jpcoar_mapping"].get("creator", {}).keys()) > 0:
                        if itm.mapping[key]["jpcoar_mapping"].get("creator", {}).get("creatorName") is not None:
                            itm.mapping[key]["jpcoar_mapping"]["creator"]["creatorName"]["@attributes"]["nameType"] = "creatorNames.creatorNameType"
            except:
                continue

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            flag_modified(creator_property, "schema")
            flag_modified(creator_property, "form")
            flag_modified(creator_property, "forms")
            for mapping in item_type_simple_mapping:
                flag_modified(mapping, "mapping")
                db.session.merge(mapping)
            db.session.merge(item_type_simple[0])
            db.session.merge(creator_property)
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for CREATOR NAME TYPE'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for CREATOR NAME TYPE'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR CREATOR NAME TYPE ~ END


#* ========================================== CONTRIBUTOR NAME TYPE
#? Parent key for Contributor Item
contributor_item_key: [str] = [
    contributor
    for contributor
    in list(item_type_simple[0].schema["properties"].keys())
    if item_type_simple[0].schema["properties"][contributor].get("items", {}).get("properties", {}).get("contributorAffiliations")
    or item_type_simple[0].schema["properties"][contributor].get("properties", {}).get("contributorAffiliations")
]

#? Element of Contributor from itemtype.form
contributor_form_list: list = [
    contributor_form
    for contributor_form
    in item_type_simple[0].form
    if contributor_form.get("title", {}) == "Contributor"
    or contributor_form.get("title_i18n", {}).get("en", {}) == "Contributor"
    or contributor_form.get("title_i18n", {}).get("ja", {}) == "寄与者"
]

#? Get Contributor Name form
contributor_name_form: list = [
    contributor_form
    for contributor_form
    in contributor_form_list[0]["items"]
    if "contributorName"
    in contributor_form["key"]
]

#? Get Contributor Name prefix
contributor_name_type_key_prefix: str or None = None
contributor_name_type_key_singular_prefix: str or None = None
if contributor_name_form:
    contributor_name_form = contributor_name_form[0].get("items", [])
if contributor_name_form:
    contributor_name_type_key_prefix = (".").join(contributor_name_form[0]["key"].split(".")[0:-1])
    contributor_name_type_key_singular_prefix = contributor_name_type_key_prefix.replace("[", "").replace("]", "")

#? Element of Contributor from itemtype.render["table_row_map"]["form"]
contributor_render_form_list: list = [
    contributor_form
    for contributor_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if contributor_form.get("title", {}) == "Contributor"
]

#? Get Contributor Name form from itemtype.render["table_row_map"]["form"]
contributor_name_render_form: list = [
    contrib_name_render_form
    for contrib_name_render_form
    in contributor_render_form_list[0]["items"]
    if "contributorName" in contrib_name_render_form["key"]
]

#? Contributor Property for Contributor Name Type
# contributor_property: ItemTypeProperty or None = None
contributor_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for contributor_schema_key in schema_keys:
        if schema.get(contributor_schema_key, {}).get('title'):
            if "寄与者" in schema.get(contributor_schema_key, {}).get('title') \
                    or "Contributor" in schema.get(contributor_schema_key, {}).get('title'):
                contributor_property.append(prop)

#? Contributor Name Type schema data
add_to_schema_contributor_name_type = {
    "contributorNameType": {
        "type": "string",
        "format": "select",
        "enum": ["Organizational", "Personal"],
        "currentEnum": ["Organizational", "Personal"],
        "title": "寄与者名タイプ",
    }
}

#? Contributor Name Type form data
add_to_form_contributor_name_type = {
    "key": contributor_name_type_key_prefix + ".contributorNameType",
    "type": "select",
    "title": "作成者名タイプ",
    "title_i18n": {"en": "Contributor Name Type", "ja": "寄与者名タイプ"},
    "titleMap": [
        {
            "value": "Organizational",
            "name": "Organizational"
        },
        {
            "value": "Personal",
            "name": "Personal"
        }
    ],
}

#? Contributor Name Type form data for singular form use
add_to_form_singular_contributor_name_type = {
    "key": contributor_name_type_key_singular_prefix + ".contributorNameType",
    "type": "text",
    "title": "作成者名タイプ",
    "title_i18n": {"en": "Contributor Name Type", "ja": "寄与者名タイプ"}
}

###! UPDATE ITEM TYPE Simple FOR CONTRIBUTOR NAME TYPE ~ START
if contributor_item_key:
    #* Modify ITEM TYPE Simple for Contributor Name Type
    item_type_simple[0].schema["properties"][contributor_item_key[0]]["contributorNameType"] = add_to_schema_contributor_name_type["contributorNameType"]
    contributor_name_form.append(add_to_form_contributor_name_type)
    item_type_simple[0].render["schemaeditor"]["schema"][contributor_item_key[0]] = add_to_schema_contributor_name_type["contributorNameType"]
    item_type_simple[0].render["table_row_map"]["schema"]["properties"][contributor_item_key[0]] = add_to_schema_contributor_name_type["contributorNameType"]
    contributor_name_render_form[0]["items"].append(add_to_form_contributor_name_type)
    if len(item_type_simple[0].render["table_row_map"]["mapping"][contributor_item_key[0]]["jpcoar_mapping"].get("contributor")) > 0:
        if len(item_type_simple[0].render["table_row_map"]["mapping"][contributor_item_key[0]]["jpcoar_mapping"]["contributor"].get("contributorName")) > 0:
            if len(item_type_simple[0].render["table_row_map"]["mapping"][contributor_item_key[0]]["jpcoar_mapping"]["contributor"]["contributorName"].get("@attributes")) > 0:
                item_type_simple[0].render["table_row_map"]["mapping"][contributor_item_key[0]]["jpcoar_mapping"]["contributor"]["contributorName"]["@attributes"]["nameType"] = "contributorNames.creatorNameType"

    #* Modify CONTRIBUTOR ITEM TYPE PROPERTY for Contributor Name Type
    if contributor_property:
        for contributor_prop in contributor_property:
            #? Get Contributor Name schema from Contributor Property
            contributor_name_property_schema_property: dict or None = None
            if len(contributor_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(contributor_prop.schema["properties"].keys()):
                    if len(contributor_prop.schema["properties"][schema_prop_key].get("items", {})) > 0:
                        if len(contributor_prop.schema["properties"][schema_prop_key]["items"].get("properties", {})) > 0:
                            if len(contributor_prop.schema["properties"][schema_prop_key]["items"]["properties"].get("contributorName", {})) > 0:
                                contributor_name_property_schema_property = contributor_prop.schema["properties"][schema_prop_key]["items"]["properties"]

            #? Get Contributor Name form from Contributor Property
            contributor_name_property_form: dict or None = None
            if len(contributor_prop.form.get("items")) > 0:
                for contributor_prop_form in contributor_prop.form["items"]:
                    if contributor_prop_form.get("items") is not None:
                        for contributor_prop_form_sublevel in contributor_prop_form.get("items"):
                            if "contributorNames" in contributor_prop_form_sublevel["key"]:
                                contributor_name_property_form = contributor_prop_form["items"]

            #? Get Contributor Name forms from Contributor Property
            contributor_name_property_forms: dict or None = None
            if len(contributor_prop.forms.get("items")) > 0:
                for contributor_prop_form in contributor_prop.forms["items"]:
                    if contributor_prop_form.get("items") is not None:
                        for contributor_prop_form_sublevel in contributor_prop_form.get("items"):
                            if "contributorNames" in contributor_prop_form_sublevel["key"]:
                                contributor_name_property_forms = contributor_prop_form["items"]
            
            if contributor_name_property_schema_property \
                    and contributor_name_property_form \
                    and contributor_name_property_forms:
                contributor_name_property_schema_property["contributorNameType"] = add_to_schema_contributor_name_type["contributorNameType"]
                contributor_name_property_form.append(add_to_form_singular_contributor_name_type)
                contributor_name_property_forms.append(add_to_form_contributor_name_type)


    #* Modify ITEM TYPE Simple MAPPING for Contributor Name Type
    contributor_item_type_mapping = None
    for itm in item_type_simple_mapping:
        for key in item_type_simple_mapping_keys:
            try:
                if isinstance(itm.mapping[key]["jpcoar_mapping"], dict):
                    if itm.mapping[key]["jpcoar_mapping"].get("contributor", {}) is not None \
                            or len(itm.mapping[key]["jpcoar_mapping"].get("contributor", {}).keys()) > 0:
                        if itm.mapping[key]["jpcoar_mapping"].get("contributor", {}).get("contributorName") is not None:
                            itm.mapping[key]["jpcoar_mapping"]["contributor"]["contributorName"]["@attributes"]["nameType"] = "contributorNames.contributorNameType"
            except:
                continue

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for contributor_prop in contributor_property:
                flag_modified(contributor_prop, "schema")
                flag_modified(contributor_prop, "form")
                flag_modified(contributor_prop, "forms")
                db.session.merge(contributor_prop)
            for mapping in item_type_simple_mapping:
                flag_modified(mapping, "mapping")
                db.session.merge(mapping)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for CONTRIBUTOR NAME TYPE'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for CONTRIBUTOR NAME TYPE'
        )
###! UPDATE ITEM TYPE Simple FOR CONTRIBUTOR NAME TYPE ~ END


#* ========================================== FUNDING IDENTIFIER TYPE URI
#? Parent key for Funding Reference Item
funding_reference_key: str or None = None
for fund_ref_key in list(item_type_simple[0].schema["properties"].keys()):
    if item_type_simple[0].schema["properties"][fund_ref_key].get("items"):
        if item_type_simple[0].schema["properties"][fund_ref_key]["items"].get("properties", {}):
            for prop_key in list(item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"].keys()):
                if item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key].get("title"):
                    if item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "助成機関識別子" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "助成機関名" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "研究課題番号" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "研究課題名":
                        funding_reference_key = fund_ref_key

#? Element of Funding Reference from itemtype.form
funding_reference_form_list: list or None = None
for funding_reference_form in item_type_simple[0].form:
    if funding_reference_form.get("items"):
        if isinstance(funding_reference_form["items"], list):
            if funding_reference_form["items"]:
                if funding_reference_form["items"][0].get("items"):
                    for fund_ref_item in funding_reference_form["items"][0]["items"]:
                        if fund_ref_item.get("title") == "助成機関識別子タイプ" \
                                or fund_ref_item.get("title") == "助成機関識別子":
                            funding_reference_form_list = funding_reference_form["items"]

#? Get Funding Reference Funder Identifier form
funding_reference_funder_identifier_form_list: list or None = None
for fund_ref_id_form in funding_reference_form_list:
    if fund_ref_id_form["title"] == "助成機関識別子":
        if fund_ref_id_form.get("items"):
            funding_reference_funder_identifier_form_list = fund_ref_id_form["items"]

#? Get Funding Reference Funder Identifier prefix
funder_identifier_type_key_prefix: str or None = None
funder_identifier_type_key_singular_prefix: str or None = None
funder_identifier_type_key_mapping_use: str or None = None
if funding_reference_funder_identifier_form_list:
    funder_identifier_type_key_prefix = (".").join(funding_reference_funder_identifier_form_list[0]["key"].split(".")[0:-1])
    funder_identifier_type_key_singular_prefix = funder_identifier_type_key_prefix.replace("[", "").replace("]", "")
    funder_identifier_type_key_mapping_use: str or None = funder_identifier_type_key_singular_prefix.split(".")[-1]

#? Element of Funding Reference from itemtype.render["table_row_map"]["form"]
funding_reference_render_form_list: list or None = None
for funding_reference_render_form in item_type_simple[0].render["table_row_map"]["form"]:
    if funding_reference_render_form.get("items"):
        if isinstance(funding_reference_render_form["items"], list):
            if funding_reference_render_form["items"]:
                if funding_reference_render_form["items"][0].get("items"):
                    for fund_ref_item in funding_reference_render_form["items"][0]["items"]:
                        if fund_ref_item.get("title") == "助成機関識別子タイプ" \
                                or fund_ref_item.get("title") == "助成機関識別子":
                            funding_reference_render_form_list = funding_reference_render_form["items"]

#? Get Funding Reference Funder Identifier form from itemtype.render["table_row_map"]["form"]
funding_reference_funder_identifier_render_form_list: list or None = None
for fund_ref_id_render_form in funding_reference_render_form_list:
    if fund_ref_id_render_form["title"] == "助成機関識別子":
        if fund_ref_id_render_form.get("items"):
            funding_reference_funder_identifier_render_form_list = fund_ref_id_render_form["items"]

#? Funding Reference Property for Funder Identifier Type
funding_reference_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for funding_reference_schema_key in schema_keys:
        if schema.get(funding_reference_schema_key, {}).get('title'):
            if "助成機関" in schema.get(funding_reference_schema_key, {}).get('title'):
                funding_reference_property.append(prop)

#? Funder Identifier schema data
add_to_schema_funder_identifier_type_uri = {
    "funderIdentifierTypeURI": {
        "type": "string",
        "format": "text",
        "title": "助成機関識別子タイプURI",
        "title_i18n": {
            "ja": "助成機関識別子タイプURI",
            "en": "Funder Identifier Type URI"
        }
    },
}

#? Funder Identifier form data
add_to_form_funder_identifier_type_uri = {
    "key": funder_identifier_type_key_prefix + ".funderIdentifierTypeURI",
    "type": "string",
    "title": "助成機関識別子タイプURI",
    "title_i18n": {"en": "Funder Identifier Type URI", "ja": "助成機関識別子タイプURI"}
}

#? Contributor Name Type form data for singular form use
add_to_form_singular_funder_identifier_type_uri = {
    "key": funder_identifier_type_key_singular_prefix + ".funderIdentifierTypeURI",
    "type": "string",
    "title": "助成機関識別子タイプURI",
    "title_i18n": {"en": "Funder Identifier Type URI", "ja": "助成機関識別子タイプURI"}
}

###! UPDATE ITEM TYPE Simple FOR FUNDING IDENTIFIER TYPE URI ~ START
if funding_reference_key:
    #* Modify ITEM TYPE Simple for FUNDING IDENTIFIER TYPE URI
    item_type_simple[0].schema["properties"][funding_reference_key]["funderIdentifierTypeURI"] = add_to_schema_funder_identifier_type_uri["funderIdentifierTypeURI"]
    funding_reference_funder_identifier_form_list.append(add_to_form_funder_identifier_type_uri)
    item_type_simple[0].render["schemaeditor"]["schema"][funding_reference_key] = add_to_schema_funder_identifier_type_uri["funderIdentifierTypeURI"]
    item_type_simple[0].render["table_row_map"]["schema"]["properties"][funding_reference_key] = add_to_schema_funder_identifier_type_uri["funderIdentifierTypeURI"]
    funding_reference_render_form_list.append(add_to_form_funder_identifier_type_uri)
    if len(item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"].get("fundingReference")) > 0:
        if len(item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"]["fundingReference"].get("funderIdentifier")) > 0:
            if len(item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"]["fundingReference"]["funderIdentifier"].get("@attributes")) > 0:
                item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"]["fundingReference"]["funderIdentifier"]["@attributes"]["funderIdentifierTypeURI"] = f"{funder_identifier_type_key_mapping_use}.funderIdentifierTypeURI"

    #* Modify FUNDING REFERENCE ITEM TYPE PROPERTY for FUNDING IDENTIFIER TYPE URI
    if funding_reference_property:
        for fund_ref_prop in funding_reference_property:
            #? Get Funder Identifier schema from Funding Reference Property
            funder_identifier_property_schema_property: dict or None = None
            if len(fund_ref_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(fund_ref_prop.schema["properties"].keys()):
                    if len(fund_ref_prop.schema["properties"][schema_prop_key].get("properties", {})) > 0:
                        for schema_prop_sub_lv_key in list(fund_ref_prop.schema["properties"][schema_prop_key].get("properties", {}).keys()):
                            if fund_ref_prop.schema["properties"][schema_prop_key]["properties"][schema_prop_sub_lv_key].get("title"):
                                if fund_ref_prop.schema["properties"][schema_prop_key]["properties"][schema_prop_sub_lv_key]["title"] == "助成機関識別子タイプ":
                                    funder_identifier_property_schema_property = fund_ref_prop.schema["properties"][schema_prop_key]["properties"]
                        
            #? Get Funder Identifier form from Funding Reference Property
            funder_identifier_property_form: dict or None = None
            if fund_ref_prop.form.get("items"):
                for funding_reference_render_form in fund_ref_prop.form["items"]:
                    if funding_reference_render_form.get("items"):
                        if isinstance(funding_reference_render_form["items"], list):
                            if funding_reference_render_form["items"]:
                                if funding_reference_render_form["items"][0].get("title"):
                                    if funding_reference_render_form["items"][0]["title"] == "助成機関識別子タイプ" \
                                            or funding_reference_render_form["items"][0]["title"] == "助成機関識別子":
                                        funder_identifier_property_form = funding_reference_render_form["items"]

            #? Get Funder Identifier forms from Funding Reference Property
            funder_identifier_property_forms: dict or None = None
            if fund_ref_prop.forms.get("items"):
                for funding_reference_render_form in fund_ref_prop.forms["items"]:
                    if funding_reference_render_form.get("items"):
                        if isinstance(funding_reference_render_form["items"], list):
                            if funding_reference_render_form["items"]:
                                if funding_reference_render_form["items"][0].get("title"):
                                    if funding_reference_render_form["items"][0]["title"] == "助成機関識別子タイプ" \
                                            or funding_reference_render_form["items"][0]["title"] == "助成機関識別子":
                                        funder_identifier_property_forms = funding_reference_render_form["items"]

            if funder_identifier_property_schema_property \
                    and funder_identifier_property_form \
                    and funder_identifier_property_forms:
                funder_identifier_property_schema_property["funderIdentifierTypeURI"] = add_to_schema_funder_identifier_type_uri["funderIdentifierTypeURI"]
                funder_identifier_property_form.append(add_to_form_singular_funder_identifier_type_uri)
                funder_identifier_property_forms.append(add_to_form_funder_identifier_type_uri)

    #* Modify ITEM TYPE Simple MAPPING for FUNDING IDENTIFIER TYPE URI
    for itm in item_type_simple_mapping:
        for key in item_type_simple_mapping_keys:
            try:
                if isinstance(itm.mapping[key]["jpcoar_mapping"], dict):
                    if itm.mapping[key]["jpcoar_mapping"].get("fundingReference", {}) is not None \
                            or len(itm.mapping[key]["jpcoar_mapping"].get("fundingReference", {}).keys()) > 0:
                        if itm.mapping[key]["jpcoar_mapping"].get("fundingReference", {}).get("funderIdentifier") is not None:
                            itm.mapping[key]["jpcoar_mapping"]["fundingReference"]["funderIdentifier"]["@attributes"]["funderIdentifierTypeURI"] = f"{funder_identifier_type_key_mapping_use}.funderIdentifierTypeURI"
            except:
                continue

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for fund_ref_prop in funding_reference_property:
                flag_modified(fund_ref_prop, "schema")
                flag_modified(fund_ref_prop, "form")
                flag_modified(fund_ref_prop, "forms")
                db.session.merge(fund_ref_prop)
            for mapping in item_type_simple_mapping:
                flag_modified(mapping, "mapping")
                db.session.merge(mapping)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for FUNDING IDENTIFIER TYPE URI'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for FUNDING IDENTIFIER TYPE URI'
        )
###! UPDATE ITEM TYPE Simple FOR FUNDING IDENTIFIER TYPE URI ~ END


#* ========================================== AWARD NUMBER TYPE
#? Parent key for Funding Reference Item
funding_reference_key: str or None = None
for fund_ref_key in list(item_type_simple[0].schema["properties"].keys()):
    if item_type_simple[0].schema["properties"][fund_ref_key].get("items"):
        if item_type_simple[0].schema["properties"][fund_ref_key]["items"].get("properties", {}):
            for prop_key in list(item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"].keys()):
                if item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key].get("title"):                 
                    if item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "助成機関識別子" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "助成機関名" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "研究課題番号" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "研究課題名":
                        funding_reference_key = fund_ref_key

#? Element of Funding Reference from itemtype.form
funding_reference_form_list: list or None = None
for funding_reference_form in item_type_simple[0].form:
    if funding_reference_form.get("items"):
        if isinstance(funding_reference_form["items"], list):
            if funding_reference_form["items"]:
                if funding_reference_form["items"][0].get("items"):
                    for fund_ref_item in funding_reference_form["items"][0]["items"]:
                        if fund_ref_item.get("title") == "助成機関識別子タイプ" \
                                or fund_ref_item.get("title") == "助成機関識別子":
                            funding_reference_form_list = funding_reference_form["items"]

#? Get Funding Reference Award Number form
funding_reference_award_number_form_list: list or None = None
for fund_ref_id_form in funding_reference_form_list:
    if fund_ref_id_form["title"] == "研究課題番号":
        if fund_ref_id_form.get("items"):
            funding_reference_award_number_form_list = fund_ref_id_form["items"]

#? Get Funding Reference Award Number prefix
award_number_type_key_prefix: str or None = None
award_number_type_key_singular_prefix: str or None = None
award_number_type_key_mapping_use: str or None = None
if funding_reference_award_number_form_list:
    award_number_type_key_prefix = (".").join(funding_reference_award_number_form_list[0]["key"].split(".")[0:-1])
    award_number_type_key_singular_prefix = award_number_type_key_prefix.replace("[", "").replace("]", "")
    award_number_type_key_mapping_use: str or None = award_number_type_key_singular_prefix.split(".")[-1]

#? Element of Funding Reference from itemtype.render["table_row_map"]["form"]
funding_reference_render_form_list: list or None = None
for funding_reference_render_form in item_type_simple[0].render["table_row_map"]["form"]:
    if funding_reference_render_form.get("items"):
        if isinstance(funding_reference_render_form["items"], list):
            if funding_reference_render_form["items"]:
                if funding_reference_render_form["items"][0].get("items"):
                    for fund_ref_item in funding_reference_render_form["items"][0]["items"]:
                        if fund_ref_item.get("title") == "助成機関識別子タイプ" \
                                or fund_ref_item.get("title") == "助成機関識別子":
                            funding_reference_render_form_list = funding_reference_render_form["items"]

#? Get Funding Reference Award Number form from itemtype.render["table_row_map"]["form"]
funding_reference_award_number_render_form_list: list or None = None
for fund_ref_id_render_form in funding_reference_render_form_list:
    if fund_ref_id_render_form["title"] == "研究課題番号":
        if fund_ref_id_render_form.get("items"):
            funding_reference_award_number_render_form_list = fund_ref_id_render_form["items"]

#? Funding Reference Property for Award Number Type
funding_reference_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for funding_reference_schema_key in schema_keys:
        if schema.get(funding_reference_schema_key, {}).get('title'):
            if "助成機関" in schema.get(funding_reference_schema_key, {}).get('title'):
                funding_reference_property.append(prop)

#? Award Number Type schema data
add_to_schema_award_number_type = {
    "awardNumberType": {
        "type": "string",
        "format": "select",
        "enum": [
            "JGN"
        ],
        "currentEnum": [
            "JGN"
        ],
        "title": "研究課題番号タイプ"
    }
}

#? Award Number Type form data
add_to_form_award_number_type = {
    "key": award_number_type_key_prefix + ".awardNumberType",
    "type": "select",
    "title": "研究課題番号タイプ",
    "title_i18n": {"en": "Award Number Type", "ja": "研究課題番号タイプ"},
    "titleMap": [
        {
            "value": "JGN",
            "name": "JGN"
        }
    ]
}

#? Award Number Type form data for singular form use
add_to_form_singular_award_number_type = {
    "key": award_number_type_key_singular_prefix + ".awardNumberType",
    "type": "select",
    "title": "研究課題番号タイプ",
    "title_i18n": {"en": "Award Number Type", "ja": "研究課題番号タイプ"},
    "titleMap": [
        {
            "value": "JGN",
            "name": "JGN"
        }
    ]
}

###! UPDATE ITEM TYPE Simple FOR AWARD NUMBER TYPE ~ START
if funding_reference_key:
    #* Modify ITEM TYPE Simple for AWARD NUMBER TYPE
    item_type_simple[0].schema["properties"][funding_reference_key]["awardNumberType"] = add_to_schema_award_number_type["awardNumberType"]
    funding_reference_award_number_form_list.append(add_to_form_award_number_type)
    item_type_simple[0].render["schemaeditor"]["schema"][funding_reference_key] = add_to_schema_award_number_type["awardNumberType"]
    item_type_simple[0].render["table_row_map"]["schema"]["properties"][funding_reference_key] = add_to_schema_award_number_type["awardNumberType"]
    funding_reference_render_form_list.append(add_to_form_award_number_type)
    if len(item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"].get("fundingReference")) > 0:
        if len(item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"]["fundingReference"].get("awardNumber")) > 0:
            if len(item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"]["fundingReference"]["awardNumber"].get("@attributes")) > 0:
                item_type_simple[0].render["table_row_map"]["mapping"][funding_reference_key]["jpcoar_mapping"]["fundingReference"]["awardNumber"]["@attributes"]["awardNumberType"] = f"{award_number_type_key_mapping_use}.awardNumberType"

    #* Modify FUNDING REFERENCE ITEM TYPE PROPERTY for AWARD NUMBER TYPE
    if funding_reference_property:
        for fund_ref_prop in funding_reference_property:
            #? Get Award Number schema from Funding Reference Property
            award_number_property_schema_property: dict or None = None
            if len(fund_ref_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(fund_ref_prop.schema["properties"].keys()):
                    if len(fund_ref_prop.schema["properties"][schema_prop_key].get("properties", {})) > 0:
                        for schema_prop_sub_lv_key in list(fund_ref_prop.schema["properties"][schema_prop_key].get("properties", {}).keys()):
                            if fund_ref_prop.schema["properties"][schema_prop_key]["properties"][schema_prop_sub_lv_key].get("title"):
                                if fund_ref_prop.schema["properties"][schema_prop_key]["properties"][schema_prop_sub_lv_key]["title"] == "研究課題番号":
                                    award_number_property_schema_property = fund_ref_prop.schema["properties"][schema_prop_key]["properties"]
                        
            #? Get Award Number form from Funding Reference Property
            award_number_property_form: dict or None = None
            if fund_ref_prop.form.get("items"):
                for funding_reference_render_form in fund_ref_prop.form["items"]:
                    if funding_reference_render_form.get("items"):
                        if isinstance(funding_reference_render_form["items"], list):
                            if funding_reference_render_form["items"]:
                                if funding_reference_render_form["items"][0].get("title"):
                                    if funding_reference_render_form["items"][0]["title"] == "研究課題URI" \
                                            or funding_reference_render_form["items"][0]["title"] == "研究課題番号":
                                        award_number_property_form = funding_reference_render_form["items"]

            #? Get Award Number forms from Funding Reference Property
            award_number_property_forms: dict or None = None
            if fund_ref_prop.forms.get("items"):
                for funding_reference_render_form in fund_ref_prop.forms["items"]:
                    if funding_reference_render_form.get("items"):
                        if isinstance(funding_reference_render_form["items"], list):
                            if funding_reference_render_form["items"]:
                                if funding_reference_render_form["items"][0].get("title"):
                                    if funding_reference_render_form["items"][0]["title"] == "研究課題URI" \
                                            or funding_reference_render_form["items"][0]["title"] == "研究課題番号":
                                        award_number_property_forms = funding_reference_render_form["items"]

            if award_number_property_schema_property \
                    and award_number_property_form \
                    and award_number_property_forms:
                award_number_property_schema_property["awardNumberType"] = add_to_schema_award_number_type["awardNumberType"]
                award_number_property_form.append(add_to_form_singular_award_number_type)
                award_number_property_forms.append(add_to_form_award_number_type)

    #* Modify ITEM TYPE Simple MAPPING for AWARD NUMBER TYPE
    for itm in item_type_simple_mapping:
        for key in item_type_simple_mapping_keys:
            try:
                if isinstance(itm.mapping[key]["jpcoar_mapping"], dict):
                    if itm.mapping[key]["jpcoar_mapping"].get("fundingReference", {}) is not None:
                        if itm.mapping[key]["jpcoar_mapping"]["fundingReference"].get("awardNumber", {}) is not None \
                                or len(itm.mapping[key]["jpcoar_mapping"]["fundingReference"].get("awardNumber", {}).keys()) > 0:
                            if itm.mapping[key]["jpcoar_mapping"]["fundingReference"]["awardNumber"].get("@attributes") is not None:
                                itm.mapping[key]["jpcoar_mapping"]["fundingReference"]["awardNumber"]["@attributes"]["awardNumberType"] = f"{funder_identifier_type_key_mapping_use}.awardNumberType"
            except:
                continue

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for fund_ref_prop in funding_reference_property:
                flag_modified(fund_ref_prop, "schema")
                flag_modified(fund_ref_prop, "form")
                flag_modified(fund_ref_prop, "forms")
                db.session.merge(fund_ref_prop)
            for mapping in item_type_simple_mapping:
                flag_modified(mapping, "mapping")
                db.session.merge(mapping)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for AWARD NUMBER TYPE'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for AWARD NUMBER TYPE'
        )
###! UPDATE ITEM TYPE Simple FOR AWARD NUMBER TYPE  ~ END


"""
(9) In accordance with the JPCOAR2.0 specifications, add and modify vocabularies for the following attribute vocabularies.
◦ jpcoar:subject@subjectScheme
◦ jpcoar:creator > jpcoar:affiliation > jpoar:nameIdentifier@nameIdentifierScheme
kakenhi（非推奨）
ISNI
Ringgold
GRID（非推奨）
ROR
◦ jpcoar:contributor > jpcoar:affiliation > jpoar:nameIdentifier@nameIdentifierScheme
kakenhi（非推奨）
ISNI
Ringgold
GRID（非推奨）
ROR
◦ jpcoar:relation@relationType
◦ jpcoar:relation > jpcoar:relatedIdentifier@identifierType
◦ jpcoar:fundingReference > jpcoar:funderIdentifier@funderIdentifierType
"""

#* ========================================== SUBJECT SCHEME
#? Parent key for Subject Item
subject_item_key: str or None = None
for subject in list(item_type_simple[0].schema["properties"].keys()):
    for y in list(item_type_simple[0].schema["properties"][subject].get("items",{}).get("properties", {}).keys()):
        if item_type_simple[0].schema["properties"][subject].get("items",{}).get("properties", {}).get(y, {}).get("title_i18n"):
            if "Subject URI" in item_type_simple[0].schema["properties"][subject].get("items",{}).get("properties", {}).get(y, {}).get("title_i18n", {}).get("en", {}) \
                    or "主題URI" in item_type_simple[0].schema["properties"][subject].get("items",{}).get("properties", {}).get(y, {}).get("title_i18n", {}).get("ja", {}):
                subject_item_key = subject

#? Subject Schema
subject_scheme_schema: dict or None = None
if subject_item_key:
    if item_type_simple[0].schema["properties"][subject_item_key].get("items", {}).get("properties"):
        if isinstance(item_type_simple[0].schema["properties"][subject_item_key]["items"]["properties"], dict):
            for subj_scheme_item in list(item_type_simple[0].schema["properties"][subject_item_key]["items"]["properties"].keys()):
                if item_type_simple[0].schema["properties"][subject_item_key]["items"]["properties"][subj_scheme_item].get("title"):
                    if "Scheme" in item_type_simple[0].schema["properties"][subject_item_key]["items"]["properties"][subj_scheme_item]["title"]:
                        subject_scheme_schema = item_type_simple[0].schema["properties"][subject_item_key]["items"]["properties"][subj_scheme_item]

#? Element of Subject from itemtype.form
subject_form_list: list = [
    subject_form
    for subject_form
    in item_type_simple[0].form
    if subject_form.get("title_i18n", {}).get("en") == "Subject"
    or subject_form.get("title_i18n", {}).get("ja") == "主題"
]

#? Element of Subject from itemtype.render["table_row_map"]["form"]
subject_render_form_list: list = [
    subject_form
    for subject_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if subject_form.get("title_i18n", {}).get("en") == "Subject"
    or subject_form.get("title_i18n", {}).get("ja") == "主題"
]

#? Get Subject scheme form from itemtype.render["table_row_map"]["form"]
subject_scheme_render_form: dict or None = None
if subject_render_form_list:
    subject_scheme_render_form: list = [
        subj_scheme
        for subj_scheme
        in subject_render_form_list[0]["items"]
        if "主題Scheme" in subj_scheme.get("title")
        or "Scheme" in subj_scheme.get("title")
    ]
    if subject_scheme_render_form:
        subject_scheme_render_form = subject_scheme_render_form[0]

#? Subject Property for Subject Scheme
subject_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for subject_schema_key in schema_keys:
        if schema.get(subject_schema_key, {}).get('title'):
            if "主題" in schema.get(subject_schema_key, {}).get('title') \
                    or "Subject" in schema.get(subject_schema_key, {}).get('title'):
                subject_property.append(prop)

#? Value to be added in Subject Scheme
subject_scheme_new_values = [
    "e-Rad_field",
    "JEL"
]
subject_scheme_new_values_title_map = [
    {
        'name': 'e-Rad_field',
        'value': 'e-Rad_field'
    },
    {
        'name': 'JEL',
        'value': 'JEL'
    },
]

###! UPDATE CHANGES IN ITEM TYPE Simple FOR SUBJECT SCHEME ~ START
if subject_item_key:
    #* Modify ITEM TYPE Simple for Subject Scheme
    if subject_scheme_schema.get("currentEnum") \
            and subject_scheme_schema.get("enum"):
        for sub_sch in subject_scheme_new_values:
            subject_scheme_schema["currentEnum"].append(sub_sch)
            subject_scheme_schema["enum"].append(sub_sch)

    if subject_form_list:
        if subject_form_list[0].get("items") \
                and isinstance(subject_form_list[0].get("items"), list) \
                and subject_form_list[0].get("items"):
            for subj_scheme_item in subject_form_list[0]["items"]:
                if isinstance(subj_scheme_item, dict):
                    if subj_scheme_item.get("title") and "主題Scheme" in subj_scheme_item.get("title") \
                            or "Scheme" in subj_scheme_item.get("title"):
                        if subj_scheme_item.get("titleMap") and isinstance(subj_scheme_item.get("titleMap"), list):
                            for new_sub_sch in subject_scheme_new_values_title_map:
                                subj_scheme_item["titleMap"].append(new_sub_sch)
    
    if subject_render_form_list:
        if subject_render_form_list[0].get("items") \
                and isinstance(subject_render_form_list[0].get("items"), list) \
                and subject_render_form_list[0].get("items"):
            for subj_scheme_item in subject_render_form_list[0]["items"]:
                if isinstance(subj_scheme_item, dict):
                    if subj_scheme_item.get("title") and "主題Scheme" in subj_scheme_item.get("title") \
                            or "Scheme" in subj_scheme_item.get("title"):
                        if subj_scheme_item.get("titleMap") and isinstance(subj_scheme_item.get("titleMap"), list):
                            for new_sub_sch in subject_scheme_new_values_title_map:
                                subj_scheme_item["titleMap"].append(new_sub_sch)

    if subject_property:
        for subj_prop in subject_property:
            #? Get Subject scheme schema from Subject Property
            subject_scheme_property_schema_property: dict or None = None
            if len(subj_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(subj_prop.schema["properties"].keys()):
                    if len(subj_prop.schema["properties"][schema_prop_key].get("enum", {})) > 0:
                        if "主題Scheme" in subj_prop.schema["properties"][schema_prop_key]["title"] \
                                or "Scheme" in subj_prop.schema["properties"][schema_prop_key]["title"]:
                            subject_scheme_property_schema_property = subj_prop.schema["properties"][schema_prop_key]

            #? Get Subject scheme form from Subject Property
            subject_scheme_property_form: dict or None = None
            if len(subj_prop.form.get("items")) > 0:
                for subj_scheme_form in subj_prop.form["items"]:
                    if "主題Scheme" in subj_scheme_form.get("title", ""):
                        subject_scheme_property_form = subj_scheme_form

            #? Get Subject scheme forms from Subject Property
            subject_scheme_property_forms: dict or None = None
            if len(subj_prop.forms.get("items")) > 0:
                for subj_scheme_forms in subj_prop.forms["items"]:
                    if "主題Scheme" in subj_scheme_forms.get("title", ""):
                        subject_scheme_property_forms = subj_scheme_forms

            if subject_scheme_property_schema_property:
                if subject_scheme_property_schema_property.get("enum"):
                    for sub_sch in subject_scheme_new_values:
                        subject_scheme_property_schema_property["enum"].append(sub_sch)

            if subject_scheme_property_form:
                if subject_scheme_property_form.get("titleMap") \
                        and isinstance(subject_scheme_property_form.get("titleMap"), list):
                    for new_sub_sch in subject_scheme_new_values_title_map:
                        subject_scheme_property_form["titleMap"].append(new_sub_sch)        
            
            if subject_scheme_property_forms:
                if subject_scheme_property_forms.get("titleMap") \
                        and isinstance(subject_scheme_property_forms.get("titleMap"), list):
                    for new_sub_sch in subject_scheme_new_values_title_map:
                        subject_scheme_property_forms["titleMap"].append(new_sub_sch)      

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for subj_prop in subject_property:
                flag_modified(subj_prop, "schema")
                flag_modified(subj_prop, "form")
                flag_modified(subj_prop, "forms")
                db.session.merge(subj_prop)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for SUBJECT SCHEME'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for SUBJECT SCHEME'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR SUBJECT SCHEME ~ END


#* ========================================== CREATOR AFFILIATION NAME IDENTIFIER TYPE
#? Parent key for Creator Item
creator_item_key: [str] = [
    creator
    for creator
    in list(item_type_simple[0].schema["properties"].keys())
    if item_type_simple[0].schema["properties"][creator].get("items", {}).get("properties", {}).get("creatorAffiliations")
    or item_type_simple[0].schema["properties"][creator].get("properties", {}).get("creatorAffiliations")
]

#? Creator Affiliation Schema
creator_affiliation_name_identifier_schema: dict or None = None
if creator_item_key:
    if item_type_simple[0].schema["properties"][creator_item_key[0]] \
            .get("items", {}) \
            .get("properties", {}) \
            .get("creatorAffiliations", {}) \
            .get("items", {}) \
            .get("properties", {}) \
            .get("affiliationNameIdentifiers", {}) \
            .get("items", {}) \
            .get("properties", {}) \
            .get("affiliationNameIdentifierScheme"):
        creator_affiliation_name_identifier_schema = item_type_simple[0].schema["properties"][creator_item_key[0]] \
            ["items"] \
            ["properties"] \
            ["creatorAffiliations"] \
            ["items"] \
            ["properties"] \
            ["affiliationNameIdentifiers"] \
            ["items"] \
            ["properties"] \
            ["affiliationNameIdentifierScheme"]

#? Element of Creator from itemtype.form
creator_form_list: list = [
    creator_form
    for creator_form
    in item_type_simple[0].form
    if creator_form.get("title", {}) == "Creator"
]

#? Get Creator Affiliation form
creator_affiliation_form: list = [
    creator_form
    for creator_form
    in creator_form_list[0]["items"]
    if "creatorAffiliations"
    in creator_form["key"]
]

#? Element of Creator from itemtype.render["table_row_map"]["form"]
creator_render_form_list: list = [
    creator_form
    for creator_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if creator_form.get("title", {}) == "Creator"
]

#? Get Creator Affiliation form from itemtype.render["table_row_map"]["form"]
creator_affiliation_render_form: list = [a for a in creator_render_form_list[0]["items"] if "creatorAffiliation" in a["key"]]

#? Creator Property for Creator Affiliation Type
creator_property: ItemTypeProperty or None = None
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for creator_schema_key in schema_keys:
        if schema.get(creator_schema_key, {}).get('title'):
            if "作成者名" in schema.get(creator_schema_key, {}).get('title'):
                creator_property = prop

#? Get Creator Affiliation schema from Creator Property
creator_affiliation_property_schema_property: dict or None = None
if len(creator_property.schema.get("properties", {})) > 0:
    for schema_prop_key in list(creator_property.schema["properties"].keys()):
        if len(creator_property.schema["properties"][schema_prop_key].get("items", {})) > 0:
            if len(creator_property.schema["properties"][schema_prop_key]["items"].get("properties", {})) > 0:
                if len(creator_property.schema["properties"][schema_prop_key]["items"]["properties"].get("affiliationNames", {})) > 0:
                    creator_affiliation_property_schema_property = creator_property.schema["properties"][schema_prop_key]["items"]["properties"]

#? Get Creator Affiliation Identifier from Creator Property
creator_affiliation_identifier_scheme_property_schema_property: dict or None = None
if creator_affiliation_property_schema_property:
    if creator_affiliation_property_schema_property.get("affiliationNameIdentifiers"):
        if creator_affiliation_property_schema_property["affiliationNameIdentifiers"].get("items", {}).get("properties"):
            if creator_affiliation_property_schema_property["affiliationNameIdentifiers"] \
                    ["items"]["properties"].get("affiliationNameIdentifierScheme"):
                creator_affiliation_identifier_scheme_property_schema_property = creator_affiliation_property_schema_property \
                    ["affiliationNameIdentifiers"] \
                    ["items"] \
                    ["properties"] \
                    ["affiliationNameIdentifierScheme"]

#? Get Creator Affiliation form from Creator Property
creator_affiliation_property_form: [dict] or None = None
if len(creator_property.form.get("items")) > 0:
    for creator_prop_form in creator_property.form["items"]:
        if creator_prop_form.get("items") is not None:
            for creator_prop_form_sublevel in creator_prop_form.get("items"):
                if "affiliationNames" in creator_prop_form_sublevel["key"]:
                    creator_affiliation_property_form = creator_prop_form["items"]

#? Get Creator Affiliation forms from Creator Property
creator_affiliation_property_forms: [dict] or None = None
if len(creator_property.forms.get("items")) > 0:
    for creator_prop_form in creator_property.form["items"]:
        if creator_prop_form.get("items") is not None:
            for creator_prop_form_sublevel in creator_prop_form.get("items"):
                if "affiliationNames" in creator_prop_form_sublevel["key"]:
                    creator_affiliation_property_forms = creator_prop_form["items"]

#? Value to be added in Creator Affiliation Name Identifier Scheme
ror = "ROR"
ror_title_map = {
    'name': 'ROR',
    'value': 'ROR'
}

###! UPDATE CHANGES IN ITEM TYPE Simple FOR CREATOR AFFILIATION NAME IDENTIFIER SCHEME ~ START
if creator_item_key:
    #* Modify ITEM TYPE Simple for Creator Affilication Name Identifier Scheme
    if creator_affiliation_name_identifier_schema.get("currentEnum") \
            and creator_affiliation_name_identifier_schema.get("enum"):
        creator_affiliation_name_identifier_schema["currentEnum"].append(ror)
        creator_affiliation_name_identifier_schema["enum"].append(ror)
        if "kakenhi" in creator_affiliation_name_identifier_schema["enum"]:
            creator_affiliation_name_identifier_schema["enum"].remove("kakenhi")
            creator_affiliation_name_identifier_schema["enum"].append("kakenhi【非推奨】")
        if "GRID" in creator_affiliation_name_identifier_schema["enum"]:
            creator_affiliation_name_identifier_schema["enum"].remove("GRID")
            creator_affiliation_name_identifier_schema["enum"].append("GRID【非推奨】")

    if creator_affiliation_form:
        if creator_affiliation_form[0].get("items") \
                and isinstance(creator_affiliation_form[0].get("items"), list):
            for cr_aff_item in creator_affiliation_form[0]["items"]:
                if isinstance(cr_aff_item, dict):
                    if cr_aff_item.get("items"):
                        if isinstance(cr_aff_item["items"], list):
                            for cr_aff_item_lv1 in cr_aff_item["items"]:
                                if "affiliationNameIdentifierScheme" in cr_aff_item_lv1.get("key"):
                                    if cr_aff_item_lv1.get("titleMap"):
                                        if isinstance(cr_aff_item_lv1.get("titleMap"), list):
                                            cr_aff_item_lv1["titleMap"].append(ror_title_map)
                                            for not_recommended_change in cr_aff_item_lv1["titleMap"]:
                                                if not_recommended_change["name"] == "kakenhi":
                                                    not_recommended_change["name"] = "kakenhi【非推奨】"
                                                    not_recommended_change["value"] = "kakenhi【非推奨】"
                                                if not_recommended_change["name"] == "GRID":
                                                    not_recommended_change["name"] = "GRID【非推奨】"
                                                    not_recommended_change["value"] = "GRID【非推奨】"
    
    if creator_render_form_list:
        if creator_render_form_list[0].get("items") \
                and isinstance(creator_render_form_list[0].get("items"), list):
            for cr_aff_item in creator_render_form_list[0]["items"]:
                if isinstance(cr_aff_item, dict):
                    if cr_aff_item.get("items"):
                        if isinstance(cr_aff_item["items"], list):
                            for cr_aff_item_lv1 in cr_aff_item["items"]:
                                if "affiliationNameIdentifiers" in cr_aff_item_lv1.get("key"):
                                    if cr_aff_item_lv1.get("items"):
                                        for cr_aff_item_lv2 in cr_aff_item_lv1["items"]:
                                            if "affiliationNameIdentifierScheme" in cr_aff_item_lv2.get("key"):
                                                if cr_aff_item_lv2.get("titleMap"):
                                                    if isinstance(cr_aff_item_lv2.get("titleMap"), list):
                                                        cr_aff_item_lv2["titleMap"].append(ror_title_map)
                                                        for not_recommended_change in cr_aff_item_lv2["titleMap"]:
                                                            if not_recommended_change["name"] == "kakenhi":
                                                                not_recommended_change["name"] = "kakenhi【非推奨】"
                                                                not_recommended_change["value"] = "kakenhi【非推奨】"
                                                            if not_recommended_change["name"] == "GRID":
                                                                not_recommended_change["name"] = "GRID【非推奨】"
                                                                not_recommended_change["value"] = "GRID【非推奨】"

    if creator_affiliation_identifier_scheme_property_schema_property:
        if creator_affiliation_identifier_scheme_property_schema_property.get("enum"):
            creator_affiliation_identifier_scheme_property_schema_property["enum"].append(ror)
        if "kakenhi" in creator_affiliation_name_identifier_schema["enum"]:
            creator_affiliation_name_identifier_schema["enum"].remove("kakenhi")
            creator_affiliation_name_identifier_schema["enum"].append("kakenhi【非推奨】")
        if "GRID" in creator_affiliation_name_identifier_schema["enum"]:
            creator_affiliation_name_identifier_schema["enum"].remove("GRID")
            creator_affiliation_name_identifier_schema["enum"].append("GRID【非推奨】")

    if creator_affiliation_property_form:
        for cr_aff_prop_form in creator_affiliation_property_form:
            if cr_aff_prop_form.get("items") and isinstance(cr_aff_prop_form.get("items"), list):
                for cr_aff_prop_form_lv1 in cr_aff_prop_form["items"]:
                    if cr_aff_prop_form_lv1.get("key") \
                            and "affiliationNameIdentifierScheme" in cr_aff_prop_form_lv1["key"]:
                        if cr_aff_prop_form_lv1.get("titleMap"):
                            cr_aff_prop_form_lv1["titleMap"].append(ror_title_map)
                        for not_recommended_change in cr_aff_prop_form_lv1["titleMap"]:
                            if not_recommended_change["name"] == "kakenhi":
                                not_recommended_change["name"] = "kakenhi【非推奨】"
                                not_recommended_change["value"] = "kakenhi【非推奨】"
                            if not_recommended_change["name"] == "GRID":
                                not_recommended_change["name"] = "GRID【非推奨】"
                                not_recommended_change["value"] = "GRID【非推奨】"
    
    if creator_affiliation_property_forms:
        for cr_aff_prop_forms in creator_affiliation_property_forms:
            if cr_aff_prop_forms.get("items") and isinstance(cr_aff_prop_forms.get("items"), list):
                for cr_aff_prop_forms_lv1 in cr_aff_prop_forms["items"]:
                    if cr_aff_prop_forms_lv1.get("key") \
                            and "affiliationNameIdentifierScheme" in cr_aff_prop_forms_lv1["key"]:
                        if cr_aff_prop_forms_lv1.get("titleMap"):
                            cr_aff_prop_forms_lv1["titleMap"].append(ror_title_map)
                        for not_recommended_change in cr_aff_prop_forms_lv1["titleMap"]:
                            if not_recommended_change["name"] == "kakenhi":
                                not_recommended_change["name"] = "kakenhi【非推奨】"
                                not_recommended_change["value"] = "kakenhi【非推奨】"
                            if not_recommended_change["name"] == "GRID":
                                not_recommended_change["name"] = "GRID【非推奨】"
                                not_recommended_change["value"] = "GRID【非推奨】"

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            flag_modified(creator_property, "schema")
            flag_modified(creator_property, "form")
            flag_modified(creator_property, "forms")
            db.session.merge(item_type_simple[0])
            db.session.merge(creator_property)
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for CREATOR AFFILIATION NAME IDENTIFIER SCHEME'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for CREATOR AFFILIATION NAME IDENTIFIER SCHEME'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR CREATORAFFILIATION NAME IDENTIFIER SCHEME ~ END


#* ========================================== CONTRIBUTOR AFFILIATION NAME IDENTIFIER SCHEME
#? Parent key for Contributor Item
contributor_item_key: [str] = [
    contributor
    for contributor
    in list(item_type_simple[0].schema["properties"].keys())
    if item_type_simple[0].schema["properties"][contributor].get("items", {}).get("properties", {}).get("contributorAffiliations")
    or item_type_simple[0].schema["properties"][contributor].get("properties", {}).get("contributorAffiliations")
]

#? Contributor Affiliation Schema
contributor_affiliation_name_identifier_schema: dict or None = None
if contributor_item_key:
    if item_type_simple[0].schema["properties"][contributor_item_key[0]] \
            .get("items", {}) \
            .get("properties", {}) \
            .get("contributorAffiliations", {}) \
            .get("items", {}) \
            .get("properties", {}) \
            .get("contributorAffiliationNameIdentifiers", {}) \
            .get("items", {}) \
            .get("properties", {}) \
            .get("contributorAffiliationScheme"):
        contributor_affiliation_name_identifier_schema = item_type_simple[0].schema["properties"][contributor_item_key[0]] \
            ["items"] \
            ["properties"] \
            ["contributorAffiliations"] \
            ["items"] \
            ["properties"] \
            ["contributorAffiliationNameIdentifiers"] \
            ["items"] \
            ["properties"] \
            ["contributorAffiliationScheme"]

#? Element of Contributor from itemtype.form
contributor_form_list: list = [
    contributor_form
    for contributor_form
    in item_type_simple[0].form
    if contributor_form.get("title", {}) == "Contributor"
]

#? Get Contributor Affiliation form
contributor_affiliation_form: list = [
    contributor_form
    for contributor_form
    in contributor_form_list[0]["items"]
    if "contributorAffiliations"
    in contributor_form["key"]
]

#? Element of Contributor from itemtype.render["table_row_map"]["form"]
contributor_render_form_list: list = [
    contributor_form
    for contributor_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if contributor_form.get("title", {}) == "Contributor"
]

#? Get Contributor Affiliation form from itemtype.render["table_row_map"]["form"]
contributor_affiliation_render_form: list = [a for a in contributor_render_form_list[0]["items"] if "contributorAffiliation" in a["key"]]

#? Contributor Property for Contributor Affiliation Scheme
contributor_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for contributor_schema_key in schema_keys:
        if schema.get(contributor_schema_key, {}).get('title'):
            if "寄与者" in schema.get(contributor_schema_key, {}).get('title') \
                    or "Contributor" in schema.get(contributor_schema_key, {}).get('title'):
                contributor_property.append(prop)

#? Value to be added in Contributor Affiliation Name Identifier Scheme
ror = "ROR"
ror_title_map = {
    'name': 'ROR',
    'value': 'ROR'
}

###! UPDATE CHANGES IN ITEM TYPE Simple FOR CONTRIBUTOR AFFILIATION NAME IDENTIFIER SCHEME ~ START
if contributor_item_key:
    #* Modify ITEM TYPE Simple for Contributor Affilication Name Identifier Scheme
    if contributor_affiliation_name_identifier_schema.get("currentEnum") \
            and contributor_affiliation_name_identifier_schema.get("enum"):
        contributor_affiliation_name_identifier_schema["currentEnum"].append(ror)
        contributor_affiliation_name_identifier_schema["enum"].append(ror)
        if "kakenhi" in contributor_affiliation_name_identifier_schema["enum"]:
            contributor_affiliation_name_identifier_schema["enum"].remove("kakenhi")
            contributor_affiliation_name_identifier_schema["enum"].append("kakenhi【非推奨】")
        if "GRID" in contributor_affiliation_name_identifier_schema["enum"]:
            contributor_affiliation_name_identifier_schema["enum"].remove("GRID")
            contributor_affiliation_name_identifier_schema["enum"].append("GRID【非推奨】")

    if contributor_affiliation_form:
        if contributor_affiliation_form[0].get("items") \
                and isinstance(contributor_affiliation_form[0].get("items"), list):
            for contrib_aff_item in contributor_affiliation_form[0]["items"]:
                if isinstance(contrib_aff_item, dict):
                    if contrib_aff_item.get("items"):
                        if isinstance(contrib_aff_item["items"], list):
                            for contrib_aff_item_lv1 in contrib_aff_item["items"]:
                                if "contributorAffiliationScheme" in contrib_aff_item_lv1.get("key"):
                                    if contrib_aff_item_lv1.get("titleMap"):
                                        if isinstance(contrib_aff_item_lv1.get("titleMap"), list):
                                            contrib_aff_item_lv1["titleMap"].append(ror_title_map)
                                            for not_recommended_change in contrib_aff_item_lv1["titleMap"]:
                                                if not_recommended_change["name"] == "kakenhi":
                                                    not_recommended_change["name"] = "kakenhi【非推奨】"
                                                    not_recommended_change["value"] = "kakenhi【非推奨】"
                                                if not_recommended_change["name"] == "GRID":
                                                    not_recommended_change["name"] = "GRID【非推奨】"
                                                    not_recommended_change["value"] = "GRID【非推奨】"
    
    if contributor_render_form_list:
        if contributor_render_form_list[0].get("items") \
                and isinstance(contributor_render_form_list[0].get("items"), list):
            for contrib_aff_item in contributor_render_form_list[0]["items"]:
                if isinstance(contrib_aff_item, dict):
                    if contrib_aff_item.get("items"):
                        if isinstance(contrib_aff_item["items"], list):
                            for contrib_aff_item_lv1 in contrib_aff_item["items"]:
                                if "contributorAffiliationNameIdentifiers" in contrib_aff_item_lv1.get("key"):
                                    if contrib_aff_item_lv1.get("items"):
                                        for contrib_aff_item_lv2 in contrib_aff_item_lv1["items"]:
                                            if "contributorAffiliationScheme" in contrib_aff_item_lv2.get("key"):
                                                if contrib_aff_item_lv2.get("titleMap"):
                                                    if isinstance(contrib_aff_item_lv2.get("titleMap"), list):
                                                        contrib_aff_item_lv2["titleMap"].append(ror_title_map)
                                                        for not_recommended_change in contrib_aff_item_lv2["titleMap"]:
                                                            if not_recommended_change["name"] == "kakenhi":
                                                                not_recommended_change["name"] = "kakenhi【非推奨】"
                                                                not_recommended_change["value"] = "kakenhi【非推奨】"
                                                            if not_recommended_change["name"] == "GRID":
                                                                not_recommended_change["name"] = "GRID【非推奨】"
                                                                not_recommended_change["value"] = "GRID【非推奨】"

    if contributor_property:
        for contributor_prop in contributor_property:
            #? Get Contributor Affiliation schema from Contributor Property
            contributor_affiliation_property_schema_property: dict or None = None
            if len(contributor_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(contributor_prop.schema["properties"].keys()):
                    if len(contributor_prop.schema["properties"][schema_prop_key].get("items", {})) > 0:
                        if len(contributor_prop.schema["properties"][schema_prop_key]["items"].get("properties", {})) > 0:
                            if len(contributor_prop.schema["properties"][schema_prop_key]["items"]["properties"].get("contributorAffiliationNameIdentifiers", {})) > 0:
                                contributor_affiliation_property_schema_property = contributor_prop.schema["properties"][schema_prop_key]["items"]["properties"]

            #? Get Contributor Affiliation Identifier schema from Contributor Property
            contributor_affiliation_identifier_scheme_property_schema_property: dict or None = None
            if contributor_affiliation_property_schema_property:
                if contributor_affiliation_property_schema_property.get("contributorAffiliationNameIdentifiers"):
                    if contributor_affiliation_property_schema_property["contributorAffiliationNameIdentifiers"].get("items", {}).get("properties"):
                        if contributor_affiliation_property_schema_property["contributorAffiliationNameIdentifiers"] \
                                ["items"]["properties"].get("contributorAffiliationScheme"):
                            contributor_affiliation_identifier_scheme_property_schema_property = contributor_affiliation_property_schema_property \
                                ["contributorAffiliationNameIdentifiers"] \
                                ["items"] \
                                ["properties"] \
                                ["contributorAffiliationScheme"]

            #? Get Contributor Affiliation form from Contributor Property
            contributor_affiliation_property_form: [dict] or None = None
            if len(contributor_prop.form.get("items")) > 0:
                for contributor_prop_form in contributor_prop.form["items"]:
                    if contributor_prop_form.get("items") is not None:
                        for contributor_prop_form_sublevel in contributor_prop_form.get("items"):
                            if "contributorAffiliationNameIdentifiers" in contributor_prop_form_sublevel["key"]:
                                contributor_affiliation_property_form = contributor_prop_form["items"]

            #? Get Contributor Affiliation forms from Contributor Property
            contributor_affiliation_property_forms: [dict] or None = None
            if len(contributor_prop.forms.get("items")) > 0:
                for contributor_prop_form in contributor_prop.form["items"]:
                    if contributor_prop_form.get("items") is not None:
                        for contributor_prop_form_sublevel in contributor_prop_form.get("items"):
                            if "contributorAffiliationNameIdentifiers" in contributor_prop_form_sublevel["key"]:
                                contributor_affiliation_property_forms = contributor_prop_form["items"]

            if contributor_affiliation_identifier_scheme_property_schema_property:
                if contributor_affiliation_identifier_scheme_property_schema_property.get("enum"):
                    contributor_affiliation_identifier_scheme_property_schema_property["enum"].append(ror)
                    if "kakenhi" in contributor_affiliation_identifier_scheme_property_schema_property["enum"]:
                        contributor_affiliation_identifier_scheme_property_schema_property["enum"].remove("kakenhi")
                        contributor_affiliation_identifier_scheme_property_schema_property["enum"].append("kakenhi【非推奨】")
                    if "GRID" in contributor_affiliation_identifier_scheme_property_schema_property["enum"]:
                        contributor_affiliation_identifier_scheme_property_schema_property["enum"].remove("GRID")
                        contributor_affiliation_identifier_scheme_property_schema_property["enum"].append("GRID【非推奨】")

            if contributor_affiliation_property_form:
                for cr_aff_prop_form in contributor_affiliation_property_form:
                    if cr_aff_prop_form.get("items") and isinstance(cr_aff_prop_form.get("items"), list):
                        for cr_aff_prop_form_lv1 in cr_aff_prop_form["items"]:
                            if cr_aff_prop_form_lv1.get("key") \
                                    and "contributorAffiliationScheme" in cr_aff_prop_form_lv1["key"]:
                                if cr_aff_prop_form_lv1.get("titleMap"):
                                    cr_aff_prop_form_lv1["titleMap"].append(ror_title_map)
                                for not_recommended_change in cr_aff_prop_forms_lv1["titleMap"]:
                                    if not_recommended_change["name"] == "kakenhi":
                                        not_recommended_change["name"] = "kakenhi【非推奨】"
                                        not_recommended_change["value"] = "kakenhi【非推奨】"
                                    if not_recommended_change["name"] == "GRID":
                                        not_recommended_change["name"] = "GRID【非推奨】"
                                        not_recommended_change["value"] = "GRID【非推奨】"
            
            if contributor_affiliation_property_forms:
                for cr_aff_prop_forms in contributor_affiliation_property_forms:
                    if cr_aff_prop_forms.get("items") and isinstance(cr_aff_prop_forms.get("items"), list):
                        for cr_aff_prop_forms_lv1 in cr_aff_prop_forms["items"]:
                            if cr_aff_prop_forms_lv1.get("key") \
                                    and "contributorAffiliationScheme" in cr_aff_prop_forms_lv1["key"]:
                                if cr_aff_prop_forms_lv1.get("titleMap"):
                                    cr_aff_prop_forms_lv1["titleMap"].append(ror_title_map)
                                for not_recommended_change in cr_aff_prop_forms_lv1["titleMap"]:
                                    if not_recommended_change["name"] == "kakenhi":
                                        not_recommended_change["name"] = "kakenhi【非推奨】"
                                        not_recommended_change["value"] = "kakenhi【非推奨】"
                                    if not_recommended_change["name"] == "GRID":
                                        not_recommended_change["name"] = "GRID【非推奨】"
                                        not_recommended_change["value"] = "GRID【非推奨】"

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for contributor_prop in contributor_property:
                flag_modified(contributor_prop, "schema")
                flag_modified(contributor_prop, "form")
                flag_modified(contributor_prop, "forms")
                db.session.merge(contributor_prop)
            db.session.merge(item_type_simple[0])
            
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for CONTRIBUTOR AFFILIATION NAME IDENTIFIER SCHEME'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for CONTRIBUTOR AFFILIATION NAME IDENTIFIER SCHEME'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR CONTRIBUTOR AFFILIATION NAME IDENTIFIER SCHEME ~ END


#* ========================================== RELATION TYPE
#? Parent key for RELATION Item
relation_item_key: str or None = None
for relation in list(item_type_simple[0].schema["properties"].keys()):
    for rel_key in list(item_type_simple[0].schema["properties"][relation].get("items",{}).get("properties", {}).keys()):
        if item_type_simple[0].schema["properties"][relation] \
                .get("items",{}) \
                .get("properties", {}) \
                .get(rel_key, {}) \
                .get("items", {}) \
                .get("properties"):
            if isinstance(
                item_type_simple[0].schema["properties"] \
                [relation] \
                ["items"] \
                ["properties"] \
                [rel_key] \
                ["items"] \
                ["properties"],
                dict
            ):
                for key in list(item_type_simple[0].schema["properties"] \
                    [relation] \
                    ["items"] \
                    ["properties"] \
                    [rel_key] \
                    ["items"] \
                    ["properties"].keys()
                ):
                    if item_type_simple[0].schema["properties"] \
                            [relation] \
                            ["items"] \
                            ["properties"] \
                            [rel_key] \
                            ["items"] \
                            ["properties"] \
                            [key] \
                            .get("title_i18n", {}) \
                            .get("en") == "Related Title" \
                    or item_type_simple[0].schema["properties"] \
                            [relation] \
                            ["items"] \
                            ["properties"] \
                            [rel_key] \
                            ["items"] \
                            ["properties"] \
                            [key] \
                            .get("title_i18n", {}) \
                            .get("ja") == "関連名称":
                        relation_item_key = relation

#? Relation Schema
relation_type_schema: dict or None = None
if relation_item_key:
    if item_type_simple[0].schema["properties"][relation_item_key].get("items", {}).get("properties"):
        if isinstance(item_type_simple[0].schema["properties"][relation_item_key]["items"]["properties"], dict):
            for rel_type_schema_key in list(item_type_simple[0].schema["properties"][relation_item_key]["items"]["properties"].keys()):
                if "関連タイプ" in item_type_simple[0].schema["properties"] \
                        [relation_item_key] \
                        ["items"] \
                        ["properties"] \
                        [rel_type_schema_key] \
                        .get("title", {}) \
                or "isVersionOf" in item_type_simple[0].schema["properties"] \
                        [relation_item_key] \
                        ["items"] \
                        ["properties"] \
                        [rel_type_schema_key] \
                        .get("enum", {}):
                    relation_type_schema = item_type_simple[0].schema["properties"][relation_item_key]["items"]["properties"][rel_type_schema_key]

#? Element of Relation from itemtype.form
relation_form_list: list = [
    relation_form
    for relation_form
    in item_type_simple[0].form
    if relation_form.get("title_i18n", {}).get("en") == "Relation"
    or relation_form.get("title_i18n", {}).get("ja") == "関連情報"
]

#? Get Relation Type form from itemtype.form
relation_type_form: dict or None = None
if relation_form_list:
    relation_type_form: list = [
        rel_type
        for rel_type
        in relation_form_list[0]["items"]
        if "関連タイプ" in rel_type.get("title")
        or "Relation Type" in rel_type.get("title_i18n", {}).get("en")
        or "関連タイプ" in rel_type.get("title_i18n", {}).get("ja")
    ]
    if relation_type_form:
        relation_type_form = relation_type_form[0]

#? Element of Relation from itemtype.render["table_row_map"]["form"]
relation_render_form_list: list = [
    relation_form
    for relation_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if relation_form.get("title_i18n", {}).get("en") == "Relation"
    or relation_form.get("title_i18n", {}).get("ja") == "関連情報"
]

#? Get Relation Type form from itemtype.render["table_row_map"]["form"]
relation_type_render_form: dict or None = None
if relation_render_form_list:
    relation_type_render_form: list = [
        rel_type
        for rel_type
        in relation_render_form_list[0]["items"]
        if "関連タイプ" in rel_type.get("title")
        or "Relation Type" in rel_type.get("title_i18n", {}).get("en")
        or "関連タイプ" in rel_type.get("title_i18n", {}).get("ja")
    ]
    if relation_type_render_form:
        relation_type_render_form = relation_type_render_form[0]

#? Relation Property for Relation Type
relation_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for relation_schema_key in schema_keys:
        if schema.get(relation_schema_key, {}).get('title'):
            if "Relation" in schema.get(relation_schema_key, {}).get('title') \
                    or "関連情報" in schema.get(relation_schema_key, {}).get('title'):
                    # or "関連情報" in schema.get(relation_schema_key, {}).get('title_i18n', {}).get("en") \
                    # or "Relation" in schema.get(relation_schema_key, {}).get('title_i18n', {}).get("ja"):
                relation_property.append(prop)

#? Value to be added in Relation Type
relation_type_new_values = [
    "inSeries",
    # "isCitedBy",
    # "Cites"
]
relation_type_new_values_title_map = [
    {
        'name': 'inSeries',
        'value': 'inSeries'
    },
    # {
    #     'name': 'isCitedBy',
    #     'value': 'isCitedBy'
    # },
    # {
    #     'name': 'Cites',
    #     'value': 'Cites'
    # },
]

###! UPDATE CHANGES IN ITEM TYPE Simple FOR RELATION TYPE ~ START
if relation_item_key:
    #* Modify ITEM TYPE Simple for Relation Type
    if relation_type_schema.get("currentEnum"):
        for sub_sch in relation_type_new_values:
            relation_type_schema["currentEnum"].append(sub_sch)
            relation_type_schema["enum"].append(sub_sch)
    if relation_type_schema.get("enum"):
        for sub_sch in relation_type_new_values:
            relation_type_schema["currentEnum"].append(sub_sch)
            relation_type_schema["enum"].append(sub_sch)

    if relation_form_list:
        if relation_form_list[0].get("items") \
                and isinstance(relation_form_list[0].get("items"), list) \
                and relation_form_list[0].get("items"):
            for rel_type_item in relation_form_list[0]["items"]:
                if isinstance(rel_type_item, dict):
                    if "関連タイプ" in rel_type_item.get("title") \
                            or rel_type_item.get("titleMap"):
                        if isinstance(rel_type_item.get("titleMap"), list):
                            for new_rel_type in relation_type_new_values_title_map:
                                rel_type_item["titleMap"].append(new_rel_type)
    
    if relation_render_form_list:
        if relation_render_form_list[0].get("items") \
                and isinstance(relation_render_form_list[0].get("items"), list) \
                and relation_render_form_list[0].get("items"):
            for rel_type_item in relation_render_form_list[0]["items"]:
                if isinstance(rel_type_item, dict):
                    if "関連タイプ" in rel_type_item.get("title") \
                            or rel_type_item.get("titleMap"):
                        if isinstance(rel_type_item.get("titleMap"), list):
                            for new_rel_type in relation_type_new_values_title_map:
                                rel_type_item["titleMap"].append(new_rel_type)

    if relation_property:
        for rel_prop in relation_property:
            #? Update Relation type schema from Relation Property
            if len(rel_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(rel_prop.schema["properties"].keys()):
                    if len(rel_prop.schema["properties"][schema_prop_key].get("enum", {})) > 0:
                        if "Relation Type" in rel_prop.schema["properties"][schema_prop_key].get("title") \
                                or "isVersionOf" in rel_prop.schema["properties"][schema_prop_key]["enum"]:
                            for rel_type_new_values in relation_type_new_values:
                                rel_prop.schema["properties"][schema_prop_key]["enum"].append(rel_type_new_values)

            #? Relation Relation type form from Relation Property
            if len(rel_prop.form.get("items")) > 0:
                for rel_type_form in rel_prop.form["items"]:
                    if rel_type_form.get("titleMap"):
                        for rel_type_new_title_map in relation_type_new_values_title_map:
                            rel_type_form["titleMap"].append(rel_type_new_title_map)

            #? Update Subject scheme forms from Subject Property
            if len(rel_prop.forms.get("items")) > 0:
                for rel_type_forms in rel_prop.forms["items"]:
                    if rel_type_forms.get("titleMap"):
                        for rel_type_new_title_map in relation_type_new_values_title_map:
                            rel_type_forms["titleMap"].append(rel_type_new_title_map)

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for rel_type_prop in relation_property:
                flag_modified(rel_type_prop, "schema")
                flag_modified(rel_type_prop, "form")
                flag_modified(rel_type_prop, "forms")
                db.session.merge(rel_type_prop)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for RELATION TYPE'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for RELATION TYPE'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR RELATION TYPE ~ END


#* ========================================== RELATION RELATED INDETIFIER TYPE
#? Parent key for RELATION Item
relation_item_key: str or None = None
for relation in list(item_type_simple[0].schema["properties"].keys()):
    for rel_key in list(item_type_simple[0].schema["properties"][relation].get("items",{}).get("properties", {}).keys()):
        if item_type_simple[0].schema["properties"][relation] \
                .get("items",{}) \
                .get("properties", {}) \
                .get(rel_key, {}) \
                .get("items", {}) \
                .get("properties"):
            if isinstance(
                item_type_simple[0].schema["properties"] \
                [relation] \
                ["items"] \
                ["properties"] \
                [rel_key] \
                ["items"] \
                ["properties"],
                dict
            ):
                for key in list(item_type_simple[0].schema["properties"] \
                    [relation] \
                    ["items"] \
                    ["properties"] \
                    [rel_key] \
                    ["items"] \
                    ["properties"].keys()
                ):
                    if item_type_simple[0].schema["properties"] \
                            [relation] \
                            ["items"] \
                            ["properties"] \
                            [rel_key] \
                            ["items"] \
                            ["properties"] \
                            [key] \
                            .get("title_i18n", {}) \
                            .get("en") == "Related Title" \
                    or item_type_simple[0].schema["properties"] \
                            [relation] \
                            ["items"] \
                            ["properties"] \
                            [rel_key] \
                            ["items"] \
                            ["properties"] \
                            [key] \
                            .get("title_i18n", {}) \
                            .get("ja") == "関連名称":
                        relation_item_key = relation

#? Relation Identifier Type Schema
relation_identifier_type_schema: dict or None = None
if relation_item_key:
    if item_type_simple[0].schema["properties"][relation_item_key].get("items", {}).get("properties"):
        if isinstance(item_type_simple[0].schema["properties"][relation_item_key]["items"]["properties"], dict):
            for rel_type_schema_key in list(item_type_simple[0].schema["properties"][relation_item_key]["items"]["properties"].keys()):
                if item_type_simple[0].schema["properties"] \
                        [relation_item_key] \
                        ["items"] \
                        ["properties"] \
                        [rel_type_schema_key] \
                        .get("properties"):
                    if isinstance(
                        item_type_simple[0].schema["properties"] \
                        [relation_item_key] \
                        ["items"] \
                        ["properties"] \
                        [rel_type_schema_key] \
                        .get("properties"),
                        dict
                    ):
                        for rel_id_key in list(item_type_simple[0].schema["properties"] \
                                [relation_item_key] \
                                ["items"] \
                                ["properties"] \
                                [rel_type_schema_key] \
                                .get("properties").keys()):
                            if "arXiv" in item_type_simple[0].schema["properties"] \
                                    [relation_item_key] \
                                    ["items"] \
                                    ["properties"] \
                                    [rel_type_schema_key] \
                                    ["properties"] \
                                    [rel_id_key] \
                                    .get("enum", {}) \
                            or "識別子タイプ" in item_type_simple[0].schema["properties"] \
                                    [relation_item_key] \
                                    ["items"] \
                                    ["properties"] \
                                    [rel_type_schema_key] \
                                    ["properties"] \
                                    [rel_id_key] \
                                    .get("title"):
                                relation_identifier_type_schema = item_type_simple[0].schema["properties"] \
                                    [relation_item_key]["items"]["properties"][rel_type_schema_key]["properties"]
                            
#? Element of Relation from itemtype.form
relation_form_list: list = [
    relation_form
    for relation_form
    in item_type_simple[0].form
    if relation_form.get("title_i18n", {}).get("en") == "Relation"
    or relation_form.get("title_i18n", {}).get("ja") == "関連情報"
]

#? Get Relation Identifier Type form from itemtype.form
relation_identifier_type_form: dict or None = None
if relation_form_list:
    relation_identifier_type_form: list = [
        rel_type
        for rel_type
        in relation_form_list[0]["items"]
        if "識別子タイプ" in rel_type.get("title")
        or "Relation Identifier" in rel_type.get("title_i18n", {}).get("en")
        or "識別子タイプ" in rel_type.get("title_i18n", {}).get("ja")
    ]
    if relation_identifier_type_form:
        relation_identifier_type_form = relation_identifier_type_form[0]

#? Element of Relation from itemtype.render["table_row_map"]["form"]
relation_render_form_list: list = [
    relation_form
    for relation_form
    in item_type_simple[0].render["table_row_map"]["form"]
    if relation_form.get("title_i18n", {}).get("en") == "Relation"
    or relation_form.get("title_i18n", {}).get("ja") == "関連情報"
]

#? Get Relation Identifier form from itemtype.render["table_row_map"]["form"]
relation_identifier_type_render_form: dict or None = None
if relation_render_form_list:
    relation_identifier_type_render_form: list = [
        rel_type
        for rel_type
        in relation_render_form_list[0]["items"]
        if "識別子タイプ" in rel_type.get("title")
        or "Relation Identifier" in rel_type.get("title_i18n", {}).get("en")
        or "識別子タイプ" in rel_type.get("title_i18n", {}).get("ja")
    ]
    if relation_identifier_type_render_form:
        relation_identifier_type_render_form = relation_identifier_type_render_form[0]

#? Relation Property for Relation Identifier Type
relation_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for relation_schema_key in schema_keys:
        if schema.get(relation_schema_key, {}).get('title'):
            if "Relation" in schema.get(relation_schema_key, {}).get('title') \
                    or "関連情報" in schema.get(relation_schema_key, {}).get('title'):
                    # or "関連情報" in schema.get(relation_schema_key, {}).get('title_i18n', {}).get("en") \
                    # or "Relation" in schema.get(relation_schema_key, {}).get('title_i18n', {}).get("ja"):
                relation_property.append(prop)

#? Value to be added in Relation Type
relation_identifer_type_new_values = [
    "CRID",
]
relation_identifer_type_new_values_title_map = [
    {
        'name': 'CRID',
        'value': 'CRID'
    },
]

###! UPDATE CHANGES IN ITEM TYPE Simple FOR RELATION IDENTIFIER TYPE ~ START
if relation_item_key:
    #* Modify ITEM TYPE Simple for Relation Type
    if relation_identifier_type_schema.get("currentEnum"):
        for rel_id_type in relation_identifer_type_new_values:
            relation_identifier_type_schema["currentEnum"].append(rel_id_type)
        if "NAID" in relation_identifier_type_schema["currentEnum"]:
            relation_identifier_type_schema["currentEnum"].remove("NAID")
            relation_identifier_type_schema["currentEnum"].append("NAID【非推奨】")
        if "PMID" in relation_identifier_type_schema["currentEnum"]:
            relation_identifier_type_schema["currentEnum"].remove("PMID")
            relation_identifier_type_schema["currentEnum"].append("PMID【非推奨】")
    if relation_identifier_type_schema.get("enum"):
        for rel_id_type in relation_identifer_type_new_values:
            relation_identifier_type_schema["enum"].append(rel_id_type)
        if "NAID" in relation_identifier_type_schema["enum"]:
            relation_identifier_type_schema["enum"].remove("NAID")
            relation_identifier_type_schema["enum"].append("NAID【非推奨】")
        if "PMID" in relation_identifier_type_schema["enum"]:
            relation_identifier_type_schema["enum"].remove("PMID")
            relation_identifier_type_schema["enum"].append("PMID【非推奨】")

    if relation_form_list:
        if relation_form_list[0].get("items") \
                and isinstance(relation_form_list[0].get("items"), list) \
                and relation_form_list[0].get("items"):
            for rel_id_type_item in relation_form_list[0]["items"]:
                if isinstance(rel_id_type_item, dict):
                    if "Identifier" in rel_id_type_item.get("title_i18n", {}).get("en") \
                            or "関連識別子" in rel_id_type_item.get("title_i18n", {}).get("ja"):
                        if rel_id_type_item.get("items") and isinstance(rel_id_type_item.get("items"), list):
                            for rel_id_type_item_sub_lv1 in rel_id_type_item["items"]:
                                if rel_id_type_item_sub_lv1.get("titleMap"):
                                    for new_rel_id_type in relation_identifer_type_new_values_title_map:
                                        rel_id_type_item_sub_lv1["titleMap"].append(new_rel_id_type)
                                    for not_recommended_change in rel_id_type_item_sub_lv1["titleMap"]:
                                        if not_recommended_change["name"] == "NAID":
                                            not_recommended_change["name"] = "NAID【非推奨】"
                                            not_recommended_change["value"] = "NAID【非推奨】"
                                        if not_recommended_change["name"] == "PMID":
                                            not_recommended_change["name"] = "PMID【非推奨】"
                                            not_recommended_change["value"] = "PMID【非推奨】"
    
    if relation_render_form_list:
        if relation_render_form_list[0].get("items") \
                and isinstance(relation_render_form_list[0].get("items"), list) \
                and relation_render_form_list[0].get("items"):
            for rel_id_type_item in relation_render_form_list[0]["items"]:
                if isinstance(rel_id_type_item, dict):
                    if "Identifier" in rel_id_type_item.get("title_i18n", {}).get("en") \
                            or "関連識別子" in rel_id_type_item.get("title_i18n", {}).get("ja"):
                        if rel_id_type_item.get("items") and isinstance(rel_id_type_item.get("items"), list):
                            for rel_id_type_item_sub_lv1 in rel_id_type_item["items"]:
                                if rel_id_type_item_sub_lv1.get("titleMap"):
                                    for new_rel_id_type in relation_identifer_type_new_values_title_map:
                                        rel_id_type_item_sub_lv1["titleMap"].append(new_rel_id_type)
                                    for not_recommended_change in rel_id_type_item_sub_lv1["titleMap"]:
                                        if not_recommended_change["name"] == "NAID":
                                            not_recommended_change["name"] = "NAID【非推奨】"
                                            not_recommended_change["value"] = "NAID【非推奨】"
                                        if not_recommended_change["name"] == "PMID":
                                            not_recommended_change["name"] = "PMID【非推奨】"
                                            not_recommended_change["value"] = "PMID【非推奨】"

    if relation_property:
        for rel_prop in relation_property:
            #? Update Relation type schema from Relation Property
            if len(rel_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(rel_prop.schema["properties"].keys()):
                    if len(rel_prop.schema["properties"][schema_prop_key].get("enum", {})) > 0:
                        if "Relation Type" in rel_prop.schema["properties"][schema_prop_key].get("title") \
                                or "isVersionOf" in rel_prop.schema["properties"][schema_prop_key]["enum"]:
                            for rel_type_new_values in relation_type_new_values:
                                rel_prop.schema["properties"][schema_prop_key]["enum"].append(rel_type_new_values)
                            if "NAID" in rel_prop.schema["properties"][schema_prop_key]["enum"]:
                                rel_prop.schema["properties"][schema_prop_key]["enum"].remove("NAID")
                                rel_prop.schema["properties"][schema_prop_key]["enum"].append("NAID【非推奨】")
                            if "PMID" in rel_prop.schema["properties"][schema_prop_key]["enum"]:
                                rel_prop.schema["properties"][schema_prop_key]["enum"].remove("PMID")
                                rel_prop.schema["properties"][schema_prop_key]["enum"].append("PMID【非推奨】")
                            

            #? Relation Relation type form from Relation Property
            if len(rel_prop.form.get("items")) > 0:
                for rel_type_form in rel_prop.form["items"]:
                    if rel_type_form.get("titleMap"):
                        for rel_type_new_title_map in relation_type_new_values_title_map:
                            rel_type_form["titleMap"].append(rel_type_new_title_map)
                        for not_recommended_change in rel_type_form["titleMap"]:
                            if not_recommended_change["name"] == "NAID":
                                not_recommended_change["name"] = "NAID【非推奨】"
                                not_recommended_change["value"] = "NAID【非推奨】"
                            if not_recommended_change["name"] == "PMID":
                                not_recommended_change["name"] = "PMID【非推奨】"
                                not_recommended_change["value"] = "PMID【非推奨】"

            #? Update Subject scheme forms from Subject Property
            if len(rel_prop.forms.get("items")) > 0:
                for rel_type_forms in rel_prop.forms["items"]:
                    if rel_type_forms.get("titleMap"):
                        for rel_type_new_title_map in relation_type_new_values_title_map:
                            rel_type_forms["titleMap"].append(rel_type_new_title_map)
                        for not_recommended_change in rel_type_forms["titleMap"]:
                            if not_recommended_change["name"] == "NAID":
                                not_recommended_change["name"] = "NAID【非推奨】"
                                not_recommended_change["value"] = "NAID【非推奨】"
                            if not_recommended_change["name"] == "PMID":
                                not_recommended_change["name"] = "PMID【非推奨】"
                                not_recommended_change["value"] = "PMID【非推奨】"

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for rel_prop in relation_property:
                flag_modified(rel_prop, "schema")
                flag_modified(rel_prop, "form")
                flag_modified(rel_prop, "forms")
                db.session.merge(rel_prop)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for RELATION IDENTIFIER TYPE'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for RELATION IDENTIFIER TYPE'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR RELATION IDENTIFIER TYPE ~ END


#* ========================================== FUNDING REFERENCE FUNDER IDENTIFIER TYPE
#? Parent key for Funding Reference Item
funding_reference_key: str or None = None
for fund_ref_key in list(item_type_simple[0].schema["properties"].keys()):
    if item_type_simple[0].schema["properties"][fund_ref_key].get("items"):
        if item_type_simple[0].schema["properties"][fund_ref_key]["items"].get("properties", {}):
            for prop_key in list(item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"].keys()):
                if item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key].get("title"):
                    if item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "助成機関識別子" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "助成機関名" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "研究課題番号" \
                            or item_type_simple[0].schema["properties"][fund_ref_key]["items"]["properties"][prop_key]["title"] == "研究課題名":
                        funding_reference_key = fund_ref_key

funder_identifier_type_schema: dict or None = None
if funding_reference_key:
    if item_type_simple[0].schema["properties"][funding_reference_key].get("items", {}).get("properties"):
        if isinstance(item_type_simple[0].schema["properties"][funding_reference_key]["items"]["properties"], dict):
            for fund_id_type_schema_key in list(item_type_simple[0].schema["properties"][funding_reference_key]["items"]["properties"].keys()):
                if item_type_simple[0].schema["properties"][funding_reference_key]["items"]["properties"][fund_id_type_schema_key].get("properties"):
                    if isinstance(
                        item_type_simple[0].schema["properties"][funding_reference_key]["items"]["properties"][fund_id_type_schema_key].get("properties"),
                        dict
                    ):
                        for fund_id_type_key \
                        in list(item_type_simple[0].schema["properties"][funding_reference_key]["items"]["properties"][fund_id_type_schema_key].get("properties").keys()):
                            if item_type_simple[0].schema["properties"] \
                                [funding_reference_key]["items"]["properties"][fund_id_type_schema_key]["properties"][fund_id_type_key].get("enum") \
                            and item_type_simple[0].schema["properties"] \
                                    [funding_reference_key]["items"]["properties"][fund_id_type_schema_key]["properties"][fund_id_type_key].get("currentEnum"):
                                funder_identifier_type_schema = item_type_simple[0].schema["properties"] \
                                    [funding_reference_key]["items"]["properties"][fund_id_type_schema_key]["properties"][fund_id_type_key]

#? Element of Funding Reference from itemtype.form
funding_reference_form_list: list or None = None
for funding_reference_form in item_type_simple[0].form:
    if funding_reference_form.get("items"):
        if isinstance(funding_reference_form["items"], list):
            if funding_reference_form["items"]:
                if funding_reference_form["items"][0].get("items"):
                    for fund_ref_item in funding_reference_form["items"][0]["items"]:
                        if fund_ref_item.get("title") == "助成機関識別子タイプ" \
                                or fund_ref_item.get("title") == "助成機関識別子":
                            funding_reference_form_list = funding_reference_form["items"]

#? Get Funding Reference Funder Identifier Type form
funder_identifier_type_form_list: list or None = None
for fund_ref_id_form in funding_reference_form_list:
    if "助成機関識別子" in fund_ref_id_form.get("title", {}) \
            or "Funder Identifier" in fund_ref_id_form.get("title_i18n", {}).get("en") \
            or "助成機関識別子" in fund_ref_id_form.get("title_i18n", {}).get("ja"):
        if fund_ref_id_form.get("items"):
            funder_identifier_type_form_list = fund_ref_id_form["items"]

#? Element of Funding Reference from itemtype.render["table_row_map"]["form"]
funding_reference_render_form_list: list or None = None
for funding_reference_render_form in item_type_simple[0].render["table_row_map"]["form"]:
    if funding_reference_render_form.get("items"):
        if isinstance(funding_reference_render_form["items"], list):
            if funding_reference_render_form["items"]:
                if funding_reference_render_form["items"][0].get("items"):
                    for fund_ref_item in funding_reference_render_form["items"][0]["items"]:
                        if fund_ref_item.get("title") == "助成機関識別子タイプ" \
                                or fund_ref_item.get("title") == "助成機関識別子":
                            funding_reference_render_form_list = funding_reference_render_form["items"]

#? Get Funding Reference Funder Identifier form from itemtype.render["table_row_map"]["form"]
funder_identifier_type_render_form_list: list or None = None
for fund_ref_id_render_form in funding_reference_render_form_list:
    if "助成機関識別子" in fund_ref_id_render_form.get("title", {}) \
            or "Funder Identifier" in fund_ref_id_render_form.get("title_i18n", {}).get("en") \
            or "助成機関識別子" in fund_ref_id_render_form.get("title_i18n", {}).get("ja"):
        if fund_ref_id_render_form.get("items"):
            funder_identifier_type_render_form_list = fund_ref_id_render_form["items"]

#? Funding Reference Property for Funder Identifier Type
funding_reference_property: [ItemTypeProperty] or None = []
for prop in all_item_type_properties:
     schema = prop.schema.get("properties", {})
     schema_keys = list(schema.keys())
     for funding_reference_schema_key in schema_keys:
        if schema.get(funding_reference_schema_key, {}).get('title'):
            if "助成機関" in schema.get(funding_reference_schema_key, {}).get('title') \
                    or "Funding Reference" in schema.get(funding_reference_schema_key, {}).get('title'):
                funding_reference_property.append(prop)

new_funder_identifier_type_values = [
    "e-Rad_funder",
    "ROR"
]
new_funder_identifier_type_title_map = [
    {
        "name": "e-Rad_funder",
        "value": "e-Rad_funder"
    },
    {
        "name": "ROR",
        "value": "ROR"
    },
]

###! UPDATE CHANGES IN ITEM TYPE Simple FOR FUNDER IDENTIFIER TYPE ~ START
if funding_reference_key:
    #* Modify ITEM TYPE Simple for Relation Type
    if funder_identifier_type_schema.get("currentEnum"):
        for fund_id_type in new_funder_identifier_type_values:
            funder_identifier_type_schema["currentEnum"].append(fund_id_type)
        if "GRID" in funder_identifier_type_schema["currentEnum"]:
            funder_identifier_type_schema["currentEnum"].remove("GRID")
            funder_identifier_type_schema["currentEnum"].append("GRID【非推奨】")
    if funder_identifier_type_schema.get("enum"):
        for fund_id_type in new_funder_identifier_type_values:
            funder_identifier_type_schema["enum"].append(fund_id_type)
        if "GRID" in funder_identifier_type_schema["enum"]:
            funder_identifier_type_schema["enum"].remove("GRID")
            funder_identifier_type_schema["enum"].append("GRID【非推奨】")

    if funder_identifier_type_form_list:
        for fund_id_type_form in funder_identifier_type_form_list:
            if "Funder Identifier Type" in fund_id_type_form.get("title_i18n", {}).get("en", {}) \
                    or "助成機関識別子タイプ" in fund_id_type_form.get("title_i18n", {}).get("ja", {}):
                if fund_id_type_form.get("titleMap") and isinstance(fund_id_type_form.get("titleMap"), list):
                    for new_fund_id_type_title_map in new_funder_identifier_type_title_map:
                        fund_id_type_form["titleMap"].append(new_fund_id_type_title_map)
                    #* FOR NOT RECOMMENDED CHANGE
                    for not_recommended_change in fund_id_type_form["titleMap"]:
                        if "GRID" in not_recommended_change["name"]:
                            not_recommended_change["name"] = "GRID【非推奨】"
                            not_recommended_change["value"] = "GRID【非推奨】"

    if funder_identifier_type_render_form_list:
        for fund_id_type_render_form in funder_identifier_type_render_form_list:
            if "Funder Identifier Type" in fund_id_type_render_form.get("title_i18n", {}).get("en") \
                    or "助成機関識別子タイプ" in fund_id_type_render_form.get("title_i18n", {}).get("ja"):
                if fund_id_type_render_form.get("titleMap") and isinstance(fund_id_type_render_form.get("titleMap"), list):
                    for new_fund_id_type_title_map in new_funder_identifier_type_title_map:
                        fund_id_type_render_form["titleMap"].append(new_fund_id_type_title_map)
                    #* FOR NOT RECOMMENDED CHANGE
                    for not_recommended_change in fund_id_type_render_form["titleMap"]:
                        if "GRID" in not_recommended_change["name"]:
                            not_recommended_change["name"] = "GRID【非推奨】"
                            not_recommended_change["value"] = "GRID【非推奨】"

    if funding_reference_property:
        for fund_ref_prop in funding_reference_property:
            #? Update Funder Identifier type schema from Funder Identifier Property
            if len(fund_ref_prop.schema.get("properties", {})) > 0:
                for schema_prop_key in list(fund_ref_prop.schema["properties"].keys()):
                    if fund_ref_prop.schema["properties"][schema_prop_key].get("properties") \
                            and isinstance(fund_ref_prop.schema["properties"][schema_prop_key].get("properties"), dict):
                        for fund_ref_type_key in list(fund_ref_prop.schema["properties"][schema_prop_key]["properties"].keys()):
                            if fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key].get("enum") \
                                    and fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key].get("currentEnum"):
                                for new_fund_id_type in new_funder_identifier_type_values:
                                    fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["enum"].append(new_fund_id_type)
                                    fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["currentEnum"].append(new_fund_id_type)
                                #* FOR NOT RECOMMENDED CHANGE
                                if "GRID" in fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["enum"]:
                                    fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["enum"].remove("GRID")
                                    fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["enum"].append("GRID【非推奨】")
                                if "GRID" in fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["currentEnum"]:
                                    fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["currentEnum"].remove("GRID")
                                    fund_ref_prop.schema["properties"][schema_prop_key]["properties"][fund_ref_type_key]["currentEnum"].append("GRID【非推奨】")

            #? Update Funder Identifier type form from Funding Reference Property
            if len(fund_ref_prop.form.get("items", {})) > 0:
                for fund_id_type_form_sub_lv1 in fund_ref_prop.form["items"]:
                    if fund_id_type_form_sub_lv1.get("items") and isinstance(fund_id_type_form.get("items"), list):
                        for fund_id_type_form_sub_lv2 in fund_id_type_form_sub_lv1["items"]:
                            if "Funder Identifier Type" in  fund_id_type_form_sub_lv2.get("title_i18n", {}).get("en", {}) \
                                    or "助成機関識別子タイプ" in  fund_id_type_form_sub_lv2.get("title_i18n", {}).get("ja", {}):
                                if fund_id_type_form_sub_lv2.get("titleMap") \
                                        and isinstance(fund_id_type_form_sub_lv2.get("titleMap"), list):
                                    for new_fund_id_type_title_map in new_funder_identifier_type_title_map:
                                        fund_id_type_form_sub_lv2["titleMap"].append(new_fund_id_type_title_map)
                                    #* FOR NOT RECOMMENDED CHANGE
                                    for not_recommended_change in fund_id_type_form_sub_lv2["titleMap"]:
                                        if "GRID" in not_recommended_change["name"]:
                                            not_recommended_change["name"] = "GRID【非推奨】"
                                            not_recommended_change["value"] = "GRID【非推奨】"


            #? Update Funder Identifier type forms from Subject Property
            if len(fund_ref_prop.forms.get("items")) > 0:
                for fund_id_type_forms_sub_lv1 in fund_ref_prop.forms["items"]:
                    if fund_id_type_forms_sub_lv1.get("items") and isinstance(fund_id_type_form.get("items"), list):
                        for fund_id_type_forms_sub_lv2 in fund_id_type_forms_sub_lv1["items"]:
                            if "Funder Identifier Type" in  fund_id_type_forms_sub_lv2.get("title_i18n", {}).get("en", {}) \
                                    or "助成機関識別子タイプ" in  fund_id_type_forms_sub_lv2.get("title_i18n", {}).get("ja", {}):
                                if fund_id_type_forms_sub_lv2.get("titleMap") \
                                        and isinstance(fund_id_type_forms_sub_lv2.get("titleMap"), list):
                                    for new_fund_id_type_title_map in new_funder_identifier_type_title_map:
                                        fund_id_type_forms_sub_lv2["titleMap"].append(new_fund_id_type_title_map)
                                    #* FOR NOT RECOMMENDED CHANGE
                                    for not_recommended_change in fund_id_type_forms_sub_lv2["titleMap"]:
                                        if "GRID" in not_recommended_change["name"]:
                                            not_recommended_change["name"] = "GRID【非推奨】"
                                            not_recommended_change["value"] = "GRID【非推奨】"

    #* Update target item type using update() method from ItemTypes
    ItemTypes.update(
        id_=item_type_simple[0].id,
        name=item_type_simple[0].item_type_name.name,
        schema=item_type_simple[0].schema,
        form=item_type_simple[0].form,
        render=item_type_simple[0].render,
    )

    try:
        #* Save changes to DB
        with db.session.begin_nested():
            flag_modified(item_type_simple[0], "schema")
            flag_modified(item_type_simple[0], "form")
            flag_modified(item_type_simple[0], "render")
            for fund_ref in funding_reference_property:
                flag_modified(fund_ref, "schema")
                flag_modified(fund_ref, "form")
                flag_modified(fund_ref, "forms")
                db.session.merge(fund_ref)
            db.session.merge(item_type_simple[0])
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully modified {item_type_simple[0].item_type_name.name} for FUNDER IDENTIFIER TYPE'
        )

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            err,
            f'Failed to modify {item_type_simple[0].item_type_name.name} for FUNDER IDENTIFIER TYPE'
        )
###! UPDATE CHANGES IN ITEM TYPE Simple FOR FUNDER IDENTIFIER TYPE ~ END