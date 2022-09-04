schema_name = "oai_dc_mapping"
target_namespace = "oai_dc"
schema_location = "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
form_data = {
    "name": "oai_dc_mapping",
    "xsd_file": "http://dublincore.org/schemas/xmls/simpledc20021212.xsd", 
    "file_name": "oai_dc.xsd",
    "root_name": "dc"
}
namespaces = {
    "": "http://www.w3.org/2001/XMLSchema",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/"
}
xsd = {
    "dc:title": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:creator": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:subject": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:description": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:publisher": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:contributor": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:date": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:type": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:format": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:identifier": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:source": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:language": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:relation": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:coverage": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    },
    "dc:rights": {
        "type": {
            "minOccurs": 1,
            "maxOccurs": 1,
            "attributes": [
                {
                    "ref": "xml:lang",
                    "name": "xml:lang",
                    "use": "optional"
                }
            ]
        }
    }
}