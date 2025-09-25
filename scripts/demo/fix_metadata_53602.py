from datetime import datetime, timedelta
import argparse
import uuid
import sys
import json

from sqlalchemy.orm.attributes import flag_modified
from invenio_db import db
from invenio_records.models import RecordMetadata
from weko_records.models import ItemMetadata
from weko_records.api import ItemTypes
from weko_workflow.models import Activity, WorkFlow, Action, ActivityStatusPolicy
from weko_deposit.api import WekoIndexer

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from elasticsearch import ConnectionError

def parse_args():
    # 初期値
    startDate = ""
    endDate = ""
    recordId = ""
    itemTypeId = ""

    try:
        parser = argparse.ArgumentParser(description="Fix metadata (#53602)")
        parser.add_argument('--start-date', action='store')
        parser.add_argument('--end-date', action='store')
        parser.add_argument("--id", action='store', help="処理対象レコードのUUID")
        parser.add_argument('--item-type-id', action='store')
        args = parser.parse_args()

        # start-date
        if args.start_date:
            try:
                dt = datetime.strptime(args.start_date, "%Y-%m-%dT%H:%M:%S")
                startDate = dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass
            try:
                dt = datetime.strptime(args.start_date, "%Y-%m-%d")
                startDate = dt.strftime("%Y-%m-%dT00:00:00")
            except ValueError as ex:
                if str(ex) == "day is out of range for month":
                    sys.stderr.write(
                        "Error: --start-date option is out of range.\n"
                    )
                    sys.exit(1)
                pass
            try:
                dt = datetime.strptime(args.start_date, "%Y-%m")
                startDate = dt.strftime("%Y-%m-01T00:00:00")
            except ValueError:
                pass
            try:
                dt = datetime.strptime(args.start_date, "%Y")
                startDate = dt.strftime("%Y-01-01T00:00:00")
            except ValueError:
                pass

            if not startDate:
                sys.stderr.write(
                    "Error: The format of the --start-date option is incorrect. "
                    "Supported formats are yyyy-MM-ddTHH:mm:ss, yyyy-MM-dd, yyyy-MM and yyyy.\n"
                )
                sys.exit(1)

        # end-date
        if args.end_date:
            try:
                dt = datetime.strptime(args.end_date, "%Y-%m-%dT%H:%M:%S")
                dt += timedelta(seconds=1)
                endDate = dt.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass
            try:
                dt = datetime.strptime(args.end_date, "%Y-%m-%d")
                dt += timedelta(days=1)
                endDate = dt.strftime("%Y-%m-%dT00:00:00")
            except ValueError as ex:
                if str(ex) == "day is out of range for month":
                    sys.stderr.write(
                        "Error: --end-date option is out of range.\n"
                    )
                    sys.exit(1)
                pass
            try:
                dt = datetime.strptime(args.end_date, "%Y-%m")
                year = dt.year + (1 if dt.month == 12 else 0)
                month = 1 if dt.month == 12 else dt.month + 1
                dt = datetime(year, month, 1)
                endDate = dt.strftime("%Y-%m-%dT00:00:00")
            except ValueError:
                pass
            try:
                dt = datetime.strptime(args.end_date, "%Y")
                dt = datetime(dt.year + 1, 1, 1)
                endDate = dt.strftime("%Y-%m-%dT00:00:00")
            except ValueError:
                pass

            if not endDate:
                sys.stderr.write(
                    "Error: The format of the --end-date option is incorrect. "
                    "Supported formats are yyyy-MM-ddTHH:mm:ss, yyyy-MM-dd, yyyy-MM and yyyy.\n"
                )
                sys.exit(1)

        # start < end の検証（両方指定されている場合のみ）
        if startDate and endDate:
            dt_start = datetime.strptime(startDate, "%Y-%m-%dT%H:%M:%S")
            dt_end = datetime.strptime(endDate, "%Y-%m-%dT%H:%M:%S")
            if not (dt_start < dt_end):
                sys.stderr.write("Error: The --start-date must be earlier than the --end-date.\n")
                sys.exit(1)

        # id チェック
        if args.id:
            try:
                uuid.UUID(args.id)
                recordId = args.id
            except ValueError:
                sys.stderr.write(
                    "Error: The format of the --id option is invalid. Please use a UUID.\n")
                sys.exit(1)

        # item-type-id チェック
        if args.item_type_id:
            try:
                int(args.item_type_id)
                itemTypeId = args.item_type_id
            except ValueError:
                sys.stderr.write(
                    "Error: The format of the --item-type-id option is invalid. Please use integer.\n")
                sys.exit(1)

        return startDate, endDate, recordId, itemTypeId
    except (TypeError, ValueError) as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)
    except SystemExit:
        # argparse のエラーはそのまま上げる
        raise

