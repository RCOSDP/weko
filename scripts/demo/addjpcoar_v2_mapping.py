from weko_records.models import ItemTypeMapping
from weko_records.api import Mapping
from sqlalchemy.sql import func
from sqlalchemy import desc
from invenio_db import db
import pickle

from properties import (
    creator,
    contributor,
    funding_reference,
    jpcoar_catalog,
    jpcoar_dataset_series,
    jpcoar_holding_agent,
    jpcoar_format,
    dcterms_extent,
    dcndl_original_language,
    dcndl_volume_title,
    dcndl_edition,
    date_literal,
    publisher_info,
)


def main():
    try:
        res = db.session.query(ItemTypeMapping.id).all()
        for _id in list(res):
            with db.session.begin_nested():
                item_type = (
                    ItemTypeMapping.query.filter(ItemTypeMapping.id == _id)
                    .order_by(desc(ItemTypeMapping.version_id))
                    .first()
                )
                print("processing item type: {}".format(item_type.id))
                mapping = pickle.loads(pickle.dumps(item_type.mapping, -1))
                for key in list(mapping.keys()):
                    if "jpcoar_v1_mapping" in mapping[key]:
                        # jpcoar_catalog,
                        if (
                            "catalog"
                            or "datasetSeries"
                            or "holdingAgent"
                            or "format"
                            or "extent"
                            or "originalLanguage"
                            or "volumeTitle"
                            or "edition"
                            or "date_dcterms"
                            or "publisher_jpcoar"
                        ) not in mapping[key]["jpcoar_mapping"]:
                            mapping[key]["jpcoar_mapping"] = mapping[key][
                                "jpcoar_v1_mapping"
                            ]
                        
                        # creator
                        if "creator" in mapping[key]["jpcoar_mapping"]:
                            if (
                                "@attributes"
                                not in mapping[key]["jpcoar_mapping"]["creator"]
                            ):
                                mapping[key]["jpcoar_mapping"]["creator"][
                                    "@attributes"
                                ] = {"creatorType": "creatorType"}
                            if (
                                "creatorName"
                                in mapping[key]["jpcoar_mapping"]["creator"]
                            ):
                                if (
                                    "@attributes"
                                    in mapping[key]["jpcoar_mapping"]["creator"][
                                        "creatorName"
                                    ]
                                ):
                                    mapping[key]["jpcoar_mapping"]["creator"][
                                        "creatorName"
                                    ]["@attributes"].update(
                                        {"nameType": "creatorNames.creatorNameType"}
                                    )
                                else:
                                    mapping[key]["jpcoar_mapping"]["creator"][
                                        "creatorName"
                                    ] = {
                                        "@attributes": {
                                            "nameType": "creatorNames.creatorNameType"
                                        }
                                    }
                        # contributor
                        if "contributor" in mapping[key]["jpcoar_mapping"]:
                            if (
                                "contributorName"
                                in mapping[key]["jpcoar_mapping"]["contributor"]
                            ):
                                if (
                                    "@attributes"
                                    in mapping[key]["jpcoar_mapping"]["contributor"][
                                        "contributorName"
                                    ]
                                ):
                                    mapping[key]["jpcoar_mapping"]["contributor"][
                                        "contributorName"
                                    ]["@attributes"].update(
                                        {"nameType": "creatorNames.creatorNameType"}
                                    )
                                else:
                                    mapping[key]["jpcoar_mapping"]["contributor"][
                                        "contributorName"
                                    ] = {
                                        "@attributes": {
                                            "nameType": "creatorNames.creatorNameType"
                                        }
                                    }
                        # funding_reference,
                        if "fundingReference" in mapping[key]["jpcoar_mapping"]:
                            if (
                                "funderIdentifier"
                                in mapping[key]["jpcoar_mapping"]["fundingReference"]
                            ):
                                if (
                                    "@attributes"
                                    in mapping[key]["jpcoar_mapping"][
                                        "fundingReference"
                                    ]["funderIdentifier"]
                                ):
                                    mapping[key]["jpcoar_mapping"]["fundingReference"][
                                        "funderIdentifier"
                                    ]["@attributes"].update(
                                        {
                                            "funderIdentifierTypeURI": "subitem_funder_identifiers.subitem_funder_identifier_type_uri"
                                        }
                                    )
                                else:
                                    mapping[key]["jpcoar_mapping"]["fundingReference"][
                                        "funderIdentifier"
                                    ] = {
                                        "@attributes": {
                                            "funderIdentifierTypeURI": "subitem_funder_identifiers.subitem_funder_identifier_type_uri"
                                        }
                                    }

                            if (
                                "awardNumber"
                                in mapping[key]["jpcoar_mapping"]["fundingReference"]
                            ):
                                if (
                                    "@attributes"
                                    in mapping[key]["jpcoar_mapping"][
                                        "fundingReference"
                                    ]["awardNumber"]
                                ):
                                    mapping[key]["jpcoar_mapping"]["fundingReference"][
                                        "awardNumber"
                                    ]["@attributes"].update(
                                        {
                                            "awardNumberType": "subitem_award_numbers.subitem_award_number_type"
                                        }
                                    )
                                else:
                                    mapping[key]["jpcoar_mapping"]["fundingReference"][
                                        "awardNumber"
                                    ] = {
                                        "@attributes": {
                                            "awardNumberType": "subitem_award_numbers.subitem_award_number_type"
                                        }
                                    }

                item_type.mapping = mapping
        db.session.commit()
    except Exception as ex:
        print(ex)
        db.session.rollback()


if __name__ == "__main__":
    """Main context."""
    main()
