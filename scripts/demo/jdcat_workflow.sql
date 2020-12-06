--
-- PostgreSQL database dump
--

-- Dumped from database version 12.4 (Debian 12.4-1.pgdg100+1)
-- Dumped by pg_dump version 12.4 (Debian 12.4-1.pgdg100+1)

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

ALTER TABLE IF EXISTS ONLY public.workflow_workflow DROP CONSTRAINT IF EXISTS fk_workflow_workflow_flow_id_workflow_flow_define;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_define DROP CONSTRAINT IF EXISTS fk_workflow_flow_define_flow_user_accounts_user;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action_role DROP CONSTRAINT IF EXISTS fk_workflow_flow_action_role_flow_action_id_workflow_flow_actio;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action_role DROP CONSTRAINT IF EXISTS fk_workflow_flow_action_role_action_user_accounts_user;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action_role DROP CONSTRAINT IF EXISTS fk_workflow_flow_action_role_action_role_accounts_role;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action DROP CONSTRAINT IF EXISTS fk_workflow_flow_action_flow_id_workflow_flow_define;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action DROP CONSTRAINT IF EXISTS fk_workflow_flow_action_action_id_workflow_action;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS fk_workflow_activity_workflow_id_workflow_workflow;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS fk_workflow_activity_flow_id_workflow_flow_define;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS fk_workflow_activity_activity_update_user_accounts_user;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS fk_workflow_activity_activity_login_user_accounts_user;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS fk_workflow_activity_action_status_workflow_action_status;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS fk_workflow_activity_action_id_workflow_action;
ALTER TABLE IF EXISTS ONLY public.workflow_activity_action DROP CONSTRAINT IF EXISTS fk_workflow_activity_action_action_status_workflow_action_statu;
ALTER TABLE IF EXISTS ONLY public.workflow_activity_action DROP CONSTRAINT IF EXISTS fk_workflow_activity_action_action_id_workflow_action;
ALTER TABLE IF EXISTS ONLY public.workflow_action_journal DROP CONSTRAINT IF EXISTS fk_workflow_action_journal_action_id_workflow_action;
ALTER TABLE IF EXISTS ONLY public.workflow_action_identifier DROP CONSTRAINT IF EXISTS fk_workflow_action_identifier_action_id_workflow_action;
ALTER TABLE IF EXISTS ONLY public.workflow_action_history DROP CONSTRAINT IF EXISTS fk_workflow_action_history_action_user_accounts_user;
ALTER TABLE IF EXISTS ONLY public.workflow_action_history DROP CONSTRAINT IF EXISTS fk_workflow_action_history_action_status_workflow_action_status;
ALTER TABLE IF EXISTS ONLY public.workflow_action_feedbackmail DROP CONSTRAINT IF EXISTS fk_workflow_action_feedbackmail_action_id_workflow_action;
DROP INDEX IF EXISTS public.ix_workflow_workflow_flows_id;
DROP INDEX IF EXISTS public.ix_workflow_flow_define_flow_name;
DROP INDEX IF EXISTS public.ix_workflow_flow_define_flow_id;
DROP INDEX IF EXISTS public.ix_workflow_flow_action_role_flow_action_id;
DROP INDEX IF EXISTS public.ix_workflow_flow_action_flow_id;
DROP INDEX IF EXISTS public.ix_workflow_activity_item_id;
DROP INDEX IF EXISTS public.ix_workflow_activity_activity_id;
DROP INDEX IF EXISTS public.ix_workflow_activity_action_activity_id;
DROP INDEX IF EXISTS public.ix_workflow_action_status_action_status_id;
DROP INDEX IF EXISTS public.ix_workflow_action_journal_activity_id;
DROP INDEX IF EXISTS public.ix_workflow_action_identifier_activity_id;
DROP INDEX IF EXISTS public.ix_workflow_action_history_activity_id;
DROP INDEX IF EXISTS public.ix_workflow_action_feedbackmail_activity_id;
ALTER TABLE IF EXISTS ONLY public.workflow_workflow DROP CONSTRAINT IF EXISTS pk_workflow_workflow;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_define DROP CONSTRAINT IF EXISTS pk_workflow_flow_define;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action_role DROP CONSTRAINT IF EXISTS pk_workflow_flow_action_role;
ALTER TABLE IF EXISTS ONLY public.workflow_flow_action DROP CONSTRAINT IF EXISTS pk_workflow_flow_action;
ALTER TABLE IF EXISTS ONLY public.workflow_activity_action DROP CONSTRAINT IF EXISTS pk_workflow_activity_action;
ALTER TABLE IF EXISTS ONLY public.workflow_activity DROP CONSTRAINT IF EXISTS pk_workflow_activity;
ALTER TABLE IF EXISTS ONLY public.workflow_action_status DROP CONSTRAINT IF EXISTS pk_workflow_action_status;
ALTER TABLE IF EXISTS ONLY public.workflow_action_journal DROP CONSTRAINT IF EXISTS pk_workflow_action_journal;
ALTER TABLE IF EXISTS ONLY public.workflow_action_identifier DROP CONSTRAINT IF EXISTS pk_workflow_action_identifier;
ALTER TABLE IF EXISTS ONLY public.workflow_action_history DROP CONSTRAINT IF EXISTS pk_workflow_action_history;
ALTER TABLE IF EXISTS ONLY public.workflow_action_feedbackmail DROP CONSTRAINT IF EXISTS pk_workflow_action_feedbackmail;
ALTER TABLE IF EXISTS ONLY public.workflow_action DROP CONSTRAINT IF EXISTS pk_workflow_action;
ALTER TABLE IF EXISTS public.workflow_workflow ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_flow_define ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_flow_action_role ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_flow_action ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_activity_action ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_activity ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_action_status ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_action_journal ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_action_identifier ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_action_history ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_action_feedbackmail ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workflow_action ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.workflow_workflow_id_seq;
DROP TABLE IF EXISTS public.workflow_workflow;
DROP SEQUENCE IF EXISTS public.workflow_flow_define_id_seq;
DROP TABLE IF EXISTS public.workflow_flow_define;
DROP SEQUENCE IF EXISTS public.workflow_flow_action_role_id_seq;
DROP TABLE IF EXISTS public.workflow_flow_action_role;
DROP SEQUENCE IF EXISTS public.workflow_flow_action_id_seq;
DROP TABLE IF EXISTS public.workflow_flow_action;
DROP SEQUENCE IF EXISTS public.workflow_activity_id_seq;
DROP SEQUENCE IF EXISTS public.workflow_activity_action_id_seq;
DROP TABLE IF EXISTS public.workflow_activity_action;
DROP TABLE IF EXISTS public.workflow_activity;
DROP SEQUENCE IF EXISTS public.workflow_action_status_id_seq;
DROP TABLE IF EXISTS public.workflow_action_status;
DROP SEQUENCE IF EXISTS public.workflow_action_journal_id_seq;
DROP TABLE IF EXISTS public.workflow_action_journal;
DROP SEQUENCE IF EXISTS public.workflow_action_identifier_id_seq;
DROP TABLE IF EXISTS public.workflow_action_identifier;
DROP SEQUENCE IF EXISTS public.workflow_action_id_seq;
DROP SEQUENCE IF EXISTS public.workflow_action_history_id_seq;
DROP TABLE IF EXISTS public.workflow_action_history;
DROP SEQUENCE IF EXISTS public.workflow_action_feedbackmail_id_seq;
DROP TABLE IF EXISTS public.workflow_action_feedbackmail;
DROP TABLE IF EXISTS public.workflow_action;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: workflow_action; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_action (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    action_name character varying(255),
    action_desc text,
    action_endpoint character varying(24),
    action_version character varying(64),
    action_makedate timestamp without time zone NOT NULL,
    action_lastdate timestamp without time zone NOT NULL,
    action_is_need_agree boolean
);


