# coding:utf-8
"""Default item type."""
from properties import AddProperty
from . import item_type_config as config

item_type_id = config.DEFAULT_DDI
item_type_name = "DDI"
property_list = [
    AddProperty(
        AddProperty.title,
        'タイトル',
        'タイトル',
        'Title',
        required=True,
        multiple=True
    ),
    AddProperty(
        AddProperty.alternative_title,
        'その他のタイトル',
        'その他のタイトル',
        'Alternative Title',
        multiple=True
    ),
    AddProperty(
        AddProperty.study_id,
        '調査番号',
        '調査番号',
        'Study ID',
        multiple=True
    ),
    AddProperty(
        AddProperty.identifier_registration,
        '識別子登録',
        '識別子登録',
        'Identifier Registration'
    ),
    AddProperty(
        AddProperty.creator,
        '調査主体 / 調査代表者',
        '調査主体 / 調査代表者',
        'Author',
        multiple=True
    ),
    AddProperty(
        AddProperty.publisher,
        '出版者',
        '出版者',
        'Publisher',
        multiple=True
    ),
    AddProperty(
        AddProperty.rights,
        'ライセンス',
        'ライセンス',
        'Copyright',
        multiple=True
    ),
    #AddProperty(
    #    AddProperty.fund_agency,
    #    '研究費拠出機関名',
    #    '研究費拠出機関名',
    #    'Fund Agency'
    #),
    AddProperty(
        AddProperty.distributor,
        '配布者、配布機関',
        '配布者、配布機関',
        'Distributor',
        multiple=True
    ),
    AddProperty(
        AddProperty.series,
        'シリーズ',
        'シリーズ',
        'Series',
        multiple=True
    ),
    AddProperty(
        AddProperty.version,  # ??
        'バージョン',
        'バージョン',
        'Version',
        multiple=True
    ),
    AddProperty(
        AddProperty.text,
        '引用形式',
        '引用形式',
        'Bibliographic Citation',
        multiple=True
    ),
    AddProperty(
        AddProperty.topic,  # ??
        'トピック',
        'トピック',
        'Topic',
        multiple=True
    ),
]