ALTER TABLE mail_config ADD COLUMN  mail_local_hostname character varying(255) DEFAULT '';
UPDATE authors SET json=(json#>> '{}')::jsonb;
ALTER TABLE shibboleth_user ALTER column shib_eppn TYPE CHARACTER VARYING(2310);

CREATE TABLE public.file_secret_download (
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    file_name character varying(255) NOT NULL,
    user_mail character varying(255) NOT NULL,
    record_id character varying(255) NOT NULL,
    download_count integer NOT NULL,
    expiration_date integer NOT NULL
);

CREATE SEQUENCE public.file_secret_download_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.file_secret_download_id_seq OWNED BY public.file_secret_download.id;
ALTER TABLE ONLY public.file_secret_download ALTER COLUMN id SET DEFAULT nextval('public.file_secret_download_id_seq'::regclass);
ALTER TABLE ONLY public.file_secret_download
    ADD CONSTRAINT pk_file_secret_download PRIMARY KEY (id);
