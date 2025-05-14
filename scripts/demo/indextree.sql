--
-- PostgreSQL database dump
--

-- Dumped from database version 12.18 (Debian 12.18-1.pgdg120+2)
-- Dumped by pg_dump version 12.18 (Debian 12.18-1.pgdg120+2)
-- docker-compose exec postgresql pg_dump -U invenio -a -t index --column-inserts > scripts/demo/indextree.sql 

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
-- Data for Name: index; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.index (created, updated, id, parent, "position", index_name, index_name_english, index_link_name, index_link_name_english, harvest_spec, index_link_enabled, comment, more_check, display_no, harvest_public_state, display_format, image_name, public_state, public_date, recursive_public_state, rss_status, coverpage_state, recursive_coverpage_check, browsing_role, recursive_browsing_role, contribute_role, recursive_contribute_role, browsing_group, recursive_browsing_group, contribute_group, recursive_contribute_group, owner_user_id, item_custom_sort, biblio_flag, online_issn, is_deleted) VALUES ('2021-06-14 01:07:10.647996', '2024-06-12 12:21:26.526676', 1623632832836, 0, 0, 'サンプルインデックス', 'Sample Index', '', 'New Index', '', false, '', false, 5, false, '1', '', false, NULL, false, false, false, false, '3,-98,-99', false, '1,2,3,4,-98', false, '', false, '', false, 1, '{}', false, '', false);


--
-- Name: index_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.index_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