def get_item_type_info(check_item_keys: dict, item_type_id: str, check_prop_ids: dict):
     # アイテムタイプ情報を取得
    item_type = ItemTypes.get_by_id(item_type_id)
    if not item_type:
        check_item_keys[item_type_id] = {}
        return

    render = item_type.render or {}
    meta_list = render.get("meta_list", {})
    table_row_map = render.get("table_row_map", {}).get("schema", {}).get("properties", {})

    item_keys_info = {}

    # meta_list を走査
    for key, meta in meta_list.items():
        input_type = meta.get("input_type")
        if not input_type or input_type not in check_prop_ids:
            continue

        prop_type = check_prop_ids[input_type]
        option = meta.get("option", {})
        multiple = option.get("multiple", False)

        # radiobutton (cus_1046) の場合
        if input_type == "cus_1046":
            if not multiple:
                radio_schema = table_row_map.get(key, {}).get("properties", {})
                if radio_schema.get("subitem_radio_item", {}).get("format") != "checkboxes" \
                        or "subitem_textarea_value" in radio_schema:
                    item_keys_info[key] = prop_type
            else:
                radio_schema = table_row_map.get(key, {}).get("items", {}).get("properties", {})
                if radio_schema.get("subitem_radio_item", {}).get("format") != "checkboxes" \
                        or "subitem_textarea_value" in radio_schema:
                    item_keys_info[key] = prop_type

        # listbox (cus_1047) の場合
        elif input_type == "cus_1047":
            if not multiple:
                select_schema = table_row_map.get(key, {}).get("properties", {})
                if select_schema.get("subitem_select_item", {}).get("format") != "checkboxes" \
                        or "subitem_textarea_value" in select_schema:
                    item_keys_info[key] = prop_type
            else:
                select_schema = table_row_map.get(key, {}).get("items", {}).get("properties", {})
                if select_schema.get("subitem_select_item", {}).get("format") != "checkboxes" \
                        or "subitem_textarea_value" in select_schema:
                    item_keys_info[key] = prop_type

        # その他の input_type は無条件で格納
        else:
            item_keys_info[key] = prop_type

    # 結果を格納（変更されたプロパティがなければ空 dict）
    check_item_keys[item_type_id] = item_keys_info

def change_metadata(prop_type: str, key: str, item, rec=None):
    change_flag = False

    if prop_type == "resource_type":
        change_flag = change_resource_type_metadata(key, item, rec)
    elif prop_type == "identifier_registration":
        change_flag = change_identifier_registration_metadata(key, item, rec)
    elif prop_type == "radiobutton":
        change_flag = change_radiobutton_metadata(key, item, rec)
    elif prop_type == "listbox":
        change_flag = change_listbox_metadata(key, item, rec)
    elif prop_type == "dcndl_original_language":
        change_flag = change_dcndl_original_language_metadata(key, item, rec)
    elif prop_type == "jpcoar_format":
        change_flag = change_jpcoar_format_metadata(key, item, rec)
    elif prop_type == "jpcoar_holding_agent":
        change_flag = change_jpcoar_holding_agent_metadata(key, item, rec)
    elif prop_type == "jpcoar_catalog":
        change_flag = change_jpcoar_catalog_metadata(key, item, rec)

    return change_flag

