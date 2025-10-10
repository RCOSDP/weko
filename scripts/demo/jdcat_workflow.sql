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

ALTER TABLE ONLY public.workflow_workflow DROP CONSTRAINT fk_workflow_workflow_flow_id_workflow_flow_define CASCADE;
ALTER TABLE ONLY public.workflow_flow_define DROP CONSTRAINT fk_workflow_flow_define_flow_user_accounts_user CASCADE;
ALTER TABLE ONLY public.workflow_flow_action_role DROP CONSTRAINT fk_workflow_flow_action_role_flow_action_id_workflow_flow_actio CASCADE;
ALTER TABLE ONLY public.workflow_flow_action_role DROP CONSTRAINT fk_workflow_flow_action_role_action_user_accounts_user CASCADE;
ALTER TABLE ONLY public.workflow_flow_action_role DROP CONSTRAINT fk_workflow_flow_action_role_action_role_accounts_role CASCADE;
ALTER TABLE ONLY public.workflow_flow_action DROP CONSTRAINT fk_workflow_flow_action_flow_id_workflow_flow_define CASCADE;
ALTER TABLE ONLY public.workflow_flow_action DROP CONSTRAINT fk_workflow_flow_action_action_id_workflow_action CASCADE;
ALTER TABLE ONLY public.workflow_activity_action DROP CONSTRAINT fk_workflow_activity_action_action_status_workflow_action_statu CASCADE;
ALTER TABLE ONLY public.workflow_activity_action DROP CONSTRAINT fk_workflow_activity_action_action_id_workflow_action CASCADE;
ALTER TABLE ONLY public.workflow_action_journal DROP CONSTRAINT fk_workflow_action_journal_action_id_workflow_action CASCADE;
ALTER TABLE ONLY public.workflow_action_identifier DROP CONSTRAINT fk_workflow_action_identifier_action_id_workflow_action CASCADE;
ALTER TABLE ONLY public.workflow_action_feedbackmail DROP CONSTRAINT fk_workflow_action_feedbackmail_action_id_workflow_action CASCADE;
DROP INDEX public.ix_workflow_workflow_flows_id CASCADE;
DROP INDEX public.ix_workflow_flow_define_flow_name CASCADE;
DROP INDEX public.ix_workflow_flow_define_flow_id CASCADE;
DROP INDEX public.ix_workflow_flow_action_role_flow_action_id CASCADE;
DROP INDEX public.ix_workflow_flow_action_flow_id CASCADE;
DROP INDEX public.ix_workflow_activity_action_activity_id CASCADE;
DROP INDEX public.ix_workflow_action_journal_activity_id CASCADE;
DROP INDEX public.ix_workflow_action_identifier_activity_id CASCADE;
DROP INDEX public.ix_workflow_action_feedbackmail_activity_id CASCADE;
ALTER TABLE ONLY public.workflow_workflow DROP CONSTRAINT pk_workflow_workflow CASCADE;
ALTER TABLE ONLY public.workflow_flow_define DROP CONSTRAINT pk_workflow_flow_define CASCADE;
ALTER TABLE ONLY public.workflow_flow_action_role DROP CONSTRAINT pk_workflow_flow_action_role CASCADE;
ALTER TABLE ONLY public.workflow_flow_action DROP CONSTRAINT pk_workflow_flow_action CASCADE;
ALTER TABLE ONLY public.workflow_activity_action DROP CONSTRAINT pk_workflow_activity_action CASCADE;
ALTER TABLE ONLY public.workflow_action_journal DROP CONSTRAINT pk_workflow_action_journal CASCADE;
ALTER TABLE ONLY public.workflow_action_identifier DROP CONSTRAINT pk_workflow_action_identifier CASCADE;
ALTER TABLE ONLY public.workflow_action_feedbackmail DROP CONSTRAINT pk_workflow_action_feedbackmail CASCADE;
ALTER TABLE public.workflow_workflow ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_flow_define ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_flow_action_role ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_flow_action ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_activity_action ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_action_journal ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_action_identifier ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.workflow_action_feedbackmail ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.workflow_workflow_id_seq CASCADE;
DROP TABLE public.workflow_workflow CASCADE;
DROP SEQUENCE public.workflow_flow_define_id_seq CASCADE;
DROP TABLE public.workflow_flow_define CASCADE;
DROP SEQUENCE public.workflow_flow_action_role_id_seq CASCADE;
DROP TABLE public.workflow_flow_action_role CASCADE;
DROP SEQUENCE public.workflow_flow_action_id_seq CASCADE;
DROP TABLE public.workflow_flow_action CASCADE;
DROP SEQUENCE public.workflow_activity_action_id_seq CASCADE;
DROP TABLE public.workflow_activity_action CASCADE;
DROP SEQUENCE public.workflow_action_journal_id_seq CASCADE;
DROP TABLE public.workflow_action_journal CASCADE;
DROP SEQUENCE public.workflow_action_identifier_id_seq CASCADE;
DROP TABLE public.workflow_action_identifier CASCADE;
DROP SEQUENCE public.workflow_action_feedbackmail_id_seq CASCADE;
DROP TABLE public.workflow_action_feedbackmail CASCADE;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: workflow_action_feedbackmail; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_action_feedbackmail (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    activity_id character varying(24) NOT NULL,
    action_id integer,
    feedback_maillist jsonb
);


