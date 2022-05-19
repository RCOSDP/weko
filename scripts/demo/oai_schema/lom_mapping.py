schema_name = "lom_mapping"
target_namespace = None
schema_location = "http://www.lido-schema.org http://www.lido-schema.org/schema/v1.0/lido-v1.0.xsd"
form_data = {
    "name": "lom",
    "zip_name": "lom.zip",
    "file_name": "lom.xsd",
    "root_name": "lom"
}
namespaces = {
    "": "http://ltsc.ieee.org/xsd/LOM",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "xml": "http://www.w3.org/XML/1998/namespace"
}
xsd = {
    "lom:general": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1,
            "attributes": [
                {
                    "name": "uniqueElementName",
                    "use": "optional",
                    "ref": None
                }
            ]
        },
        "lom:identifier": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:catalog": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            },
            "lom:entry": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:title": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:language": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            }
        },
        "lom:description": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:keyword": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:coverage": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:structure": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "atomic",
                            "collection",
                            "networked",
                            "hierarchical",
                            "linear"
                        ]
                    }
                }
            }
        },
        "lom:aggregationLevel": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "1",
                            "2",
                            "3",
                            "4"
                        ]
                    }
                }
            }
        }
    },
    "lom:lifeCycle": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1,
            "attributes": [
                {
                    "name": "uniqueElementName",
                    "use": "optional",
                    "ref": None
                }
            ]
        },
        "lom:version": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:status": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "draft",
                            "final",
                            "revised",
                            "unavailable"
                        ]
                    }
                }
            }
        },
        "lom:contribute": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:role": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:source": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {
                            "enumeration": [
                                "LOMv1.0"
                            ]
                        }
                    }
                },
                "lom:value": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {
                            "enumeration": [
                                "author",
                                "publisher",
                                "unknown",
                                "initiator",
                                "terminator",
                                "validator",
                                "editor",
                                "graphical designer",
                                "technical implementer",
                                "content provider",
                                "technical validator",
                                "educational validator",
                                "script writer",
                                "instructional designer",
                                "subject matter expert"
                            ]
                        }
                    }
                }
            },
            "lom:entity": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {}
                }
            },
            "lom:date": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:dateTime": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {
                            "patterns": [
                                "^([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]|[0-9][1-9][0-9]{2}|[1-9][0-9]{3})(\\\\-(0[1-9]|1[0-2])(\\\\-(0[1-9]|[12][0-9]|3[01])(T([01][0-9]|2[0-3])(:[0-5][0-9](:[0-5][0-9](\\\\.[0-9]{1,}(Z|((\\\\+|\\\\-)([01][0-9]|2[0-3]):[0-5][0-9]))?)?)?)?)?)?)?$"
                            ]
                        }
                    }
                },
                "lom:description": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ]
                    },
                    "lom:string": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "language",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {}
                        }
                    }
                }
            }
        }
    },
    "lom:metaMetadata": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1,
            "attributes": [
                {
                    "name": "uniqueElementName",
                    "use": "optional",
                    "ref": None
                }
            ]
        },
        "lom:identifier": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:catalog": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            },
            "lom:entry": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:contribute": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:role": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:source": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {
                            "enumeration": [
                                "LOMv1.0"
                            ]
                        }
                    }
                },
                "lom:value": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {
                            "enumeration": [
                                "creator",
                                "validator"
                            ]
                        }
                    }
                }
            },
            "lom:entity": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "restriction": {}
                }
            },
            "lom:date": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:dateTime": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {
                            "patterns": [
                                "^([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]|[0-9][1-9][0-9]{2}|[1-9][0-9]{3})(\\\\-(0[1-9]|1[0-2])(\\\\-(0[1-9]|[12][0-9]|3[01])(T([01][0-9]|2[0-3])(:[0-5][0-9](:[0-5][0-9](\\\\.[0-9]{1,}(Z|((\\\\+|\\\\-)([01][0-9]|2[0-3]):[0-5][0-9]))?)?)?)?)?)?)?$"
                            ]
                        }
                    }
                },
                "lom:description": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ]
                    },
                    "lom:string": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "language",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {}
                        }
                    }
                }
            }
        },
        "lom:metadataSchema": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "restriction": {}
            }
        },
        "lom:language": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            }
        }
    },
    "lom:technical": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1,
            "attributes": [
                {
                    "name": "uniqueElementName",
                    "use": "optional",
                    "ref": None
                }
            ]
        },
        "lom:format": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "restriction": {}
            }
        },
        "lom:size": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ],
                "restriction": {}
            }
        },
        "lom:location": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "restriction": {}
            }
        },
        "lom:requirement": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:orComposite": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1
                },
                "lom:type": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ]
                    },
                    "lom:source": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "uniqueElementName",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {
                                "enumeration": [
                                    "LOMv1.0"
                                ]
                            }
                        }
                    },
                    "lom:value": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "uniqueElementName",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {
                                "enumeration": [
                                    "operating system",
                                    "browser"
                                ]
                            }
                        }
                    }
                },
                "lom:name": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ]
                    },
                    "lom:source": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "uniqueElementName",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {
                                "enumeration": [
                                    "LOMv1.0"
                                ]
                            }
                        }
                    },
                    "lom:value": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "uniqueElementName",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {
                                "enumeration": [
                                    "pc-dos",
                                    "ms-windows",
                                    "macos",
                                    "unix",
                                    "multi-os",
                                    "none",
                                    "any",
                                    "netscape communicator",
                                    "ms-internet explorer",
                                    "opera",
                                    "amaya"
                                ]
                            }
                        }
                    }
                },
                "lom:minimumVersion": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                },
                "lom:maximumVersion": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            }
        },
        "lom:installationRemarks": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:otherPlatformRequirements": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:duration": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:duration": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "patterns": [
                            "^P([0-9]{1,}Y){0,1}([0-9]{1,}M){0,1}([0-9]{1,}D){0,1}(T([0-9]{1,}H){0,1}([0-9]{1,}M){0,1}([0-9]{1,}(\\\\.[0-9]{1,}){0,1}S){0,1}){0,1}$"
                        ]
                    }
                }
            },
            "lom:description": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:string": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "language",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            }
        }
    },
    "lom:educational": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1
        },
        "lom:interactivityType": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "active",
                            "expositive",
                            "mixed"
                        ]
                    }
                }
            }
        },
        "lom:learningResourceType": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "exercise",
                            "simulation",
                            "questionnaire",
                            "diagram",
                            "figure",
                            "graph",
                            "index",
                            "slide",
                            "table",
                            "narrative text",
                            "exam",
                            "experiment",
                            "problem statement",
                            "self assessment",
                            "lecture"
                        ]
                    }
                }
            }
        },
        "lom:interactivityLevel": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "very low",
                            "low",
                            "medium",
                            "high",
                            "very high"
                        ]
                    }
                }
            }
        },
        "lom:semanticDensity": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "very low",
                            "low",
                            "medium",
                            "high",
                            "very high"
                        ]
                    }
                }
            }
        },
        "lom:intendedEndUserRole": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "teacher",
                            "author",
                            "learner",
                            "manager"
                        ]
                    }
                }
            }
        },
        "lom:context": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "school",
                            "higher education",
                            "training",
                            "other"
                        ]
                    }
                }
            }
        },
        "lom:typicalAgeRange": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:difficulty": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "very easy",
                            "easy",
                            "medium",
                            "difficult",
                            "very difficult"
                        ]
                    }
                }
            }
        },
        "lom:typicalLearningTime": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:duration": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "patterns": [
                            "^P([0-9]{1,}Y){0,1}([0-9]{1,}M){0,1}([0-9]{1,}D){0,1}(T([0-9]{1,}H){0,1}([0-9]{1,}M){0,1}([0-9]{1,}(\\\\.[0-9]{1,}){0,1}S){0,1}){0,1}$"
                        ]
                    }
                }
            },
            "lom:description": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:string": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "language",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            }
        },
        "lom:description": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:language": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            }
        }
    },
    "lom:rights": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1,
            "attributes": [
                {
                    "name": "uniqueElementName",
                    "use": "optional",
                    "ref": None
                }
            ]
        },
        "lom:cost": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "yes",
                            "no"
                        ]
                    }
                }
            }
        },
        "lom:copyrightAndOtherRestrictions": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "yes",
                            "no"
                        ]
                    }
                }
            }
        },
        "lom:description": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        }
    },
    "lom:relation": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1
        },
        "lom:kind": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "ispartof",
                            "haspart",
                            "isversionof",
                            "hasversion",
                            "isformatof",
                            "hasformat",
                            "references",
                            "isreferencedby",
                            "isbasedon",
                            "isbasisfor",
                            "requires",
                            "isrequiredby"
                        ]
                    }
                }
            }
        },
        "lom:resource": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:identifier": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1
                },
                "lom:catalog": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                },
                "lom:entry": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            },
            "lom:description": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:string": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "language",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            }
        }
    },
    "lom:annotation": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1
        },
        "lom:entity": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ],
                "restriction": {}
            }
        },
        "lom:date": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:dateTime": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "patterns": [
                            "^([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]|[0-9][1-9][0-9]{2}|[1-9][0-9]{3})(\\\\-(0[1-9]|1[0-2])(\\\\-(0[1-9]|[12][0-9]|3[01])(T([01][0-9]|2[0-3])(:[0-5][0-9](:[0-5][0-9](\\\\.[0-9]{1,}(Z|((\\\\+|\\\\-)([01][0-9]|2[0-3]):[0-5][0-9]))?)?)?)?)?)?)?$"
                        ]
                    }
                }
            },
            "lom:description": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:string": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "language",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            }
        },
        "lom:description": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        }
    },
    "lom:classification": {
        "type": {
            "maxOccurs": 1,
            "minOccurs": 1
        },
        "lom:purpose": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "LOMv1.0"
                        ]
                    }
                }
            },
            "lom:value": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {
                        "enumeration": [
                            "discipline",
                            "idea",
                            "prerequisite",
                            "educational objective",
                            "accessibility restrictions",
                            "educational level",
                            "skill level",
                            "security level",
                            "competency"
                        ]
                    }
                }
            }
        },
        "lom:taxonPath": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:source": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "uniqueElementName",
                            "use": "optional",
                            "ref": None
                        }
                    ]
                },
                "lom:string": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "language",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                }
            },
            "lom:taxon": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1
                },
                "lom:id": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ],
                        "restriction": {}
                    }
                },
                "lom:entry": {
                    "type": {
                        "maxOccurs": 1,
                        "minOccurs": 1,
                        "attributes": [
                            {
                                "name": "uniqueElementName",
                                "use": "optional",
                                "ref": None
                            }
                        ]
                    },
                    "lom:string": {
                        "type": {
                            "maxOccurs": 1,
                            "minOccurs": 1,
                            "attributes": [
                                {
                                    "name": "language",
                                    "use": "optional",
                                    "ref": None
                                }
                            ],
                            "restriction": {}
                        }
                    }
                }
            }
        },
        "lom:description": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1,
                "attributes": [
                    {
                        "name": "uniqueElementName",
                        "use": "optional",
                        "ref": None
                    }
                ]
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        },
        "lom:keyword": {
            "type": {
                "maxOccurs": 1,
                "minOccurs": 1
            },
            "lom:string": {
                "type": {
                    "maxOccurs": 1,
                    "minOccurs": 1,
                    "attributes": [
                        {
                            "name": "language",
                            "use": "optional",
                            "ref": None
                        }
                    ],
                    "restriction": {}
                }
            }
        }
    }
}