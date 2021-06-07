-- weko#25657
CREATE TABLE public.facet_search_setting (
    id serial NOT NULL,
    name_en varchar(255) NOT NULL,
    name_jp varchar(255) NULL,
    "mapping" varchar(255) NOT NULL,
    aggregations jsonb NULL,
    active bool NULL,
    CONSTRAINT pk_facet_search_setting null
);
