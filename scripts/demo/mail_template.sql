--
-- Delete data Restricted access.
--

truncate public.mail_template_genres;

CREATE TABLE public.mail_template_genres (
	id serial NOT NULL,
	name varchar(255) NOT NULL,
	CONSTRAINT pk_mail_template_genres PRIMARY KEY (id)
);

INSERT INTO public.mail_template_genres
	(id, name)
	VALUES
		(1, 'Notification of secret URL provision'),
		(2, 'Guidance to the application form'),
		(3, 'Others');

truncate public.mail_templates;

ALTER TABLE public.mail_templates ADD genre_id int NOT NULL DEFAULT 3;
ALTER TABLE public.mail_templates ADD CONSTRAINT mail_templates_fk FOREIGN KEY (genre_id) REFERENCES public.mail_template_genres(id) ON DELETE RESTRICT ON UPDATE CASCADE;

--
-- Data for Name: mail_templates; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.mail_templates (id, mail_subject, mail_body, default_mail) FROM stdin;
1	利用申請登録のご案内／Register Application for Use	[restricted_site_name_ja]です。\n下記のリンクにアクセスしていただき、利用申請の登録を行ってください。\n\n[url_guest_user]\n\nこのメールは自動送信されているので返信しないでください。\nお問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nThis is a message from [restricted_site_name_en].\nPlease access the link below and register your Application.\n\n[url_guest_user]\n\nPlease do not reply to this email as it has been sent automatically.\nPlease direct all inquiries to the following address.\nAlso, if you received this message in error, please notify [restricted_site_name_en].\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
2	データ利用申請の受付のお知らせ／Your Application was Received	[restricted_university_institution]\n[restricted_fullname]　様\n\n[restricted_institution_name_ja]です。\n[restricted_site_name_ja]をご利用いただいて、ありがとうございます。\n\n下記の利用申請を受け付けました。\n\n申請番号： [restricted_activity_id]\n登録者名： [restricted_fullname]\nメールアドレス： [restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\n[restricted_institution_name_ja]で審査しますので、結果の連絡をお待ちください。\n\nこのメールは自動送信されているので返信しないでください。\nお問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_institution_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [restricted_fullname],\n\nThis is a message from [restricted_institution_name_en].\nThank you for using [restricted_site_name_en].\n\nWe received the below application:\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nYou will be notified once the application is approved. \n\nPlease do not reply to this email as it has been sent automatically.\nPlease direct all inquiries to the following address.\nAlso, if you received this message in error, please notify [restricted_institution_name_en].\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
3	データ利用申請の承認のお願い（ログインユーザー向け）／Request for Approval of Application for Use （for logged in users）	[advisor_university_institution]\n[advisor_fullname]　様\n\n[restricted_site_name_ja]です。\n[advisor_university_institution] [advisor_fullname]様から以下のデータの利用申請がありました。\n\n申請番号：[restricted_activity_id]\n登録者名：[restricted_fullname]\nメールアドレス：[restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\nご自身のアカウントにログインして、ワークフローより上記の申請内容をご確認ください。\n「承認」または「却下」のボタンをクリックしてください。\n\nこのメールは自動送信されているので返信しないでください。\nこのメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [advisor_fullname],\n\nThis is a message from [restricted_site_name_en].\nWe received the below application from [restricted_university_institution] [restricted_fullname]\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nPlease log in your account and From [Workflow], confirm the above application by clicking on “approve” or “reject”.\n\nPlease do not reply to this email as it has been sent automatically.\nIf you received this message in error, please notify the [restricted_site_name_en]\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
4	利用申請の承認のお知らせ（ログインユーザー向け）／Your application was approved  （for logged in users）	[restricted_university_institution]\n[restricted_fullname]　様\n\nこの度は、[restricted_site_name_ja]をご利用いただきありがとうございます。\n\n下記の利用申請を承認しました。\n\n申請番号：[restricted_activity_id]\n登録者名：[restricted_fullname]\nメールアドレス：[restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\nご申請いただいたコンテンツは、次のページよりダウンロードすることができます。\n\n[landing_url]\n\n上記アドレスより[restricted_site_name_ja]にアクセスいただき、ご登録いただいたアカウントでログインをして下さい。\nログインしていただけますと、ダウンロードボタンより申請いただいたデータをダウンロードすることができます。\n\nダウンロードは[restricted_expiration_date_ja]まで可能です。\nダウンロード期限は[restricted_expiration_date_ja]までなので、期限内に必ず保存してください。\nダウンロード回数が上限を超えたり、ダウンロード期限を過ぎると、再申請が必要になります。\n\n今後とも[restricted_site_name_ja]をよろしくお願いします。\n\nこのメールは自動送信されているので返信しないでください。\nこのメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [restricted_fullname],\n\nThank you for using [restricted_site_name_en].\nYour application below has been approved.\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nThe data can be downloaded from the address below.\n\n[landing_url]\n\nPlease access [restricted_site_name_en] from the above address and login with your registered account.\nIf you logged in, you will be able to download the submitted data from the download button.\n\nPlease do not reply to this email as it has been sent automatically.\nIf you received this message in error, please notify the [restricted_site_name_en]\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
5	利用申請の審査結果について（ログインユーザー向け）／The results of the review of your application  （for logged in users）	[restricted_university_institution]\n[restricted_fullname]　様\n\nこの度は、[restricted_site_name_ja]をご利用いただきありがとうございます。\n申請いただいた内容をもとに、所内で慎重な検討を重ねましたが、今回はコンテンツの提供を見送らせていただくこととなりました。\n\n申請番号： [restricted_activity_id]\n登録者名： [restricted_fullname]\nメールアドレス： [restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\nご申請いただいたにも関わらず、このような返事となり大変申し訳ございません。\n今後とも[restricted_site_name_ja]をよろしくお願いします。\n\nこのメールは自動送信されているので返信しないでください。\nこのメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [restricted_fullname],\n\nThank you for using [restricted_site_name_en].\nBased on the content of your application, after careful consideration within our office,\nwe have decided not to provide the content at this time.\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nWe are very sorry for this reply despite your application.\nThank you for your continued support of [restricted_site_name_en].\n\nPlease do not reply to this email as it has been sent automatically.\nIf you received this message in error, please notify the [restricted_site_name_en]\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
6	利用報告の登録のお願い／Request for register Data Usage Report	[restricted_site_name_ja]です。\n下記で申請いただいたデータについてダウンロードされたことを確認しました。\n\n申請番号： [restricted_usage_activity_id]\n登録者名： [restricted_fullname]\nメールアドレス： [restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\nダウンロードしたデータについて、下記のリンクから利用報告の登録をお願いします。\n\n[usage_report_url]\n\nこのメールは自動送信されているので返信しないでください。\nお問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nThis is a message from [restricted_site_name_en].\nWe have confirmed that the dataset which you registered at below has been downloaded.\n\nApplication No.：[restricted_usage_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nFor the downloaded data, please register the Data Usage Report by the link below.\n\n[usage_report_url]\n\nPlease do not reply to this email as it has been sent automatically.\nPlease direct all inquiries to the following address.\nAlso, if you received this message in error, please notify [restricted_site_name_en].\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]\n	t
7	利用報告の登録のお願い／Request for register Data Usage Report	[restricted_site_name_ja]です。\n現時点で、下記の利用報告が登録されていません\n\n報告番号：[restricted_activity_id]\n登録者名：[restricted_fullname]\nメールアドレス：[restricted_mail_address]\n所属機関：[restricted_university_institution]\n利用データ：[restricted_data_name]\nデータダウンロード日：[data_download_date]\n\n下記のリンクから利用報告の登録をお願いします。\n\n[usage_report_url]\n\nこのメールは自動送信されているので返信しないでください。\nお問い合わせは下記までお願いします。また、このメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nThis is a message from [restricted_site_name_en].\nAt this time, the Data Usage Report below has not been registered.\n\nUsage Report No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nUsage Dataset：[restricted_data_name]\nDownload date：[data_download_date]\n\nPlease register the Data Usage Report from the link below.\n\n[usage_report_url]\n\nPlease do not reply to this email as it has been sent automatically.\nPlease direct all inquiries to the following address.\nAlso, if you received this message in error, please notify [restricted_site_name_en].\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]\n	t
8	データ利用申請の承認のお願い（ゲストユーザー向け）／Request for Approval of Application for Use  （for guest user）	[advisor_university_institution]\n[advisor_fullname]　様\n\n[restricted_site_name_ja]です。\n[advisor_university_institution] [advisor_fullname]様から以下のデータの利用申請がありました。\n\n申請番号：[restricted_activity_id]\n登録者名：[restricted_fullname]\nメールアドレス：[restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\nご自身のアカウントにログインして、ワークフローより上記の申請内容をご確認ください。\n「承認」または「却下」のボタンをクリックしてください。\n\nこのメールは自動送信されているので返信しないでください。\nこのメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [advisor_fullname],\n\nThis is a message from [restricted_site_name_en].\nWe received the below application from [restricted_university_institution] [restricted_fullname]\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nPlease log in your account and From [Workflow], confirm the above application by clicking on “approve” or “reject”.\n\nPlease do not reply to this email as it has been sent automatically.\nIf you received this message in error, please notify the [restricted_site_name_en]\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
9	利用申請の承認のお知らせ（ゲストユーザー向け）／Guest''s application was approved （for guest user）	[restricted_university_institution]\n[restricted_fullname]　様\n\nこの度は、[restricted_site_name_ja]をご利用いただきありがとうございます。\n\n下記の利用申請を承認しました。\n\n申請番号：[restricted_activity_id]\n登録者名：[restricted_fullname]\nメールアドレス：[restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\n申請いただいたコンテンツは、次のリンクアドレスよりダウンロードすることができます。\n\n[restricted_download_link]\n\nリンクアドレスをクリックすると、メールアドレスの入力が必要となります。\n利用申請の際に登録されたメールアドレスを入力頂きますと、申請いただいたコンテンツをダウンロードすることができます。\n\nダウンロードは[restricted_expiration_date_ja]まで可能です。\nダウンロード期限は[restricted_expiration_date_ja]までなので、期限内に必ず保存してください。\nダウンロード回数が上限を超えたり、ダウンロード期限を過ぎると、再申請が必要になります。\n\n今後とも[restricted_site_name_ja]をよろしくお願いします。\n\nこのメールは自動送信されているので返信しないでください。\nこのメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [restricted_fullname]\n\nThank you for using [restricted_site_name_en].\nYour application below has been approved.\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nThe data can be downloaded from the address below.\n\n[restricted_download_link]\n\nIf you click the address, you will be required to enter your email address.\nYou can download the content you have applied for by entering the email address you registered when applying for use.\n\nPlease do not reply to this email as it has been sent automatically.\nIf you received this message in error, please notify the [restricted_site_name_en]\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
10	利用申請の審査結果について（ゲストユーザー向け）／The results of the review of your application  （for guest user）	[restricted_university_institution]\n[restricted_fullname]　様\n\nこの度は、[restricted_site_name_ja]をご利用いただきありがとうございます。\n申請いただいた内容をもとに、所内で慎重な検討を重ねましたが、今回はコンテンツの提供を見送らせていただくこととなりました。\n\n申請番号： [restricted_activity_id]\n登録者名： [restricted_fullname]\nメールアドレス： [restricted_mail_address]\n所属機関：[restricted_university_institution]\n研究題目：[restricted_research_title]\n申請データ：[restricted_data_name]\n申請年月日：[restricted_application_date]\n\nご申請いただいたにも関わらず、このような返事となり大変申し訳ございません。\n今後とも[restricted_site_name_ja]をよろしくお願いします。\n\nこのメールは自動送信されているので返信しないでください。\nこのメールに心当たりのない方は、[restricted_site_name_ja]までご連絡ください。\n\n[restricted_site_name_ja]：[restricted_site_url]\n問い合わせ窓口：[restricted_site_mail]\n\n----------------------------------------------------------------------------------\n\nDear [restricted_fullname],\n\nThank you for using [restricted_site_name_en].\nBased on the content of your application, after careful consideration within our office,\nwe have decided not to provide the content at this time.\n\nApplication No.：[restricted_activity_id]\nName：[restricted_fullname]\nE-mail：[restricted_mail_address]\nAffiliation：[restricted_university_institution]\nTitle of research：[restricted_research_title]\nDataset requested ：[restricted_data_name]\nApplication date：[restricted_application_date]\n\nWe are very sorry for this reply despite your application.\nThank you for your continued support of [restricted_site_name_en].\n\nPlease do not reply to this email as it has been sent automatically.\nIf you received this message in error, please notify the [restricted_site_name_en]\n\n[restricted_site_name_en]：[restricted_site_url]\nE-mail：[restricted_site_mail]	t
\.

INSERT INTO public.mail_templates
	(id, mail_subject, mail_body, default_mail, genre_id)
	VALUES(11,'シークレットURL提供のお知らせ／Notice of providing secret URL','[restricted_university_institution]
[restricted_fullname]様

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
E-mail：[restricted_site_mail]', true, 1);
UPDATE public.mail_templates SET genre_id=2 WHERE id = 1;

--
-- Name: mail_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.mail_templates_id_seq', 11, true);


--
-- PostgreSQL database dump complete
--