def main():
    # 引数を取得
    startDate, endDate, recordId, itemTypeId = parse_args()

    # チェック用辞書を初期化
    check_item_keys = {}
    check_prop_ids = {
        "cus_1014": "resource_type",
        "cus_1018": "identifier_registration",
        # "cus_1046": "radiobutton",  # 要確認
        # "cus_1047": "listbox",      # 要確認
        # "cus_1052": "dcndl_original_language",  # 要確認
        "cus_1054": "jpcoar_format",
        "cus_1055": "jpcoar_holding_agent",
        "cus_1056": "jpcoar_dataset_series",
        "cus_1057": "jpcoar_catalog",
    }

    try:
        # 全件の UUIDリスト取得
        uuids = []
        query = db.session.query(ItemMetadata.id, ItemMetadata.item_type_id)
        if recordId:
            query = query.filter(ItemMetadata.id == recordId)
        if startDate:
            query = query.filter(ItemMetadata.updated >= startDate)
        if endDate:
            query = query.filter(ItemMetadata.updated < endDate)
        if itemTypeId:
            query = query.filter(ItemMetadata.item_type_id == itemTypeId)
        uuids = [(str(x.id), str(x.item_type_id)) for x in query.all()]

        # 各UUID処理
        for uuid, item_type_id in uuids:
            change_flag = False
            try:
                # item_type_id の情報をキャッシュ
                if item_type_id not in check_item_keys:
                    get_item_type_info(check_item_keys, item_type_id, check_prop_ids)

                # プロパティが存在する場合のみ処理
                if check_item_keys[item_type_id]:
                    # metadata取得
                    item = ItemMetadata.query.filter_by(id=uuid).one_or_none()
                    rec = RecordMetadata.query.filter_by(id=uuid).one_or_none()

                    for key, prop_type in check_item_keys[item_type_id].items():
                        if key in item.json:
                            if change_metadata(prop_type, key, item.json, rec.json):
                                change_flag = True

                    if change_flag:
                        # # ES更新処理
                        # indexer = WekoIndexer()
                        # indexer.get_es_index()
                        # indexer.upload_metadata(rec.json, uuid, rec.version_id)
                        # DB保存
                        flag_modified(item, "json")
                        flag_modified(rec, "json")
                        db.session.commit()

            except (OperationalError, SQLAlchemyError, ConnectionError) as e:
                sys.stderr.write(f"Error updating Item UUID={uuid}: {e}")
                db.session.rollback()
            except Exception as e:
                sys.stderr.write(f"Unexpected error UUID={uuid}: {e}")
                db.session.rollback()

        # Activityの処理
        if not recordId:
            query = db.session.query(Activity.activity_id, Activity.temp_data, WorkFlow.itemtype_id)
            query = query.join(WorkFlow, Activity.workflow_id == WorkFlow.id)
            query = query.join(Action, Activity.action_id == Action.id)
            if startDate:
                query = query.filter(Activity.updated >= startDate)
            if endDate:
                query = query.filter(Activity.updated < endDate)
            if itemTypeId:
                query = query.filter(WorkFlow.itemtype_id == itemTypeId)
            query = query.filter(Action.action_name == "Item Registration")
            query = query.filter(Activity.activity_status == ActivityStatusPolicy.ACTIVITY_MAKING)
            query = query.filter(Activity.temp_data.isnot(None))

            activities = query.all()

            for data in activities:
                change_flag = False
                try:
                    item_type_id = str(data.itemtype_id)

                    if item_type_id not in check_item_keys:
                        get_item_type_info(check_item_keys, item_type_id, check_prop_ids)

                    temp_data = json.loads(data.temp_data)
                    for key, prop_type in check_item_keys[item_type_id].items():
                        if key in temp_data and temp_data[key]:
                            if change_metadata(prop_type, key, temp_data):
                                change_flag = True

                    if change_flag:
                        activity = Activity.query.filter_by(activity_id=data.activity_id).one_or_none()
                        activity.temp_data = json.dumps(temp_data)
                        flag_modified(activity, "temp_data")
                        db.session.commit()
                except (OperationalError, SQLAlchemyError) as e:
                    sys.stderr.write(f"Error updating Activity ID={data.activity_id}: {e}")
                    db.session.rollback()
                except Exception as e:
                    sys.stderr.write(f"Unexpected error Activity ID={data.activity_id}: {e}")
                    db.session.rollback()

    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}")
        raise


