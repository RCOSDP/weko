jpcoar_publisher_mapping = {
    "jpcoar_mapping": {
        "jpcoar_publisher": {
            "subitem_publisher_description": {
                "@attributes": {"xml:lang": "subitem_publisher_description_language"},
                "@value": "subitem_publisher_description_description",
            },
            "subitem_publisher_location": {"@value": "subitem_publisher_location"},
            "subitem_publisher_name": {
                "@attributes": {"xml:lang": "subitem_publisher_name_language"},
                "@value": "subitem_publisher_name_name",
            },
            "subitem_publisher_publication_place": {
                "@value": "subitem_publisher_publication_place"
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

dcterms_date_mapping = {
    "jpcoar_mapping": {
        "dcterms_date": {"subitem_dcterms_date": {"@value": "subitem_dcterms_date"}}
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

dcndl_edition_mapping = {
    "jpcoar_mapping": {
        "dcndl_edition": {
            "subitem_edition": {
                "@attributes": {"xml:lang": "subitem_edition_language"},
                "@value": "subitem_edition_edition",
            }
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
dcndl_volume_title_mapping = {
    "jpcoar_mapping": {
        "dcndl_volume": {
            "subitem_volume_title": {
                "@attributes": {"xml:lang": "subitem_volume_title_language"},
                "@value": "subitem_volume_title_volume_title",
            }
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

dcndl_original_language_mapping = {
    "jpcoar_mapping": {
        "original_language": {
            "subitem_original_language": {"@value": "subitem_original_language"}
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

dcterms_extent_mapping = {
    "jpcoar_mapping": {
        "dcterms_extent": {
            "subitem_extent": {
                "@attributes": {"xml:lang": "subitem_extent_language"},
                "@value": "subitem_extent_extent",
            }
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
jpcoar_format_mapping = {
    "jpcoar_mapping": {
        "jpcoar_format": {
            "subitem_format": {
                "@attributes": {"xml:lang": "subitem_format_language"},
                "@value": "subitem_format_extent",
            }
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

jpcoar_holding_agent_mapping = {
    "jpcoar_mapping": {
        "jpcoar_holding_agent": {
            "subitem_holding_agent_name": {
                "@attributes": {"xml:lang": "subitem_holding_agent_name_language"},
                "@value": "subitem_holding_agent_name_name",
            },
            "subitem_holding_agent_name_identifier": {
                "@attributes": {
                    "nameIdentifierScheme": "subitem_holding_agent_name_identifier_scheme",
                    "nameIdentifierURI": "subitem_holding_agent_name_identifier_uri",
                },
                "@value": "subitem_holding_agent_name_identifier_holding_agent_name_identifier",
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

jpcoar_dataset_series_mapping = {
    "jpcoar_mapping": {
        "jpcoar_dataset_series": {
            "subitem_jpcoar_dataset_series": {
                "@attributes": {"datasetSeriesType": "subitem_jpcoar_dataset_series"}
            }
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}

jpcoar_catalog_mapping = {
    "jpcoar_mapping": {
        "jpcoar_catalog": {
            "subitem_catalog_access_rights": {
                "@attributes": {
                    "accessRights": "subitem_catalog_access_rights_access_rights",
                    "rdf:resource": "subitem_catalog_access_rights_rdf_resource",
                }
            },
            "subitem_catalog_contributor": {
                "subitem_contributor_name": {
                    "@attributes": {"xml:lang": "subitem_contributor_name_language"},
                    "@value": "subitem_contributor_name_contributor_name",
                },
                "subitem_contributor_type": {
                    "@attributes": {"contributorType": "subitem_contributor_type"}
                },
            },
            "subitem_catalog_description": {
                "@attributes": {
                    "descriptionType": "subitem_catalog_description_type",
                    "xml:lang": "subitem_catalog_description_language",
                },
                "@value": "subitem_catalog_description_description",
            },
            "subitem_catalog_file": {
                "@attributes": {"objectType": "subitem_catalog_file_object_type"},
                "@value": "subitem_catalog_file_uri",
            },
            "subitem_catalog_identifier": {
                "@attributes": {"identifierType": "subitem_catalog_identifier_type"},
                "@value": "subitem_catalog_identifier_identifier",
            },
            "subitem_catalog_license": {
                "@attributes": {
                    "licenseType": "subitem_catalog_license_type",
                    "rdf:resource": "subitem_catalog_license_rdf_resource",
                    "xml:lang": "subitem_catalog_license_language",
                },
                "@value": "subitem_catalog_license_license",
            },
            "subitem_catalog_rights": {
                "@attributes": {
                    "rdf:resource": "subitem_catalog_rights_rdf_resource",
                    "xml:lang": "subitem_catalog_rights_language",
                },
                "@value": "subitem_catalog_rights_rights",
            },
            "subitem_catalog_subject": {
                "@attributes": {
                    "subjectScheme": "subitem_catalog_subject_scheme",
                    "subjectURI": "subitem_catalog_subject_uri",
                    "xml:lang": "subitem_catalog_subject_language",
                },
                "@value": "subitem_catalog_subject_subject",
            },
            "subitem_catalog_title": {
                "@attributes": {"xml:lang": "subitem_catalog_title_language"},
                "@value": "subitem_catalog_title_title",
            },
        }
    },
    "junii2_mapping": "",
    "lido_mapping": "",
    "lom_mapping": "",
    "oai_dc_mapping": "",
    "spase_mapping": "",
}
