-- 
-- Update admin_settings to disable restricted access features
--

UPDATE admin_settings
SET
    settings = jsonb_set(
        jsonb_set(
            jsonb_set(
                jsonb_set(
                    jsonb_set(
                        jsonb_set(
                            admin_settings.settings
                            , '{password_enable}'
                            , 'false'::jsonb
                        )
                        , '{item_application, item_application_enable}'
                        , 'false'::jsonb
                    )
                    , '{display_request_form}'
                    , 'false'::jsonb
                )
                , '{secret_URL_file_download, secret_enable}'
                , 'false'::jsonb
            )
            , '{edit_mail_templates_enable}'
            , 'false'::jsonb
        )
        , '{preview_workflow_approval_enable}'
        , 'false'::jsonb
    )
WHERE name = 'restricted_access';