ALTER TABLE public.workflow_action_feedbackmail OWNER TO invenio;

--
-- Name: workflow_action_feedbackmail_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_action_feedbackmail_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_action_feedbackmail_id_seq OWNER TO invenio;

--
-- Name: workflow_action_feedbackmail_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_action_feedbackmail_id_seq OWNED BY public.workflow_action_feedbackmail.id;


--
-- Name: workflow_action_identifier; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_action_identifier (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    activity_id character varying(24) NOT NULL,
    action_id integer,
    action_identifier_select integer,
    action_identifier_jalc_doi character varying(255),
    action_identifier_jalc_cr_doi character varying(255),
    action_identifier_jalc_dc_doi character varying(255),
    action_identifier_ndl_jalc_doi character varying(255)
);


ALTER TABLE public.workflow_action_identifier OWNER TO invenio;

--
-- Name: workflow_action_identifier_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_action_identifier_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_action_identifier_id_seq OWNER TO invenio;

--
-- Name: workflow_action_identifier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_action_identifier_id_seq OWNED BY public.workflow_action_identifier.id;


--
-- Name: workflow_action_journal; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_action_journal (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    activity_id character varying(24) NOT NULL,
    action_id integer,
    action_journal jsonb
);


ALTER TABLE public.workflow_action_journal OWNER TO invenio;

--
-- Name: workflow_action_journal_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_action_journal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_action_journal_id_seq OWNER TO invenio;

--
-- Name: workflow_action_journal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_action_journal_id_seq OWNED BY public.workflow_action_journal.id;


--
-- Name: workflow_activity_action; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_activity_action (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    activity_id character varying(24) NOT NULL,
    action_id integer,
    action_status character varying(1) NOT NULL,
    action_comment text,
    action_handler integer,
    action_order integer
);


ALTER TABLE public.workflow_activity_action OWNER TO invenio;

--
-- Name: workflow_activity_action_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_activity_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_activity_action_id_seq OWNER TO invenio;

--
-- Name: workflow_activity_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_activity_action_id_seq OWNED BY public.workflow_activity_action.id;


--
-- Name: workflow_flow_action; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_flow_action (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    flow_id uuid NOT NULL,
    action_id integer NOT NULL,
    action_version character varying(64),
    action_order integer NOT NULL,
    action_condition character varying(255),
    action_status character varying(1) NOT NULL,
    action_date timestamp without time zone NOT NULL,
    send_mail_setting jsonb
);


ALTER TABLE public.workflow_flow_action OWNER TO invenio;

--
-- Name: workflow_flow_action_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_flow_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_flow_action_id_seq OWNER TO invenio;

--
-- Name: workflow_flow_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_flow_action_id_seq OWNED BY public.workflow_flow_action.id;


--
-- Name: workflow_flow_action_role; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_flow_action_role (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    flow_action_id integer NOT NULL,
    action_role integer,
    action_role_exclude boolean DEFAULT false NOT NULL,
    action_user integer,
    action_user_exclude boolean DEFAULT false NOT NULL,
    specify_property character varying(255)
);


ALTER TABLE public.workflow_flow_action_role OWNER TO invenio;

--
-- Name: workflow_flow_action_role_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_flow_action_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_flow_action_role_id_seq OWNER TO invenio;

