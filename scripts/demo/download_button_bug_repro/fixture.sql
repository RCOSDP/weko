--
-- download_button_bug_repro / fixture.sql
--
-- 「利用申請が承認済みなのにダウンロードボタンではなく申請ボタンが表示される」
-- 不具合を再現するための、完全に合成（synthetic）のデモデータ。
--
-- Reproduction fixture for: an approved usage application still shows the
-- "申請 (Apply)" button instead of the "ダウンロード (Download)" button.
--
-- * このファイルに実データ（本番の個人情報・研究データ）は一切含まれない。
--   メールアドレスは populate-instance.sh が作成するデモアカウント
--   contributor@example.org のみ。
-- * 実行前提: install.sh / scripts/populate-instance.sh による通常の新規構築が
--   完了していること（item_type 15 / 31001、デモアカウント、accounts_role 1-4、
--   files_location id=1 が存在すること）。
-- * 追加されるのは以下の ID 空間のみ。既存行は一切変更・削除しない。
--     index                     : 1758900000001
--     workflow_flow_define      : 39001
--     workflow_flow_action      : 39001 - 39004
--     workflow_workflow         : 39001
--     pidstore_pid              : 32056 - 32069 (recid 2003976 / 2003977 系)
--     workflow_activity         : A-20260917-00001
--
-- ロード方法は load.sh / README.md を参照。
--

\set ON_ERROR_STOP on

BEGIN;

--
-- 再実行できるように、本フィクスチャが作る行だけを先に削除する。
-- (FK 依存の逆順)
--
DELETE FROM public.file_onetime_download WHERE record_id = '2003976';
DELETE FROM public.file_permission       WHERE record_id = '2003976';
DELETE FROM public.workflow_action_history  WHERE activity_id = 'A-20260917-00001';
DELETE FROM public.workflow_activity_action WHERE activity_id = 'A-20260917-00001';
DELETE FROM public.workflow_activity        WHERE activity_id = 'A-20260917-00001';
DELETE FROM public.pidrelations_pidrelation WHERE parent_id IN (32058, 32066);
DELETE FROM public.item_metadata   WHERE id IN ('c8af35ea-76bf-40a4-8366-07902b1a532e','d443270e-cbbb-4896-981d-614f9766b5f2','4a23ff43-5325-4bce-af99-dc6d8f0f4a3b','556f88a7-2164-4655-96ea-953365168917');
DELETE FROM public.files_object    WHERE bucket_id IN ('19efee91-8841-4e06-a612-8ec571a9d8b3','c1e6b18c-7051-4b54-bf98-00abf99f4717','845ccfdf-6316-452c-983a-68b09a04b982','c69e16b1-f626-42d6-94b2-a99140b9cb89');
DELETE FROM public.records_buckets WHERE record_id IN ('c8af35ea-76bf-40a4-8366-07902b1a532e','d443270e-cbbb-4896-981d-614f9766b5f2','4a23ff43-5325-4bce-af99-dc6d8f0f4a3b','556f88a7-2164-4655-96ea-953365168917');
DELETE FROM public.records_metadata WHERE id IN ('c8af35ea-76bf-40a4-8366-07902b1a532e','d443270e-cbbb-4896-981d-614f9766b5f2','4a23ff43-5325-4bce-af99-dc6d8f0f4a3b','556f88a7-2164-4655-96ea-953365168917');
DELETE FROM public.pidstore_pid WHERE id BETWEEN 32056 AND 32069;
DELETE FROM public.files_bucket WHERE id IN ('19efee91-8841-4e06-a612-8ec571a9d8b3','c1e6b18c-7051-4b54-bf98-00abf99f4717','845ccfdf-6316-452c-983a-68b09a04b982','c69e16b1-f626-42d6-94b2-a99140b9cb89');
DELETE FROM public.workflow_workflow    WHERE id = 39001;
DELETE FROM public.workflow_flow_action WHERE id BETWEEN 39001 AND 39004;
DELETE FROM public.workflow_flow_define WHERE id = 39001;
DELETE FROM public."index" WHERE id = 1758900000001;