def change_resource_type_metadata(key, item, rec=None):
    """
    資源タイプのメタデータを
    値: jpcoar 1.0 値 → jpcoar 2.0 値
    """
    change_flag = False
    mapping = {
        "periodical": ("journal", "http://purl.org/coar/resource_type/c_0640"),
        "conference object": ("conference output", "http://purl.org/coar/resource_type/c_c94f"),
        "interview": ("other", "http://purl.org/coar/resource_type/c_1843"),
        "internal report": ("other", "http://purl.org/coar/resource_type/c_1843"),
        "report part": ("other", "http://purl.org/coar/resource_type/c_1843"),
    }

    if (
        key in item and
        "resourcetype" in item[key] and
        "resourceuri" in item[key]
    ):
        if item[key]["resourcetype"] in mapping:
            # 新しい資源タイプを取得する
            new_type, new_uri = mapping[item[key]["resourcetype"]]

            item[key]["resourcetype"]  = new_type
            item[key]["resourceuri"] = new_uri
            if (
                rec and
                key in rec and
                "attribute_value_mlt" in rec[key] and
                rec[key]["attribute_value_mlt"]
            ):
                rec[key]["attribute_value_mlt"][0]["resourcetype"]  = new_type
                rec[key]["attribute_value_mlt"][0]["resourceuri"] = new_uri
            change_flag = True

    return change_flag


def change_identifier_registration_metadata(key, item, rec=None):
    """
    ID登録のメタデータを
    値: PMID【現在不使用】 → PMID
    """
    change_flag = False
    if (
        key in item and
        "subitem_identifier_reg_type" in item[key] and
        item[key]["subitem_identifier_reg_type"] == "PMID【現在不使用】"
    ):
        item[key]["subitem_identifier_reg_type"] = "PMID"
        if (
            rec and
            key in rec and
            "attribute_value_mlt" in rec[key] and
            rec[key]["attribute_value_mlt"]
        ):
            rec[key]["attribute_value_mlt"][0]["subitem_identifier_reg_type"] = "PMID"
        change_flag = True

    return change_flag


def change_radiobutton_metadata(key, item, rec=None):
    """
    ラジオボタンのメタデータを
    1. サブアイテムキー:
       subitem_textarea_value → subitem_radio_item
       subitem_textarea_language → subitem_radio_language
    2. 値: list 資料 → string
    """
    change_flag = False

    def update_entry(entry):
        nonlocal change_flag
        if "subitem_textarea_value" in entry:
            entry["subitem_radio_item"] = entry.pop("subitem_textarea_value")
            if "subitem_textarea_language" in entry:
                entry["subitem_radio_language"] = entry.pop("subitem_textarea_language")
            change_flag = True
        if isinstance(entry.get("subitem_radio_item"), list):
            entry["subitem_radio_item"] = entry["subitem_radio_item"][0]
            change_flag = True

    if key in item:
        if isinstance(item[key], dict):
            update_entry(item[key])
        elif isinstance(item[key], list):
            for e in item[key]:
                update_entry(e)

        if rec and key in rec and "attribute_value_mlt" in rec[key]:
            for e in rec[key]["attribute_value_mlt"]:
                update_entry(e)

    return change_flag


def change_listbox_metadata(key, item, rec=None):
    """
    リストボックスのメタデータを
    1. サブアイテムキー:
       subitem_textarea_value → subitem_select_item
       subitem_textarea_language → subitem_select_language
    2. 値: list 資料 → string
    """
    change_flag = False

    def update_entry(entry):
        nonlocal change_flag
        if "subitem_textarea_value" in entry:
            entry["subitem_select_item"] = entry.pop("subitem_textarea_value")
            if "subitem_textarea_language" in entry:
                entry["subitem_select_language"] = entry.pop("subitem_textarea_language")
            change_flag = True
        if isinstance(entry.get("subitem_select_item"), list):
            entry["subitem_select_item"] = entry["subitem_select_item"][0]
            change_flag = True

    if key in item:
        if isinstance(item[key], dict):
            update_entry(item[key])
        elif isinstance(item[key], list):
            for e in item[key]:
                update_entry(e)

        if rec and key in rec and "attribute_value_mlt" in rec[key]:
            for e in rec[key]["attribute_value_mlt"]:
                update_entry(e)

    return change_flag