ALTER TABLE public.workflow_action OWNER TO invenio;

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
-- Name: workflow_action_history; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_action_history (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    activity_id character varying(24) NOT NULL,
    action_id integer NOT NULL,
    action_version character varying(24),
    action_status character varying(1),
    action_user integer,
    action_date timestamp without time zone NOT NULL,
    action_comment text
);


ALTER TABLE public.workflow_action_history OWNER TO invenio;

--
-- Name: workflow_action_history_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_action_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_action_history_id_seq OWNER TO invenio;

--
-- Name: workflow_action_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_action_history_id_seq OWNED BY public.workflow_action_history.id;


--
-- Name: workflow_action_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_action_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_action_id_seq OWNER TO invenio;

--
-- Name: workflow_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_action_id_seq OWNED BY public.workflow_action.id;


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
-- Name: workflow_action_status; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_action_status (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    action_status_id character varying(1) NOT NULL,
    action_status_name character varying(32),
    action_status_desc text,
    action_scopes character varying(64),
    action_displays text
);


ALTER TABLE public.workflow_action_status OWNER TO invenio;

--
-- Name: workflow_action_status_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_action_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_action_status_id_seq OWNER TO invenio;

--
-- Name: workflow_action_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_action_status_id_seq OWNED BY public.workflow_action_status.id;


