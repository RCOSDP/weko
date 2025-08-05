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
DROP TABLE IF EXISTS public.workflow_workflow CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_flow_define_id_seq;
DROP TABLE IF EXISTS public.workflow_flow_define CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_flow_action_role_id_seq;
DROP TABLE IF EXISTS public.workflow_flow_action_role CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_flow_action_id_seq;
DROP TABLE IF EXISTS public.workflow_flow_action CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_activity_id_seq;
DROP SEQUENCE IF EXISTS public.workflow_activity_action_id_seq;
DROP TABLE IF EXISTS public.workflow_activity_action CASCADE;
DROP TABLE IF EXISTS public.workflow_activity CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_action_status_id_seq;
DROP TABLE IF EXISTS public.workflow_action_status CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_action_journal_id_seq;
DROP TABLE IF EXISTS public.workflow_action_journal CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_action_identifier_id_seq;
DROP TABLE IF EXISTS public.workflow_action_identifier CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_action_id_seq;
DROP SEQUENCE IF EXISTS public.workflow_action_history_id_seq;
DROP TABLE IF EXISTS public.workflow_action_history CASCADE;
DROP SEQUENCE IF EXISTS public.workflow_action_feedbackmail_id_seq;
DROP TABLE IF EXISTS public.workflow_action_feedbackmail CASCADE;
DROP TABLE IF EXISTS public.workflow_action CASCADE;
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
    shared_user_ids jsonb
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
N	2020-12-10 16:56:44.691937	2020-12-10 16:56:44.691949	1	Start	Indicates that the action has started.	begin_action	1.0.0	2018-05-15 00:00:00	2018-05-15 00:00:00	f
N	2020-12-10 16:56:44.691956	2020-12-10 16:56:44.691961	2	End	Indicates that the action has been completed.	end_action	1.0.0	2018-05-15 00:00:00	2018-05-15 00:00:00	f
N	2020-12-10 16:56:44.691966	2020-12-10 16:56:44.69197	3	Item Registration	Registering items.	item_login	1.0.1	2018-05-22 00:00:00	2018-05-22 00:00:00	f
N	2020-12-10 16:56:44.691975	2020-12-10 16:56:44.69198	4	Approval	Approval action for approval requested items.	approval	2.0.0	2018-02-11 00:00:00	2018-02-11 00:00:00	f
N	2020-12-10 16:56:44.691984	2020-12-10 16:56:44.691989	5	Item Link	Plug-in for link items.	item_link	1.0.1	2018-05-22 00:00:00	2018-05-22 00:00:00	f
N	2020-12-10 16:56:44.691994	2020-12-10 16:56:44.691998	6	OA Policy Confirmation	Action for OA Policy confirmation.	oa_policy	1.0.0	2019-03-15 00:00:00	2019-03-15 00:00:00	f
N	2020-12-10 16:56:44.692003	2020-12-10 16:56:44.692007	7	Identifier Grant	Select DOI issuing organization and CNRI.	identifier_grant	1.0.0	2019-03-15 00:00:00	2019-03-15 00:00:00	f
\.


--
-- Data for Name: workflow_action_feedbackmail; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_feedbackmail (status, created, updated, id, activity_id, action_id, feedback_maillist) FROM stdin;
N	2020-12-10 17:40:26.966435	2020-12-10 17:40:26.966461	1	A-20201210-00002	3	[]
N	2020-12-10 17:45:02.560029	2020-12-10 17:45:02.560058	2	A-20201210-00003	3	[]
N	2020-12-10 17:48:47.529917	2020-12-10 17:48:47.529943	3	A-20201210-00004	3	[]
N	2020-12-10 17:55:17.768965	2020-12-10 17:55:17.76899	4	A-20201210-00005	3	[]
\.


