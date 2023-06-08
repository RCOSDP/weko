import pytest
import sys
sys.path.append("..")

import jpcoar_v2_mapping as jpc2


xsd = jpc2.xsd
xsd_list = list(xsd.keys())

@pytest.mark.parametrize(
    "item, content",
    [
        ("jpcoar:publisher_jpcoar", [
            "jpcoar:publisherName",
            "jpcoar:publisherDescription",
            "dcndl:location",
            "dcndl:publicationPlace",
        ]),
        ("dcterms:date", []),
        ("jpcoar:fundingReference", [
            "jpcoar:fundingStreamIdentifier",
            "jpcoar:fundingStream",
        ]),
        ("dcndl:edition", []),
        ("dcndl:volumeTitle", []),
        ("dcndl:originalLanguage", []),
        ("dcterms:extent", []),
        ("jpcoar:format", []),
        ("jpcoar:holdingAgent", [
            "jpcoar:holdingAgentNameIdentifier",
            "jpcoar:holdingAgentName",
        ]),
        ("jpcoar:datasetSeries", []),
        ("jpcoar:catalog", [
            {"jpcoar:contributor": "jpcoar:contributorName"},
            "jpcoar:identifier",
            "dc:title",
            "datacite:description",
            "jpcoar:subject",
            "jpcoar:license",
            "dc:rights",
            "dcterms:accessRights",
            {"jpcoar:file": "jpcoar:URI"},
        ]),
    ]
)
def test_check_new_items(item, content):
    for key in xsd_list:
        inner_item_list = list(xsd[key].keys())

        # jpcoar:publisher_jpcoar
        if item == "jpcoar:publisher_jpcoar" and key == item:
            for value in content:
                assert value in inner_item_list

        # dcterms:date
        elif item == "dcterms:date" and key == item:
            assert item in xsd

        # jpcoar:fundingReference
        elif item == "jpcoar:fundingReference" and key == item:
            for value in content:
                if value == "jpcoar:fundingStreamIdentifier":
                    attributes = xsd[key][value]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" not in list(att.keys()):
                            assert "fundingStreamIdentifierTypeURI" == att["name"]
                        else:
                            assert "fundingStreamIdentifierType" == att["name"]
                            assert "Crossref Funder" in att["restriction"]["enumeration"]
                            assert "JGN_fundingStream" in att["restriction"]["enumeration"]
                else:
                    assert value in inner_item_list
        
        # dcterms:date
        elif item == "dcterms:date" and key == item:
            assert item in xsd
        
        # dcndl:edition
        elif item == "dcndl:edition" and key == item:
            assert item in xsd

        # dcndl:volumeTitle
        elif item == "dcndl:volumeTitle" and key == item:
            assert item in xsd

        # dcndl:originalLanguage
        elif item == "dcndl:originalLanguage" and key == item:
            assert item in xsd

        # dcterms:extent
        elif item == "dcterms:extent" and key == item:
            assert item in xsd
        
        # jpcoar:format
        elif item == "jpcoar:format" and key == item:
            assert item in xsd

        # jpcoar:holdingAgent
        elif item == "jpcoar:holdingAgent" and key == item:
            for value in content:
                assert value in inner_item_list

        # jpcoar:datasetSeries
        elif item == "jpcoar:datasetSeries" and key == item:
            assert item in xsd

        # jpcoar:catalog
        if item == "jpcoar:catalog" and key == item:
            content_that_is_an_instance_of_dict = [
                "jpcoar:contributor",
                "jpcoar:file"
            ]
            for value in content:
                if isinstance(value, dict):
                    content_key = list(value.keys())[0]
                    content_value = list(value.values())[0]
                    assert content_key in content_that_is_an_instance_of_dict
                    assert content_value in xsd[key][content_key].keys()
                else:
                    assert value in inner_item_list