-- ---------------------------------------------------------------------
-- index
-- ---------------------------------------------------------------------
COPY public.index (created, updated, id, parent, "position", index_name, index_name_english, index_link_name, index_link_name_english, harvest_spec, index_link_enabled, comment, more_check, display_no, harvest_public_state, display_format, image_name, public_state, public_date, recursive_public_state, rss_status, coverpage_state, recursive_coverpage_check, browsing_role, recursive_browsing_role, contribute_role, recursive_contribute_role, browsing_group, recursive_browsing_group, contribute_group, recursive_contribute_group, owner_user_id, item_custom_sort, biblio_flag, online_issn) FROM stdin;
2026-09-17 06:32:26.135989	2026-09-17 06:32:26.135993	1758900000001	0	99	デモ: 制限公開アイテム	Demo: Restricted Item		Demo Restricted Index		f		f	5	t	1		t	\N	f	f	f	f	1,2,3,4,-98,-99	f	1,2,3,4,-98,-99	f		f		f	1	{}	f	
\.

-- ---------------------------------------------------------------------
-- workflow_flow_define
-- ---------------------------------------------------------------------
COPY public.workflow_flow_define (status, created, updated, id, flow_id, flow_name, flow_user, flow_status, is_deleted) FROM stdin;
N	2026-09-17 06:36:22.014475	2026-09-17 06:36:22.014487	39001	7a5f0e02-3b91-4c8d-9a6e-0f1d2c3b4a59	デモ用データ利用申請 / Demo Data Usage Application	1	A	f
\.

-- ---------------------------------------------------------------------
-- workflow_flow_action
-- ---------------------------------------------------------------------
COPY public.workflow_flow_action (status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date, send_mail_setting) FROM stdin;
N	2026-09-17 06:36:22.030038	2026-09-17 06:36:22.030049	39001	7a5f0e02-3b91-4c8d-9a6e-0f1d2c3b4a59	1	1.0.0	1	\N	A	2026-09-17 06:36:22.028668	{"inform_reject": {"mail": "0", "send": false}, "inform_itemReg": {"mail": "0", "send": false}, "inform_approval": {"mail": "0", "send": false}, "request_approval": {"mail": "0", "send": false}}
N	2026-09-17 06:36:22.035653	2026-09-17 06:36:22.03566	39002	7a5f0e02-3b91-4c8d-9a6e-0f1d2c3b4a59	3	1.0.1	2	\N	A	2026-09-17 06:36:22.034932	{"inform_reject": {"mail": "0", "send": false}, "inform_itemReg": {"mail": "0", "send": false}, "inform_approval": {"mail": "0", "send": false}, "request_approval": {"mail": "0", "send": false}}
N	2026-09-17 06:36:22.038244	2026-09-17 06:36:22.038252	39003	7a5f0e02-3b91-4c8d-9a6e-0f1d2c3b4a59	4	2.0.0	3	\N	A	2026-09-17 06:36:22.037683	{"inform_reject": {"mail": "0", "send": false}, "inform_itemReg": {"mail": "0", "send": false}, "inform_approval": {"mail": "0", "send": false}, "request_approval": {"mail": "0", "send": false}}
N	2026-09-17 06:36:22.041807	2026-09-17 06:36:22.041812	39004	7a5f0e02-3b91-4c8d-9a6e-0f1d2c3b4a59	2	1.0.0	4	\N	A	2026-09-17 06:36:22.041239	{"inform_reject": {"mail": "0", "send": false}, "inform_itemReg": {"mail": "0", "send": false}, "inform_approval": {"mail": "0", "send": false}, "request_approval": {"mail": "0", "send": false}}
\.

-- ---------------------------------------------------------------------
-- workflow_workflow
-- ---------------------------------------------------------------------
COPY public.workflow_workflow (status, created, updated, id, flows_id, flows_name, itemtype_id, index_tree_id, flow_id, is_deleted, open_restricted, is_gakuninrdm) FROM stdin;
N	2026-09-17 06:36:22.047985	2026-09-17 06:36:22.04799	39001	7a5f0e02-3b91-4c8d-9a6e-0f1d2c3b4a59	デモ用データ利用申請 / Demo Data Usage Application	31001	1758900000001	39001	f	t	f
\.

-- ---------------------------------------------------------------------
-- files_bucket
-- ---------------------------------------------------------------------
COPY public.files_bucket (created, updated, id, default_location, default_storage_class, size, quota_size, max_file_size, locked, deleted) FROM stdin;
2026-09-17 06:32:26.222457	2026-09-17 06:33:53.153523	19efee91-8841-4e06-a612-8ec571a9d8b3	1	S	0	53687091200	53687091200	f	f
2026-09-17 06:34:25.218625	2026-09-17 06:34:25.231642	c1e6b18c-7051-4b54-bf98-00abf99f4717	1	S	0	53687091200	\N	f	f
2026-09-17 06:37:22.192177	2026-09-17 06:37:22.19218	845ccfdf-6316-452c-983a-68b09a04b982	1	S	0	53687091200	53687091200	f	f
2026-09-17 06:37:22.832176	2026-09-17 06:37:22.837614	c69e16b1-f626-42d6-94b2-a99140b9cb89	1	S	0	53687091200	\N	f	f
\.

