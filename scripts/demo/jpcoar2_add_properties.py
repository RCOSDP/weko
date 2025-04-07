from datetime import datetime

from weko_records.api import ItemTypeProps
from weko_records.models import ItemTypeProperty
from invenio_db import db


#* Terminal command
#* sudo docker compose exec web invenio shell scripts/demo/jpcoar2_add_properties.py


#* Function for morphing property_language
def list_to_list_of_dict(content: list = []) -> [dict] or []:
    if content:
        return [
            {'name': item, 'value': item}
            for item in content if item is not None
        ]
    else:
        return []


#* Function for creating and saving property into the database
def create_new_property(
        prop_id: int,
        prop_name: str,
        prop_schema: dict,
        prop_form: dict,
        prop_forms: dict
        ) -> None:
    try:
        newProperty = ItemTypeProps.create(
            property_id = prop_id,
            name = prop_name,
            schema = prop_schema,
            form_single = prop_form,
            form_array = prop_forms
        )
        db.session.commit()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Successfully created {prop_name}({prop_id}) property and saved to db.'
        )

        return newProperty

    except Exception as err:
        db.session.rollback()
        print(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            f'Failed to create {prop_name}({prop_id}) property.',
            err
        )


#* Get the latest existing property id 
# all_existing_item_type_properties_ids: list = sorted([prop.id for prop in ItemTypeProperty.query.filter(ItemTypeProperty.id<1001).all()])
# latest_existing_property_id: int = all_existing_item_type_properties_ids[-1]
latest_existing_property_id = 1047

#* Language selection value for all properties to be created
property_language_current_enum: list = [
    None,
    'ja',
    'ja-Kana',
    'ja-Latn',
    'en',
    'fr',
    'it',
    'de',
    'es',
    'zh-cn',
    'zh-tw',
    'ru',
    'la',
    'ms',
    'eo',
    'ar',
    'el',
    'ko',
]
property_language_enum: list = property_language_current_enum[1::]

#* JPCOAR - PUBLISHER
jpcoar_publisher_property_id: int = latest_existing_property_id + 1
jpcoar_publisher_property_name: str = "jpcoar_publisher"
jpcoar_publisher_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_publisher_name": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_publisher_name_name": {
                    "type": "string",
                    "format": "text",
                    "title": "Name",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_publisher_name_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Publisher Name"
        },
        "subitem_publisher_description": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_publisher_description_description": {
                    "type": "string",
                    "format": "text",
                    "title": "Description",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_publisher_description_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Publisher Description"
        },
        "subitem_publisher_location": {
            "type": "string",
            "format": "text",
            "title": "Location"
        },
        "subitem_publisher_publication_place": {
            "type": "string",
            "format": "text",
            "title": "Publication Place"
        }
    }
}
jpcoar_publisher_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_publisher_name",
            "type": "fieldset",
            "title": "Publisher Name",
            "items": [
                {
                    "key": "parentkey.subitem_publisher_name.subitem_publisher_name_name",
                    "type": "text",
                    "title": "Name"
                },
                {
                    "key": "parentkey.subitem_publisher_name.subitem_publisher_name_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey.subitem_publisher_description",
            "type": "fieldset",
            "title": "Publisher Description",
            "items": [
                {
                    "key": "parentkey.subitem_publisher_description.subitem_publisher_description_description",
                    "type": "text",
                    "title": "Description"
                },
                {
                    "key": "parentkey.subitem_publisher_description.subitem_publisher_description_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey.subitem_publisher_location",
            "type": "text",
            "title": "Location"
        },
        {
            "key": "parentkey.subitem_publisher_publication_place",
            "type": "text",
            "title": "Publication Place"
        }
    ],
    "key": "parentkey",
    "type": "fieldset"
}
jpcoar_publisher_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_publisher_name",
            "type": "fieldset",
            "title": "Publisher Name",
            "items": [
                {
                    "key": "parentkey[].subitem_publisher_name.subitem_publisher_name_name",
                    "type": "text",
                    "title": "Name"
                },
                {
                    "key": "parentkey[].subitem_publisher_name.subitem_publisher_name_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey[].subitem_publisher_description",
            "type": "fieldset",
            "title": "Publisher Description",
            "items": [
                {
                    "key": "parentkey[].subitem_publisher_description.subitem_publisher_description_description",
                    "type": "text",
                    "title": "Description"
                },
                {
                    "key": "parentkey[].subitem_publisher_description.subitem_publisher_description_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey[].subitem_publisher_location",
            "type": "text",
            "title": "Location"
        },
        {
            "key": "parentkey[].subitem_publisher_publication_place",
            "type": "text",
            "title": "Publication Place"
        }
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    newly_created_properted = create_new_property(
        prop_id = jpcoar_publisher_property_id,
        prop_name = jpcoar_publisher_property_name,
        prop_schema = jpcoar_publisher_schema,
        prop_form = jpcoar_publisher_form,
        prop_forms = jpcoar_publisher_forms
    )

#* DCTERMS - DATE
dcterms_date_property_id: int = latest_existing_property_id + 2
dcterms_date_property_name: str = "dcterms_date"
dcterms_date_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_dcterms_date": {
            "type": "string",
            "format": "text",
            "title": "Date(DCTERMS)"
        }
    }
}
dcterms_date_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_dcterms_date",
            "type": "text",
            "title": "Date(DCTERMS)"
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
dcterms_date_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_dcterms_date",
            "type": "text",
            "title": "Date(DCTERMS)"
        }
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = dcterms_date_property_id,
        prop_name = dcterms_date_property_name,
        prop_schema = dcterms_date_schema,
        prop_form = dcterms_date_form,
        prop_forms = dcterms_date_forms
    )