--
-- Name: workflow_flow_action_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_flow_action_role_id_seq OWNED BY public.workflow_flow_action_role.id;


--
-- Name: workflow_flow_define; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_flow_define (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    flow_id uuid NOT NULL,
    flow_name character varying(255),
    flow_user integer,
    flow_status character varying(1) NOT NULL,
    is_deleted boolean NOT NULL,
    flow_type SMALLINT NOT NULL
);


ALTER TABLE public.workflow_flow_define OWNER TO invenio;

--
-- Name: workflow_flow_define_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_flow_define_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_flow_define_id_seq OWNER TO invenio;

--
-- Name: workflow_flow_define_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_flow_define_id_seq OWNED BY public.workflow_flow_define.id;


--
-- Name: workflow_workflow; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_workflow (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    flows_id uuid NOT NULL,
    flows_name character varying(255),
    itemtype_id integer NOT NULL,
    index_tree_id bigint,
    flow_id integer NOT NULL,
    is_deleted boolean NOT NULL,
    open_restricted boolean NOT NULL
);


ALTER TABLE public.workflow_workflow OWNER TO invenio;

--
-- Name: workflow_workflow_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_workflow_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_workflow_id_seq OWNER TO invenio;

--
-- Name: workflow_workflow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_workflow_id_seq OWNED BY public.workflow_workflow.id;


--
-- Name: workflow_action_feedbackmail id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_feedbackmail ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_feedbackmail_id_seq'::regclass);


--
-- Name: workflow_action_identifier id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_identifier ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_identifier_id_seq'::regclass);


--
-- Name: workflow_action_journal id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_journal ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_journal_id_seq'::regclass);


--
-- Name: workflow_activity_action id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity_action ALTER COLUMN id SET DEFAULT nextval('public.workflow_activity_action_id_seq'::regclass);


--
-- Name: workflow_flow_action id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action ALTER COLUMN id SET DEFAULT nextval('public.workflow_flow_action_id_seq'::regclass);


--
-- Name: workflow_flow_action_role id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action_role ALTER COLUMN id SET DEFAULT nextval('public.workflow_flow_action_role_id_seq'::regclass);


--
-- Name: workflow_flow_define id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_define ALTER COLUMN id SET DEFAULT nextval('public.workflow_flow_define_id_seq'::regclass);


--
-- Name: workflow_workflow id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_workflow ALTER COLUMN id SET DEFAULT nextval('public.workflow_workflow_id_seq'::regclass);


--
-- Data for Name: workflow_action_feedbackmail; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_feedbackmail (status, created, updated, id, activity_id, action_id, feedback_maillist) FROM stdin;
\.


--
-- Data for Name: workflow_action_identifier; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_identifier (status, created, updated, id, activity_id, action_id, action_identifier_select, action_identifier_jalc_doi, action_identifier_jalc_cr_doi, action_identifier_jalc_dc_doi, action_identifier_ndl_jalc_doi) FROM stdin;
\.


--
-- Data for Name: workflow_action_journal; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_journal (status, created, updated, id, activity_id, action_id, action_journal) FROM stdin;
\.


--
-- Data for Name: workflow_activity_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_activity_action (status, created, updated, id, activity_id, action_id, action_status, action_comment, action_handler, action_order) FROM stdin;
\.


--
-- Data for Name: workflow_flow_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) FROM stdin;
N	2020-12-06 07:55:09.299439	2020-12-06 07:55:09.299456	1	8256d01f-200e-4f3f-bd85-f40552efad9b	1	1.0.0	1	\N	A	2020-12-06 07:55:09.299467	\N
N	2020-12-06 07:55:43.837413	2020-12-06 07:55:43.837427	3	8256d01f-200e-4f3f-bd85-f40552efad9b	3	1.0.1	2	\N	A	2020-12-06 07:55:43.837437	\N
N	2020-12-06 07:55:43.84151	2020-12-06 07:55:43.841529	4	8256d01f-200e-4f3f-bd85-f40552efad9b	5	1.0.1	3	\N	A	2020-12-06 07:55:43.841537	\N
N	2020-12-06 07:55:43.84538	2020-12-06 07:55:43.845399	5	8256d01f-200e-4f3f-bd85-f40552efad9b	4	2.0.0	4	\N	A	2020-12-06 07:55:43.845406	\N
N	2020-12-06 07:55:43.849682	2020-12-06 07:55:43.8497	6	8256d01f-200e-4f3f-bd85-f40552efad9b	7	1.0.0	5	\N	A	2020-12-06 07:55:43.849723	\N
N	2020-12-06 07:55:09.300486	2020-12-06 07:55:43.851955	2	8256d01f-200e-4f3f-bd85-f40552efad9b	2	1.0.0	6	\N	A	2020-12-06 07:55:09.300507	\N
\.


