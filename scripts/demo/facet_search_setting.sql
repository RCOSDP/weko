--
-- PostgreSQL database dump
--

-- Dumped from database version 12.6 (Debian 12.6-1.pgdg100+1)
-- Dumped by pg_dump version 12.6 (Debian 12.6-1.pgdg100+1)

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
-- Delete data: facet_search_setting; Type: TABLE DATA; Schema: public; Owner: invenio
--

DELETE FROM public.facet_search_setting WHERE name_en='Data Language';
DELETE FROM public.facet_search_setting WHERE name_en='Access';
DELETE FROM public.facet_search_setting WHERE name_en='Location';
DELETE FROM public.facet_search_setting WHERE name_en='Temporal';
DELETE FROM public.facet_search_setting WHERE name_en='Topic';
DELETE FROM public.facet_search_setting WHERE name_en='Distributor';
DELETE FROM public.facet_search_setting WHERE name_en='Data Type';

--
-- Data for Name: facet_search_setting; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.facet_search_setting (name_en, name_jp, mapping, aggregations, active) FROM stdin;
Data Language	デ一タの言語	language	[]	t
Access	アクセス制限	accessRights	[]	t
Location	地域	geoLocation.geoLocationPlace	[]	t
Temporal	時間的範囲	temporal	[]	t
Topic	トピック	subject.value	[]	t
Distributor	配布者	contributor.contributorName	[{"agg_value": "Distributor", "agg_mapping": "contributor.@attributes.contributorType"}]	t
Data Type	デ一タタイプ	description.value	[{"agg_value": "Other", "agg_mapping": "description.descriptionType"}]	t
\.


--
-- Name: facet_search_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.facet_search_setting_id_seq', (SELECT MAX(id) FROM public.facet_search_setting), true);


--
-- PostgreSQL database dump complete
--

