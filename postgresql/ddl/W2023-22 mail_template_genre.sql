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
ALTER TABLE public.mail_templates ADD genre_id int NOT NULL DEFAULT 3;
ALTER TABLE public.mail_templates ADD CONSTRAINT mail_templates_fk FOREIGN KEY (genre_id) REFERENCES public.mail_template_genres(id) ON DELETE RESTRICT ON UPDATE CASCADE;

INSERT INTO public.mail_templates
	(mail_subject, mail_body, default_mail, genre_id)
	VALUES('シークレットURL提供のお知らせ／Notice of providing secret URL','[restricted_university_institution]
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
E-mail：[restricted_site_mail]', true, 1),
('データ利用申請の承認のお願い（ゲストユーザー向け）／Request for Approval of Application for Use  （for guest user）','[advisor_university_institution]
[advisor_fullname]　様

[restricted_site_name_ja]です。
[restricted_university_institution] [restricted_fullname]様から以下のデータの利用申請がありました。

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
E-mail：[restricted_site_mail]',true,3),
('利用申請の審査結果について（ゲストユーザー向け）／The results of the review of your application  （for guest user）','[restricted_university_institution]
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
E-mail：[restricted_site_mail]',true,3),
('利用申請の承認のお知らせ（ゲストユーザー向け）／Guest''s application was approved （for guest user）','[restricted_university_institution]
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
E-mail：[restricted_site_mail]',true,3);

UPDATE public.mail_templates SET genre_id=2 WHERE id = 1;