--
-- Data for Name: workflow_action_history; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_history (status, created, updated, id, activity_id, action_id, action_version, action_status, action_user, action_date, action_comment) FROM stdin;
N	2020-12-10 17:38:46.076677	2020-12-10 17:38:46.076694	1	A-20201210-00001	1	1.0.0	F	1	2020-12-10 17:38:46.05512	Begin Action
N	2020-12-10 17:40:15.53635	2020-12-10 17:40:15.536373	2	A-20201210-00002	1	1.0.0	F	1	2020-12-10 17:40:15.514158	Begin Action
N	2020-12-10 17:40:33.042639	2020-12-10 17:40:33.042656	3	A-20201210-00002	3	1.0.1	M	1	2020-12-10 17:40:33.03942	
N	2020-12-10 17:40:36.083361	2020-12-10 17:40:36.083384	4	A-20201210-00002	3	1.0.1	F	1	2020-12-10 17:40:36.077838	
N	2020-12-10 17:40:39.820562	2020-12-10 17:40:39.820586	5	A-20201210-00002	5	1.0.1	F	1	2020-12-10 17:40:39.81334	
N	2020-12-10 17:40:43.950896	2020-12-10 17:40:43.95092	6	A-20201210-00002	4	2.0.0	F	1	2020-12-10 17:40:43.944601	\N
N	2020-12-10 17:40:46.602268	2020-12-10 17:40:46.602289	7	A-20201210-00002	7	1.0.0	F	1	2020-12-10 17:40:46.596948	
N	2020-12-10 17:40:47.65915	2020-12-10 17:40:47.659168	8	A-20201210-00002	2	1.0.0	F	1	2020-12-10 17:40:47.658613	End Action
N	2020-12-10 17:44:19.607293	2020-12-10 17:44:19.607308	9	A-20201210-00003	1	1.0.0	F	1	2020-12-10 17:44:19.585057	Begin Action
N	2020-12-10 17:45:06.015024	2020-12-10 17:45:06.015038	10	A-20201210-00003	3	1.0.1	M	1	2020-12-10 17:45:06.012619	
N	2020-12-10 17:45:10.000056	2020-12-10 17:45:10.00008	11	A-20201210-00003	3	1.0.1	F	1	2020-12-10 17:45:09.99338	
N	2020-12-10 17:45:13.840873	2020-12-10 17:45:13.840901	12	A-20201210-00003	5	1.0.1	F	1	2020-12-10 17:45:13.832716	
N	2020-12-10 17:45:17.934947	2020-12-10 17:45:17.935012	13	A-20201210-00003	4	2.0.0	F	1	2020-12-10 17:45:17.93004	\N
N	2020-12-10 17:45:21.304294	2020-12-10 17:45:21.304318	14	A-20201210-00003	7	1.0.0	F	1	2020-12-10 17:45:21.297057	
N	2020-12-10 17:45:23.238213	2020-12-10 17:45:23.238228	15	A-20201210-00003	2	1.0.0	F	1	2020-12-10 17:45:23.237671	End Action
N	2020-12-10 17:48:36.502606	2020-12-10 17:48:36.502651	16	A-20201210-00004	1	1.0.0	F	1	2020-12-10 17:48:36.483013	Begin Action
N	2020-12-10 17:48:50.66596	2020-12-10 17:48:50.665974	17	A-20201210-00004	3	1.0.1	M	1	2020-12-10 17:48:50.663886	
N	2020-12-10 17:48:53.481226	2020-12-10 17:48:53.481248	18	A-20201210-00004	3	1.0.1	F	1	2020-12-10 17:48:53.476417	
N	2020-12-10 17:48:56.136933	2020-12-10 17:48:56.13696	19	A-20201210-00004	5	1.0.1	F	1	2020-12-10 17:48:56.131694	
N	2020-12-10 17:48:58.588954	2020-12-10 17:48:58.589002	20	A-20201210-00004	4	2.0.0	F	1	2020-12-10 17:48:58.583791	\N
N	2020-12-10 17:49:03.095471	2020-12-10 17:49:03.095495	21	A-20201210-00004	7	1.0.0	F	1	2020-12-10 17:49:03.089462	
N	2020-12-10 17:49:05.210484	2020-12-10 17:49:05.210517	22	A-20201210-00004	2	1.0.0	F	1	2020-12-10 17:49:05.209906	End Action
N	2020-12-10 17:55:06.298177	2020-12-10 17:55:06.298201	23	A-20201210-00005	1	1.0.0	F	1	2020-12-10 17:55:06.265358	Begin Action
N	2020-12-10 18:28:41.309251	2020-12-10 18:28:41.309267	24	A-20201210-00005	3	1.0.1	M	1	2020-12-10 18:28:41.307158	
N	2020-12-10 18:28:44.776935	2020-12-10 18:28:44.776961	25	A-20201210-00005	3	1.0.1	F	1	2020-12-10 18:28:44.770992	
N	2020-12-10 18:28:49.643693	2020-12-10 18:28:49.643739	26	A-20201210-00005	5	1.0.1	F	1	2020-12-10 18:28:49.639023	
N	2020-12-10 18:28:54.602642	2020-12-10 18:28:54.602669	27	A-20201210-00005	4	2.0.0	F	1	2020-12-10 18:28:54.59646	\N
N	2020-12-10 18:28:59.113962	2020-12-10 18:28:59.113989	28	A-20201210-00005	7	1.0.0	F	1	2020-12-10 18:28:59.108208	
N	2020-12-10 18:29:00.90041	2020-12-10 18:29:00.900426	29	A-20201210-00005	2	1.0.0	F	1	2020-12-10 18:29:00.899864	End Action
\.


