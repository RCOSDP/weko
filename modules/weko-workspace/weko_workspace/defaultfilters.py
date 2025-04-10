from flask import current_app

def merge_default_filters(default_con):
    """
    Merge the default_con from the workspace_default_conditions table with DEFAULT_FILTERS.

    Args:
        default_con (dict): JSON data of default_con retrieved from the database.

    Returns:
        dict: Merged JSON template in the same format as DEFAULT_FILTERS.
    """

    # DEFAULT_FILTERS を深コピーし、元のテンプレートを変更しない
    merged_filters = {key: dict(value) for key, value in current_app.config["WEKO_WORKSPACE_DEFAULT_FILTERS"].items()}

    # default_con が空の場合、デフォルトテンプレートを返す
    if not default_con:
        return merged_filters

    # 単一選択フィールドのマッピングを定義
    single_select_mapping = {
        True: "Yes",
        False: "No",
        None: None,  # 未選択時はテンプレートのデフォルト値を保持
    }

    # default_con のキーと値を走査し、merged_filters を更新
    for key, value in default_con.items():
        if key in merged_filters:
            if key in ["peer_review","related_to_paper","related_to_data","file_present","favorite",]:
                # 単一選択フィールド：ブール値をあり/なしに変換
                merged_filters[key]["default"] = single_select_mapping.get(value, None)
            elif key == "resource_type":
                # 複数選択フィールド：options 内で有効な値のみを保持
                if value is None:
                    merged_filters[key]["default"] = []  # Noneの場合は空リスト
                else:
                    merged_filters[key]["default"] = [
                        item for item in value if item in merged_filters[key]["options"]
                    ]

    # funder_name と award_title は default_con に存在しないため、デフォルト値を保持
    return merged_filters