def change_dcndl_original_language_metadata(key, item, rec=None):
    """
    原文の言語のメタデータを
    値: ISO-639-3 コードに変換
    """
    change_flag = False
    lang_map = { "aa": "aar", "ab": "abk", "af": "afr", "ak": "aka", "am": "amh", "ar": "ara", "an": "arg", "as": "asm", "av": "ava", "ae": "ave", "ay": "aym", "az": "aze", "ba": "bak", "bm": "bam", "be": "bel", "bn": "ben", "bi": "bis", "bo": "bod", "bs": "bos", "br": "bre", "bg": "bul", "ca": "cat", "cs": "ces", "ch": "cha", "ce": "che", "cu": "chu", "cv": "chv", "kw": "cor", "co": "cos", "cr": "cre", "cy": "cym", "da": "dan", "de": "deu", "dv": "div", "dz": "dzo", "el": "ell", "en": "eng", "eo": "epo", "et": "est", "eu": "eus", "ee": "ewe", "fo": "fao", "fa": "fas", "fj": "fij", "fi": "fin", "fr": "fra", "fy": "fry", "ff": "ful", "gd": "gla", "ga": "gle", "gl": "glg", "gv": "glv", "gn": "grn", "gu": "guj", "ht": "hat", "ha": "hau", "he": "heb", "hz": "her", "hi": "hin", "ho": "hmo", "hr": "hrv", "hu": "hun", "hy": "hye", "ig": "ibo", "io": "ido", "ii": "iii", "iu": "iku", "ie": "ile", "ia": "ina", "id": "ind", "ik": "ipk", "is": "isl", "it": "ita", "jv": "jav", "ja": "jpn", "kl": "kal", "kn": "kan", "ks": "kas", "ka": "kat", "kr": "kau", "kk": "kaz", "km": "khm", "ki": "kik", "rw": "kin", "ky": "kir", "kv": "kom", "kg": "kon", "ko": "kor", "kj": "kua", "ku": "kur", "lo": "lao", "la": "lat", "lv": "lav", "li": "lim", "ln": "lin", "lt": "lit", "lb": "ltz", "lu": "lub", "lg": "lug", "mh": "mah", "ml": "mal", "mr": "mar", "mk": "mkd", "mg": "mlg", "mt": "mlt", "mn": "mon", "mi": "mri", "ms": "msa", "my": "mya", "na": "nau", "nv": "nav", "nr": "nbl", "nd": "nde", "ng": "ndo", "ne": "nep", "nl": "nld", "nn": "nno", "nb": "nob", "no": "nor", "ny": "nya", "oc": "oci", "oj": "oji", "or": "ori", "om": "orm", "os": "oss", "pa": "pan", "pi": "pli", "pl": "pol", "pt": "por", "ps": "pus", "qu": "que", "rm": "roh", "ro": "ron", "rn": "run", "ru": "rus", "sg": "sag", "sa": "san", "si": "sin", "sk": "slk", "sl": "slv", "se": "sme", "sm": "smo", "sn": "sna", "sd": "snd", "so": "som", "st": "sot", "es": "spa", "sq": "sqi", "sc": "srd", "sr": "srp", "ss": "ssw", "su": "sun", "sw": "swa", "sv": "swe", "ty": "tah", "ta": "tam", "tt": "tat", "te": "tel", "tg": "tgk", "tl": "tgl", "th": "tha", "ti": "tir", "to": "ton", "tn": "tsn", "ts": "tso", "tk": "tuk", "tr": "tur", "tw": "twi", "ug": "uig", "uk": "ukr", "ur": "urd", "uz": "uzb", "ve": "ven", "vi": "vie", "vo": "vol", "wa": "wln", "wo": "wol", "xh": "xho", "yi": "yid", "yo": "yor", "za": "zha", "zh": "zho", "zu": "zul", "日本語": "jpn", "JPN": "jpn", "ＪＰＮ": "jpn", "ja": "jpn", "英語": "eng", "ENG": "eng", "ＥＮＧ": "eng", "en": "eng"}


    def update_entry(entry):
        nonlocal change_flag
        lang = ""
        if (
            "original_language" in entry and
            entry["original_language"] not in lang_map.values()
        ):
            if entry["original_language"] in lang_map.keys():
                lang = lang_map.get(entry["original_language"], "")
            elif "original_language_language" in entry:
                lang = lang_map.get(entry["original_language_language"], "")
            if lang:
                entry["original_language"] = lang
                change_flag = True
        if "original_language_language" in entry:
            if not lang:
                lang = lang_map.get(entry["original_language_language"], "")
                entry["original_language"] = lang
            del entry["original_language_language"]
            change_flag = True

    if key in item:
        if isinstance(item[key], dict):
            update_entry(item[key])
            if (
                rec and
                key in rec and
                "attribute_value_mlt" in rec[key]
            ):
                for e in rec[key]["attribute_value_mlt"]:
                    update_entry(e)
        elif isinstance(item[key], list):
            for idx, e in enumerate(item[key]):
                update_entry(e)
                if (
                    rec and
                    key in rec and
                    "attribute_value_mlt" in rec[key]
                ):
                    update_entry(rec[key]["attribute_value_mlt"][idx])

    return change_flag


