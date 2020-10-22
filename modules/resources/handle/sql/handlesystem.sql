
CREATE DATABASE handlesystem;

\c handlesystem

--
-- PostgreSQL database dump
--

-- Dumped from database version 12.2 (Debian 12.2-2.pgdg100+1)
-- Dumped by pg_dump version 12.2 (Debian 12.2-2.pgdg100+1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: handles; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.handles (
    handle bytea NOT NULL,
    idx integer NOT NULL,
    type bytea,
    data bytea,
    ttl_type smallint,
    ttl integer,
    "timestamp" integer,
    refs text,
    admin_read boolean,
    admin_write boolean,
    pub_read boolean,
    pub_write boolean
);


ALTER TABLE public.handles OWNER TO invenio;

--
-- Name: nas; Type: TABLE; Schema: public; Owner: invenio
--

CREATE TABLE public.nas (
    na bytea NOT NULL
);


ALTER TABLE public.nas OWNER TO invenio;

--
-- Data for Name: handles; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.handles (handle, idx, type, data, ttl_type, ttl, "timestamp", refs, admin_read, admin_write, pub_read, pub_write) FROM stdin;
\.


--
-- Data for Name: nas; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.nas (na) FROM stdin;
\.


--
-- Name: handles handles_pkey; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.handles
    ADD CONSTRAINT handles_pkey PRIMARY KEY (handle, idx);


--
-- Name: nas nas_pkey; Type: CONSTRAINT; Schema: public; Owner: invenio
--

ALTER TABLE ONLY public.nas
    ADD CONSTRAINT nas_pkey PRIMARY KEY (na);


--
-- Name: dataindex; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX dataindex ON public.handles USING btree (data);


--
-- Name: handleindex; Type: INDEX; Schema: public; Owner: invenio
--

CREATE INDEX handleindex ON public.handles USING btree (handle);


--
-- Name: TABLE handles; Type: ACL; Schema: public; Owner: invenio
--

GRANT SELECT ON TABLE public.handles TO PUBLIC;


--
-- Name: TABLE nas; Type: ACL; Schema: public; Owner: invenio
--

GRANT SELECT ON TABLE public.nas TO PUBLIC;


--
-- PostgreSQL database dump complete
--