-- ---------------------------------------------------------------------
-- pidstore_pid
-- ---------------------------------------------------------------------
COPY public.pidstore_pid (created, updated, id, pid_type, pid_value, pid_provider, status, object_type, object_uuid) FROM stdin;
2026-09-17 06:32:26.239338	2026-09-17 06:32:26.239343	32056	recid	2003976	\N	R	rec	c8af35ea-76bf-40a4-8366-07902b1a532e
2026-09-17 06:32:26.248785	2026-09-17 06:32:26.24879	32057	depid	2003976	\N	R	rec	c8af35ea-76bf-40a4-8366-07902b1a532e
2026-09-17 06:32:26.453267	2026-09-17 06:32:26.453272	32058	parent	parent:2003976	\N	R	rec	c8af35ea-76bf-40a4-8366-07902b1a532e
2026-09-17 06:33:53.272521	2026-09-17 06:33:53.272525	32059	oai	oai:weko3.example.org:02003976	oai	R	rec	c8af35ea-76bf-40a4-8366-07902b1a532e
2026-09-17 06:34:25.118677	2026-09-17 06:34:25.118682	32060	recid	2003976.1	\N	R	rec	d443270e-cbbb-4896-981d-614f9766b5f2
2026-09-17 06:34:25.124467	2026-09-17 06:34:25.124474	32061	depid	2003976.1	\N	R	rec	d443270e-cbbb-4896-981d-614f9766b5f2
2026-09-17 06:34:25.399155	2026-09-17 06:34:25.39916	32062	oai	oai:weko3.example.org:02003976.1	oai	R	rec	d443270e-cbbb-4896-981d-614f9766b5f2
2026-09-17 06:37:22.149396	2026-09-17 06:37:22.149401	32063	actid	A-20260917-00001	\N	R	\N	\N
2026-09-17 06:37:22.20834	2026-09-17 06:37:22.208344	32064	recid	2003977	\N	R	rec	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b
2026-09-17 06:37:22.212088	2026-09-17 06:37:22.212091	32065	depid	2003977	\N	R	rec	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b
2026-09-17 06:37:22.228597	2026-09-17 06:37:22.228601	32066	parent	parent:2003977	\N	R	rec	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b
2026-09-17 06:37:22.398027	2026-09-17 06:37:22.398032	32067	oai	oai:weko3.example.org:02003977	oai	R	rec	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b
2026-09-17 06:37:22.792139	2026-09-17 06:37:22.792145	32068	recid	2003977.1	\N	R	rec	556f88a7-2164-4655-96ea-953365168917
2026-09-17 06:37:22.795315	2026-09-17 06:37:22.795319	32069	depid	2003977.1	\N	R	rec	556f88a7-2164-4655-96ea-953365168917
\.

