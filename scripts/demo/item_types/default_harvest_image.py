# coding:utf-8
"""Default item type."""
from properties import AddProperty
from . import item_type_config as config

item_type_id = config.DEFAULT_HARVEST_IMAGE
item_type_name = "Image"
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
        AddProperty.creator,
        '作成者',
        '作成者',
        'Creator',
        multiple=True
    ),
    AddProperty(
        AddProperty.contributor,
        '寄与者',
        '寄与者',
        'Contributor',
        multiple=True
    ),
    AddProperty(
        AddProperty.access_right,
        'アクセス権',
        'アクセス権',
        'Access Rights'
    ),
    AddProperty(
        AddProperty.apc,
        'APC',
        'APC',
        'APC'
    ),
    AddProperty(
        AddProperty.rights,
        '権利情報',
        '権利情報',
        'Rights',
        multiple=True
    ),
    AddProperty(
        AddProperty.rights_holder,
        '権利者情報',
        '権利者情報',
        'Rights Holder',
        multiple=True
    ),
    AddProperty(
        AddProperty.subject,
        '主題',
        '主題',
        'Subject',
        multiple=True
    ),
    AddProperty(
        AddProperty.description,
        '内容記述',
        '内容記述',
        'Description',
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
        AddProperty.date,
        '日付',
        '日付',
        'Date',
        multiple=True
    ),
    AddProperty(
        AddProperty.language,
        '言語',
        '言語',
        'Language',
        multiple=True
    ),
    AddProperty(
        AddProperty.resource_type,
        '資源タイプ',
        '資源タイプ',
        'Resource Type',
        required=True
    ),
    AddProperty(
        AddProperty.identifier_registration,
        'ID登録',
        'ID登録',
        'Identifier Registration'
    ),
    AddProperty(
        AddProperty.relation,
        '関連情報',
        '関連情報',
        'Relation',
        multiple=True
    ),
    AddProperty(
        AddProperty.temporal,
        '時間的範囲',
        '時間的範囲',
        'Temporal',
        multiple=True
    ),
    AddProperty(
        AddProperty.geolocation,
        '位置情報',
        '位置情報',
        'Geo Location',
        multiple=True
    ),
    AddProperty(
        AddProperty.funding_reference,
        '助成情報',
        '助成情報',
        'Funding Reference',
        multiple=True
    ),
    AddProperty(
        AddProperty.files,
        'ファイル情報',
        'ファイル情報',
        'File',
        multiple=True
    )
]