--
-- Data for Name: workflow_flow_action_role; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_action_role (status, created, updated, id, flow_action_id, action_role, action_role_exclude, action_user, action_user_exclude, specify_property) FROM stdin;
\.


--
-- Data for Name: workflow_flow_define; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_define (status, created, updated, id, flow_id, flow_name, flow_user, flow_status, is_deleted, flow_type) FROM stdin;
N	2020-12-06 07:55:09.297034	2020-12-06 07:55:43.83611	1	8256d01f-200e-4f3f-bd85-f40552efad9b	SimpleFlow	1	A	f   1
\.


--
-- Data for Name: workflow_workflow; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_workflow (status, created, updated, id, flows_id, flows_name, itemtype_id, index_tree_id, flow_id, is_deleted, open_restricted) FROM stdin;
N	2021-04-21 23:09:00.867408	2021-04-21 23:09:00.867417	1	9ff224f4-590f-4f7b-8adf-3af9c1f42d51	wf	22	\N	1	f	f
\.


--
-- Name: workflow_action_feedbackmail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_feedbackmail_id_seq', 1, false);


--
-- Name: workflow_action_identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_identifier_id_seq', 1, false);


--
-- Name: workflow_action_journal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_journal_id_seq', 1, false);


--
-- Name: workflow_activity_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_activity_action_id_seq', 1, false);


--
-- Name: workflow_flow_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_flow_action_id_seq', 6, true);


--
-- Name: workflow_flow_action_role_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_flow_action_role_id_seq', 1, false);


--
-- Name: workflow_flow_define_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_flow_define_id_seq', 1, true);


--
-- Name: workflow_workflow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_workflow_id_seq', 1, true);


--
-- Name: workflow_action_feedbackmail pk_workflow_action_feedbackmail; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_feedbackmail
    ADD CONSTRAINT pk_workflow_action_feedbackmail PRIMARY KEY (id);


--
-- Name: workflow_action_identifier pk_workflow_action_identifier; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_identifier
    ADD CONSTRAINT pk_workflow_action_identifier PRIMARY KEY (id);


--
-- Name: workflow_action_journal pk_workflow_action_journal; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_journal
    ADD CONSTRAINT pk_workflow_action_journal PRIMARY KEY (id);


--
-- Name: workflow_activity_action pk_workflow_activity_action; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity_action
    ADD CONSTRAINT pk_workflow_activity_action PRIMARY KEY (id);


--
-- Name: workflow_flow_action pk_workflow_flow_action; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action
    ADD CONSTRAINT pk_workflow_flow_action PRIMARY KEY (id);


--
-- Name: workflow_flow_action_role pk_workflow_flow_action_role; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action_role
    ADD CONSTRAINT pk_workflow_flow_action_role PRIMARY KEY (id);


--
-- Name: workflow_flow_define pk_workflow_flow_define; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_define
    ADD CONSTRAINT pk_workflow_flow_define PRIMARY KEY (id);


--
-- Name: workflow_workflow pk_workflow_workflow; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_workflow
    ADD CONSTRAINT pk_workflow_workflow PRIMARY KEY (id);


--
-- Name: ix_workflow_action_feedbackmail_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_action_feedbackmail_activity_id ON public.workflow_action_feedbackmail USING btree (activity_id);


--
-- Name: ix_workflow_action_identifier_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_action_identifier_activity_id ON public.workflow_action_identifier USING btree (activity_id);


--
-- Name: ix_workflow_action_journal_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_action_journal_activity_id ON public.workflow_action_journal USING btree (activity_id);


--
-- Name: ix_workflow_activity_action_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_activity_action_activity_id ON public.workflow_activity_action USING btree (activity_id);


--
-- Name: ix_workflow_flow_action_flow_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_flow_action_flow_id ON public.workflow_flow_action USING btree (flow_id);


