from pprint import pprint as pp
import pytest
import sys
sys.path.append("..")

import jpcoar_v1_mapping as jpc1
import jpcoar_v2_mapping as jpc2


xsd1 = jpc1.xsd
xsd1_list = list(xsd1.keys())
xsd2 = jpc2.xsd
xsd2_list = list(xsd2.keys())


@pytest.mark.parametrize(
    "item",
    [
        'jpcoar:pageEnd',
        'dc:publisher',
        'datacite:description',
        'jpcoar:sourceTitle',
        'jpcoar:creator',
        'jpcoar:rightsHolder',
        'jpcoar:issue',
        'jpcoar:relation',
        'jpcoar:contributor',
        'jpcoar:datasetSeries',
        'datacite:geoLocation',
        'jpcoar:holdingAgent',
        'jpcoar:fundingReference',
        'dcterms:date_dcterms',
        'jpcoar:sourceIdentifier',
        'jpcoar:pageStart',
        'jpcoar:conference',
        'jpcoar:publisher_jpcoar',
        'dcndl:dissertationNumber',
        'jpcoar:catalog',
        'dc:language',
        'dc:type',
        'jpcoar:identifierRegistration',
        'dc:title',
        'dcterms:accessRights',
        'dcndl:degreeName',
        'dcterms:alternative',
        'jpcoar:identifier',
        'dcndl:edition',
        'dcndl:volumeTitle',
        'dcterms:extent',
        'jpcoar:degreeGrantor',
        'dc:rights',
        'jpcoar:subject',
        'custom:system_file',
        'jpcoar:volume',
        'jpcoar:file',
        'jpcoar:numPages',
        'datacite:date',
        'datacite:version',
        'dcterms:temporal',
        'dcndl:originalLanguage',
        'dcndl:dateGranted',
        'oaire:versiontype',
        'jpcoar:format'
    ]
)
def test_jpcoar_v2_item_key_check(item):
    if item == "jpcoar:publisher_jpcoar":
        assert item not in xsd1_list
        assert item in xsd2_list
    
    elif item == "dcterms:date_dcterms":
        assert item not in xsd1_list
        assert item in xsd2_list
    
    elif item == "dcndl:edition":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "dcndl:volumeTitle":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "dcndl:originalLanguage":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "dcterms:extent":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "jpcoar:format":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "jpcoar:holdingAgent":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "jpcoar:datasetSeries":
        assert item not in xsd1_list
        assert item in xsd2_list

    elif item == "jpcoar:catalog":
        assert item not in xsd1_list
        assert item in xsd2_list

    else:
        assert item in xsd1_list
        assert item in xsd2_list


