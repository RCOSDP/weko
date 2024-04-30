from weko_records.models import ItemTypeMapping
from weko_records.api import Mapping, ItemTypes
from sqlalchemy.sql import func
from sqlalchemy import desc
from invenio_db import db
import pickle
import traceback

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
                itemType = ItemTypes.get_by_id(item_type.item_type_id)
                for key in list(mapping.keys()):
                    if "jpcoar_mapping" not in mapping[key] and "jpcoar_v1_mapping" in mapping[key]:
                        mapping[key]["jpcoar_mapping"] = mapping[key][
                                "jpcoar_v1_mapping"
                            ]
                    if "jpcoar_v1_mapping" in mapping[key] and ((
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
                        ) not in mapping[key]["jpcoar_mapping"]):
                            mapping[key]["jpcoar_mapping"] = mapping[key][
                                "jpcoar_v1_mapping"
                            ]
                    
                item_type.mapping = mapping
        db.session.commit()
    except Exception as ex:
        print(traceback.format_exc())
        db.session.rollback()


if __name__ == "__main__":
    """Main context."""
    main()
