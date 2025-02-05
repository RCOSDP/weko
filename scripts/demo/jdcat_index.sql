--
-- PostgreSQL database dump
--

-- Dumped from database version 12.3 (Debian 12.3-1.pgdg100+1)
-- Dumped by pg_dump version 12.3 (Debian 12.3-1.pgdg100+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE ONLY public.index DROP CONSTRAINT uix_position CASCADE;
ALTER TABLE ONLY public.index DROP CONSTRAINT pk_index CASCADE;
ALTER TABLE public.index ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.index_id_seq CASCADE;
DROP TABLE public.index CASCADE;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: index; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.index (
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id bigint NOT NULL,
    parent bigint NOT NULL,
    "position" integer NOT NULL,
    index_name text,
    index_name_english text NOT NULL,
    index_link_name text,
    index_link_name_english text NOT NULL,
    harvest_spec text,
    index_link_enabled boolean NOT NULL,
    comment text,
    more_check boolean NOT NULL,
    display_no integer NOT NULL,
    harvest_public_state boolean NOT NULL,
    display_format text,
    image_name text NOT NULL,
    public_state boolean NOT NULL,
    public_date timestamp without time zone,
    recursive_public_state boolean,
    rss_status boolean,
    coverpage_state boolean,
    recursive_coverpage_check boolean,
    browsing_role text,
    recursive_browsing_role boolean,
    contribute_role text,
    recursive_contribute_role boolean,
    browsing_group text,
    recursive_browsing_group boolean,
    contribute_group text,
    recursive_contribute_group boolean,
    owner_user_id integer,
    item_custom_sort jsonb,
    biblio_flag boolean DEFAULT false,
    online_issn text DEFAULT ''::text,
    is_deleted boolean DEFAULT false
);


ALTER TABLE public.index OWNER TO invenio;

--
-- Name: index_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.index_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.index_id_seq OWNER TO invenio;

--
-- Name: index_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.index_id_seq OWNED BY public.index.id;


--
-- Name: index id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.index ALTER COLUMN id SET DEFAULT nextval('public.index_id_seq'::regclass);


--
-- Data for Name: index; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.index (created, updated, id, parent, "position", index_name, index_name_english, index_link_name, index_link_name_english, harvest_spec, index_link_enabled, comment, more_check, display_no, harvest_public_state, display_format, image_name, public_state, public_date, recursive_public_state, rss_status, coverpage_state, recursive_coverpage_check, browsing_role, recursive_browsing_role, contribute_role, recursive_contribute_role, browsing_group, recursive_browsing_group, contribute_group, recursive_contribute_group, owner_user_id, item_custom_sort, biblio_flag, online_issn, is_deleted) FROM stdin;
2020-12-06 13:38:50.703059	2020-12-06 13:52:57.159823	1607261930660	0	0	New Index	New Index		New Index		f		f	5	t	1		t	\N	f	f	f	f	3,98,99	t	1,2,3,4,98,99	t		t		t	1	{}	f		f
\.


--
-- Name: index_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.index_id_seq', 1, false);


--
-- Name: index pk_index; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.index
    ADD CONSTRAINT pk_index PRIMARY KEY (id);


--
-- Name: index uix_position; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.index
    ADD CONSTRAINT uix_position UNIQUE (parent, "position");


--
-- PostgreSQL database dump complete
--

