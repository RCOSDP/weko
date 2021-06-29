-- weko#25657
create table facet_search_setting
(
    id           serial       not null
        constraint pk_facet_search_setting
            primary key,
    name_en      varchar(255) not null,
    name_jp      varchar(255),
    mapping      varchar(255) not null,
    aggregations jsonb,
    active       boolean
);