-- ---------------------------------------------------------------------
-- records_metadata
-- ---------------------------------------------------------------------
COPY public.records_metadata (created, updated, id, json, version_id) FROM stdin;
2026-09-17 06:37:22.220152	2026-09-17 06:37:22.726298	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b	{"_oai": {"id": "oai:weko3.example.org:02003977", "sets": ["1758900000001"]}, "path": ["1758900000001"], "owner": "3", "recid": "2003977", "title": ["サンプル制限公開アイテム / Sample Restricted Item"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2026-09-17"}, "_buckets": {"deposit": "845ccfdf-6316-452c-983a-68b09a04b982"}, "_deposit": {"id": "2003977", "pid": {"type": "depid", "value": "2003977", "revision_id": 0}, "owners": [3], "status": "published", "created_by": 3}, "item_title": "サンプル制限公開アイテム / Sample Restricted Item", "author_link": [], "item_type_id": "31001", "publish_date": "2026-09-17", "publish_status": "0", "weko_shared_id": -1, "item_1616221831877": {"attribute_name": "Dataset Usage", "attribute_value_mlt": [{"subitem_restricted_access_dataset_usage": "sample_restricted_data.txt"}]}, "item_1616221941275": {"attribute_name": "Research Title", "attribute_value_mlt": [{"subitem_restricted_access_research_title": "デモ用研究タイトル / Demo Research Title"}]}, "item_1616221960771": {"attribute_name": "Research Plan", "attribute_value_mlt": [{"subitem_restricted_access_research_plan": "これはデモ用の架空の研究計画です。", "subitem_restricted_access_research_plan_type": "Free"}]}, "item_1616222047122": {"attribute_name": "WF Issued Date", "attribute_value_mlt": [{"subitem_restricted_access_wf_issued_date": "2026-09-17", "subitem_restricted_access_wf_issued_date_type": "Created"}]}, "item_1616222067301": {"attribute_name": "Application Date", "attribute_value_mlt": [{"subitem_restricted_access_application_date": "2026-09-17", "subitem_restricted_access_application_date_type": "Created"}]}, "item_1616222093486": {"attribute_name": "Approval Date", "attribute_value_mlt": [{"subitem_restricted_access_approval_date": "2026-09-17", "subitem_restricted_access_approval_date_type": "Created"}]}, "item_1616222117209": {"attribute_name": "Item Title", "attribute_value_mlt": [{"subitem_restricted_access_item_title": "サンプル制限公開アイテム / Sample Restricted Item"}]}, "item_1648134694613": {"attribute_name": "Applicant", "attribute_value_mlt": [{"subitem_fullname": "デモ 花子", "subitem_position": "その他", "subitem_mail_address": "contributor@example.org", "subitem_phone_number": "000-0000-0000", "subitem_university/institution": "デモ大学", "subitem_affiliated_division/department": "デモ学部"}]}, "relation_version_is_last": true}	5
2026-09-17 06:32:26.374506	2026-09-17 06:35:00.688205	c8af35ea-76bf-40a4-8366-07902b1a532e	{"_oai": {"id": "oai:weko3.example.org:02003976", "sets": []}, "path": ["1758900000001"], "owner": "1", "recid": "2003976", "title": ["サンプル制限公開アイテム / Sample Restricted Item"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2026-09-17"}, "_buckets": {"deposit": "19efee91-8841-4e06-a612-8ec571a9d8b3"}, "_deposit": {"id": "2003976", "pid": {"type": "depid", "value": "2003976", "revision_id": 0}, "owner": "1", "owners": [1], "status": "published"}, "item_title": "サンプル制限公開アイテム / Sample Restricted Item", "author_link": [], "item_type_id": "15", "publish_date": "2026-09-17", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "サンプル制限公開アイテム / Sample Restricted Item", "subitem_1551255648112": "ja"}]}, "item_1617186419668": {"attribute_name": "Creator", "attribute_type": "creator", "attribute_value_mlt": [{"creatorNames": [{"creatorName": "デモ 太郎", "creatorNameLang": "ja"}]}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_ddb1", "resourcetype": "dataset"}]}, "item_1617605131499": {"attribute_name": "File", "attribute_type": "file", "attribute_value_mlt": [{"url": {"url": "https://weko3.example.org/record/2003976/files/sample_restricted_data.txt"}, "date": [{"dateType": "Available", "dateValue": "2026-09-17"}], "terms": "term_free", "format": "text/plain", "provide": [{"role_id": "3", "workflow_id": "39001"}, {"role": "3", "workflow": "39001"}], "filename": "sample_restricted_data.txt", "filesize": [{"value": "134 B"}], "mimetype": "text/plain", "accessrole": "open_restricted", "version_id": "76f234e4-2460-4c86-b9b9-e0c871b381ee", "termsDescription": "これはデモ用の利用規約テキストです（架空）。"}]}, "relation_version_is_last": true}	6
2026-09-17 06:34:25.132515	2026-09-17 06:35:00.931397	d443270e-cbbb-4896-981d-614f9766b5f2	{"_oai": {"id": "oai:weko3.example.org:02003976.1", "sets": []}, "path": ["1758900000001"], "owner": "1", "recid": "2003976.1", "title": ["サンプル制限公開アイテム / Sample Restricted Item"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2026-09-17"}, "_buckets": {"deposit": "c1e6b18c-7051-4b54-bf98-00abf99f4717"}, "_deposit": {"id": "2003976.1", "pid": {"type": "depid", "value": "2003976.1", "revision_id": 0}, "owners": [1], "status": "published"}, "item_title": "サンプル制限公開アイテム / Sample Restricted Item", "author_link": [], "item_type_id": "15", "publish_date": "2026-09-17", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "サンプル制限公開アイテム / Sample Restricted Item", "subitem_1551255648112": "ja"}]}, "item_1617186419668": {"attribute_name": "Creator", "attribute_type": "creator", "attribute_value_mlt": [{"creatorNames": [{"creatorName": "デモ 太郎", "creatorNameLang": "ja"}]}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_ddb1", "resourcetype": "dataset"}]}, "item_1617605131499": {"attribute_name": "File", "attribute_type": "file", "attribute_value_mlt": [{"url": {"url": "https://weko3.example.org/record/2003976/files/sample_restricted_data.txt"}, "date": [{"dateType": "Available", "dateValue": "2026-09-17"}], "terms": "term_free", "format": "text/plain", "provide": [{"role_id": "3", "workflow_id": "39001"}, {"role": "3", "workflow": "39001"}], "filename": "sample_restricted_data.txt", "filesize": [{"value": "134 B"}], "mimetype": "text/plain", "accessrole": "open_restricted", "version_id": "", "termsDescription": "これはデモ用の利用規約テキストです（架空）。"}]}, "relation_version_is_last": true}	6
2026-09-17 06:37:22.797574	2026-09-17 06:37:23.104641	556f88a7-2164-4655-96ea-953365168917	{"_oai": {"id": "oai:weko3.example.org:02003977.1", "sets": ["1758900000001"]}, "path": ["1758900000001"], "owner": "3", "recid": "2003977.1", "title": ["サンプル制限公開アイテム / Sample Restricted Item"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2026-09-17"}, "_buckets": {"deposit": "c69e16b1-f626-42d6-94b2-a99140b9cb89"}, "_deposit": {"id": "2003977.1", "pid": {"type": "depid", "value": "2003977.1", "revision_id": 0}, "owners": [3], "status": "published", "created_by": 3}, "item_title": "サンプル制限公開アイテム / Sample Restricted Item", "author_link": [], "item_type_id": "31001", "publish_date": "2026-09-17", "publish_status": "0", "weko_shared_id": -1, "item_1616221831877": {"attribute_name": "Dataset Usage", "attribute_value_mlt": [{"subitem_restricted_access_dataset_usage": "sample_restricted_data.txt"}]}, "item_1616221941275": {"attribute_name": "Research Title", "attribute_value_mlt": [{"subitem_restricted_access_research_title": "デモ用研究タイトル / Demo Research Title"}]}, "item_1616221960771": {"attribute_name": "Research Plan", "attribute_value_mlt": [{"subitem_restricted_access_research_plan": "これはデモ用の架空の研究計画です。", "subitem_restricted_access_research_plan_type": "Free"}]}, "item_1616222047122": {"attribute_name": "WF Issued Date", "attribute_value_mlt": [{"subitem_restricted_access_wf_issued_date": "2026-09-17", "subitem_restricted_access_wf_issued_date_type": "Created"}]}, "item_1616222067301": {"attribute_name": "Application Date", "attribute_value_mlt": [{"subitem_restricted_access_application_date": "2026-09-17", "subitem_restricted_access_application_date_type": "Created"}]}, "item_1616222093486": {"attribute_name": "Approval Date", "attribute_value_mlt": [{"subitem_restricted_access_approval_date": "2026-09-17", "subitem_restricted_access_approval_date_type": "Created"}]}, "item_1616222117209": {"attribute_name": "Item Title", "attribute_value_mlt": [{"subitem_restricted_access_item_title": "サンプル制限公開アイテム / Sample Restricted Item"}]}, "item_1648134694613": {"attribute_name": "Applicant", "attribute_value_mlt": [{"subitem_fullname": "デモ 花子", "subitem_position": "その他", "subitem_mail_address": "contributor@example.org", "subitem_phone_number": "000-0000-0000", "subitem_university/institution": "デモ大学", "subitem_affiliated_division/department": "デモ学部"}]}, "relation_version_is_last": true}	5
\.

-- ---------------------------------------------------------------------
-- records_buckets
-- ---------------------------------------------------------------------
COPY public.records_buckets (record_id, bucket_id) FROM stdin;
c8af35ea-76bf-40a4-8366-07902b1a532e	19efee91-8841-4e06-a612-8ec571a9d8b3
d443270e-cbbb-4896-981d-614f9766b5f2	c1e6b18c-7051-4b54-bf98-00abf99f4717
4a23ff43-5325-4bce-af99-dc6d8f0f4a3b	845ccfdf-6316-452c-983a-68b09a04b982
556f88a7-2164-4655-96ea-953365168917	c69e16b1-f626-42d6-94b2-a99140b9cb89
\.

-- ---------------------------------------------------------------------
-- files_object
-- ---------------------------------------------------------------------
COPY public.files_object (created, updated, version_id, key, bucket_id, file_id, _mimetype, is_head, created_user_id, updated_user_id, is_show, is_thumbnail, root_file_id) FROM stdin;
2026-09-17 06:33:53.155148	2026-09-17 06:33:53.155151	76f234e4-2460-4c86-b9b9-e0c871b381ee	sample_restricted_data.txt	19efee91-8841-4e06-a612-8ec571a9d8b3	\N	\N	t	0	0	f	f	\N
\.

-- ---------------------------------------------------------------------
-- item_metadata
-- ---------------------------------------------------------------------
COPY public.item_metadata (created, updated, id, item_type_id, json, version_id) FROM stdin;
2026-09-17 06:34:25.779796	2026-09-17 06:34:26.093626	d443270e-cbbb-4896-981d-614f9766b5f2	15	{"pid": {"type": "depid", "value": "2003976", "revision_id": 0}, "owner": "1", "title": "サンプル制限公開アイテム / Sample Restricted Item", "owners": [1], "status": "published", "$schema": "/items/jsonschema/15", "pubdate": "2026-09-17", "item_1617186331708": [{"subitem_1551255647225": "サンプル制限公開アイテム / Sample Restricted Item", "subitem_1551255648112": "ja"}], "item_1617186419668": [{"creatorNames": [{"creatorName": "デモ 太郎", "creatorNameLang": "ja"}]}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_ddb1", "resourcetype": "dataset"}, "item_1617605131499": [{"url": {"url": "https://weko3.example.org/record/2003976/files/sample_restricted_data.txt"}, "date": [{"dateType": "Available", "dateValue": "2026-09-17"}], "terms": "term_free", "format": "text/plain", "provide": [{"role_id": "3", "workflow_id": "39001"}, {"role": "3", "workflow": "39001"}], "filename": "sample_restricted_data.txt", "filesize": [{"value": "134 B"}], "mimetype": "text/plain", "accessrole": "open_restricted", "version_id": "", "termsDescription": "これはデモ用の利用規約テキストです（架空）。"}]}	2
2026-09-17 06:33:55.17853	2026-09-17 06:34:24.740311	c8af35ea-76bf-40a4-8366-07902b1a532e	15	{"id": "2003976", "pid": {"type": "depid", "value": "2003976", "revision_id": 0}, "owner": "1", "title": "サンプル制限公開アイテム / Sample Restricted Item", "owners": [1], "status": "published", "$schema": "/items/jsonschema/15", "pubdate": "2026-09-17", "item_1617186331708": [{"subitem_1551255647225": "サンプル制限公開アイテム / Sample Restricted Item", "subitem_1551255648112": "ja"}], "item_1617186419668": [{"creatorNames": [{"creatorName": "デモ 太郎", "creatorNameLang": "ja"}]}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_ddb1", "resourcetype": "dataset"}, "item_1617605131499": [{"url": {"url": "https://weko3.example.org/record/2003976/files/sample_restricted_data.txt"}, "date": [{"dateType": "Available", "dateValue": "2026-09-17"}], "terms": "term_free", "format": "text/plain", "provide": [{"role_id": "3", "workflow_id": "39001"}, {"role": "3", "workflow": "39001"}], "filename": "sample_restricted_data.txt", "filesize": [{"value": "134 B"}], "mimetype": "text/plain", "accessrole": "open_restricted", "version_id": "76f234e4-2460-4c86-b9b9-e0c871b381ee", "termsDescription": "これはデモ用の利用規約テキストです（架空）。"}]}	2
2026-09-17 06:37:22.51334	2026-09-17 06:37:22.671283	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b	31001	{"owner": "3", "title": "サンプル制限公開アイテム / Sample Restricted Item", "$schema": "/items/jsonschema/31001", "pubdate": "2026-09-17", "item_1616221831877": {"subitem_restricted_access_dataset_usage": "sample_restricted_data.txt"}, "item_1616221941275": {"subitem_restricted_access_research_title": "デモ用研究タイトル / Demo Research Title"}, "item_1616221960771": {"subitem_restricted_access_research_plan": "これはデモ用の架空の研究計画です。", "subitem_restricted_access_research_plan_type": "Free"}, "item_1616222047122": {"subitem_restricted_access_wf_issued_date": "2026-09-17", "subitem_restricted_access_wf_issued_date_type": "Created"}, "item_1616222067301": {"subitem_restricted_access_application_date": "2026-09-17", "subitem_restricted_access_application_date_type": "Created"}, "item_1616222093486": {"subitem_restricted_access_approval_date": "2026-09-17", "subitem_restricted_access_approval_date_type": "Created"}, "item_1616222117209": {"subitem_restricted_access_item_title": "サンプル制限公開アイテム / Sample Restricted Item"}, "item_1648134694613": {"subitem_fullname": "デモ 花子", "subitem_position": "その他", "subitem_mail_address": "contributor@example.org", "subitem_phone_number": "000-0000-0000", "subitem_university/institution": "デモ大学", "subitem_affiliated_division/department": "デモ学部"}}	2
2026-09-17 06:37:22.963799	2026-09-17 06:37:23.040161	556f88a7-2164-4655-96ea-953365168917	31001	{"owner": "3", "title": "サンプル制限公開アイテム / Sample Restricted Item", "$schema": "/items/jsonschema/31001", "pubdate": "2026-09-17", "item_1616221831877": {"subitem_restricted_access_dataset_usage": "sample_restricted_data.txt"}, "item_1616221941275": {"subitem_restricted_access_research_title": "デモ用研究タイトル / Demo Research Title"}, "item_1616221960771": {"subitem_restricted_access_research_plan": "これはデモ用の架空の研究計画です。", "subitem_restricted_access_research_plan_type": "Free"}, "item_1616222047122": {"subitem_restricted_access_wf_issued_date": "2026-09-17", "subitem_restricted_access_wf_issued_date_type": "Created"}, "item_1616222067301": {"subitem_restricted_access_application_date": "2026-09-17", "subitem_restricted_access_application_date_type": "Created"}, "item_1616222093486": {"subitem_restricted_access_approval_date": "2026-09-17", "subitem_restricted_access_approval_date_type": "Created"}, "item_1616222117209": {"subitem_restricted_access_item_title": "サンプル制限公開アイテム / Sample Restricted Item"}, "item_1648134694613": {"subitem_fullname": "デモ 花子", "subitem_position": "その他", "subitem_mail_address": "contributor@example.org", "subitem_phone_number": "000-0000-0000", "subitem_university/institution": "デモ大学", "subitem_affiliated_division/department": "デモ学部"}}	2
\.

-- ---------------------------------------------------------------------
-- pidrelations_pidrelation
-- ---------------------------------------------------------------------
COPY public.pidrelations_pidrelation (created, updated, parent_id, child_id, relation_type, index) FROM stdin;
2026-09-17 06:32:27.106201	2026-09-17 06:34:25.159513	32058	32056	2	0
2026-09-17 06:34:25.152128	2026-09-17 06:34:25.159531	32058	32060	2	1
2026-09-17 06:37:22.257437	2026-09-17 06:37:22.808889	32066	32064	2	0
2026-09-17 06:37:22.807676	2026-09-17 06:37:22.808902	32066	32068	2	1
\.

-- ---------------------------------------------------------------------
-- workflow_activity
-- ---------------------------------------------------------------------
COPY public.workflow_activity (status, created, updated, id, activity_id, activity_name, item_id, workflow_id, workflow_status, flow_id, action_id, action_status, activity_login_user, activity_update_user, activity_status, activity_start, activity_end, activity_community_id, activity_confirm_term_of_use, title, shared_user_id, temp_data, approval1, approval2, extra_info, action_order) FROM stdin;
N	2026-09-17 06:37:22.124937	2026-09-17 06:37:23.291471	8325	A-20260917-00001	\N	4a23ff43-5325-4bce-af99-dc6d8f0f4a3b	39001	\N	39001	2	F	3	3	F	2026-09-17 06:37:22.123573	2026-09-17 06:37:23.290517	\N	t	\N	\N	\N	\N	\N	{"file_name": "sample_restricted_data.txt", "record_id": 2003976, "user_mail": "contributor@example.org", "related_title": "サンプル制限公開アイテム / Sample Restricted Item", "is_restricted_access": true}	4
\.

-- ---------------------------------------------------------------------
-- workflow_activity_action
-- ---------------------------------------------------------------------
COPY public.workflow_activity_action (status, created, updated, id, activity_id, action_id, action_status, action_comment, action_handler, action_order) FROM stdin;
N	2026-09-17 06:37:22.173741	2026-09-17 06:37:22.17375	34220	A-20260917-00001	1	F	\N	3	1
N	2026-09-17 06:37:22.17743	2026-09-17 06:37:22.177436	34221	A-20260917-00001	3	F	\N	3	2
N	2026-09-17 06:37:22.178157	2026-09-17 06:37:22.178161	34222	A-20260917-00001	4	F	\N	-1	3
N	2026-09-17 06:37:22.178706	2026-09-17 06:37:22.17871	34223	A-20260917-00001	2	F	\N	3	4
\.

-- ---------------------------------------------------------------------
-- workflow_action_history
-- ---------------------------------------------------------------------
COPY public.workflow_action_history (status, created, updated, id, activity_id, action_id, action_version, action_status, action_user, action_date, action_comment, action_order) FROM stdin;
N	2026-09-17 06:37:22.154563	2026-09-17 06:37:22.15457	33190	A-20260917-00001	1	1.0.0	F	3	2026-09-17 06:37:22.123573	Begin Action	1
N	2026-09-17 06:37:23.181015	2026-09-17 06:37:23.181021	33191	A-20260917-00001	3	\N	\N	3	2026-09-17 06:37:23.173192	\N	2
N	2026-09-17 06:37:23.29699	2026-09-17 06:37:23.296996	33192	A-20260917-00001	2	1.0.0	F	2	2026-09-17 06:37:23.29614	End Action	4
\.

-- ---------------------------------------------------------------------
-- file_onetime_download
-- ---------------------------------------------------------------------
COPY public.file_onetime_download (created, updated, id, file_name, user_mail, record_id, download_count, expiration_date, extra_info) FROM stdin;
2026-09-17 06:37:23.246002	2026-09-17 06:37:23.246007	3100	sample_restricted_data.txt	contributor@example.org	2003976	4	7	{"is_guest": false, "send_usage_report": true, "usage_application_activity_id": "A-20260917-00001"}
\.

-- ---------------------------------------------------------------------
-- file_permission:
--   **意図的に 1 行も入れない。** これが本不具合の DB 上のシグネチャ。
--   利用申請の開始時に status=-1 の行が作られるが、承認完了時
--   (weko_workflow/views.py の next_action, 1153-1156 行付近) で
--   FilePermission.delete_object() により削除され、status=1 に更新される
--   経路はコード上どこにも存在しない。
--   そのため weko_records_ui/permissions.py:check_permission_period() は
--   常に False を返し、詳細画面は「申請」ボタンを出し続ける。
-- ---------------------------------------------------------------------

--
-- 明示 ID を挿入したテーブルのシーケンスを進めておく（既存採番との衝突防止）。
--
SELECT setval('public.pidstore_pid_id_seq',            GREATEST((SELECT last_value FROM public.pidstore_pid_id_seq),            (SELECT max(id) FROM public.pidstore_pid)));
SELECT setval('public.workflow_flow_define_id_seq',    GREATEST((SELECT last_value FROM public.workflow_flow_define_id_seq),    (SELECT max(id) FROM public.workflow_flow_define)));
SELECT setval('public.workflow_flow_action_id_seq',    GREATEST((SELECT last_value FROM public.workflow_flow_action_id_seq),    (SELECT max(id) FROM public.workflow_flow_action)));
SELECT setval('public.workflow_workflow_id_seq',       GREATEST((SELECT last_value FROM public.workflow_workflow_id_seq),       (SELECT max(id) FROM public.workflow_workflow)));
SELECT setval('public.workflow_activity_id_seq',       GREATEST((SELECT last_value FROM public.workflow_activity_id_seq),       (SELECT max(id) FROM public.workflow_activity)));
SELECT setval('public.workflow_activity_action_id_seq',GREATEST((SELECT last_value FROM public.workflow_activity_action_id_seq),(SELECT max(id) FROM public.workflow_activity_action)));
SELECT setval('public.workflow_action_history_id_seq', GREATEST((SELECT last_value FROM public.workflow_action_history_id_seq), (SELECT max(id) FROM public.workflow_action_history)));
SELECT setval('public.file_onetime_download_id_seq',   GREATEST((SELECT last_value FROM public.file_onetime_download_id_seq),   (SELECT max(id) FROM public.file_onetime_download)));

COMMIT;

\echo '== download_button_bug_repro fixture loaded =='