--
-- Name: workflow_activity; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.workflow_activity (
    status character varying(1) NOT NULL,
    created timestamp without time zone NOT NULL,
    updated timestamp without time zone NOT NULL,
    id integer NOT NULL,
    activity_id character varying(24) NOT NULL,
    activity_name character varying(255),
    item_id uuid,
    workflow_id integer NOT NULL,
    workflow_status integer,
    flow_id integer,
    action_id integer,
    action_status character varying(1),
    activity_login_user integer,
    activity_update_user integer,
    activity_status character varying(1),
    activity_start timestamp without time zone NOT NULL,
    activity_end timestamp without time zone,
    activity_community_id text,
    activity_confirm_term_of_use boolean,
    title text,
    shared_user_id integer
);


ALTER TABLE public.workflow_activity OWNER TO invenio;

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
    action_handler integer
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
-- Name: workflow_activity_id_seq; Type: SEQUENCE; Schema: public; Owner: invenio
--

CREATE SEQUENCE public.workflow_activity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workflow_activity_id_seq OWNER TO invenio;

--
-- Name: workflow_activity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: invenio
--

ALTER SEQUENCE public.workflow_activity_id_seq OWNED BY public.workflow_activity.id;


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
    action_date timestamp without time zone NOT NULL
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
    action_user_exclude boolean DEFAULT false NOT NULL
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
    is_deleted boolean NOT NULL
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
    is_deleted boolean NOT NULL
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
-- Name: workflow_action id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_id_seq'::regclass);


--
-- Name: workflow_action_feedbackmail id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_feedbackmail ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_feedbackmail_id_seq'::regclass);


--
-- Name: workflow_action_history id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_history ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_history_id_seq'::regclass);


--
-- Name: workflow_action_identifier id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_identifier ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_identifier_id_seq'::regclass);


--
-- Name: workflow_action_journal id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_journal ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_journal_id_seq'::regclass);


--
-- Name: workflow_action_status id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_status ALTER COLUMN id SET DEFAULT nextval('public.workflow_action_status_id_seq'::regclass);


--
-- Name: workflow_activity id; Type: DEFAULT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity ALTER COLUMN id SET DEFAULT nextval('public.workflow_activity_id_seq'::regclass);


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
-- Data for Name: workflow_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action (status, created, updated, id, action_name, action_desc, action_endpoint, action_version, action_makedate, action_lastdate, action_is_need_agree) FROM stdin;
N	2020-12-06 07:35:11.049248	2020-12-06 07:35:11.049262	1	Start	Indicates that the action has started.	begin_action	1.0.0	2018-05-15 00:00:00	2018-05-15 00:00:00	f
N	2020-12-06 07:35:11.049269	2020-12-06 07:35:11.049274	2	End	Indicates that the action has been completed.	end_action	1.0.0	2018-05-15 00:00:00	2018-05-15 00:00:00	f
N	2020-12-06 07:35:11.049279	2020-12-06 07:35:11.049284	3	Item Registration	Registering items.	item_login	1.0.1	2018-05-22 00:00:00	2018-05-22 00:00:00	f
N	2020-12-06 07:35:11.04929	2020-12-06 07:35:11.049294	4	Approval	Approval action for approval requested items.	approval	2.0.0	2018-02-11 00:00:00	2018-02-11 00:00:00	f
N	2020-12-06 07:35:11.0493	2020-12-06 07:35:11.049304	5	Item Link	Plug-in for link items.	item_link	1.0.1	2018-05-22 00:00:00	2018-05-22 00:00:00	f
N	2020-12-06 07:35:11.04931	2020-12-06 07:35:11.049314	6	OA Policy Confirmation	Action for OA Policy confirmation.	oa_policy	1.0.0	2019-03-15 00:00:00	2019-03-15 00:00:00	f
N	2020-12-06 07:35:11.04932	2020-12-06 07:35:11.049324	7	Identifier Grant	Select DOI issuing organization and CNRI.	identifier_grant	1.0.0	2019-03-15 00:00:00	2019-03-15 00:00:00	f
\.


--
-- Data for Name: workflow_action_feedbackmail; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_feedbackmail (status, created, updated, id, activity_id, action_id, feedback_maillist) FROM stdin;
\.


