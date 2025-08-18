--VARCHAR型カラムの文字数を変更する
ALTER TABLE admin_lang_settings ALTER COLUMN lang_code TYPE character varying(5);

--「zh」を「zh-cn」に変更する
UPDATE admin_lang_settings SET lang_code = 'zh-cn', lang_name = '中文 (簡体)' WHERE lang_code = 'zh';

--「zh-tw」を追加する
INSERT INTO admin_lang_settings (lang_code, lang_name, is_registered, sequence, is_active)
SELECT 'zh-tw', '中文 (繁体)', 'false', 0, 'true' FROM (SELECT COUNT(*) as count FROM admin_lang_settings WHERE lang_code in ('zh-cn','zh-tw')) c WHERE c.count = 1;