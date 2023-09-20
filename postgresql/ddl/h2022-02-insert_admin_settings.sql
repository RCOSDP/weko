insert into
    admin_settings (id, name, settings)
values
    (
        (select max(id) + 1 from admin_settings),
        'ums_management_url',
        '{"url":""}'
    );

-- update column type
ALTER TABLE shibboleth_user ALTER COLUMN shib_page_name TYPE text;