--
-- Data for Name: workflow_action_history; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_history (status, created, updated, id, activity_id, action_id, action_version, action_status, action_user, action_date, action_comment) FROM stdin;
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
-- Data for Name: workflow_action_status; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_status (status, created, updated, id, action_status_id, action_status_name, action_status_desc, action_scopes, action_displays) FROM stdin;
N	2020-12-06 07:35:11.04615	2020-12-06 07:35:11.046167	1	B	action_begin	Indicates that the action has started.	sys	
N	2020-12-06 07:35:11.046174	2020-12-06 07:35:11.046179	2	F	action_done	Indicates that the action has been completed.	sys,user	Complete
N	2020-12-06 07:35:11.046184	2020-12-06 07:35:11.046189	3	P	action_not_done	Indicates that the flow is suspended and                    no subsequent action is performed.	user	Suspend
N	2020-12-06 07:35:11.046194	2020-12-06 07:35:11.046199	4	R	action_retry	Indicates that redo the workflow.                    (from start action)	user	Redo
N	2020-12-06 07:35:11.046204	2020-12-06 07:35:11.046208	5	M	action_doing	Indicates that the action is not                     completed.(There are following actions)	user	Doing
N	2020-12-06 07:35:11.046213	2020-12-06 07:35:11.046218	6	T	action_thrown_out	Indicates that the action has been rejected.	user	Reject
N	2020-12-06 07:35:11.046223	2020-12-06 07:35:11.046228	7	S	action_skipped	Indicates that the action has been skipped.	user	Skip
N	2020-12-06 07:35:11.046233	2020-12-06 07:35:11.046238	8	E	action_error	Indicates that the action has been errored.	user	Error
N	2020-12-06 07:35:11.046243	2020-12-06 07:35:11.046247	9	C	action_canceled	Indicates that the action has been canceled.	user	Cancel
\.


--
-- Data for Name: workflow_activity; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_activity (status, created, updated, id, activity_id, activity_name, item_id, workflow_id, workflow_status, flow_id, action_id, action_status, activity_login_user, activity_update_user, activity_status, activity_start, activity_end, activity_community_id, activity_confirm_term_of_use, title, shared_user_id) FROM stdin;
\.


--
-- Data for Name: workflow_activity_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_activity_action (status, created, updated, id, activity_id, action_id, action_status, action_comment, action_handler) FROM stdin;
\.


--
-- Data for Name: workflow_flow_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date) FROM stdin;
N	2020-12-06 07:55:09.299439	2020-12-06 07:55:09.299456	1	8256d01f-200e-4f3f-bd85-f40552efad9b	1	1.0.0	1	\N	A	2020-12-06 07:55:09.299467
N	2020-12-06 07:55:43.837413	2020-12-06 07:55:43.837427	3	8256d01f-200e-4f3f-bd85-f40552efad9b	3	1.0.1	2	\N	A	2020-12-06 07:55:43.837437
N	2020-12-06 07:55:43.84151	2020-12-06 07:55:43.841529	4	8256d01f-200e-4f3f-bd85-f40552efad9b	5	1.0.1	3	\N	A	2020-12-06 07:55:43.841537
N	2020-12-06 07:55:43.84538	2020-12-06 07:55:43.845399	5	8256d01f-200e-4f3f-bd85-f40552efad9b	4	2.0.0	4	\N	A	2020-12-06 07:55:43.845406
N	2020-12-06 07:55:43.849682	2020-12-06 07:55:43.8497	6	8256d01f-200e-4f3f-bd85-f40552efad9b	7	1.0.0	5	\N	A	2020-12-06 07:55:43.849723
N	2020-12-06 07:55:09.300486	2020-12-06 07:55:43.851955	2	8256d01f-200e-4f3f-bd85-f40552efad9b	2	1.0.0	6	\N	A	2020-12-06 07:55:09.300507
\.


--
-- Data for Name: workflow_flow_action_role; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_action_role (status, created, updated, id, flow_action_id, action_role, action_role_exclude, action_user, action_user_exclude) FROM stdin;
\.


--
-- Data for Name: workflow_flow_define; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_define (status, created, updated, id, flow_id, flow_name, flow_user, flow_status, is_deleted) FROM stdin;
N	2020-12-06 07:55:09.297034	2020-12-06 07:55:43.83611	1	8256d01f-200e-4f3f-bd85-f40552efad9b	SimpleFlow	1	A	f
\.


--
-- Data for Name: workflow_workflow; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_workflow (status, created, updated, id, flows_id, flows_name, itemtype_id, index_tree_id, flow_id, is_deleted) FROM stdin;
N	2020-12-06 07:56:09.568765	2020-12-06 07:56:09.568794	1	0c416588-d664-4c77-b9c2-f01002b149ba	Item Registration	22	\N	1	f
\.


