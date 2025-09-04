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
-- Data for Name: jsonld_mappings; Type: TABLE DATA; Schema: public; Owner: invenio
--

INSERT INTO public.jsonld_mappings (created, updated, id, name, mapping, item_type_id, version_id, is_deleted) VALUES
('2025-02-25 04:05:58.957687',	'2025-02-25 04:05:58.957691',	51000,	'未病アイテムタイプ',	'{"PubDate": "datePublished", "備考.値": "rdm:description", "キーワード": "keywords.value", "ライセンス": "license", "有償・無償": "rdm:licenseInformation.ams:dataPolicyFree", "資源タイプ": "dc:type", "データ作成者": "creator", "データ管理者": "contributor", "ファイル情報": "hasPart", "有償・無償.値": "rdm:licenseInformation.ams:dataPolicyFree.value", "その他補足事項": "rdm:storedIn", "プロジェクトURL": "ams:projectid", "プロジェクト名": "name", "商用利用の可否": "rdm:licenseInformation.ams:availabilityOfCommercialUse", "解析対象データ": "ams:analysisType.ams:analysisType", "キーワード.主題": "keywords.value.value", "キーワード.言語": "keywords.value.language", "有償・無償.言語": "rdm:licenseInformation.ams:dataPolicyFree.language", "（IC無の場合）.値": "rdm:AccessRights.ams:icIsNo", "その他補足事項.値": "rdm:storedIn.rdm:description", "ファイル情報.日付": "hasPart.datetime", "商用利用の可否.値": "rdm:licenseInformation.ams:availabilityOfCommercialUse.value", "解析対象データ.値": "ams:analysisType.ams:analysisType.value", "データセットの分野": "rdm:field", "データセットの名称": "rdm:name", "謝辞に記載の要不要": "rdm:licenseInformation.ams:necessityOfIncludingInAcknowledgments", "連絡・許諾の要不要": "rdm:licenseInformation.ams:necessityOfContactAndPermission", "ファイル情報.本文URL": "hasPart.identifier", "商用利用の可否.言語": "rdm:licenseInformation.ams:availabilityOfCommercialUse.language", "解析対象データ.言語": "ams:analysisType.ams:analysisType.language", "取得データの対象種別": "ams:targetTypeOfAcquiredData", "アクセス権.アクセス権": "rdm:accessRightsInformation", "データ作成者.作成者名": "creator.givenName", "データ作成者.作成者姓": "creator.familyName", "データ管理者.寄与者名": "contributor.givenName", "データ管理者.寄与者姓": "contributor.familyName", "ファイル情報.アクセス": "hasPart.accessMode", "メタデータ更新日.日付": "dateModified", "メタデータ登録日.日付": "dateCreated", "ライセンス.ライセンス": "license.name", "謝辞に記載の要不要.値": "rdm:licenseInformation.ams:necessityOfIncludingInAcknowledgments.value", "資源タイプ.資源タイプ": "dc:type.value", "連絡・許諾の要不要.値": "rdm:licenseInformation.ams:necessityOfContactAndPermission.value", "ファイル情報.日付.日付": "hasPart.datetime.date", "リポジトリURL・DOIリンク": "rdm:storedIn", "データセットの分野.主題": "rdm:field.value.value", "データセットの分野.言語": "rdm:field.value.language", "データセットの名称.言語": "rdm:name.value.language", "データ作成者.作成者別名": "creator.alternateName", "データ作成者.作成者姓名": "creator.name", "データ作成者.作成者所属": "creator.affiliation", "データ管理者.寄与者別名": "contributor.alternateName", "データ管理者.寄与者姓名": "contributor.name", "データ管理者.寄与者所属": "contributor.affiliation", "ファイル情報.ファイル名": "hasPart.name", "取得データの対象種別.値": "ams:targetTypeOfAcquiredData.value", "謝辞に記載の要不要.言語": "rdm:licenseInformation.ams:necessityOfIncludingInAcknowledgments.language", "連絡・許諾の要不要.言語": "rdm:licenseInformation.ams:necessityOfContactAndPermission.language", "データ作成者.作成者名.名": "creator.givenName.value", "データ作成者.作成者姓.姓": "creator.familyName.value", "データ管理者.寄与者名.名": "contributor.givenName.value", "データ管理者.寄与者姓.姓": "contributor.familyName.value", "解析対象データ（その他）": "ams:analysisType.ams:analysisType", "（IC有の場合）海外提供.値": "rdm:AccessRights.ams:overseasOfferings", "データ作成者.作成者識別子": "creator.identifier", "データ管理者.寄与者識別子": "contributor.identifier", "ファイル情報.フォーマット": "hasPart.encodingFormat", "プロジェクトURL.関連タイプ": "$isVersionOf", "取得データの対象種別.言語": "ams:targetTypeOfAcquiredData.language", "（ヒト）匿名加工の有無.値": "rdm:AccessRights.ams:anonymousProcessing", "データ作成者.作成者名.言語": "creator.givenName.language", "データ作成者.作成者姓.言語": "creator.familyName.language", "データ管理者.寄与者名.言語": "contributor.givenName.language", "データ管理者.寄与者姓.言語": "contributor.familyName.language", "ファイル情報.サイズ.サイズ": "hasPart.contentSize", "ファイル情報.公開日.公開日": "hasPart.datePublished", "ファイル情報.本文URL.ラベル": "hasPart.@id", "（IC有の場合）産業利用等.値": "rdm:AccessRights.ams:industrialUse", "データセットの名称.タイトル": "rdm:name.value.value", "ファイル情報.バージョン情報": "hasPart.version", "メタデータ更新日.日付タイプ": "$Updated", "メタデータ登録日.日付タイプ": "$Created", "解析対象データ（その他）.値": "ams:analysisType.ams:analysisType.value", "資源タイプ.資源タイプ識別子": "dc:type.@id", "データ作成者.作成者別名.別名": "creator.alternateName.value", "データ作成者.作成者別名.言語": "creator.alternateName.language", "データ作成者.作成者姓名.姓名": "creator.name.value", "データ作成者.作成者姓名.言語": "creator.name.language", "データ管理者.寄与者別名.別名": "contributor.alternateName.value", "データ管理者.寄与者別名.言語": "contributor.alternateName.language", "データ管理者.寄与者姓名.姓名": "contributor.name.value", "データ管理者.寄与者姓名.言語": "contributor.name.language", "ファイル情報.日付.日付タイプ": "hasPart.datetime.type", "解析対象データ（その他）.言語": "ams:analysisType.ams:analysisType.language", "プロジェクト名.研究課題名.言語": "name.language", "その他条件、あるいは、特記事項": "rdm:licenseInformation.ams:otherConditionsOrSpecialNotes", "（IC有の場合）第三者提供の同意.値": "rdm:AccessRights.ams:consentForProvisionToAThirdParty", "その他条件、あるいは、特記事項.値": "rdm:licenseInformation.ams:otherConditionsOrSpecialNotes.value", "リポジトリURL・DOIリンク.関連タイプ": "rdm:storedIn.@type", "データ作成者.作成者所属.所属機関名": "creator.affiliation.name", "データ管理者.寄与者所属.所属機関名": "contributor.affiliation.name", "その他条件、あるいは、特記事項.言語": "rdm:licenseInformation.ams:otherConditionsOrSpecialNotes.language", "プロジェクトURL.関連識別子.関連識別子": "ams:projectid.value", "プロジェクト名.研究課題名.研究課題名": "name.value", "データ作成者.作成者識別子.作成者識別子": "creator.identifier.value", "データ管理者.寄与者所属.所属機関識別子": "contributor.affiliation.identifier", "データ管理者.寄与者識別子.寄与者識別子": "contributor.identifier.value", "ファイル情報.本文URL.オブジェクトタイプ": "hasPart.identifier.jpcoar:objectType", "データ作成者.作成者所属.所属機関名.言語": "creator.affiliation.name.language", "データ管理者.寄与者所属.所属機関名.言語": "contributor.affiliation.name.language", "データ管理者.寄与者識別子.寄与者識別子URI": "contributor.identifier.uri", "リポジトリURL・DOIリンク.関連名称.関連名称": "rdm:storedIn.rdm:url", "データ作成者.作成者識別子.作成者識別子Scheme": "creator.identifier.jpcoar:nameIdentifierScheme", "データ管理者.寄与者識別子.寄与者識別子Scheme": "contributor.identifier.jpcoar:nameIdentifierScheme", "リポジトリURL・DOIリンク.関連識別子.関連識別子": "rdm:storedIn.@id", "データ作成者.作成者所属.所属機関名.所属機関名": "creator.affiliation.name.value", "データ管理者.寄与者所属.所属機関名.所属機関名": "contributor.affiliation.name.value", "実験（もしくは解析結果・解析ツールなど）の目的": "ams:purposeOfExperiment", "実験（もしくは解析結果・解析ツールなど）の目的.値": "ams:purposeOfExperiment.value", "（アクセス権が「公開」でない場合）公開予定日.日付": "rdm:dateAvailable", "実験（もしくは解析結果・解析ツールなど）の目的.言語": "ams:purposeOfExperiment.language", "データ作成者.作成者所属.所属機関識別子.所属機関識別子": "creator.affiliation.identifier.value", "データ管理者.寄与者所属.所属機関識別子.所属機関識別子": "contributor.affiliation.identifier.value", "データ作成者.作成者所属.所属機関識別子.所属機関識別子URI": "creator.affiliation.identifier.uri", "データ管理者.寄与者所属.所属機関識別子.所属機関識別子URI": "contributor.affiliation.identifier.uri", "（アクセス権が「公開」でない場合）公開予定日.日付タイプ": "$Available", "プロジェクト名.プログラム情報識別子.プログラム情報識別子": "name.@id", "データ作成者.作成者所属.所属機関識別子.所属機関識別子Scheme": "creator.affiliation.identifier.jpcoar:nameIdentifierScheme", "データ管理者.寄与者所属.所属機関識別子.所属機関識別子Scheme": "contributor.affiliation.identifier.jpcoar:nameIdentifierScheme", "謝辞に記載する名称（個人名、グループ名等）、または謝辞全文": "rdm:licenseInformation.ams:namesToBeIncludedInTheAcknowledgments", "実験状況など（もしくは解析結果・解析ツールの背景など）の説明": "ams:descriptionOfExperimentalCondition", "謝辞に記載する名称（個人名、グループ名等）、または謝辞全文.値": "rdm:licenseInformation.ams:namesToBeIncludedInTheAcknowledgments.value", "実験状況など（もしくは解析結果・解析ツールの背景など）の説明.値": "ams:descriptionOfExperimentalCondition.value", "謝辞に記載する名称（個人名、グループ名等）、または謝辞全文.言語": "rdm:licenseInformation.ams:namesToBeIncludedInTheAcknowledgments.language", "実験状況など（もしくは解析結果・解析ツールの背景など）の説明.言語": "ams:descriptionOfExperimentalCondition.language"}',	51000,	1,	false)
ON CONFLICT (id) DO UPDATE SET
  created = EXCLUDED.created,
  updated = EXCLUDED.updated,
  id = EXCLUDED.id,
  name = EXCLUDED.name,
  mapping = EXCLUDED.mapping,
  item_type_id = EXCLUDED.item_type_id,
  version_id = EXCLUDED.version_id,
  is_deleted = EXCLUDED.is_deleted;


--
-- Name: jsonld_mappings_seq; Type: SEQUENCE SET; Schema: public; Owner: invenio
--

--
-- PostgreSQL database dump complete
--
