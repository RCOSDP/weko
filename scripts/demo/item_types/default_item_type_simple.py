# coding:utf-8
"""Default item type."""
from properties import AddProperty
from . import item_type_config as config

item_type_id = config.DEFAULT_ITEM_TYPE_SIMPLE
item_type_name = "デフォルトアイテムタイプ（シンプル）"
property_list = [
    AddProperty(
        AddProperty.title,
        'タイトル',
        'タイトル',
        'Title',
        required=True,
        multiple=True,
        showlist=True,
        newline=True
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
        multiple=True,
        showlist=True,
        newline=True
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
        AddProperty.language,
        '言語',
        '言語',
        'Language',
        multiple=True
    ),
    AddProperty(
        AddProperty.resource_type_simple,
        '資源タイプ',
        '資源タイプ',
        'Resource Type',
        required=True
    ),
    AddProperty(
        AddProperty.version_type,
        '出版タイプ',
        '出版タイプ',
        'Version Type'
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
        AddProperty.funding_reference,
        '助成情報',
        '助成情報',
        'Funding Reference',
        multiple=True
    ),
    AddProperty(
        AddProperty.source_id,
        '収録物識別子',
        '収録物識別子',
        'Source Identifier',
        multiple=True
    ),
    AddProperty(
        AddProperty.biblio_info,
        '書誌情報',
        '書誌情報',
        'Bibliographic Information',
        showlist=True
    ),
    AddProperty(
        AddProperty.dissertation_number,
        '学位授与番号',
        '学位授与番号',
        'Dissertation Number',
        showlist=True
    ),
    AddProperty(
        AddProperty.degree_name,
        '学位名',
        '学位名',
        'Degree Name',
        multiple=True,
        showlist=True
    ),
    AddProperty(
        AddProperty.date_granted,
        '学位授与年月日',
        '学位授与年月日',
        'Date Granted',
        showlist=True
    ),
    AddProperty(
        AddProperty.degree_grantor,
        '学位授与機関',
        '学位授与機関',
        'Degree Grantor',
        multiple=True,
        showlist=True
    ),
    AddProperty(
        AddProperty.files,
        'ファイル情報',
        'ファイル情報',
        'File',
        multiple=True,
        showlist=True
    ),
    AddProperty(
        AddProperty.heading,
        '見出し',
        '見出し',
        'Heading',
        multiple=True
    )
]
