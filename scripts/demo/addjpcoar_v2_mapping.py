from weko_records.models import ItemType,ItemTypeMapping
from weko_records.api import Mapping, ItemTypes
from sqlalchemy.sql import func
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc
from invenio_db import db
import pickle
import traceback

from properties import (
    property_config,
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
        res = db.session.query(ItemType.id).all()
        for _id in list(res):
            with db.session.begin_nested():
                # itemtypemappingはversion_idがあるにもかかわらず、idが優先される。
                item_type_mapping = (
                    ItemTypeMapping.query.filter(ItemTypeMapping.item_type_id == _id)
                    .order_by(desc(ItemTypeMapping.id))
                    .first()
                )
                print("processing... item type id({}) mapping id({})".format(_id,item_type_mapping.id))
                mapping = pickle.loads(pickle.dumps(item_type_mapping.mapping, -1))
                for key in list(mapping.keys()):
                    if "jpcoar_mapping" not in mapping[key] and "jpcoar_v1_mapping" in mapping[key]:
                        mapping[key]["jpcoar_mapping"] = mapping[key][
                                "jpcoar_v1_mapping"
                            ]
                    elif "jpcoar_mapping" not in mapping[key] and "jpcoar_v1_mapping" not in mapping[key] and ( "oai_dc_mapping" in mapping[key] or "ddi_mapping" in mapping[key]):
                        mapping[key]["jpcoar_v1_mapping"] = ""
                        mapping[key]["jpcoar_mapping"] = ""
                    else:
                        mapping[key]={"display_lang_type": "","jpcoar_v1_mapping":"","jpcoar_mapping": "","junii2_mapping": "","lido_mapping": "","lom_mapping": "","oai_dc_mapping":"","spase_mapping": "",}

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
                    
                item_type_mapping.mapping = pickle.loads(pickle.dumps(mapping, -1))
                flag_modified(item_type_mapping,"mapping")
                db.session.merge(item_type_mapping)
        db.session.commit()
    except Exception as ex:
        print(traceback.format_exc())
        db.session.rollback()


if __name__ == "__main__":
    """Main context."""
    main()
