-- mail_template.sql

INSERT INTO mail_template_genres
	(id, name)
	VALUES
		(1, 'Notification of secret URL provision'),
		(2, 'Guidance to the application form'),
		(3, 'Others')
    ON CONFLICT (id) DO NOTHING;

--
-- Data for Name: mail_templates; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO mail_templates
    (id, mail_subject, mail_body, default_mail, genre_id)
VALUES
    (1, '利用申請登録のご案内／Register Application for Use', '[restricted_site_name_ja]です。
下記のリンクにアクセスしていただき、利用申請の登録を行ってください。

[url_guest_user]

このメールは自動送信されているので返信しないでください。
お問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

This is a message from [restricted_site_name_en].
Please access the link below and register your Application.

[url_guest_user]

Please do not reply to this email as it has been sent automatically.
Please direct all inquiries to the following address.
Also, if you received this message in error, please notify [restricted_site_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 2),
    (2, 'データ利用申請の受付のお知らせ／Your Application was Received', '[restricted_university_institution]
[restricted_fullname]　様

[restricted_institution_name_ja]です。
[restricted_site_name_ja]をご利用いただいて、ありがとうございます。

下記の利用申請を受け付けました。

申請番号： [restricted_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

[restricted_institution_name_ja]で審査しますので、結果の連絡をお待ちください。

このメールは自動送信されているので返信しないでください。
お問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_institution_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname],

This is a message from [restricted_institution_name_en].
Thank you for using [restricted_site_name_en].

We received the below application:

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

You will be notified once the application is approved.

Please do not reply to this email as it has been sent automatically.
Please direct all inquiries to the following address.
Also, if you received this message in error, please notify [restricted_institution_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (3, 'データ利用申請の承認のお願い（ログインユーザー向け）／Request for Approval of Application for Use （for logged in users）', '[advisor_university_institution]
[advisor_fullname]　様

[restricted_site_name_ja]です。
[advisor_university_institution] [advisor_fullname]様から以下のデータの利用申請がありました。

申請番号：[restricted_activity_id]
登録者名：[restricted_fullname]
メールアドレス：[restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ご自身のアカウントにログインして、ワークフローより上記の申請内容をご確認ください。
「承認」または「却下」のボタンをクリックしてください。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [advisor_fullname],

This is a message from [restricted_site_name_en].
We received the below application from [restricted_university_institution] [restricted_fullname]

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

Please log in your account and From [Workflow], confirm the above application by clicking on “approve” or “reject”.

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (4, '利用申請の承認のお知らせ（ログインユーザー向け）／Your application was approved  （for logged in users）', '[restricted_university_institution]
[restricted_fullname]　様

この度は、[restricted_site_name_ja]をご利用いただきありがとうございます。

下記の利用申請を承認しました。

申請番号：[restricted_activity_id]
登録者名：[restricted_fullname]
メールアドレス：[restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ご申請いただいたコンテンツは、次のページよりダウンロードすることができます。

[landing_url]

上記アドレスより[restricted_site_name_ja]にアクセスいただき、ご登録いただいたアカウントでログインをして下さい。
ログインしていただけますと、ダウンロードボタンより申請いただいたデータをダウンロードすることができます。

ダウンロードは[restricted_expiration_date_ja]まで可能です。
ダウンロード期限は[restricted_expiration_date_ja]までなので、期限内に必ず保存してください。
ダウンロード回数が上限を超えたり、ダウンロード期限を過ぎると、再申請が必要になります。

今後とも[restricted_site_name_ja]をよろしくお願いします。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname],

Thank you for using [restricted_site_name_en].
Your application below has been approved.

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

The data can be downloaded from the address below.

[landing_url]

Please access [restricted_site_name_en] from the above address and login with your registered account.
If you logged in, you will be able to download the submitted data from the download button.

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (5, '利用申請の審査結果について（ログインユーザー向け）／The results of the review of your application  （for logged in users）', '[restricted_university_institution]
[restricted_fullname]　様

この度は、[restricted_site_name_ja]をご利用いただきありがとうございます。
申請いただいた内容をもとに、所内で慎重な検討を重ねましたが、今回はコンテンツの提供を見送らせていただくこととなりました。

申請番号： [restricted_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ご申請いただいたにも関わらず、このような返事となり大変申し訳ございません。
今後とも[restricted_site_name_ja]をよろしくお願いします。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname],

Thank you for using [restricted_site_name_en].
Based on the content of your application, after careful consideration within our office,
we have decided not to provide the content at this time.

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

We are very sorry for this reply despite your application.
Thank you for your continued support of [restricted_site_name_en].

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (6, '利用報告の登録のお願い／Request for register Data Usage Report', '[restricted_site_name_ja]です。
下記で申請いただいたデータについてダウンロードされたことを確認しました。

申請番号： [restricted_usage_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ダウンロードしたデータについて、下記のリンクから利用報告の登録をお願いします。

[usage_report_url]

このメールは自動送信されているので返信しないでください。
お問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

This is a message from [restricted_site_name_en].
We have confirmed that the dataset which you registered at below has been downloaded.

Application No.：[restricted_usage_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

For the downloaded data, please register the Data Usage Report by the link below.

[usage_report_url]

Please do not reply to this email as it has been sent automatically.
Please direct all inquiries to the following address.
Also, if you received this message in error, please notify [restricted_site_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]
', true, 3),
    (7, '利用報告の登録のお願い／Request for register Data Usage Report', '[restricted_site_name_ja]です。
現時点で、下記の利用報告が登録されていません

報告番号：[restricted_activity_id]
登録者名：[restricted_fullname]
メールアドレス：[restricted_mail_address]
所属機関：[restricted_university_institution]
利用データ：[restricted_data_name]
データダウンロード日：[data_download_date]

下記のリンクから利用報告の登録をお願いします。

[usage_report_url]

このメールは自動送信されているので返信しないでください。
お問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

This is a message from [restricted_site_name_en].
At this time, the Data Usage Report below has not been registered.

Usage Report No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Usage Dataset：[restricted_data_name]
Download date：[data_download_date]

Please register the Data Usage Report from the link below.

[usage_report_url]

Please do not reply to this email as it has been sent automatically.
Please direct all inquiries to the following address.
Also, if you received this message in error, please notify [restricted_site_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]
', true, 3),
    (8, 'データ利用申請の承認のお願い（ゲストユーザー向け）／Request for Approval of Application for Use  （for guest user）', '[advisor_university_institution]
[advisor_fullname]　様

[restricted_site_name_ja]です。
[advisor_university_institution] [advisor_fullname]様から以下のデータの利用申請がありました。

申請番号：[restricted_activity_id]
登録者名：[restricted_fullname]
メールアドレス：[restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ご自身のアカウントにログインして、ワークフローより上記の申請内容をご確認ください。
「承認」または「却下」のボタンをクリックしてください。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [advisor_fullname],

This is a message from [restricted_site_name_en].
We received the below application from [restricted_university_institution] [restricted_fullname]

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

Please log in your account and From [Workflow], confirm the above application by clicking on “approve” or “reject”.

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (9, '利用申請の承認のお知らせ（ゲストユーザー向け）／Guest''s application was approved （for guest user）', '[restricted_university_institution]
[restricted_fullname]　様

この度は、[restricted_site_name_ja]をご利用いただきありがとうございます。

下記の利用申請を承認しました。

申請番号：[restricted_activity_id]
登録者名：[restricted_fullname]
メールアドレス：[restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

申請いただいたコンテンツは、次のリンクアドレスよりダウンロードすることができます。

[restricted_download_link]

リンクアドレスをクリックすると、メールアドレスの入力が必要となります。
利用申請の際に登録されたメールアドレスを入力頂きますと、申請いただいたコンテンツをダウンロードすることができます。

ダウンロードは[restricted_expiration_date_ja]まで可能です。
ダウンロード期限は[restricted_expiration_date_ja]までなので、期限内に必ず保存してください。
ダウンロード回数が上限を超えたり、ダウンロード期限を過ぎると、再申請が必要になります。

今後とも[restricted_site_name_ja]をよろしくお願いします。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname]

Thank you for using [restricted_site_name_en].
Your application below has been approved.

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

The data can be downloaded from the address below.

[restricted_download_link]

If you click the address, you will be required to enter your email address.
You can download the content you have applied for by entering the email address you registered when applying for use.

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (10, '利用申請の審査結果について（ゲストユーザー向け）／The results of the review of your application  （for guest user）', '[restricted_university_institution]
[restricted_fullname]　様

この度は、[restricted_site_name_ja]をご利用いただきありがとうございます。
申請いただいた内容をもとに、所内で慎重な検討を重ねましたが、今回はコンテンツの提供を見送らせていただくこととなりました。

申請番号： [restricted_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ご申請いただいたにも関わらず、このような返事となり大変申し訳ございません。
今後とも[restricted_site_name_ja]をよろしくお願いします。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname],

Thank you for using [restricted_site_name_en].
Based on the content of your application, after careful consideration within our office,
we have decided not to provide the content at this time.

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

We are very sorry for this reply despite your application.
Thank you for your continued support of [restricted_site_name_en].

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
   (11, 'シークレットURL提供のお知らせ／Notice of providing secret URL', '
シークレットURL機能利用者　様

[restricted_data_name]に登録されている[file_name]のシークレットURLを作成しました。

以下のURLからダウンロードが可能です。

ダウンロードURL：
[secret_url]

有効期限：[restricted_expiration_date]まで有効です
ダウンロード回数：[restricted_download_count]回まで可能です。

＊本URLは、当該コンテンツを特定の方に共有することを前提として発行されています。
＊セキュリティ保護のため、第三者への転送・共有は固くご遠慮ください。
＊このメールは自動送信されているので返信しないでください。
＊このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear Secret URL Feature User,

A secret URL has been generated for the file [file_name] registered under [restricted_data_name].

You can download the file from the link below:

Download URL:  
[secret_url]

Expiration Date: Valid until [restricted_expiration_date]
Download Limit: Up to [restricted_download_count] downloads

Please note the following:

* This URL is issued on the premise that the content will be shared only with specific intended recipients.
* For security reasons, please refrain from forwarding or sharing this URL with third parties.
* This email was sent automatically; please do not reply.
* If you received this message in error, please notify the [restricted_site_name_en].

[restricted_site_name_en]：[restricted_site_url]
Contact: [restricted_site_mail]
', true, 1),
    (12, '利用申請のお知らせ / Notice of application for use', 'データ提供者 様

[restricted_institution_name_ja]です。
[restricted_fullname]様から、ご登録いただいたコンテンツに対して、下記のデータの利用申請がありましたので報告いたします。

申請番号： [restricted_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

このメールは自動送信されているので返信しないでください。
お問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_institution_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear Data Provider,

This is a message from [restricted_institution_name_en].
We received the below application from [restricted_fullname].

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

Please do not reply to this email as it has been sent automatically.
Please direct all inquiries to the following address.
Also, if you received this message in error, please notify [restricted_institution_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (13, '利用報告の受付のお知らせ／Your Application was Received', '[restricted_university_institution]
[restricted_fullname]　様

[restricted_institution_name_ja]です。
[restricted_site_name_ja]をご利用いただいて、ありがとうございます。

下記の利用申請を受け付けました。

申請番号： [restricted_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

[restricted_institution_name_ja]で審査しますので、結果の連絡をお待ちください。

このメールは自動送信されているので返信しないでください。
お問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_institution_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname],

This is a message from [restricted_institution_name_en].
Thank you for using [restricted_site_name_en].

We received the below application:

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

You will be notified once the application is approved.

Please do not reply to this email as it has been sent automatically.
Please direct all inquiries to the following address.
Also, if you received this message in error, please notify [restricted_institution_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (14, '利用報告の承認のお知らせ／Guest''s application was approved （for guest user）', '[restricted_university_institution]
[restricted_fullname]　様

この度は、[restricted_site_name_ja]をご利用いただきありがとうございます。

下記の利用申請を承認しました。

申請番号：[restricted_activity_id]
登録者名：[restricted_fullname]
メールアドレス：[restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

申請いただいたコンテンツは、次のリンクアドレスよりダウンロードすることができます。

[restricted_download_link]

リンクアドレスをクリックすると、メールアドレスの入力が必要となります。
利用申請の際に登録されたメールアドレスを入力頂きますと、申請いただいたコンテンツをダウンロードすることができます。

ダウンロードは[restricted_expiration_date_ja]まで可能です。
ダウンロード期限は[restricted_expiration_date_ja]までなので、期限内に必ず保存してください。
ダウンロード回数が上限を超えたり、ダウンロード期限を過ぎると、再申請が必要になります。

今後とも[restricted_site_name_ja]をよろしくお願いします。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname]

Thank you for using [restricted_site_name_en].
Your application below has been approved.

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

The data can be downloaded from the address below.

[restricted_download_link]

If you click the address, you will be required to enter your email address.
You can download the content you have applied for by entering the email address you registered when applying for use.

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3),
    (15, '利用報告の審査結果について／The results of the review of your application  （for guest user）', '[restricted_university_institution]
[restricted_fullname]　様

この度は、[restricted_site_name_ja]をご利用いただきありがとうございます。
申請いただいた内容をもとに、所内で慎重な検討を重ねましたが、今回はコンテンツの提供を見送らせていただくこととなりました。

申請番号： [restricted_activity_id]
登録者名： [restricted_fullname]
メールアドレス： [restricted_mail_address]
所属機関：[restricted_university_institution]
研究題目：[restricted_research_title]
申請データ：[restricted_data_name]
申請年月日：[restricted_application_date]

ご申請いただいたにも関わらず、このような返事となり大変申し訳ございません。
今後とも[restricted_site_name_ja]をよろしくお願いします。

このメールは自動送信されているので返信しないでください。
このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]

----------------------------------------------------------------------------------

Dear [restricted_fullname],

Thank you for using [restricted_site_name_en].
Based on the content of your application, after careful consideration within our office,
we have decided not to provide the content at this time.

Application No.：[restricted_activity_id]
Name：[restricted_fullname]
E-mail：[restricted_mail_address]
Affiliation：[restricted_university_institution]
Title of research：[restricted_research_title]
Dataset requested ：[restricted_data_name]
Application date：[restricted_application_date]

We are very sorry for this reply despite your application.
Thank you for your continued support of [restricted_site_name_en].

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en]

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]', true, 3)
-- ON CONFLICT (id) DO NOTHING;
-- SecretURL mail template is updated, so use "DO UPDATE" for id=11
ON CONFLICT (id)
DO UPDATE SET
    mail_body = EXCLUDED.mail_body
WHERE EXCLUDED.id = 11;
--
-- Name: mail_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('mail_templates_id_seq', 15, true);
