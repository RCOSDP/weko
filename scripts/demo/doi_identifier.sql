--
-- PostgreSQL database dump
--

-- Dumped from database version 12.18 (Debian 12.18-1.pgdg120+2)
-- Dumped by pg_dump version 12.18 (Debian 12.18-1.pgdg120+2)
-- docker-compose exec postgresql pg_dump -U invenio -a -t doi_identifier  --column-inserts > scripts/demo/doi_identifier.sql

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

--
-- Data for Name: doi_identifier; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.doi_identifier (id, repository, jalc_flag, jalc_crossref_flag, jalc_datacite_flag, ndl_jalc_flag, jalc_doi, jalc_crossref_doi, jalc_datacite_doi, ndl_jalc_doi, suffix, "created_userId", created_date, "updated_userId", updated_date) VALUES (1, 'Root Index', false, false, false, false, '', '', '', '10.11501', '', '1', '2024-06-12 15:10:00', '2', '2024-06-12 15:11:13');


--
-- Name: doi_identifier_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.doi_identifier_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