--
-- Data for Name: workflow_action_identifier; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_action_identifier (status, created, updated, id, activity_id, action_id, action_identifier_select, action_identifier_jalc_doi, action_identifier_jalc_cr_doi, action_identifier_jalc_dc_doi, action_identifier_ndl_jalc_doi) FROM stdin;
N	2020-12-10 17:40:46.592835	2020-12-10 17:40:46.592864	1	A-20201210-00002	7	0				
N	2020-12-10 17:44:19.61854	2020-12-10 17:45:21.293208	2	A-20201210-00003	7	0				
N	2020-12-10 17:48:36.518007	2020-12-10 17:49:03.085672	3	A-20201210-00004	7	0				
N	2020-12-10 17:55:06.327778	2020-12-10 18:28:59.104905	4	A-20201210-00005	7	0				
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
N	2020-12-10 16:56:44.689597	2020-12-10 16:56:44.689615	1	B	action_begin	Indicates that the action has started.	sys	
N	2020-12-10 16:56:44.689621	2020-12-10 16:56:44.689626	2	F	action_done	Indicates that the action has been completed.	sys,user	Complete
N	2020-12-10 16:56:44.689631	2020-12-10 16:56:44.689635	3	P	action_not_done	Indicates that the flow is suspended and                    no subsequent action is performed.	user	Suspend
N	2020-12-10 16:56:44.68964	2020-12-10 16:56:44.689645	4	R	action_retry	Indicates that redo the workflow.                    (from start action)	user	Redo
N	2020-12-10 16:56:44.689649	2020-12-10 16:56:44.689654	5	M	action_doing	Indicates that the action is not                     completed.(There are following actions)	user	Doing
N	2020-12-10 16:56:44.689658	2020-12-10 16:56:44.689663	6	T	action_thrown_out	Indicates that the action has been rejected.	user	Reject
N	2020-12-10 16:56:44.689668	2020-12-10 16:56:44.689672	7	S	action_skipped	Indicates that the action has been skipped.	user	Skip
N	2020-12-10 16:56:44.689677	2020-12-10 16:56:44.689681	8	E	action_error	Indicates that the action has been errored.	user	Error
N	2020-12-10 16:56:44.689686	2020-12-10 16:56:44.68969	9	C	action_canceled	Indicates that the action has been canceled.	user	Cancel
\.


