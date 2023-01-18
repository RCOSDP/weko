# coding:utf-8
"""Default item type."""
from re import M
from properties import AddProperty
from . import item_type_config as config

item_type_id = config.DEFAULT_HARVEST_DDI
item_type_name = "Harvesting DDI"
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
        AddProperty.study_id,
        '整理番号',
        '整理番号',
        'Study ID',
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
        AddProperty.distributor,
        '配布者',
        '配布者',
        'Distributor',
        multiple=True
    ),
    AddProperty(
        AddProperty.uri,
        'URI',
        'URI',
        'URI'
    ),
    AddProperty(
        AddProperty.topic,
        'トピック',
        'トピック',
        'Topic',
        multiple=True
    ),
    AddProperty(
        AddProperty.description,
        '概要',
        '概要',
        'Summary DDI',
        multiple=True
    ),
    AddProperty(
        AddProperty.time_period,
        '対象時期',
        '対象時期',
        'Time Period(s)',
        multiple=True
    ),
    AddProperty(
        AddProperty.geocover,
        '対象地域',
        '対象地域',
        'Geographic Coverage',
        multiple=True
    ),
    AddProperty(
        AddProperty.data_type,
        'データタイプ',
        'データタイプ',
        'Data Type',
        multiple=True
    ),
    AddProperty(
        AddProperty.access,
        'アクセス権',
        'アクセス権',
        'Access',
        multiple=True
    ),
    #AddProperty(   # ??
    #    AddProperty.license,
    #    '権利情報',
    #    '権利情報',
    #    'License'
    #),
    AddProperty(
        AddProperty.language,
        '言語',
        '言語',
        'Language'
    ),
    AddProperty(
        AddProperty.version,
        'バージョン情報',
        'バージョン情報',
        'Version',
        multiple=True
    ),
    AddProperty(
        AddProperty.unit_of_analysis,
        '観察単位',
        '観察単位',
        'Unit of Analysis',
        multiple=True
    ),
    AddProperty(
        AddProperty.universe,
        '母集団',
        '母集団',
        'Universe / Population',
        multiple=True
    ),
    AddProperty(
        AddProperty.sampling,
        'サンプリング方法',
        'サンプリング方法',
        'Sampling Procedure',
        multiple=True
    ),
    AddProperty(
        AddProperty.collection_method,
        '調査方法',
        '調査方法',
        'Collection Method',
        multiple=True
    ),
    #AddProperty(    # ??
    #    AddProperty.funding_agency,
    #    '研究助成機関',
    #    '研究助成機関',
    #    'Funding Agency',
    #    multiple=True
    #),
    #AddProperty(   # ??
    #    AddProperty.grant_id,
    #    '研究費番号',
    #    '研究費番号',
    #    'Grant ID',
    #    multiple=True
    #),
    AddProperty(
        AddProperty.alternative_title,
        'その他のタイトル',
        'その他のタイトル',
        'Alternative Title',
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
        AddProperty.time_period,
        '調査日',
        '調査日',
        'Time Period(s)'
    ),
    AddProperty(
        AddProperty.sampling,
        '回収率',
        '回収率',
        'Sampling Rate',
        multiple=True
    ),
    AddProperty(
        AddProperty.text,
        '引用上の注意',
        '引用上の注意',
        'Bibliographic Citation',
        multiple=True
    ),
    #AddProperty(  # ??
    #    AddProperty.datafile_uri,
    #    'データファイルURI',
    #    'データファイルURI',
    #    'Datafile URI',
    #    multiple=True
    #),
    #AddProperty(   # ??
    #    AddProperty.related_studies,
    #    '関連情報',
    #    '関連情報',
    #    'Related Studies'
    #),
    AddProperty(
        AddProperty.related_publications,
        '関連文献',
        '関連文献',
        'Related Publications'
    ),
    AddProperty(
        AddProperty.publisher,
        '編集者',
        '編集者',
        'Publisher',
        multiple=True
    ),
    #AddProperty(   # ??
    #    AddProperty.provider,
    #    '所蔵者・寄託者',
    #    '所蔵者・寄託者',
    #    'Provider'
    #),
    AddProperty(
        AddProperty.files,
        'ファイル情報',
        'ファイル情報',
        'File',
        multiple=True
    )
]