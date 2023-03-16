insert into
    admin_settings (id, name, settings)
values
    (
        (select max(id) + 1 from admin_settings),
        'ums_management_url',
        '{"url":""}'
    );