#* DCNDL - EDITION
dcndl_edition_property_id: int = latest_existing_property_id + 3
dcndl_edition_property_name: str = "dcndl_edition"
dcndl_edition_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_edition": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_edition_edition": {
                    "type": "string",
                    "format": "text",
                    "title": "Edition",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_edition_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Edition"
        },
    }
}
dcndl_edition_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_edition",
            "type": "fieldset",
            "title": "Edition",
            "items": [
                {
                    "key": "parentkey.subitem_edition.subitem_edition_edition",
                    "type": "text",
                    "title": "Edition"
                },
                {
                    "key": "parentkey.subitem_edition.subitem_edition_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
dcndl_edition_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_edition",
            "type": "fieldset",
            "title": "Edition",
            "items": [
                {
                    "key": "parentkey[].subitem_edition.subitem_edition_edition",
                    "type": "text",
                    "title": "Edition"
                },
                {
                    "key": "parentkey[].subitem_edition.subitem_edition_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = dcndl_edition_property_id,
        prop_name = dcndl_edition_property_name,
        prop_schema = dcndl_edition_schema,
        prop_form = dcndl_edition_form,
        prop_forms = dcndl_edition_forms
    )

#* DCNDL - VOLUME TITLE
dcndl_volume_title_property_id: int = latest_existing_property_id + 4
dcndl_volume_title_property_name: str = "dcndl_volume_title"
dcndl_volume_title_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_volume_title": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_volume_title_volume_title": {
                    "type": "string",
                    "format": "text",
                    "title": "Volume Title",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_volume_title_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Volume Title"
        },
    }
}
dcndl_volume_title_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_volume_title",
            "type": "fieldset",
            "title": "Volume Title",
            "items": [
                {
                    "key": "parentkey.subitem_volume_title.subitem_volume_title_volume_title",
                    "type": "text",
                    "title": "Volume Title"
                },
                {
                    "key": "parentkey.subitem_volume_title.subitem_volume_title_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
dcndl_volume_title_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_volume_title",
            "type": "fieldset",
            "title": "Volume Title",
            "items": [
                {
                    "key": "parentkey[].subitem_volume_title.subitem_volume_title_volume_title",
                    "type": "text",
                    "title": "Volume Title"
                },
                {
                    "key": "parentkey[].subitem_volume_title.subitem_volume_title_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = dcndl_volume_title_property_id,
        prop_name = dcndl_volume_title_property_name,
        prop_schema = dcndl_volume_title_schema,
        prop_form = dcndl_volume_title_form,
        prop_forms = dcndl_volume_title_forms
    )

#* DCNDL - ORIGINAL LANGUAGE
dcndl_original_language_property_id: int = latest_existing_property_id + 5
dcndl_original_language_property_name: str = "dcndl_original_language"
dcndl_original_language_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_original_language": {
            "type": "string",
            "format": "text",
            "title": "Original Language"
        }
    }
}
dcndl_original_language_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_original_language",
            "type": "text",
            "title": "Original Language"
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
dcndl_original_language_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_original_language",
            "type": "text",
            "title": "Original Language"
        }
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = dcndl_original_language_property_id,
        prop_name = dcndl_original_language_property_name,
        prop_schema = dcndl_original_language_schema,
        prop_form = dcndl_original_language_form,
        prop_forms = dcndl_original_language_forms
    )

