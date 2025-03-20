
# すべてのフィルタ条件のJSONテンプレートを定義
DEFAULT_FILTERS = {
    "resource_type": {
        "label": "リソースタイプ",
        "options": [
            "conference paper",
            "data paper",
            "departmental bulletin paper",
            "editorial",
            "journal",
            "journal article",
            "newspaper",
            "review article",
            "other periodical",
            "software paper",
            "article",
            "book",
            "book part",
            "cartographic material",
            "map",
            "conference output",
            "conference presentation",
            "conference proceedings",
            "conference poster",
            "aggregated data",
            "clinical trial data",
            "compiled data",
            "dataset",
            "encoded data",
            "experimental data",
            "genomic data",
            "geospatial data",
            "laboratory notebook",
            "measurement and test data",
            "observational data",
            "recorded data",
            "simulation data",
            "survey data",
            "image",
            "still image",
            "moving image",
            "video",
            "lecture",
            "design patent",
            "patent",
            "PCT application",
            "plant patent",
            "plant variety protection",
            "software patent",
            "trademark",
            "utility model",
            "report",
            "research report",
            "technical report",
            "policy report",
            "working paper",
            "data management plan",
            "sound",
            "thesis",
            "bachelor thesis",
            "master thesis",
            "doctoral thesis",
            "commentary",
            "design",
            "industrial design",
            "interactive resource",
            "layout design",
            "learning object",
            "manuscript",
            "musical notation",
            "peer review",
            "research proposal",
            "research protocol",
            "software",
            "source code",
            "technical documentation",
            "transcription",
            "workflow",
            "other",
        ],
        "default": [],  # 複数選択フィールド、文字列配列を保持
    },
    "peer_review": {
        "label": "査読",
        "options": ["あり", "なし"],
        "default": [],  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_paper": {
        "label": "論文への関連",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_data": {
        "label": "根拠データへの関連",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "funder_name": {
        "label": "資金別情報 - 助成機関名",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "award_title": {
        "label": "資金別情報 - 研究課題名",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "file_present": {
        "label": "本文ファイル",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "favorite": {
        "label": "お気に入り",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
}


def get_default_filters():
    """Return the default filter condition template"""
    return DEFAULT_FILTERS


def merge_default_filters(default_con):
    """
    Merge the default_con from the workspace_default_conditions table with DEFAULT_FILTERS.

    Args:
        default_con (dict): JSON data of default_con retrieved from the database.

    Returns:
        dict: Merged JSON template in the same format as DEFAULT_FILTERS.
    """

    # DEFAULT_FILTERS を深コピーし、元のテンプレートを変更しない
    merged_filters = {key: dict(value) for key, value in DEFAULT_FILTERS.items()}

    # default_con が空の場合、デフォルトテンプレートを返す
    if not default_con:
        return merged_filters

    # 単一選択フィールドのマッピングを定義
    single_select_mapping = {
        True: "あり",
        False: "なし",
        None: None,  # 未選択時はテンプレートのデフォルト値を保持
    }

    # default_con のキーと値を走査し、merged_filters を更新
    for key, value in default_con.items():
        if key in merged_filters:
            if key in [
                "peer_review",
                "related_to_paper",
                "related_to_data",
                "file_present",
                "favorite",
            ]:
                # 単一選択フィールド：ブール値をあり/なしに変換
                merged_filters[key]["default"] = single_select_mapping.get(value, None)
            elif key == "resource_type":
                # 複数選択フィールド：options 内で有効な値のみを保持
                merged_filters[key]["default"] = [
                    item for item in value if item in merged_filters[key]["options"]
                ]

    # funder_name と award_title は default_con に存在しないため、デフォルト値を保持
    return merged_filters
