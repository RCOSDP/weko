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
-- Data for Name: item_type_name; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.item_type_name (created, updated, id, name, has_site_license, is_active) VALUES
('2025-02-25 04:05:58.871334', '2025-02-25 04:05:58.871341', 51000, '未病アイテムタイプ', true, true)
ON CONFLICT (id) DO UPDATE SET
  created = EXCLUDED.created,
  updated = EXCLUDED.updated,
  id = EXCLUDED.id,
  name = EXCLUDED.name,
  has_site_license = EXCLUDED.has_site_license,
  is_active = EXCLUDED.is_active;



--
-- Name: item_type_name_id_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

--
-- PostgreSQL database dump complete
--