#* DCTERMS - EXTENT
dcterms_extent_property_id: int = latest_existing_property_id + 6
dcterms_extent_property_name: str = "dcterms_extent"
dcterms_extent_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_extent": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_extent_extent": {
                    "type": "string",
                    "format": "text",
                    "title": "Extent",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_extent_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Extent"
        },
    }
}
dcterms_extent_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_extent",
            "type": "fieldset",
            "title": "Extent",
            "items": [
                {
                    "key": "parentkey.subitem_extent.subitem_extent_extent",
                    "type": "text",
                    "title": "Extent"
                },
                {
                    "key": "parentkey.subitem_extent.subitem_extent_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
dcterms_extent_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_extent",
            "type": "fieldset",
            "title": "Extent",
            "items": [
                {
                    "key": "parentkey[].subitem_extent.subitem_extent_extent",
                    "type": "text",
                    "title": "Extent"
                },
                {
                    "key": "parentkey[].subitem_extent.subitem_extent_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = dcterms_extent_property_id,
        prop_name = dcterms_extent_property_name,
        prop_schema = dcterms_extent_schema,
        prop_form = dcterms_extent_form,
        prop_forms = dcterms_extent_forms
    )

#* JPCOAR - FORMAT
jpcoar_format_property_id: int = latest_existing_property_id + 7
jpcoar_format_property_name: str = "jpcoar_format"
jpcoar_format_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_format": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_format_format": {
                    "type": "string",
                    "format": "text",
                    "title": "Format",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_format_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Format"
        },
    }
}
jpcoar_format_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_format",
            "type": "fieldset",
            "title": "Format",
            "items": [
                {
                    "key": "parentkey.subitem_format.subitem_format_format",
                    "type": "text",
                    "title": "Format"
                },
                {
                    "key": "parentkey.subitem_format.subitem_format_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
jpcoar_format_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_format",
            "type": "fieldset",
            "title": "Format",
            "items": [
                {
                    "key": "parentkey[].subitem_format.subitem_format_format",
                    "type": "text",
                    "title": "Format"
                },
                {
                    "key": "parentkey[].subitem_format.subitem_format_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = jpcoar_format_property_id,
        prop_name = jpcoar_format_property_name,
        prop_schema = jpcoar_format_schema,
        prop_form = jpcoar_format_form,
        prop_forms = jpcoar_format_forms
    )

#* JPCOAR - HOLDING AGENT
jpcoar_holding_agent_scheme = [
    "kakenhi",
    "ISNI",
    "Ringgold",
    "GRID",
    "ROR",
    "FANO",
    "ISIL",
    "MARC",
    "OCLC",
]
jpcoar_holding_agent_property_id: int = latest_existing_property_id + 8
jpcoar_holding_agent_property_name: str = "jpcoar_holding_agent"
jpcoar_holding_agent_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_holding_agent_name": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_holding_agent_name_name": {
                    "type": "string",
                    "format": "text",
                    "title": "Holding Agent Name",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_holding_agent_name_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Holding Agent Name"
        },
        "subitem_holding_agent_name_identifier": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_holding_agent_name_identifier_holding_agent_name_identifier": {
                    "type": "string",
                    "format": "text",
                    "title": "Holding Agent Name Identifier",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_holding_agent_name_identifier_scheme": {
                    "type": "string",
                    "format": "select",
                    "enum": jpcoar_holding_agent_scheme,
                    "currentEnum": jpcoar_holding_agent_scheme,
                    "title": "Holding Agent Name Identifier Scheme"
                },
                "subitem_holding_agent_name_identifier_uri": {
                    "type": "string",
                    "format": "text",
                    "title": "Holding Agent Name Identifier URI",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
            },
            "title": "Holding Agent Name Identifier"
        },
    }
}
jpcoar_holding_agent_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_holding_agent_name",
            "type": "fieldset",
            "title": "Holding Agent Name",
            "items": [
                {
                    "key": "parentkey.subitem_holding_agent_name.subitem_holding_agent_name_name",
                    "type": "text",
                    "title": "Holding Agent Name"
                },
                {
                    "key": "parentkey.subitem_holding_agent_name.subitem_holding_agent_name_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey.subitem_holding_agent_name_identifier",
            "type": "fieldset",
            "title": "Holding Agent Name Identifier",
            "items": [
                {
                    "key": "parentkey.subitem_holding_agent_name_identifier.subitem_holding_agent_name_identifier_holding_agent_name_identifier",
                    "type": "text",
                    "title": "Holding Agent Name Identifier"
                },
                {
                    "key": "parentkey.subitem_holding_agent_name_identifier.subitem_holding_agent_name_identifier_scheme",
                    "type": "select",
                    "title": "Holding Agent Name Identifier Scheme",
                    "titleMap": list_to_list_of_dict(jpcoar_holding_agent_scheme)
                },
                {
                    "key": "parentkey.subitem_holding_agent_name_identifier.subitem_holding_agent_name_identifier_uri",
                    "type": "text",
                    "title": "Holding Agent Name Identifier URI"
                },
            ]
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
jpcoar_holding_agent_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_holding_agent_name",
            "type": "fieldset",
            "title": "Holding Agent Name",
            "items": [
                {
                    "key": "parentkey[].subitem_holding_agent_name.subitem_holding_agent_name_name",
                    "type": "text",
                    "title": "Holding Agent Name"
                },
                {
                    "key": "parentkey[].subitem_holding_agent_name.subitem_holding_agent_name_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey[].subitem_holding_agent_name_identifier",
            "type": "fieldset",
            "title": "Holding Agent Name Identifier",
            "items": [
                {
                    "key": "parentkey[].subitem_holding_agent_name_identifier.subitem_holding_agent_name_identifier_holding_agent_name_identifier",
                    "type": "text",
                    "title": "Holding Agent Name Identifier"
                },
                {
                    "key": "parentkey[].subitem_holding_agent_name_identifier.subitem_holding_agent_name_identifier_scheme",
                    "type": "select",
                    "title": "Holding Agent Name Identifier Scheme",
                    "titleMap": list_to_list_of_dict(jpcoar_holding_agent_scheme)
                },
                {
                    "key": "parentkey[].subitem_holding_agent_name_identifier.subitem_holding_agent_name_identifier_uri",
                    "type": "text",
                    "title": "Holding Agent Name Identifier URI"
                },
            ]
        },
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = jpcoar_holding_agent_property_id,
        prop_name = jpcoar_holding_agent_property_name,
        prop_schema = jpcoar_holding_agent_schema,
        prop_form = jpcoar_holding_agent_form,
        prop_forms = jpcoar_holding_agent_forms
    )

#* JPCOAR - DATASET SERIES
jpcoar_dataset_series_property_id: int = latest_existing_property_id + 9
jpcoar_dataset_series_property_name: str = "jpcoar_dataset_series"
jpcoar_dataset_series_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_jpcoar_dataset_series": {
            "type": "string",
            "format": "select",
            "enum": [
                "True",
                "False"
            ],
            "currentEnum": [
                None,
                "True",
                "False"
            ],
            "title": "Dataset Series"
        }
    }
}
jpcoar_dataset_series_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_jpcoar_dataset_series",
            "type": "select",
            "title": "Dataset Series",
            "titleMap": [
                {
                    "value": "True",
                    "name": "True"
                },
                {
                    "value": "False",
                    "name": "False"
                }
            ]
        },
    ],
    "key": "parentkey",
    "type": "fieldset"
}
jpcoar_dataset_series_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_jpcoar_dataset_series",
            "type": "select",
            "title": "Dataset Series",
            "titleMap": [
                {
                    "value": "True",
                    "name": "True"
                },
                {
                    "value": "False",
                    "name": "False"
                }
            ]
        }
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = jpcoar_dataset_series_property_id,
        prop_name = jpcoar_dataset_series_property_name,
        prop_schema = jpcoar_dataset_series_schema,
        prop_form = jpcoar_dataset_series_form,
        prop_forms = jpcoar_dataset_series_forms
    )

