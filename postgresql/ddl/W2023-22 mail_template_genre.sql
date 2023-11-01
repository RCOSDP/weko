CREATE TABLE public.mail_template_genres (
	id serial NOT NULL,
	name varchar(255) NOT NULL,
	CONSTRAINT pk_mail_template_genres PRIMARY KEY (id)
);
ALTER TABLE public.mail_templates ADD genre_id int NOT NULL DEFAULT 3;
ALTER TABLE public.mail_templates ADD CONSTRAINT mail_templates_fk FOREIGN KEY (genre_id) REFERENCES public.mail_template_genres(id) ON DELETE RESTRICT ON UPDATE CASCADE;
INSERT INTO public.mail_template_genres
	(id, name)
	VALUES
		(1, 'Notification of secret URL provision'),
		(2, 'Guidance to the application form'),
		(3, 'Others');
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
E-mail：[restricted_site_mail]', true, 1);
UPDATE public.mail_templates SET genre_id=2 WHERE mail_subject='利用申請登録のご案内／Register Application for Use';