--
-- Data for Name: workflow_activity; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_activity (status, created, updated, id, activity_id, activity_name, item_id, workflow_id, workflow_status, flow_id, action_id, action_status, activity_login_user, activity_update_user, activity_status, activity_start, activity_end, activity_community_id, activity_confirm_term_of_use, title, shared_user_ids) FROM stdin;
N	2020-12-10 17:38:46.057615	2020-12-10 17:38:46.071099	1	A-20201210-00001	\N	\N	1	\N	1	2	B	1	1	M	2020-12-10 17:38:46.05512	\N	\N	t	\N	\N
N	2020-12-10 17:40:15.515309	2020-12-10 17:40:47.65665	2	A-20201210-00002	\N	2370d707-b92a-4313-a803-980861f76a90	1	\N	1	2	F	1	1	F	2020-12-10 17:40:15.514158	2020-12-10 17:40:47.655567	\N	t	s	[]
N	2020-12-10 17:44:19.586797	2020-12-10 17:45:23.236078	3	A-20201210-00003	\N	2370d707-b92a-4313-a803-980861f76a90	1	\N	1	2	F	1	1	F	2020-12-10 17:44:19.585057	2020-12-10 17:45:23.235378	\N	t	s	[]
N	2020-12-10 17:48:36.484473	2020-12-10 17:49:05.207873	4	A-20201210-00004	\N	2370d707-b92a-4313-a803-980861f76a90	1	\N	1	2	F	1	1	F	2020-12-10 17:48:36.483013	2020-12-10 17:49:05.206811	\N	t	s	[]
N	2020-12-10 17:55:06.26716	2020-12-10 18:29:00.898479	5	A-20201210-00005	\N	2370d707-b92a-4313-a803-980861f76a90	1	\N	1	2	F	1	1	F	2020-12-10 17:55:06.265358	2020-12-10 18:29:00.897907	\N	t	s	[]
\.


--
-- Data for Name: workflow_activity_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_activity_action (status, created, updated, id, activity_id, action_id, action_status, action_comment, action_handler) FROM stdin;
N	2020-12-10 17:38:46.074302	2020-12-10 17:38:46.074323	1	A-20201210-00001	1	F	\N	\N
N	2020-12-10 17:38:46.075728	2020-12-10 17:38:46.075747	2	A-20201210-00001	2	F	\N	\N
N	2020-12-10 17:40:15.537744	2020-12-10 17:40:15.537758	3	A-20201210-00002	1	F	\N	\N
N	2020-12-10 17:40:15.539729	2020-12-10 17:40:15.53974	8	A-20201210-00002	2	F	\N	\N
N	2020-12-10 17:40:15.538437	2020-12-10 17:40:36.090246	4	A-20201210-00002	3	F		\N
N	2020-12-10 17:40:15.538768	2020-12-10 17:40:39.827389	5	A-20201210-00002	5	F		\N
N	2020-12-10 17:40:15.539091	2020-12-10 17:40:43.963103	6	A-20201210-00002	4	F		\N
N	2020-12-10 17:40:15.53941	2020-12-10 17:40:46.608073	7	A-20201210-00002	7	F		\N
N	2020-12-10 17:44:19.608498	2020-12-10 17:44:19.608511	9	A-20201210-00003	1	F	\N	\N
N	2020-12-10 17:44:19.610985	2020-12-10 17:44:19.610997	14	A-20201210-00003	2	F	\N	\N
N	2020-12-10 17:44:19.60912	2020-12-10 17:45:10.006595	10	A-20201210-00003	3	F		\N
N	2020-12-10 17:44:19.60945	2020-12-10 17:45:13.849613	11	A-20201210-00003	5	F		\N
N	2020-12-10 17:44:19.609991	2020-12-10 17:45:17.940316	12	A-20201210-00003	4	F		\N
N	2020-12-10 17:44:19.610477	2020-12-10 17:45:21.310445	13	A-20201210-00003	7	F		\N
N	2020-12-10 17:48:36.504941	2020-12-10 17:48:36.504959	15	A-20201210-00004	1	F	\N	\N
N	2020-12-10 17:48:36.50769	2020-12-10 17:48:36.507703	20	A-20201210-00004	2	F	\N	\N
N	2020-12-10 17:48:36.505845	2020-12-10 17:48:53.487747	16	A-20201210-00004	3	F		\N
N	2020-12-10 17:48:36.506368	2020-12-10 17:48:56.14228	17	A-20201210-00004	5	F		\N
N	2020-12-10 17:48:36.50687	2020-12-10 17:48:58.594479	18	A-20201210-00004	4	F		\N
N	2020-12-10 17:48:36.507321	2020-12-10 17:49:03.102654	19	A-20201210-00004	7	F		\N
N	2020-12-10 17:55:06.308904	2020-12-10 17:55:06.308933	21	A-20201210-00005	1	F	\N	\N
N	2020-12-10 17:55:06.311837	2020-12-10 17:55:06.31185	26	A-20201210-00005	2	F	\N	\N
N	2020-12-10 17:55:06.310158	2020-12-10 18:28:44.783246	22	A-20201210-00005	3	F		\N
N	2020-12-10 17:55:06.310573	2020-12-10 18:28:49.648802	23	A-20201210-00005	5	F		\N
N	2020-12-10 17:55:06.311029	2020-12-10 18:28:54.61063	24	A-20201210-00005	4	F		\N
N	2020-12-10 17:55:06.311436	2020-12-10 18:28:59.119933	25	A-20201210-00005	7	F		\N
\.


