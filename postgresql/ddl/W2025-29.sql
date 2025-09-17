BEGIN;

-- W2023-23-item-application.sql

-- public.workflow_activity_item_application definition
CREATE TABLE public.workflow_activity_item_application (
	status varchar(1) NOT NULL,
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	activity_id varchar(24) NOT NULL,
	item_application jsonb NULL,
	display_item_application_button bool NOT NULL,
	CONSTRAINT pk_workflow_activity_item_application PRIMARY KEY (id)
);
CREATE INDEX ix_workflow_activity_item_application_activity_id ON public.workflow_activity_item_application USING btree (activity_id);

-- public.item_application definition
CREATE TABLE public.item_application (
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	item_id uuid NOT NULL,
	item_application jsonb NULL,
	CONSTRAINT pk_item_application PRIMARY KEY (id)
);

-- mail_template.sql

INSERT INTO public.mail_template_genres
	(id, name)
	VALUES
		(1, 'Notification of secret URL provision'),
		(2, 'Guidance to the application form'),
		(3, 'Others');

--
-- Data for Name: mail_templates; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.mail_templates
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
    (11, 'シークレットURL提供のお知らせ／Notice of providing secret URL', '[restricted_university_institution]
[restricted_fullname]

[restricted_site_name_ja]です。

[restricted_data_name]に登録されている[file_name]のシークレットURLを作成しました。

下記アドレスよりダウンロードすることができます。

[secret_url]

このURLは[restricted_expiration_date][restricted_expiration_date_ja]まで有効です。ダウンロードは[restricted_download_count][restricted_download_count_ja]回まで可能です。

＊このメールは自動送信されているので返信しないでください。
＊このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。

[restricted_site_name_ja]：[restricted_site_url]
問い合わせ窓口：[restricted_site_mail]


----------------------------------------------------------------------------------

[restricted_university_institution]
[restricted_fullname]

This is a message from [restricted_site_name_en].
Secret URL for [file_name] registered in [restricted_data_name] is created.

The data can be downloaded from the address below.

[secret_url]

This URL is valid until [restricted_expiration_date][restricted_expiration_date_en]. You can download it up to [restricted_download_count][restricted_download_count_en] times.

Please do not reply to this email as it has been sent automatically.
If you received this message in error, please notify the [restricted_site_name_en].

[restricted_site_name_en]：[restricted_site_url]
E-mail：[restricted_site_mail]
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
E-mail：[restricted_site_mail]', true, 3);

--
-- Name: mail_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.mail_templates_id_seq', 15, true);

-- W2023-23-request_mail.sql

-- public.request_mail_list definition
CREATE TABLE public.request_mail_list (
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	item_id uuid NOT NULL,
	mail_list jsonb NULL,
	CONSTRAINT pk_request_mail_list PRIMARY KEY (id)
);

-- public.workflow_flow_action_role definition
ALTER TABLE public.workflow_flow_action_role ADD action_request_mail Boolean NOT NULL DEFAULT false;

-- W2023-21 workflow_flow_action_role.sql

ALTER TABLE public.workflow_flow_action_role ADD column action_item_registrant Boolean NOT NULL DEFAULT false;

-- W2023-21 update_resticted_items.sql

-- 1. Add "shared_user_ids" column into workflow_activity table
ALTER TABLE
	workflow_activity
ADD
	shared_user_ids jsonb NULL;

-- 2. Update "shared_user_ids" with "shared_user_id column"
UPDATE
	workflow_activity
SET
	shared_user_ids = json_build_array(json_build_object('user', shared_user_id))
WHERE
	shared_user_ids IS NULL
	AND (
		shared_user_id IS NOT NULL
		AND shared_user_id > 0
	);

--3. Drop "shared_user_ids" column
ALTER TABLE
	workflow_activity DROP COLUMN shared_user_id;

-- WOA-06-jsonld_mapping.sql

INSERT INTO public.jsonld_mappings(created, updated, id, name, mapping, item_type_id, version_id, is_deleted) VALUES ('2025-03-21 17:00:00.000000', '2025-03-21 17:00:00.000000', 30001, 'デフォルトマッピング（シンプル）', '{"PubDate": "datePublished", "Title": "dc:title", "Title.タイトル": "dc:title.value", "Title.言語": "dc:title.language", "Alternative Title": "dcterms:alternative", "Alternative Title.その他のタイトル": "dcterms:alternative.value", "Alternative Title.言語": "dcterms:alternative.language", "Creator": "jpcoar:creator", "Creator.作成者名": "jpcoar:creator.jpcoar:givenName", "Creator.作成者名.名": "jpcoar:creator.jpcoar:givenName.value", "Creator.作成者名.言語": "jpcoar:creator.jpcoar:givenName.language", "Creator.作成者タイプ": "jpcoar:creator.creatorType", "Creator.作成者姓": "jpcoar:creator.jpcoar:familyName", "Creator.作成者姓.姓": "jpcoar:creator.jpcoar:familyName.value", "Creator.作成者姓.言語": "jpcoar:creator.jpcoar:familyName.language", "Creator.作成者メールアドレス": "jpcoar:creator.email", "Creator.作成者メールアドレス.メールアドレス": "jpcoar:creator.email.value", "Creator.作成者姓名": "jpcoar:creator.jpcoar:creatorName", "Creator.作成者姓名.姓名": "jpcoar:creator.jpcoar:creatorName.value", "Creator.作成者姓名.言語": "jpcoar:creator.jpcoar:creatorName.language", "Creator.作成者姓名.名前タイプ": "jpcoar:creator.jpcoar:creatorName.nameType", "Creator.作成者識別子": "jpcoar:creator.jpcoar:nameIdentifier", "Creator.作成者識別子.作成者識別子": "jpcoar:creator.jpcoar:nameIdentifier.value", "Creator.作成者識別子.作成者識別子URI": "jpcoar:creator.jpcoar:nameIdentifier.nameIdentifierURI", "Creator.作成者識別子.作成者識別子Scheme": "jpcoar:creator.jpcoar:nameIdentifier.nameIdentifierScheme", "Creator.作成者所属": "jpcoar:creator.jpcoar:affiliation", "Creator.作成者所属.所属機関名": "jpcoar:creator.jpcoar:affiliation.jpcoar:affiliationName", "Creator.作成者所属.所属機関名.所属機関名": "jpcoar:creator.jpcoar:affiliation.jpcoar:affiliationName.value", "Creator.作成者所属.所属機関名.言語": "jpcoar:creator.jpcoar:affiliation.jpcoar:affiliationName.language", "Creator.作成者所属.所属機関識別子": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier", "Creator.作成者所属.所属機関識別子.所属機関識別子": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier.value", "Creator.作成者所属.所属機関識別子.所属機関識別子URI": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierURI", "Creator.作成者所属.所属機関識別子.所属機関識別子Scheme": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierScheme", "Creator.作成者別名": "jpcoar:creator.jpcoar:creatorAlternative", "Creator.作成者別名.別名": "jpcoar:creator.jpcoar:creatorAlternative.value", "Creator.作成者別名.言語": "jpcoar:creator.jpcoar:creatorAlternative.language", "Contributor": "jpcoar:contributor", "Contributor.寄与者名": "jpcoar:contributor.jpcoar:givenName", "Contributor.寄与者名.名": "jpcoar:contributor.jpcoar:givenName.value", "Contributor.寄与者名.言語": "jpcoar:contributor.jpcoar:givenName.language", "Contributor.寄与者タイプ": "jpcoar:contributor.contributorType", "Contributor.寄与者姓": "jpcoar:contributor.jpcoar:familyName", "Contributor.寄与者姓.姓": "jpcoar:contributor.jpcoar:familyName.value", "Contributor.寄与者姓.言語": "jpcoar:contributor.jpcoar:familyName.language", "Contributor.寄与者メールアドレス": "jpcoar:contributor.email", "Contributor.寄与者メールアドレス.メールアドレス": "jpcoar:contributor.email.value", "Contributor.寄与者姓名": "jpcoar:contributor.jpcoar:contributorName", "Contributor.寄与者姓名.姓名": "jpcoar:contributor.jpcoar:contributorName.value", "Contributor.寄与者姓名.言語": "jpcoar:contributor.jpcoar:contributorName.language", "Contributor.寄与者姓名.名前タイプ": "jpcoar:contributor.jpcoar:contributorName.nameType", "Contributor.寄与者識別子": "jpcoar:contributor.jpcoar:nameIdentifier", "Contributor.寄与者識別子.寄与者識別子": "jpcoar:contributor.jpcoar:nameIdentifier.value", "Contributor.寄与者識別子.寄与者識別子URI": "jpcoar:contributor.jpcoar:nameIdentifier.nameIdentifierURI", "Contributor.寄与者識別子.寄与者識別子Scheme": "jpcoar:contributor.jpcoar:nameIdentifier.nameIdentifierScheme", "Contributor.寄与者所属": "jpcoar:contributor.jpcoar:affiliation", "Contributor.寄与者所属.所属機関名": "jpcoar:contributor.jpcoar:affiliationjpcoar:affiliationName", "Contributor.寄与者所属.所属機関名.所属機関名": "jpcoar:contributor.jpcoar:affiliationjpcoar:affiliationName.value", "Contributor.寄与者所属.所属機関名.言語": "jpcoar:contributor.jpcoar:affiliationjpcoar:affiliationName.language", "Contributor.寄与者所属.所属機関識別子": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier", "Contributor.寄与者所属.所属機関識別子.所属機関識別子": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier.value", "Contributor.寄与者所属.所属機関識別子.所属機関識別子URI": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierURI", "Contributor.寄与者所属.所属機関識別子.所属機関識別子Scheme": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierScheme", "Contributor.寄与者別名": "jpcoar:contributor.jpcoar:contributorAlternative", "Contributor.寄与者別名.別名": "jpcoar:contributor.jpcoar:contributorAlternative.value", "Contributor.寄与者別名.言語": "jpcoar:contributor.jpcoar:contributorAlternative.language", "Access Rights": "dcterms:accessRights", "Access Rights.アクセス権": "dcterms:accessRights.value", "Access Rights.アクセス権URI": "dcterms:accessRights.rdf:resource", "Rights": "dc:rights", "Rights.権利情報": "dc:rights.value", "Rights.言語": "dc:rights.language", "Rights.権利情報Resource": "dc:rights.rdf:resource", "Rights Holder": "jpcoar:rightsHolder", "Rights Holder.権利者識別子": "jpcoar:rightsHolder.jpcoar:nameIdentifier", "Rights Holder.権利者識別子.権利者識別子": "jpcoar:rightsHolder.jpcoar:nameIdentifier.value", "Rights Holder.権利者識別子.権利者識別子Scheme": "jpcoar:rightsHolder.jpcoar:nameIdentifier.nameIdentifierScheme", "Rights Holder.権利者識別子.権利者識別子URI": "jpcoar:rightsHolder.jpcoar:nameIdentifier.nameIdentifierURI", "Rights Holder.権利者名": "jpcoar:rightsHolder.jpcoar:rightsHolderName", "Rights Holder.権利者名.言語": "jpcoar:rightsHolder.jpcoar:rightsHolderName.value", "Rights Holder.権利者名.権利者名": "jpcoar:rightsHolder.jpcoar:rightsHolderName.language", "Subject": "jpcoar:subject", "Subject.主題": "jpcoar:subject.value", "Subject.言語": "jpcoar:subject.language", "Subject.主題Scheme": "jpcoar:subject.subjectScheme", "Subject.主題URI": "jpcoar:subject.subjectURI", "Description": "datacite:description", "Description.内容記述": "datacite:description.value", "Description.言語": "datacite:description.language", "Description.内容記述タイプ": "datacite:description.descriptionType", "Publisher": "dc:publisher", "Publisher.出版者": "dc:publisher.value", "Publisher.言語": "dc:publisher.language", "Language": "dc:language", "Language.言語": "dc:language.value", "Resource Type": "dc:type", "Resource Type.資源タイプ識別子": "dc:type.value", "Resource Type.資源タイプ": "dc:type.rdf:resource", "Version Type": "oaire:version", "Version Type.査読の有無": "oaire:version.itemReviewed", "Version Type.出版タイプResource": "oaire:version.rdf:resource", "Version Type.出版タイプ": "oaire:version.value", "Identifier Registration": "jpcoar:identifierRegistration", "Identifier Registration.ID登録": "jpcoar:identifierRegistration.value", "Identifier Registration.ID登録タイプ": "jpcoar:identifierRegistration.identifierType", "Relation": "jpcoar:relation", "Relation.関連名称": "jpcoar:relation.jpcoar:relatedTitle", "Relation.関連名称.言語": "jpcoar:relation.jpcoar:relatedTitle.language", "Relation.関連名称.関連名称": "jpcoar:relation.jpcoar:relatedTitle.value", "Relation.関連タイプ": "jpcoar:relation.relationType", "Relation.関連識別子": "jpcoar:relation.jpcoar:relatedIdentifier", "Relation.関連識別子.関連識別子": "jpcoar:relation.jpcoar:relatedIdentifier.value", "Relation.関連識別子.識別子タイプ": "jpcoar:relation.jpcoar:relatedIdentifier.identifierType", "Funding Reference": "jpcoar:fundingReference", "Funding Reference.研究課題番号": "jpcoar:fundingReference.jpcoar:awardNumber", "Funding Reference.研究課題番号.研究課題番号": "jpcoar:fundingReference.jpcoar:awardNumber.value", "Funding Reference.研究課題番号.研究課題番号タイプ": "jpcoar:fundingReference.jpcoar:awardNumber.awardNumberType", "Funding Reference.研究課題番号.研究課題番号URI": "jpcoar:fundingReference.jpcoar:awardNumber.awardURI", "Funding Reference.研究課題名": "jpcoar:fundingReference.jpcoar:awardTitle", "Funding Reference.研究課題名.研究課題名": "jpcoar:fundingReference.jpcoar:awardTitle.value", "Funding Reference.研究課題名.言語": "jpcoar:fundingReference.jpcoar:awardTitle.language", "Funding Reference.助成機関識別子": "jpcoar:fundingReference.jpcoar:funderIdentifier", "Funding Reference.助成機関識別子.助成機関識別子": "jpcoar:fundingReference.jpcoar:funderIdentifier.value", "Funding Reference.助成機関識別子.識別子タイプ": "jpcoar:fundingReference.jpcoar:funderIdentifier.funderIdentifierType", "Funding Reference.助成機関名": "jpcoar:fundingReference.jpcoar:funderName", "Funding Reference.助成機関名.助成機関名": "jpcoar:fundingReference.jpcoar:funderName.value", "Funding Reference.助成機関名.言語": "jpcoar:fundingReference.jpcoar:funderName.language", "Funding Reference.プログラム情報識別子": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier", "Funding Reference.プログラム情報識別子.プログラム情報識別子": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier.value", "Funding Reference.プログラム情報識別子.プログラム情報識別子タイプ": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier.fundingStreamIdentifierType", "Funding Reference.プログラム情報識別子.プログラム情報識別子タイプURI": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier.fundingStreamIdentifierTypeURI", "Funding Reference.プログラム情報": "jpcoar:fundingReference.jpcoar:fundingStream", "Funding Reference.プログラム情報.プログラム情報": "jpcoar:fundingReference.jpcoar:fundingStream.value", "Funding Reference.プログラム情報.言語": "jpcoar:fundingReference.jpcoar:fundingStream.language", "Source Identifier": "jpcoar:sourceIdentifier", "Source Identifier.収録物識別子": "jpcoar:sourceIdentifier.value", "Source Identifier.収録物識別子タイプ": "jpcoar:sourceIdentifier.identifierType", "Bibliographic Information": "dcterms:medium", "Bibliographic Information.発行日": "dcterms:medium.datePublished", "Bibliographic Information.発行日.日付": "dcterms:medium.datePublished.value", "Bibliographic Information.発行日.日付タイプ": "dcterms:medium.datePublished.dateType", "Bibliographic Information.ページ数": "dcterms:medium.issueNumber", "Bibliographic Information.終了ページ": "dcterms:medium.numberOfPages", "Bibliographic Information.開始ページ": "dcterms:medium.pageEnd", "Bibliographic Information.号": "dcterms:medium.pageStart", "Bibliographic Information.巻": "dcterms:medium.volumeNumber", "Bibliographic Information.雑誌名": "dcterms:medium.name", "Bibliographic Information.雑誌名.タイトル": "dcterms:medium.name.value", "Bibliographic Information.雑誌名.言語": "dcterms:medium.name.language", "Dissertation Number": "dcndl:dissertationNumber", "Dissertation Number.学位授与番号": "dcndl:dissertationNumber.value", "Degree Name": "dcndl:degreeName", "Degree Name.学位名": "dcndl:degreeName.value", "Degree Name.言語": "dcndl:degreeName.language", "Date Granted": "dcndl:dateGranted", "Date Granted.学位授与年月日": "dcndl:dateGranted.value", "Degree Grantor": "jpcoar:degreeGrantor", "Degree Grantor.学位授与機関名": "jpcoar:degreeGrantor.jpcoar:degreeGrantorName", "Degree Grantor.学位授与機関名.言語": "jpcoar:degreeGrantor.jpcoar:degreeGrantorName.language", "Degree Grantor.学位授与機関名.学位授与機関名": "jpcoar:degreeGrantor.jpcoar:degreeGrantorName.value", "Degree Grantor.学位授与機関識別子": "jpcoar:degreeGrantor.jpcoar:nameIdentifier", "Degree Grantor.学位授与機関識別子.学位授与機関識別子": "jpcoar:degreeGrantor.jpcoar:nameIdentifier.value", "Degree Grantor.学位授与機関識別子.学位授与機関識別子Scheme": "jpcoar:degreeGrantor.jpcoar:nameIdentifier.nameIdentifierScheme", "File": "hasPart", "File.アクセス": "hasPart.dcterms:accessRights", "File.公開日.タイプ": "$Available", "File.公開日.公開日": "hasPart.datePublished", "File.表示形式": "hasPart.jpcoar:format", "File.日付": "hasPart.datacite:date", "File.日付.日付タイプ": "hasPart.datacite:date.dateType", "File.日付.日付": "hasPart.datacite:date.value", "File.ファイル名": "hasPart.name", "File.サイズ": "hasPart.jpcoar:extent", "File.サイズ.サイズ": "hasPart.jpcoar:extent.value", "File.フォーマット": "hasPart.jpcoar:mimeType", "File.グループ": "hasPart.department", "File.ライセンス": "hasPart.license", "File.本文URL": "hasPart.jpcoar:URI", "File.本文URL.ラベル": "hasPart.@id", "File.本文URL.オブジェクトタイプ": "hasPart.jpcoar:URI.objectType", "File.本文URL.本文URL": "hasPart.jpcoar:URI.value", "File.バージョン情報": "hasPart.datacite:version", "Heading": "headline", "Heading.大見出し": "headline.value", "Heading.小見出し": "headline.alternativeHeadline", "Heading.言語": "headline.language"}', 30001, 1, false);
INSERT INTO public.jsonld_mappings(created, updated, id, name, mapping, item_type_id, version_id, is_deleted) VALUES ('2025-03-21 17:00:00.000000', '2025-03-21 17:00:00.000000', 30002, 'デフォルトマッピング（フル）', '{"PubDate": "datePublished", "Title": "dc:title", "Title.タイトル": "dc:title.value", "Title.言語": "dc:title.language", "Alternative Title": "dcterms:alternative", "Alternative Title.その他のタイトル": "dcterms:alternative.value", "Alternative Title.言語": "dcterms:alternative.language", "Creator": "jpcoar:creator", "Creator.作成者名": "jpcoar:creator.jpcoar:givenName", "Creator.作成者名.名": "jpcoar:creator.jpcoar:givenName.value", "Creator.作成者名.言語": "jpcoar:creator.jpcoar:givenName.language", "Creator.作成者タイプ": "jpcoar:creator.creatorType", "Creator.作成者姓": "jpcoar:creator.jpcoar:familyName", "Creator.作成者姓.姓": "jpcoar:creator.jpcoar:familyName.value", "Creator.作成者姓.言語": "jpcoar:creator.jpcoar:familyName.language", "Creator.作成者メールアドレス": "jpcoar:creator.email", "Creator.作成者メールアドレス.メールアドレス": "jpcoar:creator.email.value", "Creator.作成者姓名": "jpcoar:creator.jpcoar:creatorName", "Creator.作成者姓名.姓名": "jpcoar:creator.jpcoar:creatorName.value", "Creator.作成者姓名.言語": "jpcoar:creator.jpcoar:creatorName.language", "Creator.作成者姓名.名前タイプ": "jpcoar:creator.jpcoar:creatorName.nameType", "Creator.作成者識別子": "jpcoar:creator.jpcoar:nameIdentifier", "Creator.作成者識別子.作成者識別子": "jpcoar:creator.jpcoar:nameIdentifier.value", "Creator.作成者識別子.作成者識別子URI": "jpcoar:creator.jpcoar:nameIdentifier.nameIdentifierURI", "Creator.作成者識別子.作成者識別子Scheme": "jpcoar:creator.jpcoar:nameIdentifier.nameIdentifierScheme", "Creator.作成者所属": "jpcoar:creator.jpcoar:affiliation", "Creator.作成者所属.所属機関名": "jpcoar:creator.jpcoar:affiliation.jpcoar:affiliationName", "Creator.作成者所属.所属機関名.所属機関名": "jpcoar:creator.jpcoar:affiliation.jpcoar:affiliationName.value", "Creator.作成者所属.所属機関名.言語": "jpcoar:creator.jpcoar:affiliation.jpcoar:affiliationName.language", "Creator.作成者所属.所属機関識別子": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier", "Creator.作成者所属.所属機関識別子.所属機関識別子": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier.value", "Creator.作成者所属.所属機関識別子.所属機関識別子URI": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierURI", "Creator.作成者所属.所属機関識別子.所属機関識別子Scheme": "jpcoar:creator.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierScheme", "Creator.作成者別名": "jpcoar:creator.jpcoar:creatorAlternative", "Creator.作成者別名.別名": "jpcoar:creator.jpcoar:creatorAlternative.value", "Creator.作成者別名.言語": "jpcoar:creator.jpcoar:creatorAlternative.language", "Contributor": "jpcoar:contributor", "Contributor.寄与者名": "jpcoar:contributor.jpcoar:givenName", "Contributor.寄与者名.名": "jpcoar:contributor.jpcoar:givenName.value", "Contributor.寄与者名.言語": "jpcoar:contributor.jpcoar:givenName.language", "Contributor.寄与者タイプ": "jpcoar:contributor.contributorType", "Contributor.寄与者姓": "jpcoar:contributor.jpcoar:familyName", "Contributor.寄与者姓.姓": "jpcoar:contributor.jpcoar:familyName.value", "Contributor.寄与者姓.言語": "jpcoar:contributor.jpcoar:familyName.language", "Contributor.寄与者メールアドレス": "jpcoar:contributor.email", "Contributor.寄与者メールアドレス.メールアドレス": "jpcoar:contributor.email.value", "Contributor.寄与者姓名": "jpcoar:contributor.jpcoar:contributorName", "Contributor.寄与者姓名.姓名": "jpcoar:contributor.jpcoar:contributorName.value", "Contributor.寄与者姓名.言語": "jpcoar:contributor.jpcoar:contributorName.language", "Contributor.寄与者姓名.名前タイプ": "jpcoar:contributor.jpcoar:contributorName.nameType", "Contributor.寄与者識別子": "jpcoar:contributor.jpcoar:nameIdentifier", "Contributor.寄与者識別子.寄与者識別子": "jpcoar:contributor.jpcoar:nameIdentifier.value", "Contributor.寄与者識別子.寄与者識別子URI": "jpcoar:contributor.jpcoar:nameIdentifier.nameIdentifierURI", "Contributor.寄与者識別子.寄与者識別子Scheme": "jpcoar:contributor.jpcoar:nameIdentifier.nameIdentifierScheme", "Contributor.寄与者所属": "jpcoar:contributor.jpcoar:affiliation", "Contributor.寄与者所属.所属機関名": "jpcoar:contributor.jpcoar:affiliationjpcoar:affiliationName", "Contributor.寄与者所属.所属機関名.所属機関名": "jpcoar:contributor.jpcoar:affiliationjpcoar:affiliationName.value", "Contributor.寄与者所属.所属機関名.言語": "jpcoar:contributor.jpcoar:affiliationjpcoar:affiliationName.language", "Contributor.寄与者所属.所属機関識別子": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier", "Contributor.寄与者所属.所属機関識別子.所属機関識別子": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier.value", "Contributor.寄与者所属.所属機関識別子.所属機関識別子URI": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierURI", "Contributor.寄与者所属.所属機関識別子.所属機関識別子Scheme": "jpcoar:contributor.jpcoar:affiliation.jpcoar:nameIdentifier.nameIdentifierScheme", "Contributor.寄与者別名": "jpcoar:contributor.jpcoar:contributorAlternative", "Contributor.寄与者別名.別名": "jpcoar:contributor.jpcoar:contributorAlternative.value", "Contributor.寄与者別名.言語": "jpcoar:contributor.jpcoar:contributorAlternative.language", "Access Rights": "dcterms:accessRights", "Access Rights.アクセス権": "dcterms:accessRights.value", "Access Rights.アクセス権URI": "dcterms:accessRights.rdf:resource", "APC": "rioxxterms:apc", "APC.APC": "rioxxterms:apc.value", "Rights": "dc:rights", "Rights.権利情報": "dc:rights.value", "Rights.言語": "dc:rights.language", "Rights.権利情報Resource": "dc:rights.rdf:resource", "Rights Holder": "jpcoar:rightsHolder", "Rights Holder.権利者識別子": "jpcoar:rightsHolder.jpcoar:nameIdentifier", "Rights Holder.権利者識別子.権利者識別子": "jpcoar:rightsHolder.jpcoar:nameIdentifier.value", "Rights Holder.権利者識別子.権利者識別子Scheme": "jpcoar:rightsHolder.jpcoar:nameIdentifier.nameIdentifierScheme", "Rights Holder.権利者識別子.権利者識別子URI": "jpcoar:rightsHolder.jpcoar:nameIdentifier.nameIdentifierURI", "Rights Holder.権利者名": "jpcoar:rightsHolder.jpcoar:rightsHolderName", "Rights Holder.権利者名.言語": "jpcoar:rightsHolder.jpcoar:rightsHolderName.value", "Rights Holder.権利者名.権利者名": "jpcoar:rightsHolder.jpcoar:rightsHolderName.language", "Subject": "jpcoar:subject", "Subject.主題": "jpcoar:subject.value", "Subject.言語": "jpcoar:subject.language", "Subject.主題Scheme": "jpcoar:subject.subjectScheme", "Subject.主題URI": "jpcoar:subject.subjectURI", "Description": "datacite:description", "Description.内容記述": "datacite:description.value", "Description.言語": "datacite:description.language", "Description.内容記述タイプ": "datacite:description.descriptionType", "Publisher": "dc:publisher", "Publisher.出版者": "dc:publisher.value", "Publisher.言語": "dc:publisher.language", "Date": "datacite:date", "Date.日付": "datacite:date.value", "Date.日付タイプ": "datacite:date.dateType", "Language": "dc:language", "Language.言語": "dc:language.value", "Resource Type": "dc:type", "Resource Type.資源タイプ": "dc:type.value", "Resource Type.資源タイプ識別子": "dc:type.rdf:resource", "Version": "datacite:version", "Version.バージョン情報": "datacite:version.value", "Version Type": "oaire:version", "Version Type.査読の有無": "oaire:version.itemReviewed", "Version Type.出版タイプResource": "oaire:version.rdf:resource", "Version Type.出版タイプ": "oaire:version.value", "Identifier": "jpcoar:identifier", "Identifier.識別子タイプ": "jpcoar:identifier.identifierType", "Identifier.識別子": "jpcoar:identifier.value", "Identifier Registration": "jpcoar:identifierRegistration", "Identifier Registration.ID登録": "jpcoar:identifierRegistration.value", "Identifier Registration.ID登録タイプ": "jpcoar:identifierRegistration.identifierType", "Relation": "jpcoar:relation", "Relation.関連名称": "jpcoar:relation.jpcoar:relatedTitle", "Relation.関連名称.言語": "jpcoar:relation.jpcoar:relatedTitle.language", "Relation.関連名称.関連名称": "jpcoar:relation.jpcoar:relatedTitle.value", "Relation.関連タイプ": "jpcoar:relation.relationType", "Relation.関連識別子": "jpcoar:relation.jpcoar:relatedIdentifier", "Relation.関連識別子.関連識別子": "jpcoar:relation.jpcoar:relatedIdentifier.value", "Relation.関連識別子.識別子タイプ": "jpcoar:relation.jpcoar:relatedIdentifier.identifierType", "Temporal": "dcterms:temporal", "Temporal.言語": "dcterms:temporal.language", "Temporal.時間的範囲": "dcterms:temporal.value", "Geo Location": "datacite:geoLocation", "Geo Location.位置情報（空間）": "datacite:geoLocation.datacite:geoLocationBox", "Geo Location.位置情報（空間）.東部経度": "datacite:geoLocation.datacite:geoLocationBox.datacite:eastBoundLongitude", "Geo Location.位置情報（空間）.北部緯度": "datacite:geoLocation.datacite:geoLocationBox.datacite:northBoundLatitude", "Geo Location.位置情報（空間）.南部緯度": "datacite:geoLocation.datacite:geoLocationBox.datacite:southBoundLatitude", "Geo Location.位置情報（空間）.西部経度": "datacite:geoLocation.datacite:geoLocationBox.datacite:westBoundLongitude", "Geo Location.位置情報（自由記述）": "datacite:geoLocation.datacite:geoLocationPlace", "Geo Location.位置情報（自由記述）.位置情報（自由記述）": "datacite:geoLocation.datacite:geoLocationPlace.value", "Geo Location.位置情報（点）": "datacite:geoLocation.datacite:geoLocationPoint", "Geo Location.位置情報（点）.緯度": "datacite:geoLocation.datacite:geoLocationPoint.datacite:pointLatitude", "Geo Location.位置情報（点）.経度": "datacite:geoLocation.datacite:geoLocationPoint.datacite:pointLongitude", "Funding Reference": "jpcoar:fundingReference", "Funding Reference.研究課題番号": "jpcoar:fundingReference.jpcoar:awardNumber", "Funding Reference.研究課題番号.研究課題番号": "jpcoar:fundingReference.jpcoar:awardNumber.value", "Funding Reference.研究課題番号.研究課題番号タイプ": "jpcoar:fundingReference.jpcoar:awardNumber.awardNumberType", "Funding Reference.研究課題番号.研究課題番号URI": "jpcoar:fundingReference.jpcoar:awardNumber.awardURI", "Funding Reference.研究課題名": "jpcoar:fundingReference.jpcoar:awardTitle", "Funding Reference.研究課題名.研究課題名": "jpcoar:fundingReference.jpcoar:awardTitle.value", "Funding Reference.研究課題名.言語": "jpcoar:fundingReference.jpcoar:awardTitle.language", "Funding Reference.助成機関識別子": "jpcoar:fundingReference.jpcoar:funderIdentifier", "Funding Reference.助成機関識別子.助成機関識別子": "jpcoar:fundingReference.jpcoar:funderIdentifier.value", "Funding Reference.助成機関識別子.識別子タイプ": "jpcoar:fundingReference.jpcoar:funderIdentifier.funderIdentifierType", "Funding Reference.助成機関名": "jpcoar:fundingReference.jpcoar:funderName", "Funding Reference.助成機関名.助成機関名": "jpcoar:fundingReference.jpcoar:funderName.value", "Funding Reference.助成機関名.言語": "jpcoar:fundingReference.jpcoar:funderName.language", "Funding Reference.プログラム情報識別子": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier", "Funding Reference.プログラム情報識別子.プログラム情報識別子": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier.value", "Funding Reference.プログラム情報識別子.プログラム情報識別子タイプ": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier.fundingStreamIdentifierType", "Funding Reference.プログラム情報識別子.プログラム情報識別子タイプURI": "jpcoar:fundingReference.jpcoar:fundingStreamIdentifier.fundingStreamIdentifierTypeURI", "Funding Reference.プログラム情報": "jpcoar:fundingReference.jpcoar:fundingStream", "Funding Reference.プログラム情報.プログラム情報": "jpcoar:fundingReference.jpcoar:fundingStream.value", "Funding Reference.プログラム情報.言語": "jpcoar:fundingReference.jpcoar:fundingStream.language", "Source Identifier": "jpcoar:sourceIdentifier", "Source Identifier.収録物識別子": "jpcoar:sourceIdentifier.value", "Source Identifier.収録物識別子タイプ": "jpcoar:sourceIdentifier.identifierType", "Source Title": "jpcoar:sourceTitle", "Source Title.収録物名": "jpcoar:sourceTitle.value", "Source Title.言語": "jpcoar:sourceTitle.language", "Volume Number": "jpcoar:volume", "Volume Number.巻": "jpcoar:volume.value", "Issue Number": "jpcoar:issue", "Issue Number.号": "jpcoar:issue.value", "Number of Pages": "jpcoar:numPages", "Number of Pages.ページ数": "jpcoar:numPages.value", "Page Start": "jpcoar:pageStart", "Page Start.開始ページ": "jpcoar:pageStart.value", "Page End": "jpcoar:pageEnd", "Page End.終了ページ": "jpcoar:pageEnd.value", "Bibliographic Information": "dcterms:medium", "Bibliographic Information.発行日": "dcterms:medium.datePublished", "Bibliographic Information.発行日.日付": "dcterms:medium.datePublished.value", "Bibliographic Information.発行日.日付タイプ": "dcterms:medium.datePublished.dateType", "Bibliographic Information.号": "dcterms:medium.issueNumber", "Bibliographic Information.ページ数": "dcterms:medium.numberOfPages", "Bibliographic Information.終了ページ": "dcterms:medium.pageEnd", "Bibliographic Information.開始ページ": "dcterms:medium.pageStart", "Bibliographic Information.巻": "dcterms:medium.volumeNumber", "Bibliographic Information.雑誌名": "dcterms:medium.name", "Bibliographic Information.雑誌名.タイトル": "dcterms:medium.name.value", "Bibliographic Information.雑誌名.言語": "dcterms:medium.name.language", "Dissertation Number": "dcndl:dissertationNumber", "Dissertation Number.学位授与番号": "dcndl:dissertationNumber.value", "Degree Name": "dcndl:degreeName", "Degree Name.学位名": "dcndl:degreeName.value", "Degree Name.言語": "dcndl:degreeName.language", "Date Granted": "dcndl:dateGranted", "Date Granted.学位授与年月日": "dcndl:dateGranted.value", "Degree Grantor": "jpcoar:degreeGrantor", "Degree Grantor.学位授与機関名": "jpcoar:degreeGrantor.jpcoar:degreeGrantorName", "Degree Grantor.学位授与機関名.言語": "jpcoar:degreeGrantor.jpcoar:degreeGrantorName.language", "Degree Grantor.学位授与機関名.学位授与機関名": "jpcoar:degreeGrantor.jpcoar:degreeGrantorName.value", "Degree Grantor.学位授与機関識別子": "jpcoar:degreeGrantor.jpcoar:nameIdentifier", "Degree Grantor.学位授与機関識別子.学位授与機関識別子": "jpcoar:degreeGrantor.jpcoar:nameIdentifier.value", "Degree Grantor.学位授与機関識別子.学位授与機関識別子Scheme": "jpcoar:degreeGrantor.jpcoar:nameIdentifier.nameIdentifierScheme", "Conference": "jpcoar:conference", "Conference.開催国": "jpcoar:conference.jpcoar:conferenceCountry", "Conference.開催期間": "jpcoar:conference.jpcoar:conferenceDate.language", "Conference.開催期間.言語": "jpcoar:conference.jpcoar:conferenceDate", "Conference.開催期間.終了日": "jpcoar:conference.jpcoar:conferenceDate.endDay", "Conference.開催期間.終了月": "jpcoar:conference.jpcoar:conferenceDate.endMonth", "Conference.開催期間.終了年": "jpcoar:conference.jpcoar:conferenceDate.endYear", "Conference.開催期間.開催期間": "jpcoar:conference.jpcoar:conferenceDate.value", "Conference.開催期間.開始日": "jpcoar:conference.jpcoar:conferenceDate.startDay", "Conference.開催期間.開始月": "jpcoar:conference.jpcoar:conferenceDate.startMonth", "Conference.開催期間.開始年": "jpcoar:conference.jpcoar:conferenceDate.startYear", "Conference.会議名": "jpcoar:conference.jpcoar:conferenceName", "Conference.会議名.会議名": "jpcoar:conference.jpcoar:conferenceName.value", "Conference.会議名.言語": "jpcoar:conference.jpcoar:conferenceName.language", "Conference.開催地": "jpcoar:conference.jpcoar:conferencePlace", "Conference.開催地.開催地": "jpcoar:conference.jpcoar:conferencePlace.value", "Conference.開催地.言語": "jpcoar:conference.jpcoar:conferencePlace.language", "Conference.回次": "jpcoar:conference.jpcoar:conferenceSequence", "Conference.主催機関": "jpcoar:conference.jpcoar:conferenceSponsor", "Conference.主催機関.主催機関": "jpcoar:conference.jpcoar:conferenceSponsor.value", "Conference.主催機関.言語": "jpcoar:conference.jpcoar:conferenceSponsor.language", "Conference.開催会場": "jpcoar:conference.jpcoar:conferenceVenue", "Conference.開催会場.開催会場": "jpcoar:conference.jpcoar:conferenceVenue.value", "Conference.開催会場.言語": "jpcoar:conference.jpcoar:conferenceVenue.language", "File": "hasPart", "File.アクセス": "hasPart.dcterms:accessRights", "File.公開日.タイプ": "$Available", "File.公開日.公開日": "hasPart.datePublished", "File.表示形式": "hasPart.jpcoar:format", "File.日付": "hasPart.datacite:date", "File.日付.日付タイプ": "hasPart.datacite:date.dateType", "File.日付.日付": "hasPart.datacite:date.value", "File.ファイル名": "hasPart.name", "File.サイズ": "hasPart.jpcoar:extent", "File.サイズ.サイズ": "hasPart.jpcoar:extent.value", "File.フォーマット": "hasPart.jpcoar:mimeType", "File.グループ": "hasPart.department", "File.ライセンス": "hasPart.license", "File.本文URL": "hasPart.jpcoar:URI", "File.本文URL.ラベル": "hasPart.@id", "File.本文URL.オブジェクトタイプ": "hasPart.jpcoar:URI.objectType", "File.本文URL.本文URL": "hasPart.jpcoar:URI.value", "File.バージョン情報": "hasPart.datacite:version", "Heading": "headline", "Heading.大見出し": "headline.value", "Heading.小見出し": "headline.alternativeHeadline", "Heading.言語": "headline.language", "所蔵機関": "jpcoar:holdingAgent", "所蔵機関.所蔵機関識別子": "jpcoar:holdingAgent.jpcoar:holdingAgentNameIdentifier", "所蔵機関.所蔵機関識別子.所蔵機関識別子スキーマ": "jpcoar:holdingAgent.jpcoar:holdingAgentNameIdentifier.nameIdentifierScheme", "所蔵機関.所蔵機関識別子.所蔵機関識別子URI": "jpcoar:holdingAgent.jpcoar:holdingAgentNameIdentifier.nameIdentifierURI", "所蔵機関.所蔵機関識別子.所蔵機関識別子": "jpcoar:holdingAgent.jpcoar:holdingAgentNameIdentifier.value", "所蔵機関.所蔵機関名": "jpcoar:holdingAgent.jpcoar:holdingAgentName", "所蔵機関.所蔵機関名.所蔵機関名": "jpcoar:holdingAgent.jpcoar:holdingAgentName.value", "所蔵機関.所蔵機関名.Language": "jpcoar:holdingAgent.jpcoar:holdingAgentName.language", "日付（リテラル）": "dcterms:date", "日付（リテラル）.日付（リテラル）": "dcterms:date.value", "日付（リテラル）.言語": "dcterms:date.language", "データセットシリーズ": "jpcoar:datasetSeries", "データセットシリーズ.Dataset Series": "jpcoar:datasetSeries.value", "出版者情報": "jpcoar:publisher", "出版者情報.出版地（国名コード）": "jpcoar:publisher.dcndl:publicationPlace", "出版者情報.出版地（国名コード）.出版地（国名コード）": "jpcoar:publisher.dcndl:publicationPlace.value", "出版者情報.出版者注記": "jpcoar:publisher.jpcoar:publisherDescription", "出版者情報.出版者注記.出版者注記": "jpcoar:publisher.jpcoar:publisherDescription.value", "出版者情報.出版者注記.言語": "jpcoar:publisher.jpcoar:publisherDescription.language", "出版者情報.出版地": "jpcoar:publisher.dcndl:location", "出版者情報.出版地.出版地": "jpcoar:publisher.dcndl:location.value", "出版者情報.出版者名": "jpcoar:publisher.jpcoar:publisherName", "出版者情報.出版者名.出版者名": "jpcoar:publisher.jpcoar:publisherName.value", "出版者情報.出版者名.言語": "jpcoar:publisher.jpcoar:publisherName.language", "大きさ": "dcterms:extent", "大きさ.Extent": "dcterms:extent.value", "大きさ.Language": "dcterms:extent.language", "カタログ": "jpcoar:catalog", "カタログ.Access Rights": "jpcoar:catalog.dcterms:accessRights", "カタログ.Access Rights.Access Rights": "jpcoar:catalog.dcterms:accessRights.value", "カタログ.Access Rights.RDF Resource": "jpcoar:catalog.dcterms:accessRights.rdf:resource", "カタログ.Contributor": "jpcoar:catalog.jpcoar:contributor", "カタログ.Contributor.Contributor Name": "jpcoar:catalog.jpcoar:contributor.jpcoar:contributorName", "カタログ.Contributor.Contributor Name.Contributor Name": "jpcoar:catalog.jpcoar:contributor.jpcoar:contributorName.value", "カタログ.Contributor.Contributor Name.Language": "jpcoar:catalog.jpcoar:contributor.jpcoar:contributorName.language", "カタログ.Contributor.Contributor Type": "jpcoar:catalog.jpcoar:contributor.contributorType", "カタログ.Description": "jpcoar:catalog.datacite:description", "カタログ.Description.Description": "jpcoar:catalog.datacite:description.value", "カタログ.Description.Language": "jpcoar:catalog.datacite:description.language", "カタログ.Description.Description Type": "jpcoar:catalog.datacite:description.descriptionType", "カタログ.File": "jpcoar:catalog.jpcoar:file", "カタログ.File.Object Type": "jpcoar:catalog.jpcoar:file.objectType", "カタログ.File.File URI": "jpcoar:catalog.jpcoar:file.jpcoar:URI", "カタログ.Identifier": "jpcoar:catalog.jpcoar:identifier", "カタログ.Identifier.Identifier": "jpcoar:catalog.jpcoar:identifier.value", "カタログ.Identifier.Identifier Type": "jpcoar:catalog.jpcoar:identifier.identifierType", "カタログ.License": "jpcoar:catalog.jpcoar:license", "カタログ.License.License": "jpcoar:catalog.jpcoar:license.value", "カタログ.License.Language": "jpcoar:catalog.jpcoar:license.language", "カタログ.License.RDF Resource": "jpcoar:catalog.jpcoar:license.rdf:resource", "カタログ.License.License Type": "jpcoar:catalog.jpcoar:license.licenseType", "カタログ.Rights": "jpcoar:catalog.dc:rights", "カタログ.Rights.Language": "jpcoar:catalog.dc:rights.language", "カタログ.Rights.RDF Resource": "jpcoar:catalog.dc:rights.rdf:resource", "カタログ.Rights.Rights": "jpcoar:catalog.dc:rights.value", "カタログ.Subject": "jpcoar:catalog.jpcoar:subject", "カタログ.Subject.Subject": "jpcoar:catalog.jpcoar:subject.value", "カタログ.Subject.Language": "jpcoar:catalog.jpcoar:subject.language", "カタログ.Subject.Subject Scheme": "jpcoar:catalog.jpcoar:subject.subjectScheme", "カタログ.Subject.Subject URI": "jpcoar:catalog.jpcoar:subject.subjectURI", "カタログ.Title": "jpcoar:catalog.dc:title", "カタログ.Title.Title": "jpcoar:catalog.dc:title.value", "カタログ.Title.Language": "jpcoar:catalog.dc:title.language", "原文の言語": "dcndl:originalLanguage", "原文の言語.Original Language": "dcndl:originalLanguage.value", "原文の言語.Language": "dcndl:originalLanguage.language", "部編名": "dcndl:volumeTitle", "部編名.部編名": "dcndl:volumeTitle.value", "部編名.Language": "dcndl:volumeTitle.language", "版": "dcndl:edition", "版.版": "dcndl:edition.value", "版.言語": "dcndl:edition.language", "物理的形態": "jpcoar:format", "物理的形態.物理的形態": "jpcoar:format.value", "物理的形態.Language": "jpcoar:format.language"}' , 30002, 1, false);

-- fix_issue_37736.sql

ALTER TABLE site_info DROP COLUMN addthis_user_id;

-- fix_issue_39700.sql

--VARCHAR型カラムの文字数を変更する
ALTER TABLE admin_lang_settings ALTER COLUMN lang_code TYPE character varying(5);

--「zh」を「zh-cn」に変更する
UPDATE admin_lang_settings SET lang_code = 'zh-cn', lang_name = '中文 (簡体)' WHERE lang_code = 'zh';

--「zh-tw」を追加する
INSERT INTO admin_lang_settings (lang_code, lang_name, is_registered, sequence, is_active)
SELECT 'zh-tw', '中文 (繁体)', 'false', 0, 'true' FROM (SELECT COUNT(*) as count FROM admin_lang_settings WHERE lang_code in ('zh-cn','zh-tw')) c WHERE c.count = 1;

-- 202409_BioResource_ddl.sql

ALTER TABLE resync_indexes ALTER COLUMN saving_format TYPE character varying(20);

-- v1.0.8.sql

ALTER TABLE public.feedback_mail_list ADD COLUMN account_author text;
ALTER TABLE public.index ADD COLUMN is_deleted boolean DEFAULT false;

-- public.authors_prefix_settings.sql

INSERT INTO public.authors_prefix_settings(name, scheme, url, created, updated) VALUES 
('researchmap', 'researchmap', 'https://researchmap.jp/##', TIMESTAMP '2024-01-01 00:00:00.000', TIMESTAMP '2024-01-01 00:00:00.000');

COMMIT;