def change_jpcoar_format_metadata(key, item, rec=None):
    """
    物理的形態のメタデータを
    サブアイテムキー: json_format_language → jpcoar_format_language
    """
    change_flag = False

    def update_entry(entry):
        nonlocal change_flag
        if "json_format_language" in entry:
            entry["jpcoar_format_language"] = entry.pop("json_format_language")
            change_flag = True

    if key in item:
        if isinstance(item[key], dict):
            update_entry(item[key])
        elif isinstance(item[key], list):
            for e in item[key]:
                update_entry(e)

        if rec and key in rec and "attribute_value_mlt" in rec[key]:
            for e in rec[key]["attribute_value_mlt"]:
                update_entry(e)

    return change_flag


def change_jpcoar_holding_agent_metadata(key, item, rec=None):
    """
    所蔵機関のメタデータを
    1. サブアイテムキー: holding_agent_name_idenfitier_value → holding_agent_name_identifier_value
    2. サブアイテムキー: holding_agent_names_language → holding_agent_name_language
    """
    change_flag = False

    if key in item:
        if "holding_agent_name_identifier" in item[key]:
            haid = item[key]["holding_agent_name_identifier"]
            if "holding_agent_name_idenfitier_value" in haid:
                haid["holding_agent_name_identifier_value"] = haid.pop("holding_agent_name_idenfitier_value")
                if rec and key in rec and "attribute_value_mlt" in rec[key] and rec[key]["attribute_value_mlt"]:
                    r_haid = rec[key]["attribute_value_mlt"][0]["holding_agent_name_identifier"]
                    if "holding_agent_name_idenfitier_value" in r_haid:
                        r_haid["holding_agent_name_identifier_value"] = r_haid.pop("holding_agent_name_idenfitier_value")
                change_flag = True

        if "holding_agent_names" in item[key]:
            for idx, e in enumerate(item[key]["holding_agent_names"]):
                if "holding_agent_names_language" in e:
                    e["holding_agent_name_language"] = e.pop("holding_agent_names_language")
                    if rec and key in rec and "attribute_value_mlt" in rec[key] and rec[key]["attribute_value_mlt"]:
                        r_entry = rec[key]["attribute_value_mlt"][0]["holding_agent_names"][idx]
                        if "holding_agent_names_language" in r_entry:
                            r_entry["holding_agent_name_language"] = r_entry.pop("holding_agent_names_language")
                    change_flag = True

    return change_flag


