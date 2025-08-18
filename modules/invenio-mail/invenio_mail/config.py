# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Configuration for Invenio-Mail.

Invenio-Mail is a tiny integration layer between Invenio and Flask-Mail, so
please refer to
`Flask-Mail <https://pythonhosted.org/Flask-Mail/#configuring-flask-mail>`_'s
list of configuration variables.
"""
INVENIO_MAIL_BASE_TEMPLATE = 'invenio_mail/base.html'
INVENIO_MAIL_SETTING_TEMPLATE = 'invenio_mail/mail_setting.html'
INVENIO_MAIL_TEMPLATES_TEMPLATE = 'invenio_mail/mail_templates.html'
INVENIO_MAIL_HELP_TEMPLATE = 'invenio_mail/mail_help.html'

INVENIO_MAIL_VARIABLE_HELP = [
    {
        "key": "[url_guest_user]",
        "comment": "ゲスト用の利用申請登録の案内URL"
    },
    {
        "key": "[register_date]",
        "comment": "登録年月日、報告年月日"
    },
    {
        "key": "[restricted_fullname]",
        "comment": "登録者名"
    },
    {
        "key": "[restricted_university_institution]",
        "comment": "登録者の所属機関"
    },
    {
        "key": "[restricted_activity_id]",
        "comment": "利用申請の申請番号"
    },
    {
        "key": "[restricted_research_title]",
        "comment": "登録者の研究題目"
    },
    {
        "key": "[restricted_data_name]",
        "comment": "利用申請データ"
    },
    {
        "key": "[restricted_application_date]",
        "comment": "利用申請年月日"
    },
    {
        "key": "[restricted_mail_address]",
        "comment": "登録者のメールアドレス"
    },
    {
        "key": "[advisor_fullname]",
        "comment": "指導教員の姓名"
    },
    {
        "key": "[advisor_university_institution]",
        "comment": "指導教員の所属機関"
    },
    {
        "key": "[guarantor_fullname]",
        "comment": "保証人の姓名"
    },
    {
        "key": "[guarantor_university_institution]",
        "comment": "保証人の所属機関"
    },
    {
        "key": "[restricted_download_link]",
        "comment": "ファイルのダウンロードURL"
    },
    {
        "key": "[restricted_expiration_date]",
        "comment": "ダウンロードURLの有効期限日数"
    },
    {
        "key": "[restricted_expiration_date_ja]",
        "comment": "日本語のダウンロード期限説明"
    },
    {
        "key": "[restricted_expiration_date_en]",
        "comment": "英語のダウンロード期限説明"
    },
    {
        "key": "[restricted_site_name_ja]",
        "comment": "日本語のサイト名"
    },
    {
        "key": "[restricted_site_name_en]",
        "comment": "英語のサイト名"
    },
    {
        "key": "[restricted_institution_name_ja]",
        "comment": "日本語のサイト機関名"
    },
    {
        "key": "[restricted_institution_name_en]",
        "comment": "英語のサイト機関名"
    },
    {
        "key": "[restricted_site_mail]",
        "comment": "サイトの連絡メール"
    },
    {
        "key": "[restricted_site_url]",
        "comment": "サイトのURL"
    },
    {
        "key": "[data_download_date]",
        "comment": "データダウンロード日"
    },
    {
        "key": "[usage_report_url]",
        "comment": "利用報告登録の案内URL"
    },
    {
        "key": "[restricted_usage_activity_id]",
        "comment": "利用報告の申請番号"
    },
    {
        "key": "[output_report_activity_id]",
        "comment": "成果物登録の申請番号"
    },
    {
        "key": "[output_report_title]",
        "comment": "成果物登録のタイトル"
    },
    {
        "key": "[terms_of_use_jp]",
        "comment": "申請対象の利用規約（日本語）",
    },
    {
        "key": "[terms_of_use_en]",
        "comment": "申請対象の利用規約（英語、自由入力）",
    },
    {
        "key": "[secret_url]",
        "comment": "非公開、エンバーゴデータ向けシークレットURL",
    },
    {
        "key": "[landing_url]",
        "comment": "申請対象のランディングページURL",
    },
    {
        "key": "[resricted_download_count]",
        "comment": "ダウンロード回数",
    },
    {
        "key": "[restricted_download_count_ja]",
        "comment": "ダウンロード回数説明（日本語）",
    },
    {
        "key": "[restricted_download_count_en]",
        "comment": "ダウンロード回数説明（英語）"
    },
    {
        "key": "[restricted_research_plan]",
        "comment": "研究計画"
    }
]

INVENIO_MAIL_DEFAULT_TEMPLATE_CATEGORY_ID = 3
