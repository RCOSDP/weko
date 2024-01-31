schema_name = "jpcoar_mapping"
target_namespace = None
schema_location = "https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"
form_data = {
    "name": "jpcoar",
    "file_name": "jpcoar_scm.xsd",
    "root_name": "jpcoar"
}
namespaces = {
    "": "https://github.com/JPCOAR/schema/blob/master/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "dcndl": "http://ndl.go.jp/dcndl/terms/",
    "oaire": "http://namespace.openaire.eu/schema/oaire/",
    "jpcoar": "https://github.com/JPCOAR/schema/blob/master/2.0/",
    "dcterms": "http://purl.org/dc/terms/",
    "datacite": "https://schema.datacite.org/meta/kernel-4/",
    "rioxxterms": "http://www.rioxx.net/schema/v2.0/rioxxterms/"
}
xsd = {
    "dc:title": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 1,
            "attributes": [
                {
                    "use": "required",
                    "name": "xml:lang",
                    "ref": "xml:lang",
                }
            ]
        }
    },
    "dcterms:alternative": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }
            ]
        }
    },
    "jpcoar:creator": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "creatorType",
                    "ref": None
                }
            ]
        },
        "jpcoar:nameIdentifier": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "nameIdentifierScheme",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "e-Rad",
                                "NRID",
                                "ORCID",
                                "ISNI",
                                "VIAF",
                                "AID",
                                "kakenhi",
                                "Ringgold",
                                "GRID",
                                "ROR"
                            ]
                        }
                    },
                    {
                        "use": "optional",
                        "name": "nameIdentifierURI",
                        "ref": None
                    }
                ]
            }
        },
        "jpcoar:creatorName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "required",
                        "name": "nameType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "Organizational",
                                "Personal",
                            ]
                        }
                    }
                ]
            }
        },
        "jpcoar:familyName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:givenName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:creatorAlternative": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:affiliation": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0
            },
            "jpcoar:nameIdentifier": {
                "type": {
                    "maxOccurs": "unbounded",
                    "minOccurs": 0,
                    "attributes": [
                        {
                            "use": "required",
                            "name": "nameIdentifierScheme",
                            "ref": None,
                            "restriction": {
                                "enumeration": [
                                    "kakenhi",
                                    "ISNI",
                                    "Ringgold",
                                    "GRID",
                                    "ROR",
                                ]
                            }
                        },
                        {
                            "use": "optional",
                            "name": "nameIdentifierURI",
                            "ref": None
                        }
                    ]
                }
            },
            "jpcoar:affiliationName": {
                "type": {
                    "maxOccurs": "unbounded",
                    "minOccurs": 0,
                    "attributes": [
                        {
                            "use": "optional",
                            "name": "xml:lang",
                            "ref": "xml:lang"
                        }
                    ]
                }
            }
        }
    },
    "jpcoar:contributor": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "contributorType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "ContactPerson",
                            "DataCollector",
                            "DataCurator",
                            "DataManager",
                            "Distributor",
                            "Editor",
                            "HostingInstitution",
                            "Producer",
                            "ProjectLeader",
                            "ProjectManager",
                            "ProjectMember",
                            "RegistrationAgency",
                            "RegistrationAuthority",
                            "RelatedPerson",
                            "Researcher",
                            "ResearchGroup",
                            "Sponsor",
                            "Supervisor",
                            "WorkPackageLeader",
                            "Other"
                        ]
                    }
                }
            ]
        },
        "jpcoar:nameIdentifier": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "nameIdentifierScheme",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "e-Rad",
                                "NRID",
                                "ORCID",
                                "ISNI",
                                "VIAF",
                                "AID",
                                "kakenhi",
                                "Ringgold",
                                "GRID",
                                "ROR"
                            ]
                        }
                    },
                    {
                        "use": "optional",
                        "name": "nameIdentifierURI",
                        "ref": None
                    }
                ]
            }
        },
        "jpcoar:contributorName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "required",
                        "name": "nameType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "Organizational",
                                "Personal",
                            ]
                        }
                    }
                ]
            }
        },
        "jpcoar:familyName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:givenName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:contributorAlternative": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:affiliation": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0
            },
            "jpcoar:nameIdentifier": {
                "type": {
                    "maxOccurs": "unbounded",
                    "minOccurs": 0,
                    "attributes": [
                        {
                            "use": "required",
                            "name": "nameIdentifierScheme",
                            "ref": None,
                            "restriction": {
                                "enumeration": [
                                    "kakenhi",
                                    "ISNI",
                                    "Ringgold",
                                    "GRID",
                                    "ROR",
                                ]
                            }
                        },
                        {
                            "use": "optional",
                            "name": "nameIdentifierURI",
                            "ref": None
                        }
                    ]
                }
            },
            "jpcoar:affiliationName": {
                "type": {
                    "maxOccurs": "unbounded",
                    "minOccurs": 0,
                    "attributes": [
                        {
                            "use": "optional",
                            "name": "xml:lang",
                            "ref": "xml:lang"
                        }
                    ]
                }
            }
        }
    },
    "dcterms:accessRights": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "required",
                    "name": "rdf:resource",
                    "ref": "rdf:resource"
                }
            ],
            "restriction": {
                "enumeration": [
                    "embargoed access",
                    "metadata only access",
                    "open access",
                    "restricted access"
                ]
            }
        }
    },
    "dc:rights": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "rdf:resource",
                    "ref": "rdf:resource"
                },
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }
            ]
        }
    },
    "jpcoar:rightsHolder": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0
        },
        "jpcoar:nameIdentifier": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "nameIdentifierScheme",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "e-Rad",
                                "NRID",
                                "ORCID",
                                "ISNI",
                                "VIAF",
                                "AID",
                                "kakenhi",
                                "Ringgold",
                                "GRID"
                            ]
                        }
                    },
                    {
                        "use": "optional",
                        "name": "nameIdentifierURI",
                        "ref": None
                    }
                ]
            }
        },
        "jpcoar:rightsHolderName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        }
    },
    "jpcoar:subject": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                },
                {
                    "use": "optional",
                    "name": "subjectURI",
                    "ref": None
                },
                {
                    "use": "required",
                    "name": "subjectScheme",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "BSH",
                            "DDC",
                            "e-Rad_field",
                            "JEL",
                            "LCC",
                            "LCSH",
                            "MeSH",
                            "NDC",
                            "NDLC",
                            "NDLSH",
                            "SciVal",
                            "UDC",
                            "Other",
                        ]
                    }
                }
            ]
        }
    },
    "datacite:description": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                },
                {
                    "use": "required",
                    "name": "descriptionType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "Abstract",
                            "Methods",
                            "TableOfContents",
                            "TechnicalInfo",
                            "Other"
                        ]
                    }
                }
            ]
        }
    },
    "dc:publisher": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }
            ]
        }
    },
    "datacite:date": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "required",
                    "name": "dateType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "Accepted",
                            "Available",
                            "Collected",
                            "Copyrighted",
                            "Created",
                            "Issued",
                            "Submitted",
                            "Updated",
                            "Valid"
                        ]
                    }
                }
            ]
        }
    },
    "dc:language": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "restriction": {
                "patterns": [
                    "^[a-z]{3}$"
                ]
            }
        }
    },
    "dc:type": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1,
            "attributes": [
                {
                    "use": "required",
                    "name": "rdf:resource",
                    "ref": "rdf:resource"
                }
            ],
            "restriction": {
                "enumeration": [
                    "conference paper",
                    "data paper",
                    "departmental bulletin paper",
                    "editorial",
                    "journal article",
                    "newspaper",
                    "periodical",
                    "review article",
                    "software paper",
                    "article",
                    "book",
                    "book part",
                    "cartographic material",
                    "map",
                    "conference object",
                    "conference proceedings",
                    "conference poster",
                    "dataset",
                    "aggregated data",
                    "clinical trial data",
                    "compiled data",
                    "encoded data",
                    "experimental data",
                    "genomic data",
                    "geospatial data",
                    "laboratory notebook",
                    "measurement and test data",
                    "observational data",
                    "recorded data",
                    "simulation data",
                    "survey data",
                    "interview",
                    "image",
                    "still image",
                    "moving image",
                    "video",
                    "lecture",
                    "patent",
                    "internal report",
                    "report",
                    "research report",
                    "technical report",
                    "policy report",
                    "report part",
                    "working paper",
                    "data management plan",
                    "sound",
                    "thesis",
                    "bachelor thesis",
                    "master thesis",
                    "doctoral thesis",
                    "interactive resource",
                    "learning object",
                    "manuscript",
                    "musical notation",
                    "research proposal",
                    "software",
                    "technical documentation",
                    "workflow",
                    "other"
                ]
            }
        }
    },
    "datacite:version": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "oaire:versiontype": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "required",
                    "name": "rdf:resource",
                    "ref": "rdf:resource"
                }
            ],
            "restriction": {
                "enumeration": [
                    "AO",
                    "SMUR",
                    "AM",
                    "P",
                    "VoR",
                    "CVoR",
                    "EVoR",
                    "NA"
                ]
            }
        }
    },
    "jpcoar:identifier": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "required",
                    "name": "identifierType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "DOI",
                            "HDL",
                            "URI"
                        ]
                    }
                }
            ]
        }
    },
    "jpcoar:identifierRegistration": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "required",
                    "name": "identifierType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "JaLC",
                            "Crossref",
                            "DataCite",
                            "PMID"
                        ]
                    }
                }
            ]
        }
    },
    "jpcoar:relation": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "relationType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "inSeries",
                            "isCitedBy",
                            "Cites",
                            "isVersionOf",
                            "hasVersion",
                            "isPartOf",
                            "hasPart",
                            "isReferencedBy",
                            "references",
                            "isFormatOf",
                            "hasFormat",
                            "isReplacedBy",
                            "replaces",
                            "isRequiredBy",
                            "requires",
                            "isSupplementTo",
                            "isSupplementedBy",
                            "isIdenticalTo",
                            "isDerivedFrom",
                            "isSourceOf"
                        ]
                    }
                }
            ]
        },
        "jpcoar:relatedIdentifier": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "identifierType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "ARK",
                                "arXiv",
                                "CRID",
                                "DOI",
                                "HDL",
                                "ICHUSHI",
                                "ISBN",
                                "J-GLOBAL",
                                "Local",
                                "PISSN",
                                "EISSN",
                                "ISSN",
                                "NAID",
                                "NCID",
                                "PMID",
                                "PURL",
                                "SCOPUS",
                                "URI",
                                "WOS",
                            ]
                        }
                    }
                ]
            }
        },
        "jpcoar:relatedTitle": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        }
    },
    "dcterms:temporal": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }
            ]
        }
    },
    "datacite:geoLocation": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0
        },
        "datacite:geoLocationPoint": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0
            },
            "datacite:pointLongitude": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {
                        "maxInclusive": 180,
                        "minInclusive": -180
                    }
                }
            },
            "datacite:pointLatitude": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {
                        "maxInclusive": 90,
                        "minInclusive": -90
                    }
                }
            }
        },
        "datacite:geoLocationBox": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0
            },
            "datacite:westBoundLongitude": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {
                        "maxInclusive": 180,
                        "minInclusive": -180
                    }
                }
            },
            "datacite:eastBoundLongitude": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {
                        "maxInclusive": 180,
                        "minInclusive": -180
                    }
                }
            },
            "datacite:southBoundLatitude": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {
                        "maxInclusive": 90,
                        "minInclusive": -90
                    }
                }
            },
            "datacite:northBoundLatitude": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {
                        "maxInclusive": 90,
                        "minInclusive": -90
                    }
                }
            }
        },
        "datacite:geoLocationPlace": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0
            }
        }
    },
    "jpcoar:fundingReference": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0
        },
        "jpcoar:funderIdentifier": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "funderIdentifierType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "Crossref Funder",
                                "e-Rad_funder",
                                "GRID",
                                "ISNI",
                                "ROR",
                                "Other",
                            ]
                        },
                    },
                    {
                        "use": "optional",
                        "name": "funderIdentifierTypeURI",
                        "ref": None
                    }
                ]
            }
        },
        "jpcoar:funderName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 1,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:awardNumber": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "awardURI",
                        "ref": None
                    },
                    {
                        "use": "optional",
                        "name": "awardNumberType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "JGN"
                            ]
                        },
                    }
                ]
            }
        },
        "jpcoar:awardTitle": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:fundingStreamIdentifier": {
            "type": {
                "maxOccurs": "1",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "fundingStreamIdentifierType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "Crossref Funder",
                                "JGN_fundingStream",
                            ]
                        }
                    },
                    {
                        "use": "optional",
                        "name": "fundingStreamIdentifierTypeURI",
                        "ref": None,
                    }
                ]
            }
        },
        "jpcoar:fundingStream": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang",
                }]
            },
        },
    },
    "jpcoar:sourceIdentifier": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "required",
                    "name": "identifierType",
                    "ref": None,
                    "restriction": {
                        "enumeration": [
                            "PISSN",
                            "EISSN",
                            "ISSN",
                            "NCID"
                        ]
                    }
                }
            ]
        }
    },
    "jpcoar:sourceTitle": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }
            ]
        }
    },
    "jpcoar:volume": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "jpcoar:issue": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "jpcoar:numPages": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "jpcoar:pageStart": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "jpcoar:pageEnd": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "dcndl:dissertationNumber": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "dcndl:degreeName": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [
                {
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }
            ]
        }
    },
    "dcndl:dateGranted": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0
        }
    },
    "jpcoar:degreeGrantor": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0
        },
        "jpcoar:nameIdentifier": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "nameIdentifierScheme",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "e-Rad",
                                "NRID",
                                "ORCID",
                                "ISNI",
                                "VIAF",
                                "AID",
                                "kakenhi",
                                "Ringgold",
                                "GRID"
                            ]
                        }
                    },
                    {
                        "use": "optional",
                        "name": "nameIdentifierURI",
                        "ref": None
                    }
                ]
            }
        },
        "jpcoar:degreeGrantorName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        }
    },
    "jpcoar:conference": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0
        },
        "jpcoar:conferenceName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:conferenceSequence": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0
            }
        },
        "jpcoar:conferenceSponsor": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:conferenceDate": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "startMonth",
                        "ref": None,
                        "restriction": {
                            "maxInclusive": 12,
                            "minInclusive": 1,
                            "totalDigits": 2
                        }
                    },
                    {
                        "use": "optional",
                        "name": "endYear",
                        "ref": None,
                        "restriction": {
                            "maxInclusive": 2200,
                            "minInclusive": 1400,
                            "totalDigits": 4
                        }
                    },
                    {
                        "use": "optional",
                        "name": "startDay",
                        "ref": None,
                        "restriction": {
                            "maxInclusive": 31,
                            "minInclusive": 1,
                            "totalDigits": 2
                        }
                    },
                    {
                        "use": "optional",
                        "name": "endDay",
                        "ref": None,
                        "restriction": {
                            "maxInclusive": 31,
                            "minInclusive": 1,
                            "totalDigits": 2
                        }
                    },
                    {
                        "use": "optional",
                        "name": "endMonth",
                        "ref": None,
                        "restriction": {
                            "maxInclusive": 12,
                            "minInclusive": 1,
                            "totalDigits": 2
                        }
                    },
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "optional",
                        "name": "startYear",
                        "ref": None,
                        "restriction": {
                            "maxInclusive": 2200,
                            "minInclusive": 1400,
                            "totalDigits": 4
                        }
                    }
                ]
            }
        },
        "jpcoar:conferenceVenue": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:conferencePlace": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }
                ]
            }
        },
        "jpcoar:conferenceCountry": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "restriction": {
                    "patterns": [
                        "^[A-Z]{3}$"
                    ]
                }
            }
        }
    },
    "jpcoar:file": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0
        },
        "jpcoar:URI": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "label",
                        "ref": None
                    },
                    {
                        "use": "optional",
                        "name": "objectType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "abstract",
                                "dataset",
                                "fulltext",
                                "software",
                                "summary",
                                "thumbnail",
                                "other"
                            ]
                        }
                    }
                ]
            }
        },
        "jpcoar:mimeType": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0
            }
        },
        "jpcoar:extent": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0
            }
        },
        "datacite:date": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "dateType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "Accepted",
                                "Available",
                                "Collected",
                                "Copyrighted",
                                "Created",
                                "Issued",
                                "Submitted",
                                "Updated",
                                "Valid"
                            ]
                        }
                    }
                ]
            }
        },
        "datacite:version": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0
            }
        }
    },
    "custom:system_file": {
        "type": {
            "minOccurs": 0,
            "maxOccurs": "unbounded"
        },
        "jpcoar:URI": {
            "type": {
                "minOccurs": 0,
                "maxOccurs": 1,
                "attributes": [
                    {
                        "name": "objectType",
                        "ref": None,
                        "use": "optional",
                        "restriction": {
                            "enumeration": [
                                "abstract",
                                "summary",
                                "fulltext",
                                "thumbnail",
                                "other"
                            ]
                        }
                    },
                    {
                        "name": "label",
                        "ref": None,
                        "use": "optional"
                    }
                ]
            }
        },
        "jpcoar:mimeType": {
            "type": {
                "minOccurs": 0,
                "maxOccurs": 1
            }
        },
        "jpcoar:extent": {
            "type": {
                "minOccurs": 0,
                "maxOccurs": "unbounded"
            }
        },
        "datacite:date": {
            "type": {
                "minOccurs": 1,
                "maxOccurs": "unbounded",
                "attributes": [
                    {
                        "name": "dateType",
                        "ref": None,
                        "use": "required",
                        "restriction": {
                            "enumeration": [
                                "Accepted",
                                "Available",
                                "Collected",
                                "Copyrighted",
                                "Created",
                                "Issued",
                                "Submitted",
                                "Updated",
                                "Valid"
                            ]
                        }
                    }
                ]
            }
        },
        "datacite:version": {
            "type": {
                "minOccurs": 0,
                "maxOccurs": 1
            }
        }
    },
    "jpcoar:publisher_jpcoar": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
        },
        "jpcoar:publisherName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }]
            }
        },
        "jpcoar:publisherDescription": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }]
            }
        },
        "dcndl:location": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }]
            }
        },
        "dcndl:publicationPlace": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }]
            }
        },
    },
    "dcterms:date_dcterms": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [{
                "use": "optional",
                "name": "xml:lang",
                "ref": "xml:lang"
            }]
        },
    },
    "dcndl:edition": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [{
                "use": "optional",
                "name": "xml:lang",
                "ref": "xml:lang"
            }]
        },
    },
    "dcndl:volumeTitle": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [{
                "use": "optional",
                "name": "xml:lang",
                "ref": "xml:lang"
            }]
        },
    },
    "dcndl:originalLanguage": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [{
                "use": "optional",
                "name": "xml:lang",
                "ref": "xml:lang"
            }]
        },
    },
    "dcterms:extent": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [{
                "use": "optional",
                "name": "xml:lang",
                "ref": "xml:lang"
            }]
        },
    },
    "jpcoar:format": {
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
            "attributes": [{
                "use": "optional",
                "name": "xml:lang",
                "ref": "xml:lang"
            }]
        },
    },
    "jpcoar:holdingAgent": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0,
        },
        "jpcoar:holdingAgentNameIdentifier": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "use": "required",
                        "name": "nameIdentifierScheme",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
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
                        }
                    },
                    {
                        "use": "optional",
                        "name": "nameIdentifierURI",
                        "ref": None
                    }
                ]
            }
        },
        "jpcoar:holdingAgentName": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "optional",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }]
            }
        },
    },
    "jpcoar:datasetSeries": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 0,
            # "attributes": [
            #     {
            #         "use": "optional",
            #         "name": "datasetSeriesType",
            #         "ref": None,
            #         "restriction": {
            #             "enumeration": [
            #                 "True",
            #                 "False",
            #             ]
            #         }
            #     },
            # ]
        },
    },
    "jpcoar:catalog": { 
        "type": {
            "maxOccurs": "unbounded",
            "minOccurs": 0,
        },
        "jpcoar:contributor": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "contributorType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "HostingInstitution",
                            ]
                        }
                    }
                ]
            },
            "jpcoar:contributorName": {
                "type": {
                    "maxOccurs": "unbounded",
                    "minOccurs": 1,
                    "attributes": [{
                        "use": "required",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    }]
                },
            },
        },
        "jpcoar:identifier": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "identifierType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "DOI",
                                "HDL",
                                "URI"
                            ]
                        }
                    }
                ]
            }
        },
        "dc:title": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [{
                    "use": "required",
                    "name": "xml:lang",
                    "ref": "xml:lang"
                }]
            },
        },
        "datacite:description": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "required",
                        "name": "descriptionType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "Abstract",
                                "Methods",
                                "TableOfContents",
                                "TechnicalInfo",
                                "Other"
                            ]
                        }
                    }
                ]
            }
        },
        "jpcoar:subject": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "optional",
                        "name": "subjectURI",
                        "ref": None
                    },
                    {
                        "use": "required",
                        "name": "subjectScheme",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
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
                                "Other",
                            ]
                        }
                    }
                ]
            }
        },
        "jpcoar:license": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "optional",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "required",
                        "name": "licenseType",
                        "ref": None,
                        "restriction": {
                            "enumeration": [
                                "file",
                                "metadata",
                                "thumbnail",
                            ]
                        }
                    },
                    {
                        "use": "required",
                        "name": "rdf:resource",
                        "ref": None
                    },
                ]
            }
        },
        "dc:rights": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "name": "xml:lang",
                        "ref": "xml:lang"
                    },
                    {
                        "use": "required",
                        "name": "rdf:resource",
                        "ref": None
                    },
                ]
            }
        },
        "dcterms:accessRights": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 0,
                "attributes": [
                    {
                        "use": "required",
                        "ref": None,
                        "name": "accessRights",
                        "restriction": {
                            "enumeration": [
                                "embargoed access",
                                "metadata only access",
                                "restricted access",
                                "open access"
                            ]
                        }
                    },
                    {
                        "use": "required",
                        "name": "rdf:resource",
                        "ref": None
                    },
                ]
            }
        },
        "jpcoar:file": {
            "type": {
                "maxOccurs": "unbounded",
                "minOccurs": 0
            },
            "jpcoar:URI": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 0,
                    "attributes": [
                        {
                            "use": "required",
                            "name": "objectType",
                            "ref": None,
                            "restriction": {
                                "enumeration": [
                                    "thumbnail",
                                ]
                            }
                        }
                    ]
                }
            },
        },
    },
}