#* JPCOAR - CATALOG
jpcoar_catalog_property_id: int = latest_existing_property_id + 10
jpcoar_catalog_property_name: str = "jpcoar_catalog"
jpcoar_catalog_schema: dict = {
    "type": "object",
    "format": "object",
    "properties": {
        "subitem_catalog_contributor": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_contributor_type": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "HostingInstitution"
                    ],
                    "currentEnum": [
                        "HostingInstitution"
                    ],
                    "title": "Contributor Type"
                },
                "subitem_contributor_name": {
                    "type": "object",
                    "format": "object",
                    "properties": {
                        "subitem_contributor_name_contributor_name": {
                            "type": "string",
                            "format": "text",
                            "title": "Contributor Name",
                            "title_i18n": {
                                "ja": "",
                                "en": ""
                            }
                        },
                        "subitem_contributor_name_language": {
                            "type": "string",
                            "format": "select",
                            "enum": property_language_enum,
                            "currentEnum": property_language_current_enum,
                            "title": "Language"
                        }
                    },
                    "title": "Contributor Name"
                }
            },
            "title": "Contributor"
        },
        "subitem_catalog_identifier": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_identifier_identifier": {
                    "type": "string",
                    "format": "text",
                    "title": "Identifier",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_identifier_type": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "DOI",
                        "HDL",
                        "URI"
                    ],
                    "currentEnum": [
                        "DOI",
                        "HDL",
                        "URI"
                    ],
                    "title": "Identifier Type"
                }
            },
            "title": "Identifier"
        },
        "subitem_catalog_title": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_title_title": {
                    "type": "string",
                    "format": "text",
                    "title": "Title",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_title_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                }
            },
            "title": "Title"
        },
        "subitem_catalog_description": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_description_description": {
                    "type": "string",
                    "format": "text",
                    "title": "Description",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_description_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                },
                "subitem_catalog_description_type": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "Abstract",
                        "Methods",
                        "TableOfContents",
                        "TechnicalInfo",
                        "Other"
                    ],
                    "currentEnum": [
                        "Abstract",
                        "Methods",
                        "TableOfContents",
                        "TechnicalInfo",
                        "Other"
                    ],
                    "title": "Description Type"
                }
            },
            "title": "Description"
        },
        "subitem_catalog_subject": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_subject_subject": {
                    "type": "string",
                    "format": "text",
                    "title": "Subject",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_subject_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                },
                "subitem_catalog_subject_uri": {
                    "type": "string",
                    "format": "text",
                    "title": "Subject URI",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_subject_scheme": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "BSH",
                        "DDC",
                        "e-Rad",
                        "LCC",
                        "LCSH",
                        "MeSH",
                        "NDC",
                        "NDLC",
                        "NDLSH",
                        "SciVal",
                        "UDC",
                        "Other"
                    ],
                    "currentEnum": [
                        "BSH",
                        "DDC",
                        "e-Rad",
                        "LCC",
                        "LCSH",
                        "MeSH",
                        "NDC",
                        "NDLC",
                        "NDLSH",
                        "SciVal",
                        "UDC",
                        "Other"
                    ],
                    "title": "Subject Scheme"
                }
            },
            "title": "Subject"
        },
        "subitem_catalog_license": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_license_license": {
                    "type": "string",
                    "format": "text",
                    "title": "License",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_license_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                },
                "subitem_catalog_license_type": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "file",
                        "metadata",
                        "thumbnail"
                    ],
                    "currentEnum": [
                        "file",
                        "metadata",
                        "thumbnail"
                    ],
                    "title": "License Type"
                },
                "subitem_catalog_license_rdf_resource": {
                    "type": "string",
                    "format": "text",
                    "title": "RDF Resource",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                }
            },
            "title": "License"
        },
        "subitem_catalog_rights": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_rights_rights": {
                    "type": "string",
                    "format": "text",
                    "title": "Rights",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_rights_language": {
                    "type": "string",
                    "format": "select",
                    "enum": property_language_enum,
                    "currentEnum": property_language_current_enum,
                    "title": "Language"
                },
                "subitem_catalog_rights_rdf_resource": {
                    "type": "string",
                    "format": "text",
                    "title": "RDF Resource",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                }
            },
            "title": "Rights"
        },
        "subitem_catalog_access_rights": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_access_rights_access_rights": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "embargoed access",
                        "metadata only access",
                        "restricted access",
                        "open access"
                    ],
                    "currentEnum": [
                        "embargoed access",
                        "metadata only access",
                        "restricted access",
                        "open access"
                    ],
                    "title": "Access Rights"
                },
                "subitem_catalog_access_rights_rdf_resource": {
                    "type": "string",
                    "format": "text",
                    "title": "RDF Resource",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                }
            },
            "title": "Access Rights"
        },
        "subitem_catalog_file": {
            "type": "object",
            "format": "object",
            "properties": {
                "subitem_catalog_file_uri": {
                    "type": "string",
                    "format": "text",
                    "title": "File URI",
                    "title_i18n": {
                        "ja": "",
                        "en": ""
                    }
                },
                "subitem_catalog_file_object_type": {
                    "type": "string",
                    "format": "select",
                    "enum": [
                        "thumbnail"
                    ],
                    "currentEnum": [
                        "thumbnail"
                    ],
                    "title": "Object Type"
                }
            },
            "title": "File"
        }
    }
}
jpcoar_catalog_form: dict = {
    "items": [
        {
            "key": "parentkey.subitem_catalog_contributor",
            "type": "fieldset",
            "title": "Contributor",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_contributor.subitem_contributor_type",
                    "type": "select",
                    "title": "Contributor Type",
                    "titleMap": [
                        {
                            "value": "HostingInstitution",
                            "name": "HostingInstitution"
                        }
                    ]
                },
                {
                    "key": "parentkey.subitem_catalog_contributor.subitem_contributor_name",
                    "type": "fieldset",
                    "title": "Contributor Name",
                    "items": [
                        {
                            "key": "parentkey.subitem_catalog_contributor.subitem_contributor_name.subitem_contributor_name_contributor_name",
                            "type": "text",
                            "title": "Contributor Name"
                        },
                        {
                            "key": "parentkey.subitem_catalog_contributor.subitem_contributor_name.subitem_contributor_name_language",
                            "type": "select",
                            "title": "Language",
                            "titleMap": list_to_list_of_dict(property_language_enum)
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_identifier",
            "type": "fieldset",
            "title": "Identifier",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_identifier.subitem_catalog_identifier_identifier",
                    "type": "text",
                    "title": "Identifier"
                },
                {
                    "key": "parentkey.subitem_catalog_identifier.subitem_catalog_identifier_type",
                    "type": "select",
                    "title": "Identifier Type",
                    "titleMap": [
                        {
                            "value": "DOI",
                            "name": "DOI"
                        },
                        {
                            "value": "HDL",
                            "name": "HDL"
                        },
                        {
                            "value": "URI",
                            "name": "URI"
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_title",
            "type": "fieldset",
            "title": "Title",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_title.subitem_catalog_title_title",
                    "type": "text",
                    "title": "Title"
                },
                {
                    "key": "parentkey.subitem_catalog_title.subitem_catalog_title_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_description",
            "type": "fieldset",
            "title": "Description",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_description.subitem_catalog_description_description",
                    "type": "text",
                    "title": "Description"
                },
                {
                    "key": "parentkey.subitem_catalog_description.subitem_catalog_description_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey.subitem_catalog_description.subitem_catalog_description_type",
                    "type": "select",
                    "title": "Description Type",
                    "titleMap": [
                        {
                            "value": "Abstract",
                            "name": "Abstract"
                        },
                        {
                            "value": "Methods",
                            "name": "Methods"
                        },
                        {
                            "value": "TableOfContents",
                            "name": "TableOfContents"
                        },
                        {
                            "value": "TechnicalInfo",
                            "name": "TechnicalInfo"
                        },
                        {
                            "value": "Other",
                            "name": "Other"
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_subject",
            "type": "fieldset",
            "title": "Subject",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_subject.subitem_catalog_subject_subject",
                    "type": "text",
                    "title": "Subject"
                },
                {
                    "key": "parentkey.subitem_catalog_subject.subitem_catalog_subject_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey.subitem_catalog_subject.subitem_catalog_subject_uri",
                    "type": "text",
                    "title": "Subject URI"
                },
                {
                    "key": "parentkey.subitem_catalog_subject.subitem_catalog_subject_scheme",
                    "type": "select",
                    "title": "Subject Scheme",
                    "titleMap": [
                        {
                            "value": "BSH",
                            "name": "BSH"
                        },
                        {
                            "value": "DDC",
                            "name": "DDC"
                        },
                        {
                            "value": "e-Rad",
                            "name": "e-Rad"
                        },
                        {
                            "value": "LCC",
                            "name": "LCC"
                        },
                        {
                            "value": "LCSH",
                            "name": "LCSH"
                        },
                        {
                            "value": "",
                            "name": ""
                        },
                        {
                            "value": "MeSH",
                            "name": "MeSH"
                        },
                        {
                            "value": "NDC",
                            "name": "NDC"
                        },
                        {
                            "value": "NDLC",
                            "name": "NDLC"
                        },
                        {
                            "value": "NDLSH",
                            "name": "NDLSH"
                        },
                        {
                            "value": "SciVal",
                            "name": "SciVal"
                        },
                        {
                            "value": "UDC",
                            "name": "UDC"
                        },
                        {
                            "value": "Other",
                            "name": "Other"
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_license",
            "type": "fieldset",
            "title": "License",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_license.subitem_catalog_license_license",
                    "type": "text",
                    "title": "License"
                },
                {
                    "key": "parentkey.subitem_catalog_license.subitem_catalog_license_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey.subitem_catalog_license.subitem_catalog_license_type",
                    "type": "select",
                    "title": "License Type",
                    "titleMap": [
                        {
                            "value": "file",
                            "name": "file"
                        },
                        {
                            "value": "metadata",
                            "name": "metadata"
                        },
                        {
                            "value": "thumbnail",
                            "name": "thumbnail"
                        }
                    ]
                },
                {
                    "key": "parentkey.subitem_catalog_license.subitem_catalog_license_rdf_resource",
                    "type": "text",
                    "title": "RDF Resource"
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_rights",
            "type": "fieldset",
            "title": "Rights",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_rights.subitem_catalog_rights_rights",
                    "type": "text",
                    "title": "Rights"
                },
                {
                    "key": "parentkey.subitem_catalog_rights.subitem_catalog_rights_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey.subitem_catalog_rights.subitem_catalog_rights_rdf_resource",
                    "type": "text",
                    "title": "RDF Resource"
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_access_rights",
            "type": "fieldset",
            "title": "Access Rights",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_access_rights.subitem_catalog_access_rights_access_rights",
                    "type": "select",
                    "title": "Access Rights",
                    "titleMap": [
                        {
                            "value": "embargoed access",
                            "name": "embargoed access"
                        },
                        {
                            "value": "metadata only access",
                            "name": "metadata only access"
                        },
                        {
                            "value": "restricted access",
                            "name": "restricted access"
                        },
                        {
                            "value": "open access",
                            "name": "open access"
                        }
                    ]
                },
                {
                    "key": "parentkey.subitem_catalog_access_rights.subitem_catalog_access_rights_rdf_resource",
                    "type": "text",
                    "title": "RDF Resource"
                }
            ]
        },
        {
            "key": "parentkey.subitem_catalog_file",
            "type": "fieldset",
            "title": "File",
            "items": [
                {
                    "key": "parentkey.subitem_catalog_file.subitem_catalog_file_uri",
                    "type": "text",
                    "title": "File URI"
                },
                {
                    "key": "parentkey.subitem_catalog_file.subitem_catalog_file_object_type",
                    "type": "select",
                    "title": "Object Type",
                    "titleMap": [
                        {
                            "value": "thumbnail",
                            "name": "thumbnail"
                        }
                    ]
                }
            ]
        }
    ],
    "key": "parentkey",
    "type": "fieldset"
}
jpcoar_catalog_forms: dict = {
    "items": [
        {
            "key": "parentkey[].subitem_catalog_contributor",
            "type": "fieldset",
            "title": "Contributor",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_contributor.subitem_contributor_type",
                    "type": "select",
                    "title": "Contributor Type",
                    "titleMap": [
                        {
                            "value": "HostingInstitution",
                            "name": "HostingInstitution"
                        }
                    ]
                },
                {
                    "key": "parentkey[].subitem_catalog_contributor.subitem_contributor_name",
                    "type": "fieldset",
                    "title": "Contributor Name",
                    "items": [
                        {
                            "key": "parentkey[].subitem_catalog_contributor.subitem_contributor_name.subitem_contributor_name_contributor_name",
                            "type": "text",
                            "title": "Contributor Name"
                        },
                        {
                            "key": "parentkey[].subitem_catalog_contributor.subitem_contributor_name.subitem_contributor_name_language",
                            "type": "select",
                            "title": "Language",
                            "titleMap": list_to_list_of_dict(property_language_enum)
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_identifier",
            "type": "fieldset",
            "title": "Identifier",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_identifier.subitem_catalog_identifier_identifier",
                    "type": "text",
                    "title": "Identifier"
                },
                {
                    "key": "parentkey[].subitem_catalog_identifier.subitem_catalog_identifier_type",
                    "type": "select",
                    "title": "Identifier Type",
                    "titleMap": [
                        {
                            "value": "DOI",
                            "name": "DOI"
                        },
                        {
                            "value": "HDL",
                            "name": "HDL"
                        },
                        {
                            "value": "URI",
                            "name": "URI"
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_title",
            "type": "fieldset",
            "title": "Title",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_title.subitem_catalog_title_title",
                    "type": "text",
                    "title": "Title"
                },
                {
                    "key": "parentkey[].subitem_catalog_title.subitem_catalog_title_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_description",
            "type": "fieldset",
            "title": "Description",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_description.subitem_catalog_description_description",
                    "type": "text",
                    "title": "Description"
                },
                {
                    "key": "parentkey[].subitem_catalog_description.subitem_catalog_description_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey[].subitem_catalog_description.subitem_catalog_description_type",
                    "type": "select",
                    "title": "Description Type",
                    "titleMap": [
                        {
                            "value": "Abstract",
                            "name": "Abstract"
                        },
                        {
                            "value": "Methods",
                            "name": "Methods"
                        },
                        {
                            "value": "TableOfContents",
                            "name": "TableOfContents"
                        },
                        {
                            "value": "TechnicalInfo",
                            "name": "TechnicalInfo"
                        },
                        {
                            "value": "Other",
                            "name": "Other"
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_subject",
            "type": "fieldset",
            "title": "Subject",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_subject.subitem_catalog_subject_subject",
                    "type": "text",
                    "title": "Subject"
                },
                {
                    "key": "parentkey[].subitem_catalog_subject.subitem_catalog_subject_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey[].subitem_catalog_subject.subitem_catalog_subject_uri",
                    "type": "text",
                    "title": "Subject URI"
                },
                {
                    "key": "parentkey[].subitem_catalog_subject.subitem_catalog_subject_scheme",
                    "type": "select",
                    "title": "Subject Scheme",
                    "titleMap": [
                        {
                            "value": "BSH",
                            "name": "BSH"
                        },
                        {
                            "value": "DDC",
                            "name": "DDC"
                        },
                        {
                            "value": "e-Rad",
                            "name": "e-Rad"
                        },
                        {
                            "value": "LCC",
                            "name": "LCC"
                        },
                        {
                            "value": "LCSH",
                            "name": "LCSH"
                        },
                        {
                            "value": "MeSH",
                            "name": "MeSH"
                        },
                        {
                            "value": "NDC",
                            "name": "NDC"
                        },
                        {
                            "value": "NDLC",
                            "name": "NDLC"
                        },
                        {
                            "value": "NDLSH",
                            "name": "NDLSH"
                        },
                        {
                            "value": "SciVal",
                            "name": "SciVal"
                        },
                        {
                            "value": "UDC",
                            "name": "UDC"
                        },
                        {
                            "value": "Other",
                            "name": "Other"
                        }
                    ]
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_license",
            "type": "fieldset",
            "title": "License",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_license.subitem_catalog_license_license",
                    "type": "text",
                    "title": "License"
                },
                {
                    "key": "parentkey[].subitem_catalog_license.subitem_catalog_license_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey[].subitem_catalog_license.subitem_catalog_license_type",
                    "type": "select",
                    "title": "License Type",
                    "titleMap": [
                        {
                            "value": "file",
                            "name": "file"
                        },
                        {
                            "value": "metadata",
                            "name": "metadata"
                        },
                        {
                            "value": "thumbnail",
                            "name": "thumbnail"
                        }
                    ]
                },
                {
                    "key": "parentkey[].subitem_catalog_license.subitem_catalog_license_rdf_resource",
                    "type": "text",
                    "title": "RDF Resource"
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_rights",
            "type": "fieldset",
            "title": "Rights",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_rights.subitem_catalog_rights_rights",
                    "type": "text",
                    "title": "Rights"
                },
                {
                    "key": "parentkey[].subitem_catalog_rights.subitem_catalog_rights_language",
                    "type": "select",
                    "title": "Language",
                    "titleMap": list_to_list_of_dict(property_language_enum)
                },
                {
                    "key": "parentkey[].subitem_catalog_rights.subitem_catalog_rights_rdf_resource",
                    "type": "text",
                    "title": "RDF Resource"
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_access_rights",
            "type": "fieldset",
            "title": "Access Rights",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_access_rights.subitem_catalog_access_rights_access_rights",
                    "type": "select",
                    "title": "Access Rights",
                    "titleMap": [
                        {
                            "value": "embargoed access",
                            "name": "embargoed access"
                        },
                        {
                            "value": "metadata only access",
                            "name": "metadata only access"
                        },
                        {
                            "value": "restricted access",
                            "name": "restricted access"
                        },
                        {
                            "value": "open access",
                            "name": "open access"
                        }
                    ]
                },
                {
                    "key": "parentkey[].subitem_catalog_access_rights.subitem_catalog_access_rights_rdf_resource",
                    "type": "text",
                    "title": "RDF Resource"
                }
            ]
        },
        {
            "key": "parentkey[].subitem_catalog_file",
            "type": "fieldset",
            "title": "File",
            "items": [
                {
                    "key": "parentkey[].subitem_catalog_file.subitem_catalog_file_uri",
                    "type": "text",
                    "title": "File URI"
                },
                {
                    "key": "parentkey[].subitem_catalog_file.subitem_catalog_file_object_type",
                    "type": "select",
                    "title": "Object Type",
                    "titleMap": [
                        {
                            "value": "thumbnail",
                            "name": "thumbnail"
                        }
                    ]
                }
            ]
        }
    ],
    "key": "parentkey",
    "add": "New",
    "style": {
        "add": "btn-success"
    }
}
if __name__ == "__main__":
    create_new_property(
        prop_id = jpcoar_catalog_property_id,
        prop_name = jpcoar_catalog_property_name,
        prop_schema = jpcoar_catalog_schema,
        prop_form = jpcoar_catalog_form,
        prop_forms = jpcoar_catalog_forms
    )

