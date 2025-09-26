import sys
import traceback

from flask import current_app
from invenio_db import db
from properties import property_config
from register_properties import del_properties, get_properties_id, register_properties_from_folder
from tools import updateRestrictedRecords, update_weko_links
from fix_metadata_53602 import main as fix_metadata_53602_main
from weko_records.api import ItemTypes
from fix_issue_47128_jdcat import main as fix_issue_47128_jdcat_main
from fix_issue_47128_newbuild import main as fix_issue_47128_newbuild_main
from update_itemtype_multiple import main as update_itemtype_multiple_main

def main(restricted_item_type_id):
    try:
        current_app.logger.info("run updateRestrictedRecords")
        updateRestrictedRecords.main(restricted_item_type_id) # 制限公開用のアイテムタイプ変更。全アイテムの代理投稿者変更
        current_app.logger.info("run register_properties_only_specified")
        register_properties_only_specified() # propertiesディレクトリ以下にしたがってプロパティの更新
        current_app.logger.info("run renew_all_item_types")
        renew_all_item_types() # 更新されたプロパティを使用してアイテムタイプの更新
        current_app.logger.info("run update_weko_links")
        update_weko_links.main() # 著者DBのweko idの変更。それに伴うメタデータの変更
        update_itemtype_multiple_main()# Multipleという名前のアイテムタイプを修正（アイテムの変更なし)
        fix_issue_47128_jdcat_main() # itemtype_id:12,20の修正＋アイテムの修正
        fix_issue_47128_newbuild_main() # harvesting_type=Trueかつitemtype_id=12の修正＋アイテムの修正
        fix_metadata_53602_main() # プロパティ変更を全アイテムのメタデータに適用
    except Exception as ex:
        current_app.logger.error(ex)
        db.session.rollback()


def register_properties_only_specified():
    exclusion_list = [int(x) for x in property_config.EXCLUSION_LIST]
    try:
        specified_list = property_config.SPECIFIED_LIST
        del_properties(specified_list)
        exclusion_list += get_properties_id()
        register_properties_from_folder(exclusion_list, specified_list)
        db.session.commit()
    except:
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()


def renew_all_item_types():
    try:
        fix_ids = []
        itemtypes = ItemTypes.get_all()
        for itemtype in itemtypes:
            ret = ItemTypes.reload(itemtype.id)
            current_app.logger.info("itemtype id:{}, itemtype name:{}".format(itemtype.id,itemtype.item_type_name.name))
            current_app.logger.info(ret['msg'])
            print(f"[FIX][renew_all_item_types]item_type:{itemtype.id}")
            is_fix_mapping = False
            if "mapping" in ret.get("msg",""):
                is_fix_mapping = True
            else:
                is_fix_mapping = False
            fix_ids.append((itemtype.id, is_fix_mapping))
        db.session.commit()
        
        for (itemtype_id, is_fix_mapping) in fix_ids:
            print(f"[FIX][renew_all_item_types]item_type:{itemtype_id}")
            if is_fix_mapping:
                print(f"[FIX][renew_all_item_types]item_type_mapping:{itemtype_id}(item_type_id)")
    except:
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        restricted_item_type_id = int(args[1])
        main(restricted_item_type_id)
    else:
        print("Please provide restricted_item_type_id as an argument.")
        sys.exit(1)