def change_jpcoar_catalog_metadata(key, item, rec=None) -> bool:
    """
    カタログのメタデータを
    1. 値: e-Rad → e-Rad_field
    2. 構造: catalog_licenses, catalog_file
    3. サブアイテムキー: catalog_access_right_access_rights → catalog_access_right
    """
    change_flag = False

    if key in item:
        # catalog_subjects
        if "catalog_subjects" in item[key]:
            for subj in item[key]["catalog_subjects"]:
                if subj.get("catalog_subject_scheme") == "e-Rad":
                    subj["catalog_subject_scheme"] = "e-Rad_field"
                    change_flag = True

            if (
                rec and
                key in rec and
                "attribute_value_mlt" in rec[key] and
                rec[key]["attribute_value_mlt"]
            ):
                for subj in rec[key]["attribute_value_mlt"][0]["catalog_subjects"]:
                    if subj.get("catalog_subject_scheme") == "e-Rad":
                        subj["catalog_subject_scheme"] = "e-Rad_field"
                        change_flag = True

        # catalog_licenses
        if "catalog_license" in item[key] and item[key]["catalog_license"]:
            if "catalog_licenses" in item[key]:
                # merge licenses
                for license in item[key]["catalog_licenses"]:
                    if (
                        "catalog_license_language" not in license and
                        "catalog_license_type" not in license
                    ):
                        license.update(item[key]["catalog_license"])
            else:
                # create new licenses list
                item[key]["catalog_licenses"] = [item[key]["catalog_license"]]
            del item[key]["catalog_license"]

            if (
                rec and
                key in rec and
                "attribute_value_mlt" in rec[key] and
                rec[key]["attribute_value_mlt"]
            ):
                rec0 = rec[key]["attribute_value_mlt"][0]
                if "catalog_license" in rec0 and rec0["catalog_license"]:
                    if "catalog_licenses" in rec0:
                        # merge licenses
                        for license in rec0["catalog_licenses"]:
                            if (
                                "catalog_license_language" not in license and
                                "catalog_license_type" not in license
                            ):
                                license.update(rec0["catalog_license"])
                    else:
                        rec0["catalog_licenses"] = [rec0["catalog_license"]]
                    del rec0["catalog_license"]
            change_flag = True

        # catalog_access_rights
        if "catalog_access_rights" in item[key]:
            for rights in item[key]["catalog_access_rights"]:
                if "catalog_access_right_access_rights" in rights:
                    rights["catalog_access_right"] = rights.pop("catalog_access_right_access_rights")
                    change_flag = True

            if (
                rec and
                key in rec and
                "attribute_value_mlt" in rec[key] and
                rec[key]["attribute_value_mlt"]
            ):
                for rights in rec[key]["attribute_value_mlt"][0]["catalog_access_rights"]:
                    if "catalog_access_right_access_rights" in rights:
                        rights["catalog_access_right"] = rights.pop("catalog_access_right_access_rights")
                        change_flag = True

        # catalog_file
        def update_catalog_file_entry(entry):
            nonlocal change_flag
            if "catalog_file_uri" in entry and isinstance(entry["catalog_file_uri"], str):
                entry["catalog_file_uri"] = {
                        "catalog_file_uri_value": entry["catalog_file_uri"]
                    }
                change_flag = True
            if "catalog_file_object_type" in entry:
                if "catalog_file_uri" not in entry:
                    entry["catalog_file_uri"] = {}
                entry["catalog_file_uri"]["catalog_file_object_type"] = entry.pop("catalog_file_object_type")
                change_flag = True

        if "catalog_file" in item[key]:
            cfile = item[key]["catalog_file"]
            update_catalog_file_entry(cfile)

            if (
                rec and
                key in rec and
                "attribute_value_mlt" in rec[key] and
                rec[key]["attribute_value_mlt"]
            ):
                rfile = rec[key]["attribute_value_mlt"][0]["catalog_file"]
                update_catalog_file_entry(rfile)

    return change_flag


if __name__ == '__main__':
    main()