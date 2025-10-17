--
-- PostgreSQL database dump
--

-- Dumped from database version 12.22 (Debian 12.22-1.pgdg120+1)
-- Dumped by pg_dump version 12.22 (Debian 12.22-1.pgdg120+1)

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
-- Data for Name: facet_search_setting; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.facet_search_setting (id, name_en, name_jp, mapping, aggregations, active, ui_type, display_number, is_open, search_condition) FROM stdin;
51001	genre_filter	データセットの分野	text1.raw	[]	t	CheckboxList	5	t	OR
51002	subjectOf_filter	データセットの名称	title	[]	t	CheckboxList	5	t	OR
51003	payOrFree_filter	有償・無償	text2.raw	[]	t	CheckboxList	5	t	OR
51004	contactPermission_filter	連絡・許諾の要不要	text3.raw	[]	t	CheckboxList	5	t	OR
51005	creator_filter	データ作成者 氏名	text4.raw	[]	t	CheckboxList	5	t	OR
51006	projectName_filter	プロジェクト名	text5.raw	[]	t	CheckboxList	5	t	OR
51007	iCIsNo_filter	（IC無の場合）	text6.raw	[]	t	CheckboxList	5	t	OR
51008	accessMode_filter	アクセス権	text7.raw	[]	t	CheckboxList	5	t	OR
51009	informedConsent_filter	（ヒト）インフォームドコンセント（IC） 有・無・不要	text8.raw	[]	t	CheckboxList	5	t	OR
\.


--
-- Name: facet_search_setting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

--
-- PostgreSQL database dump complete
--
