# Legacy SQL Inventory

These files are legacy DB change assets under `postgresql/ddl/` and `postgresql/update/`.
They are candidates for future classification and Alembic migration.

## Review status key

- `unreviewed`: not yet classified
- `migrated`: behavior is already covered by Alembic or another maintained path
- `keep`: still intentionally retained outside Alembic
- `remove`: obsolete after verification

## Inventory

| File | Status | Notes |
|------|--------|-------|
| `postgresql/ddl/W-OA-user_activity_log.sql` | unreviewed | |
| `postgresql/ddl/W2023-21 update_resticted_items.sql` | unreviewed | |
| `postgresql/ddl/W2023-21 workflow_flow_action_role.sql` | unreviewed | |
| `postgresql/ddl/W2023-22 mail_template_genre.sql` | unreviewed | |
| `postgresql/ddl/W2023-23-item_application.sql` | unreviewed | |
| `postgresql/ddl/W2023-23-request_mail.sql` | unreviewed | |
| `postgresql/ddl/W2024-58-ams.sql` | unreviewed | |
| `postgresql/ddl/W2025-29.sql` | unreviewed | |
| `postgresql/ddl/WOA-06-jsonld_mapping.sql` | unreviewed | |
| `postgresql/ddl/fix_issue_37699.sql` | unreviewed | |
| `postgresql/ddl/fix_issue_37736.sql` | unreviewed | |
| `postgresql/ddl/fix_issue_39700.sql` | unreviewed | |
| `postgresql/ddl/fix_itemtype_issue_45614.sql` | unreviewed | |
| `postgresql/ddl/pr1025.sql` | unreviewed | |
| `postgresql/ddl/pr1274.sql` | unreviewed | |
| `postgresql/ddl/pr873.sql` | unreviewed | |
| `postgresql/ddl/sp52_workflow_userrole.sql` | unreviewed | |
| `postgresql/ddl/sp53_index_biblio_flag.sql` | unreviewed | |
| `postgresql/ddl/sp54_shibboleth_userrole.sql` | unreviewed | |
| `postgresql/ddl/sp56-change-record-save-logic.sql` | unreviewed | |
| `postgresql/ddl/sp56-onetime-download.sql` | unreviewed | |
| `postgresql/ddl/sp56-widgetDesign.sql` | unreviewed | |
| `postgresql/ddl/sp57-restricted-access.sql` | unreviewed | |
| `postgresql/ddl/sp58-stats-event-issue.sql` | unreviewed | |
| `postgresql/ddl/sp59-communities-role.sql` | unreviewed | |
| `postgresql/ddl/sp61-AllowsTableManagementOfFacetItemSettings.sql` | unreviewed | |
| `postgresql/ddl/sp63-ReplaceFileContents.sql` | unreviewed | |
| `postgresql/ddl/sp65-ExportAuthors.sql` | unreviewed | |
| `postgresql/ddl/sp66-ImportAuthors.sql` | unreviewed | |
| `postgresql/ddl/sp70-FixOaireVersionInOaiserverSchema.sql` | unreviewed | |
| `postgresql/ddl/sp70-enhancedSiteInformationScreen.sql` | unreviewed | |
| `postgresql/ddl/sp70-gakuninrdm.sql` | unreviewed | |
| `postgresql/ddl/sp70-resync.sql` | unreviewed | |
| `postgresql/ddl/sp70-workflow_location.sql` | unreviewed | |
| `postgresql/ddl/sp71-UpdateAuthorPermission.sql` | unreviewed | |
| `postgresql/ddl/sp71-UpdateSearchLicence.sql` | unreviewed | |
| `postgresql/ddl/sp71-oaiset.sql` | unreviewed | |
| `postgresql/ddl/sp72-CreateAuthersAffiliation.sql` | unreviewed | |
| `postgresql/ddl/sp72-createindex.sql` | unreviewed | |
| `postgresql/ddl/v0.9.27.sql` | unreviewed | |
| `postgresql/update/2023_Q4.sql` | unreviewed | |
| `postgresql/update/202409_BioResource_ddl.sql` | unreviewed | |
| `postgresql/update/fix_issue45092.sql` | unreviewed | |
| `postgresql/update/v0.9.15_search_management.sql` | unreviewed | |
| `postgresql/update/v1.0.7b.sql` | unreviewed | |
| `postgresql/update/v1.0.8.sql` | unreviewed | |
| `postgresql/update/v1_0_7a2.sql` | unreviewed | |
