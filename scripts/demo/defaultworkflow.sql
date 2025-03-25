--
-- PostgreSQL database dump
--

-- Dumped from database version 12.18 (Debian 12.18-1.pgdg120+2)
-- Dumped by pg_dump version 12.18 (Debian 12.18-1.pgdg120+2)
-- docker-compose exec postgresql pg_dump -U invenio -a -t workflow_flow_action -t workflow_flow_define -t workflow_workflow  --column-inserts > scripts/demo/defaultworkflow.sql

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
-- Data for Name: workflow_flow_define; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.workflow_flow_define (status, created, updated, id, flow_id, flow_name, flow_user, flow_status, is_deleted) VALUES ('N', '2024-06-12 21:30:19.564693', '2024-06-12 21:31:01.443099', 1, '95b9a88f-3318-4da4-8949-7345b9396e87', 'Registration Flow', 1, 'A', false);


--
-- Data for Name: workflow_flow_action; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) VALUES ('N', '2024-06-12 21:30:19.569872', '2024-06-12 21:31:01.428911', 1, '95b9a88f-3318-4da4-8949-7345b9396e87', 1, '1.0.0', 1, NULL, 'A', '2024-06-12 21:30:19.56991', '{"inform_reject": false, "inform_approval": false, "request_approval": false}');
INSERT INTO public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) VALUES ('N', '2024-06-12 21:31:01.445882', '2024-06-12 21:31:01.445905', 3, '95b9a88f-3318-4da4-8949-7345b9396e87', 3, '1.0.1', 2, NULL, 'A', '2024-06-12 21:31:01.44592', '{"inform_reject": false, "inform_approval": false, "request_approval": false}');
INSERT INTO public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) VALUES ('N', '2024-06-12 21:31:01.459539', '2024-06-12 21:31:01.459581', 4, '95b9a88f-3318-4da4-8949-7345b9396e87', 5, '1.0.1', 3, NULL, 'A', '2024-06-12 21:31:01.459591', '{"inform_reject": false, "inform_approval": false, "request_approval": false}');
INSERT INTO public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) VALUES ('N', '2024-06-12 21:31:01.471524', '2024-06-12 21:31:01.471544', 5, '95b9a88f-3318-4da4-8949-7345b9396e87', 7, '1.0.0', 4, NULL, 'A', '2024-06-12 21:31:01.471574', '{"inform_reject": false, "inform_approval": false, "request_approval": false}');
INSERT INTO public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) VALUES ('N', '2024-06-12 21:31:01.483476', '2024-06-12 21:31:01.483496', 6, '95b9a88f-3318-4da4-8949-7345b9396e87', 4, '2.0.0', 5, NULL, 'A', '2024-06-12 21:31:01.483505', '{"inform_reject": false, "inform_approval": false, "request_approval": false}');
INSERT INTO public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) VALUES ('N', '2024-06-12 21:30:19.573765', '2024-06-12 21:31:01.491945', 2, '95b9a88f-3318-4da4-8949-7345b9396e87', 2, '1.0.0', 6, NULL, 'A', '2024-06-12 21:30:19.573793', '{"inform_reject": false, "inform_approval": false, "request_approval": false}');


--
-- Data for Name: workflow_workflow; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.workflow_workflow (status, created, updated, id, flows_id, flows_name, itemtype_id, index_tree_id, flow_id, is_deleted, open_restricted, location_id, is_gakuninrdm) VALUES ('N', '2024-06-12 21:33:29.550958', '2024-06-12 21:33:29.550985', 1, '4bb9d036-fc1e-4eab-a7de-cffed26a2bb4', 'デフォルトアイテムタイプ（フル）', 30002, NULL, 1, false, false, NULL, false);
INSERT INTO public.workflow_workflow (status, created, updated, id, flows_id, flows_name, itemtype_id, index_tree_id, flow_id, is_deleted, open_restricted, location_id, is_gakuninrdm) VALUES ('N', '2024-06-12 21:33:55.106678', '2024-06-12 21:33:55.106704', 2, 'bbbb1d7f-2e3a-4bb2-945c-d71b221cb068', 'デフォルトアイテムタイプ（シンプル）', 30001, NULL, 1, false, false, NULL, false);


--
-- Name: workflow_flow_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_flow_action_id_seq', 6, true);


--
-- Name: workflow_flow_define_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_flow_define_id_seq', 1000, true);


--
-- Name: workflow_workflow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

SELECT pg_catalog.setval('public.workflow_workflow_id_seq', 1000, true);


--
-- PostgreSQL database dump complete
--