@pytest.mark.parametrize(
    "item",
    [
        'jpcoar:pageEnd',
        'dc:publisher',
        'datacite:description',
        'jpcoar:sourceTitle',
        'jpcoar:creator',
        'jpcoar:rightsHolder',
        'jpcoar:issue',
        'jpcoar:relation',
        'jpcoar:contributor',
        'jpcoar:datasetSeries',
        'datacite:geoLocation',
        'jpcoar:holdingAgent',
        'jpcoar:fundingReference',
        'dcterms:date_dcterms',
        'jpcoar:sourceIdentifier',
        'jpcoar:pageStart',
        'jpcoar:conference',
        'jpcoar:publisher_jpcoar',
        'dcndl:dissertationNumber',
        'jpcoar:catalog',
        'dc:language',
        'dc:type',
        'jpcoar:identifierRegistration',
        'dc:title',
        'dcterms:accessRights',
        'dcndl:degreeName',
        'dcterms:alternative',
        'jpcoar:identifier',
        'dcndl:edition',
        'dcndl:volumeTitle',
        'dcterms:extent',
        'jpcoar:degreeGrantor',
        'dc:rights',
        'jpcoar:subject',
        'custom:system_file',
        'jpcoar:volume',
        'jpcoar:file',
        'jpcoar:numPages',
        'datacite:date',
        'datacite:version',
        'dcterms:temporal',
        'dcndl:originalLanguage',
        'dcndl:dateGranted',
        'oaire:versiontype',
        'jpcoar:format'
    ]
)
def test_jpcoar_v2_value_key_check(item):
    if item == "jpcoar:publisher_jpcoar":
        assert xsd2[item]["jpcoar:publisherName"] is not None
        assert xsd2[item]["jpcoar:publisherName"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert xsd2[item]["jpcoar:publisherDescription"] is not None
        assert xsd2[item]["jpcoar:publisherDescription"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert xsd2[item]["dcndl:location"] is not None
        assert xsd2[item]["dcndl:publicationPlace"] is not None

    elif item == "dcterms:date_dcterms":
        assert xsd2[item] is not None
    
    elif item == "dcndl:edition":
        assert xsd2[item] is not None
        assert xsd2[item]["type"]["attributes"][0]["name"] == "xml:lang"

    elif item == "dcndl:volumeTitle":
        assert xsd2[item] is not None
        assert xsd2[item]["type"]["attributes"][0]["name"] == "xml:lang"

    elif item == "dcndl:originalLanguage":
        assert xsd2[item] is not None

    elif item == "dcterms:extent":
        assert xsd2[item] is not None
        assert xsd2[item]["type"]["attributes"][0]["name"] == "xml:lang"

    elif item == "jpcoar:format":
        print(xsd2[item])
        assert xsd2[item] is not None
        assert xsd2[item]["type"]["attributes"][0]["name"] == "xml:lang"

    elif item == "jpcoar:holdingAgent":
        assert xsd2[item]["jpcoar:holdingAgentNameIdentifier"] is not None
        assert xsd2[item]["jpcoar:holdingAgentNameIdentifier"]["type"]["attributes"][0]["name"] == "nameIdentifierScheme"

        nameIdentifierScheme = [
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

        for content in nameIdentifierScheme:
            assert content in xsd2[item]["jpcoar:holdingAgentNameIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]

        assert xsd2[item]["jpcoar:holdingAgentNameIdentifier"]["type"]["attributes"][1]["name"] == "nameIdentifierURI"
        assert xsd2[item]["jpcoar:holdingAgentName"] is not None
        assert xsd2[item]["jpcoar:holdingAgentName"]["type"]["attributes"][0]["name"] == "xml:lang"
        
    elif item == "jpcoar:datasetSeries":
        assert xsd2[item] is not None
        assert "True" in xsd2[item]["type"]["attributes"][0]["restriction"]["enumeration"]
        assert "False" in xsd2[item]["type"]["attributes"][0]["restriction"]["enumeration"]

    elif item == "jpcoar:catalog":
        assert xsd2[item]["jpcoar:contributor"] is not None
        assert xsd2[item]["jpcoar:contributor"]["type"]["attributes"][0]["name"] == "contributorType"
        assert xsd2[item]["jpcoar:contributor"]["jpcoar:contributorName"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert "HostingInstitution" in xsd2[item]["jpcoar:contributor"]["type"]["attributes"][0]["restriction"]["enumeration"]

        assert xsd2[item]["jpcoar:identifier"] is not None
        assert xsd2[item]["jpcoar:identifier"]["type"]["attributes"][0]["name"] == "identifierType"
        assert "DOI" in xsd2[item]["jpcoar:identifier"]["type"]["attributes"][0]["restriction"]["enumeration"]
        assert "HDL" in xsd2[item]["jpcoar:identifier"]["type"]["attributes"][0]["restriction"]["enumeration"]
        assert "URI" in xsd2[item]["jpcoar:identifier"]["type"]["attributes"][0]["restriction"]["enumeration"]

        assert xsd2[item]["dc:title"] is not None
        assert xsd2[item]["dc:title"]["type"]["attributes"][0]["name"] == "xml:lang"

        assert xsd2[item]["datacite:description"] is not None
        assert xsd2[item]["datacite:description"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert xsd2[item]["datacite:description"]["type"]["attributes"][1]["name"] == "descriptionType"
        descriptionType = [
            "Abstract",
            "Methods",
            "TableOfContents",
            "TechnicalInfo",
            "Other"
        ]
        for content in descriptionType:
            assert content in xsd2[item]["datacite:description"]["type"]["attributes"][1]["restriction"]["enumeration"]
            
        assert xsd2[item]["jpcoar:subject"] is not None
        assert xsd2[item]["jpcoar:subject"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert xsd2[item]["jpcoar:subject"]["type"]["attributes"][1]["name"] == "subjectURI"
        assert xsd2[item]["jpcoar:subject"]["type"]["attributes"][2]["name"] == "subjectScheme"
        subjectScheme = [
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
        for content in subjectScheme:
            assert content in xsd2[item]["jpcoar:subject"]["type"]["attributes"][2]["restriction"]["enumeration"]

        assert xsd2[item]["jpcoar:license"] is not None
        assert xsd2[item]["jpcoar:license"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert xsd2[item]["jpcoar:license"]["type"]["attributes"][1]["name"] == "licenseType"
        licenseType = [
            "file",
            "metadata",
            "thumbnail",
        ]
        for content in licenseType:
            assert content in xsd2[item]["jpcoar:license"]["type"]["attributes"][1]["restriction"]["enumeration"]
        assert xsd2[item]["jpcoar:license"]["type"]["attributes"][2]["name"] == "rdf:resource"

        assert xsd2[item]["dc:rights"] is not None
        assert xsd2[item]["dc:rights"]["type"]["attributes"][0]["name"] == "xml:lang"
        assert xsd2[item]["dc:rights"]["type"]["attributes"][1]["name"] == "rdf:resource"

        assert xsd2[item]["dcterms:accessRights"] is not None
        accessRightsList = [
            "embargoed access",
            "metadata only access",
            "restricted access",
            "open access"
        ]
        for content in accessRightsList:
            assert content in xsd2[item]["dcterms:accessRights"]["type"]["attributes"][0]["restriction"]["enumeration"]
        assert xsd2[item]["dcterms:accessRights"]["type"]["attributes"][1]["name"] == "rdf:resource"

        assert xsd2[item]["jpcoar:file"] is not None
        assert "thumbnail" in xsd2[item]["jpcoar:file"]["jpcoar:URI"]["type"]["attributes"][0]["restriction"]["enumeration"]

    elif item == "jpcoar:fundingReference":
        assert "datacite:funderIdentifier" in xsd1[item]
        assert "datacite:funderIdentifier" not in xsd2
        assert "datacite:awardNumber" in xsd1[item]
        assert "datacite:awardNumber" not in xsd2

        assert xsd2[item]["jpcoar:fundingStreamIdentifier"]["type"]["attributes"][0]["name"] == "fundingStreamIdentifierType"
        assert "Crossref Funder" in xsd2[item]["jpcoar:fundingStreamIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]
        assert "JGN_fundingStream" in xsd2[item]["jpcoar:fundingStreamIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]
        assert xsd2[item]["jpcoar:fundingStreamIdentifier"]["type"]["attributes"][0]["name"] == "fundingStreamIdentifierType"
        assert xsd2[item]["jpcoar:fundingStreamIdentifier"]["type"]["attributes"][1]["name"] == "fundingStreamIdentifierTypeURI"

        assert xsd2[item]["jpcoar:fundingStream"]["type"]["attributes"][0]["name"] == "xml:lang"

        assert xsd2[item]["jpcoar:awardNumber"]["type"]["attributes"][1]["name"] == "awardNumberType"
        assert "JGN" in xsd2[item]["jpcoar:awardNumber"]["type"]["attributes"][1]["restriction"]["enumeration"]

        funderIdentifierType = [
            "Crossref Funder",
            "e-Rad_funder",
            "GRID",
            "ISNI",
            "ROR",
            "Other",
        ]
        for content in funderIdentifierType:
            assert content in xsd2[item]["jpcoar:funderIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]

    elif item == "jpcoar:creator":
        assert xsd2[item]["type"]["attributes"][0]["name"] == "creatorType"
        assert xsd2[item]["jpcoar:creatorName"]["type"]["attributes"][1]["name"] == "nameType"
        assert "Organizational" in xsd2[item]["jpcoar:creatorName"]["type"]["attributes"][1]["restriction"]["enumeration"]
        assert "Personal" in xsd2[item]["jpcoar:creatorName"]["type"]["attributes"][1]["restriction"]["enumeration"]
        nameIdentifierScheme = [
            "kakenhi",
            "ISNI",
            "Ringgold",
            "GRID",
            "ROR",
        ]
        for content in nameIdentifierScheme:
            assert content in xsd2[item]["jpcoar:nameIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]

    elif item == "jpcoar:contributor":
        assert xsd2[item]["jpcoar:contributorName"]["type"]["attributes"][1]["name"] == "nameType"
        assert "Organizational" in xsd2[item]["jpcoar:contributorName"]["type"]["attributes"][1]["restriction"]["enumeration"]
        assert "Personal" in xsd2[item]["jpcoar:contributorName"]["type"]["attributes"][1]["restriction"]["enumeration"]
        nameIdentifierScheme = [
            "kakenhi",
            "ISNI",
            "Ringgold",
            "GRID",
            "ROR",
        ]
        for content in nameIdentifierScheme:
            assert content in xsd2[item]["jpcoar:nameIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]

    elif item == "jpcoar:relation":
        relationType = [
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
        for content in relationType:
            assert content in xsd2[item]["type"]["attributes"][0]["restriction"]["enumeration"]
        
        identifierType = [
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
            "NAID",
            "PMID",
            "PURL",
            "SCOPUS",
            "URI",
            "WOS"
        ]
        for content in identifierType:
            assert content in xsd2[item]["jpcoar:relatedIdentifier"]["type"]["attributes"][0]["restriction"]["enumeration"]


def test_apc_key_check():
    item = "rioxxterms:apc"
    assert item in xsd1_list
    assert item not in xsd2_list

# raise BaseException