--
-- Name: workflow_action_feedbackmail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_feedbackmail_id_seq', 1, false);


--
-- Name: workflow_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_history_id_seq', 1, false);


--
-- Name: workflow_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_id_seq', 7, true);


--
-- Name: workflow_action_identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_identifier_id_seq', 1, false);


--
-- Name: workflow_action_journal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_journal_id_seq', 1, false);


--
-- Name: workflow_action_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_status_id_seq', 9, true);


--
-- Name: workflow_activity_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_activity_action_id_seq', 1, false);


--
-- Name: workflow_activity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_activity_id_seq', 1, false);


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
-- Name: workflow_action pk_workflow_action; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action
    ADD CONSTRAINT pk_workflow_action PRIMARY KEY (id);


--
-- Name: workflow_action_feedbackmail pk_workflow_action_feedbackmail; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_feedbackmail
    ADD CONSTRAINT pk_workflow_action_feedbackmail PRIMARY KEY (id);


--
-- Name: workflow_action_history pk_workflow_action_history; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_history
    ADD CONSTRAINT pk_workflow_action_history PRIMARY KEY (id);


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
-- Name: workflow_action_status pk_workflow_action_status; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_status
    ADD CONSTRAINT pk_workflow_action_status PRIMARY KEY (id);


--
-- Name: workflow_activity pk_workflow_activity; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT pk_workflow_activity PRIMARY KEY (id);


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
-- Name: ix_workflow_action_history_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_action_history_activity_id ON public.workflow_action_history USING btree (activity_id);


--
-- Name: ix_workflow_action_identifier_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_action_identifier_activity_id ON public.workflow_action_identifier USING btree (activity_id);


--
-- Name: ix_workflow_action_journal_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_action_journal_activity_id ON public.workflow_action_journal USING btree (activity_id);


--
-- Name: ix_workflow_action_status_action_status_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE UNIQUE INDEX ix_workflow_action_status_action_status_id ON public.workflow_action_status USING btree (action_status_id);


--
-- Name: ix_workflow_activity_action_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_activity_action_activity_id ON public.workflow_activity_action USING btree (activity_id);


--
-- Name: ix_workflow_activity_activity_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE UNIQUE INDEX ix_workflow_activity_activity_id ON public.workflow_activity USING btree (activity_id);


--
-- Name: ix_workflow_activity_item_id; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX ix_workflow_activity_item_id ON public.workflow_activity USING btree (item_id);


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
-- Name: workflow_action_history fk_workflow_action_history_action_status_workflow_action_status; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_history
    ADD CONSTRAINT fk_workflow_action_history_action_status_workflow_action_status FOREIGN KEY (action_status) REFERENCES public.workflow_action_status(action_status_id);


--
-- Name: workflow_action_history fk_workflow_action_history_action_user_accounts_user; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_action_history
    ADD CONSTRAINT fk_workflow_action_history_action_user_accounts_user FOREIGN KEY (action_user) REFERENCES public.accounts_user(id);


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
-- Name: workflow_activity fk_workflow_activity_action_id_workflow_action; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT fk_workflow_activity_action_id_workflow_action FOREIGN KEY (action_id) REFERENCES public.workflow_action(id);


--
-- Name: workflow_activity fk_workflow_activity_action_status_workflow_action_status; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT fk_workflow_activity_action_status_workflow_action_status FOREIGN KEY (action_status) REFERENCES public.workflow_action_status(action_status_id);


--
-- Name: workflow_activity fk_workflow_activity_activity_login_user_accounts_user; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT fk_workflow_activity_activity_login_user_accounts_user FOREIGN KEY (activity_login_user) REFERENCES public.accounts_user(id);


--
-- Name: workflow_activity fk_workflow_activity_activity_update_user_accounts_user; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT fk_workflow_activity_activity_update_user_accounts_user FOREIGN KEY (activity_update_user) REFERENCES public.accounts_user(id);


--
-- Name: workflow_activity fk_workflow_activity_flow_id_workflow_flow_define; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT fk_workflow_activity_flow_id_workflow_flow_define FOREIGN KEY (flow_id) REFERENCES public.workflow_flow_define(id);


--
-- Name: workflow_activity fk_workflow_activity_workflow_id_workflow_workflow; Type: FK CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.workflow_activity
    ADD CONSTRAINT fk_workflow_activity_workflow_id_workflow_workflow FOREIGN KEY (workflow_id) REFERENCES public.workflow_workflow(id);


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

