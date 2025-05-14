from weko_records.models import ItemType, ItemTypeMapping
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
                    .order_by(desc(ItemTypeMapping.created))
                    .first()
                )
                if item_type_mapping is not None:
                    print(
                        "processing... item type id({}) mapping id({})".format(
                            _id, item_type_mapping.id
                        )
                    )
                    mapping = pickle.loads(pickle.dumps(item_type_mapping.mapping, -1))
                    for key in list(mapping.keys()):
                        if "jpcoar_mapping" in mapping[key]:
                            if "catalog" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "datasetSeries" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "holdingAgent" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "format" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "extent" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "originalLanguage" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "volumeTitle" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "edition" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "date_dcterms" in mapping[key]["jpcoar_mapping"]:
                                continue
                            elif "publisher_jpcoar" in mapping[key]["jpcoar_mapping"]:
                                continue
                            # elif "=" in str(mapping[key]["jpcoar_mapping"]):
                            #     continue
                            elif "jpcoar_v1_mapping" in mapping[key]:
                                mapping[key][
                                    "jpcoar_mapping"
                                ] = item_type_mapping.mapping[key]["jpcoar_v1_mapping"]
                        else:
                            if "jpcoar_v1_mapping" in mapping[key]:
                                mapping[key][
                                    "jpcoar_mapping"
                                ] = item_type_mapping.mapping[key]["jpcoar_v1_mapping"]
                            else:
                                mapping[key] = {
                                    "display_lang_type": "",
                                    "jpcoar_v1_mapping": "",
                                    "jpcoar_mapping": "",
                                    "junii2_mapping": "",
                                    "lido_mapping": "",
                                    "lom_mapping": "",
                                    "oai_dc_mapping": "",
                                    "spase_mapping": "",
                                }

                    item_type_mapping.mapping = pickle.loads(pickle.dumps(mapping, -1))
                    flag_modified(item_type_mapping, "mapping")
                    db.session.merge(item_type_mapping)
                    item_type = ItemTypes.get_by_id(_id,with_deleted=True)
                    if item_type is not None:
                        item_type.render['table_row_map']['mapping']=pickle.loads(pickle.dumps(mapping, -1))
                        flag_modified(item_type, "render")
                        db.session.merge(item_type)

                else:
                    print("No mapping: {}".format(_id))
        db.session.commit()
    except Exception as ex:
        print(traceback.format_exc())
        db.session.rollback()


if __name__ == "__main__":
    """Main context."""
    main()