--
-- Data for Name: workflow_flow_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date) FROM stdin;
N	2020-12-10 17:05:38.807533	2020-12-10 17:05:38.807551	1	6c27b492-3986-4770-b336-c1bd01cb325b	1	1.0.0	1	\N	A	2020-12-10 17:05:38.807562
N	2020-12-10 17:39:49.445437	2020-12-10 17:39:49.445454	3	6c27b492-3986-4770-b336-c1bd01cb325b	3	1.0.1	2	\N	A	2020-12-10 17:39:49.445464
N	2020-12-10 17:39:49.449281	2020-12-10 17:39:49.4493	4	6c27b492-3986-4770-b336-c1bd01cb325b	5	1.0.1	3	\N	A	2020-12-10 17:39:49.449308
N	2020-12-10 17:39:49.453412	2020-12-10 17:39:49.45343	5	6c27b492-3986-4770-b336-c1bd01cb325b	4	2.0.0	4	\N	A	2020-12-10 17:39:49.453437
N	2020-12-10 17:39:49.456644	2020-12-10 17:39:49.456658	6	6c27b492-3986-4770-b336-c1bd01cb325b	7	1.0.0	5	\N	A	2020-12-10 17:39:49.456665
N	2020-12-10 17:05:38.808585	2020-12-10 17:39:49.458761	2	6c27b492-3986-4770-b336-c1bd01cb325b	2	1.0.0	6	\N	A	2020-12-10 17:05:38.808609
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
N	2020-12-10 17:05:38.805756	2020-12-10 17:39:49.444296	1	6c27b492-3986-4770-b336-c1bd01cb325b	SampleFlow	1	A	f
\.


--
-- Data for Name: workflow_workflow; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.workflow_workflow (status, created, updated, id, flows_id, flows_name, itemtype_id, index_tree_id, flow_id, is_deleted) FROM stdin;
N	2020-12-10 17:08:28.909461	2020-12-10 17:40:00.315794	1	4a3d8993-5d51-4d47-b39b-15fe212efa2f	SampleWorkFlow	21	\N	1	f
\.


--
-- Name: workflow_action_feedbackmail_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_feedbackmail_id_seq', 4, true);


--
-- Name: workflow_action_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_history_id_seq', 29, true);


--
-- Name: workflow_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_id_seq', 7, true);


--
-- Name: workflow_action_identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_action_identifier_id_seq', 4, true);


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

SELECT pg_catalog.setval('public.workflow_activity_action_id_seq', 26, true);


--
-- Name: workflow_activity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_activity_id_seq', 5, true);


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