@pytest.mark.parametrize(
    "item, content",
    [
        ("jpcoar:fundingReference", [
            "jpcoar:funderIdentifier",
            "jpcoar:awardNumber",
        ]),
        ("jpcoar:fundingReferenceOld", [
            "datacite:funderIdentifier",
            "datacite:awardNumber",
        ]),
        ("jpcoar:creator", [
            "type",
            "jpcoar:creatorName",
            "jpcoar:affiliation"
        ]),
        ("jpcoar:contributor", [
            "jpcoar:contributorName",
            "jpcoar:affiliation"
        ]),
        ("jpcoar:subject", [
            "type"
        ]),
        ("jpcoar:relation", [
            "type",
            "jpcoar:relatedIdentifier"
        ]),
    ]
)
def test_check_changed_items(item, content):
    for key in xsd_list:
        inner_item_list = list(xsd[key].keys())

        # jpcoar:fundingReference
        if item == "jpcoar:fundingReference" and key == item:
            for value in content:
                assert value in inner_item_list

                if value == "jpcoar:funderIdentifier":
                    attributes = xsd[key][value]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" not in list(att.keys()):
                            assert "funderIdentifierTypeURI" == att["name"]
                        else:
                            assert "e-Rad_funder" in att["restriction"]["enumeration"]
                            assert "ROR" in att["restriction"]["enumeration"]

                elif value == "jpcoar:awardNumber":
                    attributes = xsd[key][value]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "awardNumberType" == att["name"]
                            assert "JGN" in att["restriction"]["enumeration"]
                        
        elif item == "jpcoar:fundingReferenceOld" and key == item:
            for value in content:
                assert not value in inner_item_list

        # jpcoar:creator
        elif item == "jpcoar:creator" and key == item:
            for value in content:
                if value == "type":
                    attributes = xsd[key][value]["attributes"]
                    for att in attributes:
                        assert "creatorType" == att["name"]

                elif value == "jpcoar:creatorName":
                    attributes = xsd[key][value]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "Organizational" in att["restriction"]["enumeration"]
                            assert "Personal" in att["restriction"]["enumeration"]
                
                elif value == "jpcoar:affiliation":
                    attributes = xsd[key][value]["jpcoar:nameIdentifier"]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "kakenhi" in att["restriction"]["enumeration"]
                            assert "GRID" in att["restriction"]["enumeration"]
                            assert "ROR" in att["restriction"]["enumeration"]

        # jpcoar:contributor
        elif item == "jpcoar:contributor" and key == item:
            for value in content:
                if value == "jpcoar:contributorName":
                    attributes = xsd[key][value]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "Organizational" in att["restriction"]["enumeration"]
                            assert "Personal" in att["restriction"]["enumeration"]

                elif value == "jpcoar:affiliation":
                    attributes = xsd[key][value]["jpcoar:nameIdentifier"]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "kakenhi" in att["restriction"]["enumeration"]
                            assert "ISNI" in att["restriction"]["enumeration"]
                            assert "Ringgold" in att["restriction"]["enumeration"]
                            assert "GRID" in att["restriction"]["enumeration"]
                            assert "ROR" in att["restriction"]["enumeration"]
                            assert len(att["restriction"]["enumeration"]) == 5

        # jpcoar:subject
        elif item == "jpcoar:subject" and key == item:
            for value in content:
                attributes = xsd[key][value]["attributes"]
                for att in attributes:
                    if att["name"] == "subjectScheme":
                        assert "e-Rad_field" in att["restriction"]["enumeration"]
                        assert "JEL" in att["restriction"]["enumeration"]
                    else:
                        assert "subjectScheme" != att["name"]

        # jpcoar:relation
        elif item == "jpcoar:relation" and key == item:
            for value in content:
                if value == "type":
                    attributes = xsd[key][value]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "inSeries" in att["restriction"]["enumeration"]
                            assert "isCitedBy" in att["restriction"]["enumeration"]
                            assert "Cites" in att["restriction"]["enumeration"]

                elif value == "jpcoar:relatedIdentifier":
                    attributes = xsd[key][value]["type"]["attributes"]
                    for att in attributes:
                        if "restriction" in list(att.keys()):
                            assert "CRID" in att["restriction"]["enumeration"]


@pytest.mark.parametrize(
    "item, content",
    [
        ("rioxxterms:apc", []),
    ]
)
def test_check_deleted_items(item, content):
    assert item not in xsd_list