--
-- Name: ix_workflow_flow_action_role_flow_action_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_flow_action_role_flow_action_id ON public.workflow_flow_action_role USING btree (flow_action_id);


--
-- Name: ix_workflow_flow_define_flow_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE UNIQUE INDEX ix_workflow_flow_define_flow_id ON public.workflow_flow_define USING btree (flow_id);


--
-- Name: ix_workflow_flow_define_flow_name; Type: INDEX; Schema: public; Owner: invenio
--

CREATE UNIQUE INDEX ix_workflow_flow_define_flow_name ON public.workflow_flow_define USING btree (flow_name);


--
-- Name: ix_workflow_workflow_flows_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE UNIQUE INDEX ix_workflow_workflow_flows_id ON public.workflow_workflow USING btree (flows_id);


--
-- Name: workflow_action_feedbackmail fk_workflow_action_feedbackmail_action_id_workflow_action; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_feedbackmail
    ADD CONSTRAINT fk_workflow_action_feedbackmail_action_id_workflow_action FOREIGN KEY (action_id) REFERENCES public.workflow_action(id);


--
-- Name: workflow_action_identifier fk_workflow_action_identifier_action_id_workflow_action; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_identifier
    ADD CONSTRAINT fk_workflow_action_identifier_action_id_workflow_action FOREIGN KEY (action_id) REFERENCES public.workflow_action(id);


--
-- Name: workflow_action_journal fk_workflow_action_journal_action_id_workflow_action; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_journal
    ADD CONSTRAINT fk_workflow_action_journal_action_id_workflow_action FOREIGN KEY (action_id) REFERENCES public.workflow_action(id);


--
-- Name: workflow_activity_action fk_workflow_activity_action_action_id_workflow_action; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity_action
    ADD CONSTRAINT fk_workflow_activity_action_action_id_workflow_action FOREIGN KEY (action_id) REFERENCES public.workflow_action(id);


--
-- Name: workflow_activity_action fk_workflow_activity_action_action_status_workflow_action_statu; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity_action
    ADD CONSTRAINT fk_workflow_activity_action_action_status_workflow_action_statu FOREIGN KEY (action_status) REFERENCES public.workflow_action_status(action_status_id);


--
-- Name: workflow_flow_action fk_workflow_flow_action_action_id_workflow_action; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action
    ADD CONSTRAINT fk_workflow_flow_action_action_id_workflow_action FOREIGN KEY (action_id) REFERENCES public.workflow_action(id);


--
-- Name: workflow_flow_action fk_workflow_flow_action_flow_id_workflow_flow_define; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action
    ADD CONSTRAINT fk_workflow_flow_action_flow_id_workflow_flow_define FOREIGN KEY (flow_id) REFERENCES public.workflow_flow_define(flow_id);


--
-- Name: workflow_flow_action_role fk_workflow_flow_action_role_action_role_accounts_role; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action_role
    ADD CONSTRAINT fk_workflow_flow_action_role_action_role_accounts_role FOREIGN KEY (action_role) REFERENCES public.accounts_role(id);


--
-- Name: workflow_flow_action_role fk_workflow_flow_action_role_action_user_accounts_user; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action_role
    ADD CONSTRAINT fk_workflow_flow_action_role_action_user_accounts_user FOREIGN KEY (action_user) REFERENCES public.accounts_user(id);


--
-- Name: workflow_flow_action_role fk_workflow_flow_action_role_flow_action_id_workflow_flow_actio; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_action_role
    ADD CONSTRAINT fk_workflow_flow_action_role_flow_action_id_workflow_flow_actio FOREIGN KEY (flow_action_id) REFERENCES public.workflow_flow_action(id);


--
-- Name: workflow_flow_define fk_workflow_flow_define_flow_user_accounts_user; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_flow_define
    ADD CONSTRAINT fk_workflow_flow_define_flow_user_accounts_user FOREIGN KEY (flow_user) REFERENCES public.accounts_user(id);


--
-- Name: workflow_workflow fk_workflow_workflow_flow_id_workflow_flow_define; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_workflow
    ADD CONSTRAINT fk_workflow_workflow_flow_id_workflow_flow_define FOREIGN KEY (flow_id) REFERENCES public.workflow_flow_define(id);


--
-- PostgreSQL database dump complete
--

