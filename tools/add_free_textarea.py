"""Add a free textarea to itemtype property and itemtypes"""

import copy, traceback, os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

# ファイル情報プロパティのID
FILE_PROP_ID = "1035"

# アイテムタイプ設定画面で表示される項目名
TITLE = "コメント"

# ワークフロー画面で表示される自由記述欄の項目名(日本語)
TITLE_JA = "自由記述"

# ワークフロー画面で表示される自由記述欄の項目名(英語)
TITLE_EN = "free text area"

# DB内で使用するテキストエリアサブプロパティのID
SUBPROP_NAME = "free_text_area"

# DBに接続するためのユーザー名
USERNAME = os.getenv('INVENIO_POSTGRESQL_DBUSER')

# DBに接続するためのパスワード
PASSWORD = os.getenv('INVENIO_POSTGRESQL_DBPASS')

# DBのホスト名
HOST = os.getenv('INVENIO_POSTGRESQL_HOST')

# DBのポート番号
PORT = 5432

# DB名
DBNAME = os.getenv('INVENIO_POSTGRESQL_DBNAME')

COMMENT_DICT_A = {
    "type": "string",
    "title": "",
    "format": "textarea"
}
COMMENT_DICT_B_TEMPLATE = {
    "key": "",
    "type": "textarea",
    "title": "",
    "title_i18n": {
        "en": "",
        "ja": ""
    }
}

# テーブル名
TABLE_NAME_DICT = {'ITEM_TYPE':'item_type', 'ITEM_TYPE_PROPERTY': 'item_type_property'}


def update_schema(prop):
    """ propに自由記述用のdictを追加または更新する

    Args:
        prop(dict): 更新対象の辞書
    """
    if prop and isinstance(prop, dict):
        prop[SUBPROP_NAME] = COMMENT_DICT_A


def update_items(items, comment_dict):
    """ items内の辞書に自由記述用のdictを追加または更新する

    Args:
        items(list): 更新対象の辞書のリスト
        comment_dict(dict): 更新用の辞書
    """
    exist_index_list = [i for i, item in enumerate(items) if item.get("key") == comment_dict["key"]]
    if exist_index_list:
        for exist_index in exist_index_list:
            items[exist_index] = comment_dict
    else:
        items.append(comment_dict)


def update_render(record, file_prop_name, comment_dict):
    """アイテムタイプのrender列に自由記述用のdictを追加または更新する

    Args:
        record: アイテムタイプのレコード
        file_prop_name(str): ファイルプロパティを設定している部分のキー
        comment_dict(dict): 更新用の辞書
    """
    update_schema(record.render.get("schemaeditor", {}).get("schema", {}).get(file_prop_name, {}).get("properties", {}))
    update_schema(record.render.get("table_row_map", {}).get("schema", {}).get("properties", {}).get(file_prop_name, {}).get("items", {}))
    for data in record.render.get("table_row_map", {}).get("form", {}):
        if data.get("key") == file_prop_name:
            update_items(data.get("items"), comment_dict)


def add_textarea(title=TITLE, title_ja=TITLE_JA, title_en=TITLE_EN, username=USERNAME, password=PASSWORD,
        host=HOST, port=PORT, dbname=DBNAME, file_prop_id=FILE_PROP_ID, subprop_name=SUBPROP_NAME):
    """
    file_prop_idで指定したプロパティとプロパティを使用しているアイテムタイプにテキストエリアを追加する

    Args:
        title (str): The title of the textarea.
        title_ja (str): The Japanese title of the textarea.
        title_en (str): The English title of the textarea.
        username (str): The username for the database connection.
        password (str): The password for the database connection.
        host (str): The host of the database.
        port (int): The port of the database.
        dbname (str): The name of the database.
        file_prop_id (str): The file property ID.
        subprop_name (str): The subproperty name.

    Returns:
        None
    """

    COMMENT_DICT_A["title"] = title
    COMMENT_DICT_B_TEMPLATE["title"] = title
    COMMENT_DICT_B_TEMPLATE["title_i18n"]["ja"] = title_ja
    COMMENT_DICT_B_TEMPLATE["title_i18n"]["en"] = title_en

    # セッション作成
    engine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}')
    Session = sessionmaker(bind=engine)
    session = Session()
    Base = declarative_base()

    class ItemType(Base):
        __tablename__ = TABLE_NAME_DICT.get('ITEM_TYPE')
        id = Column(Integer, primary_key=True)
        schema = Column(JSON)
        form = Column(JSON)
        render = Column(JSON)
        updated = Column(DateTime)

    class ItemTypeProperty(Base):
        __tablename__ = TABLE_NAME_DICT.get('ITEM_TYPE_PROPERTY')
        id = Column(Integer, primary_key=True)
        schema = Column(JSON)
        form = Column(JSON)
        forms = Column(JSON)
        updated = Column(DateTime)
        name = Column(Text)

    updated_itemtype_ids = []
    updated_itemtype_property_id = None

    try:
        if not subprop_name:
            raise Exception("subproperty name must not be empty")

        # update file property
        record = session.query(ItemTypeProperty).filter(ItemTypeProperty.id == file_prop_id).first()

        if record:
            # update schema
            update_schema(record.schema["properties"])
            flag_modified(record, "schema")

            # update form
            comment_dict = copy.deepcopy(COMMENT_DICT_B_TEMPLATE)
            comment_dict["key"] = "parentkey." + subprop_name
            update_items(record.form["items"], comment_dict)
            flag_modified(record, "form")

            # update forms
            comment_dict = copy.deepcopy(COMMENT_DICT_B_TEMPLATE)
            comment_dict["key"] = "parentkey[]." + subprop_name
            update_items(record.forms["items"], comment_dict)
            flag_modified(record, "forms")

            record.updated = datetime.now(timezone.utc)
            updated_itemtype_property_id = record.id
        else:
            raise Exception(f"property with id = {file_prop_id} does not exist")

        # update itemtypes
        records = session.query(ItemType).all()
        for record in records:

            # get file property name
            file_prop_name = None
            for metadata_name, value in record.render.get("meta_list").items():
                if value.get("input_type") == "cus_" + file_prop_id:
                    file_prop_name = metadata_name

            if file_prop_name:
                comment_dict = copy.deepcopy(COMMENT_DICT_B_TEMPLATE)
                comment_dict["key"] = file_prop_name + "[]." + subprop_name

                update_schema(record.schema.get("properties", {}).get(file_prop_name, {}).get("items", {}).get("properties", {}))
                flag_modified(record, "schema")

                for data in record.form:
                    if data.get("key") == file_prop_name:
                        update_items(data.get("items"), comment_dict)
                flag_modified(record, "form")

                update_render(record, file_prop_name, comment_dict)
                flag_modified(record, "render")

                record.updated = datetime.now(timezone.utc)
                updated_itemtype_ids.append(record.id)


    except Exception:
        traceback.print_exc()
        session.rollback()
    else:
        session.commit()
        print("success")
        print("updated_itemtype_property_id:", updated_itemtype_property_id)
        print("updated_itemtype_ids:", updated_itemtype_ids)


add_textarea()