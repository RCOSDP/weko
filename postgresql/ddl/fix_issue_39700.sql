--VARCHAR型カラムの文字数を変更する
ALTER TABLE admin_lang_settings ALTER COLUMN lang_code TYPE character varying(10);

--「zh」、「zh-cn」を「zh-Hans」に変更する
UPDATE admin_lang_settings SET lang_code = 'zh_Hans', lang_name = '中文 (簡体)' WHERE lang_code = 'zh' OR lang_code = 'zh-cn';

-- 「zh-tw」を「zh_Hant」に書き換える
UPDATE admin_lang_settings SET lang_code = 'zh_Hant', lang_name = '中文 (繁体)' WHERE lang_code = 'zh-tw';

--「zh-Hant」を追加する
INSERT INTO admin_lang_settings (lang_code, lang_name, is_registered, sequence, is_active)
SELECT 'zh_Hant', '中文 (繁体)', 'false', 0, 'true' FROM (SELECT COUNT(*) as count FROM admin_lang_settings WHERE lang_code in ('zh_Hans','zh_Hant')) c WHERE c.count = 1;