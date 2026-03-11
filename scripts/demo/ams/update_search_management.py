import traceback, os
from sqlalchemy import create_engine, Column, Integer, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified


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
# テーブル名
TABLE_NAME_DICT = {'SEARCH_MANAGEMENT':'search_management'}
# 検索設定を追加するアイテムタイプのID
ITEM_TYPE_ID = 51000


def update(username=USERNAME, password=PASSWORD, host=HOST, port=PORT, dbname=DBNAME, item_type_id = ITEM_TYPE_ID):
    """
    search_managementテーブルに未病DB用の検索設定を追加する

    Args:
        username (str): The username for the database connection.
        password (str): The password for the database connection.
        host (str): The host of the database.
        port (int): The port of the database.
        dbname (str): The name of the database.
        item_type_id (int): The id of AMS itemtype.

    Returns:
        None
    """

    engine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}')
    Session = sessionmaker(bind=engine)
    session = Session()
    Base = declarative_base()

    class SearchManagement(Base):
        __tablename__ = TABLE_NAME_DICT.get('SEARCH_MANAGEMENT')
        id = Column(Integer, primary_key=True)
        default_dis_num = Column(Integer)
        default_dis_sort_index = Column(Text)
        default_dis_sort_keyword =Column(JSON)
        sort_setting = Column(JSON)
        search_conditions = Column(JSON)
        search_setting_all = Column(JSON)
        display_control = Column(JSON)
        init_disp_setting = Column(JSON)
        create_date = Column(DateTime)
    try:
        record = session.query(SearchManagement).first()

        text_list = {
            "text1": "$.item_1739173568107.attribute_value_mlt[*].subitem_subject",
            "text2": "$.item_1739174747677.attribute_value_mlt[*].subitem_select_item",
            "text3": "$.item_1739174293548.attribute_value_mlt[*].subitem_select_item",
            "text4": "$.item_1736146927028.attribute_value_mlt[*].creatorNames[*].creatorName",
            "text5": "$.item_1739173036322.attribute_value_mlt[*].subitem_funder_names[*].subitem_funder_name",
            "text6": "$.item_1739175658606.attribute_value_mlt[*].subitem_select_item",
            "text7": "$.item_1736146823660.attribute_value_mlt[*].subitem_access_right",
            "text8": "$.item_1739175379485.attribute_value_mlt[*].subitem_select_item"
        }

        date_list = {
            "date_range1": "$.item_1736145554459.attribute_value_mlt[*].subitem_date_issued_datetime",
            "date_range2": "$.item_1736145631851.attribute_value_mlt[*].subitem_date_issued_datetime"
        }

        for item in record.search_conditions:
            if item["id"] in text_list:
                item["item_value"][item_type_id] = {
                    "path": text_list[item["id"]],
                    "path_type": "json",
                    "condition_path": "",
                    "condition_value": ""
                }
            if item["id"] in date_list:
                item["item_value"][item_type_id] = {}
                item["item_value"][item_type_id] = {
                    "path": {
                        "gte": date_list[item["id"]],
                        "lte": date_list[item["id"]],
                    },
                    "path_type": {
                        "gte": "json",
                        "lte": "json"
                    }
                }

        for item in record.search_setting_all["detail_condition"]:
            if item["id"] in text_list:
                item["item_value"][item_type_id] = {
                    "path": text_list[item["id"]],
                    "path_type": "json",
                    "condition_path": "",
                    "condition_value": ""
                }
            if item["id"] in date_list:
                item["item_value"][item_type_id] = {
                    "path": {
                        "gte": date_list[item["id"]],
                        "lte": date_list[item["id"]],
                    },
                    "path_type": {
                        "gte": "json",
                        "lte": "json"
                    }
                }

        flag_modified(record, "search_conditions")
        flag_modified(record, "search_setting_all")

    except Exception:
        traceback.print_exc()
        session.rollback()
        session.commit()

    else:
        session.commit()
        print("success")

update()
