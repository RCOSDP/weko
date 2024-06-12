--
-- PostgreSQL database dump
--

-- Dumped from database version 11.2 (Debian 11.2-1.pgdg90+1)
-- Dumped by pg_dump version 11.2 (Debian 11.2-1.pgdg90+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: index; Type: TABLE DATA; Schema: public; Owner: invenio
--

COPY public.index (created, updated, id, parent, "position", index_name, index_name_english, index_link_name, index_link_name_english, harvest_spec, index_link_enabled, comment, more_check, display_no, harvest_public_state, display_format, image_name, public_state, public_date, recursive_public_state, rss_status, coverpage_state, recursive_coverpage_check, browsing_role, recursive_browsing_role, contribute_role, recursive_contribute_role, browsing_group, recursive_browsing_group, contribute_group, recursive_contribute_group, owner_user_id, item_custom_sort) FROM stdin;
2019-05-14 07:42:13.445317	2019-05-14 07:42:29.574536	1557819733276	1557819692844	0	会議発表論文	conference paper		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:42:14.945336	2019-05-14 07:42:48.358597	1557819734732	1557819692844	1	データ論文	data paper		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:42:15.996667	2019-05-14 07:43:09.555409	1557819735780	1557819692844	2	紀要論文	departmental bulletin paper		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:42:16.962963	2019-05-14 07:43:34.545454	1557819736796	1557819692844	3	エディトリアル	editorial		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:42:17.908313	2019-05-14 07:44:06.836126	1557819737740	1557819692844	4	研究論文	journal article		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:44:12.90935	2019-05-14 07:44:29.016641	1557819852742	1557819692844	5	記事	article		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:44:13.642605	2019-05-14 07:44:42.789074	1557819853470	1557819692844	6	図書	book		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:44:16.517593	2019-05-14 07:45:02.643294	1557819856350	1557819692844	7	図書（部分）	book part		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:45:15.945366	2019-05-14 07:45:26.923618	1557819915775	1557819692844	8	地図資料	cartographic material		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:45:16.81092	2019-05-14 07:45:42.782895	1557819916647	1557819692844	9	地図	map		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:45:31.248519	2019-05-14 07:45:57.945421	1557819931079	1557819692844	10	会議発表資料	conference object		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:46:06.61857	2019-05-14 07:46:29.211277	1557819966447	1557819692844	11	会議発表ポスター	conference poster		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:46:34.326783	2019-05-14 07:46:49.998286	1557819994152	1557819692844	12	データセット	dataset		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:48:06.704791	2019-05-14 07:48:49.432827	1557820086539	0	1	人文社会系 (Faculty of Humanities and Social Sciences)	Faculty of Humanities and Social Sciences		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:48:07.424015	2019-05-14 07:49:05.499008	1557820087258	0	2	ビジネスサイエンス系 (Faculty of Business Sciences)	Faculty of Business Sciences		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:48:07.896402	2019-05-14 07:49:26.621391	1557820087730	0	3	数理物質系 (Faculty of Pure and Applied Sciences)	Faculty of Pure and Applied Sciences		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:49:11.022607	2019-05-14 07:49:47.370292	1557820150852	0	4	システム情報系 (Faculty of Engineering, Information and Systems)	Faculty of Engineering, Information and Systems		New Index	\N	f		f	5	t	1		f	\N	f	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:49:11.804901	2019-05-14 07:50:10.59232	1557820151636	0	5	生命環境系 (Faculty of Life and Environmental Sciences)	Faculty of Life and Environmental Sciences		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:50:15.866266	2019-05-14 07:50:34.173188	1557820215685	0	6	人間系 (Faculty of Human Sciences)	Faculty of Human Sciences		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:50:17.137674	2019-05-14 07:50:58.405093	1557820216972	0	7	体育系 (Faculty of Health and Sport Sciences)	Faculty of Health and Sport Sciences		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:50:17.982404	2019-05-14 07:51:15.607163	1557820217812	0	8	芸術系 (Faculty of Art and Design)	Faculty of Art and Design		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:52:46.404317	2019-05-14 07:53:03.224176	1557820366232	0	9	医学医療系 (Faculty of Medicine)	Faculty of Medicine		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:52:47.770204	2019-05-14 07:53:21.214801	1557820367608	0	10	図書館情報メディア系 (Faculty of Library, Information and Media Science)	Faculty of Library, Information and Media Science		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
2019-05-14 07:41:33.055032	2019-05-14 07:54:10.573466	1557819692844	0	0	コンテンツタイプ (Contents Type)	Contents Type		New Index	\N	f		f	5	t	1		t	\N	t	f	f	f	3,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}
\.


--
-- Name: index_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.index_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

