# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [v1.0.8a] 2025-07-08
### Fixed
- Fixed an issue where the tika library was not included in the Docker image.


## [v1.0.8] 2025-05-20
### Changed
- Improved an issue where the Tika process consumed excessive memory.
- Optimized inefficient logic in index display processing to improve rendering speed.
- Changed the timeout duration for Elasticsearch index creation from 30 seconds to 2 minutes.
### Fixed
- Fixed a problem where bulk import/export operations failed due to database connection timeouts.
- Fixed a 500 error caused by citation formatting for records.
- Resolved an issue where users could not edit items due to a message stating "Another activity is already open" caused by expired DB sessions.
- Fixed a problem where Redis TTL was set to unlimited, causing activity locks.
- Fixed an issue where accessing an activity sometimes showed a popup: "The item you are editing has already been deleted."
- Fixed a 500 error caused by unexpected query parameters.
- Fixed a 500 error occurring at /items/export.
- Fixed a 500 error occurring at /admin/load_widget_design_setting.
- Fixed a 500 error occurring at /get_uri.
- Fixed a 500 error occurring at /api/stats/<record_id>.

## [v1.0.7b] 2025-01-06 
### Changed
- Improved data compatibility with migrated institutions. 
- Added the function to specify an itemtype ID as a target for reindexing. 
### Fixed  
- Reduced the increasing number of database queries.  


## [v1.0.7a2] - 2024-12-27  
### Changed
- Enabled the edit of metadata fields, including author identifier URLs and author affiliation identifier URLs.
### Fixed
- Fixed a bug in the data correction tool (`itemtype_fix_form_title.py`) for resolving inconsistencies between render and form.  
- Fixed an issue where importing items would fail if "Allow Multiple" was not checked for the item title.  
- Fixed a bug causing errors when importing items with thumbnails.  
- Resolved an issue where the item details screen could not be displayed if the creator identifier was set to "hide."  

## [v1.0.7a] - 2024-10-29
### Changed
- Added a feature that allows users to forcibly unlock activity locks.
### Fixed
- Fixed an issue where comments on the first index would overwrite comments on indexes at the same level.
- Fixed an issue where the item details screen and the item type editing screen could not be displayed due to data errors in the item type mapping.
- Fixed an issue where the lock function was not working when the workflow was opened in multiple tabs.
- Corrected an issue with the validation check for dissertations where the StartPage field was included erroneously.
- Fixed an URL encoding issue of Shibboleth redirection.
- Fixed issues with the item type correction tool and added a tool to revert states to a previous version.

## [v1.0.9] - 2024-10-03
### Fixed
- Fixed an issue where running the script `renew_all_item_types.py` cleared the attribute information of item types. Added a tool, `replace_item_type_data.py`, to restore the cleared data to a specified date and time.
- Modified the error message "Item already DELIETED in the system" on the import screen to be displayed in Japanese.

## [v1.0.8] - 2024-10-02
### Changed
- Modified the email processing logic for the feedback email feature
- Updated the Secret URL button to be accessible to behalf of creator as well
- Organized the Secret URL section in the admin panel
### Fixed
- Fixed issues with JPCOAR Schema 2.0 catalog metadata
- Fixked an feature restrictions during bulk import function issue 
- Fixed a bug in the bulk deletion function for indexes

## [v1.0.7] - 2024-09-09
### Added
- Added validation to prevent searching with non-existent dates in advanced search date input.
- Added an automatic metadata input feature using CiNii Research ID.
- Added functionality to prevent deletion and editing of indexes set for harvesting.
- Added functionality to prevent deletion and editing of item types during import.
- Added a "Back Button" function to activity execution.
- Added index selection as a criterion for starting activities when editing items.
- Added icon display for author ID in item lists.
- Added functionality to delete previous versions of items.
- Added a Secret URL issuing feature.
- Added an OAIPMH provider and harvester function compatible with JPCOAR 2.0 schema.
- Added DOI validation functionality compatible with JPCOAR 2.0.
### Changed
- Updated export functionality to include file paths in TSV files even without file output.
- Modified the full-text extraction logic.
- Partially revised and enhanced item creation event logging for bulk registration and harvesting.
- Changed processes that previously used browser time to now use server time.
- Modified file embedding in widgets to use relative paths instead of FQDN.
- Changed property mapping to output the first property when title is mapped multiple times.
- Modified JaLC DOI issuance check to no longer require the "xml" attribute for "dc".
- Made some resource type changes possible for items with assigned DOIs.
### Fixed
- Fixed an error issue when user names are not recorded, and added session expiration handling during bulk registration.
- Resolved issues with multiple mappings.
- Fixed a bug that prevented the deletion of DOI-withdrawn items with multiple files.
- Corrected an issue where the static function of item types failed if no input value was present.
- Fixed an issue where child indexes would display in English if the parent index lacked a Japanese name.
- Resolved an issue where display options were overwritten when using the same property multiple times.
- Fixed an issue where items with a future publication date were not displayed in the item list for users other than the registrant.
- Resolved error handling issues when an error occurs during author consolidation.
- Fixed an issue where author IDs added were in an uneditable state.
- Corrected an issue preventing searches by "last name △ first name" in Author DB > Bulk Registration.
- Fixed an author consolidation issue when the author's "institution identifier" and corresponding institution name were not set.
- Corrected import functionality to prevent importing items into non-existent indexes.
- Resolved an issue where combining full-text and detailed search fields was not functional.
- Fixed an issue where "Item Link" information persisted in the database after activity completion during new item registration.
- Corrected a display issue in the "Most Recently Published Item’s Index" setting where index publication status was not checked.
- Fixed an issue where an error occurred upon clicking the information button in item detail screens with hidden publication dates.
- Fixed pagination issues when search results exceeded 10,000 items.
- Enabled file size autofill during bulk registration.
- Resolved issues preventing file output when multiple errors occur in bulk registration results.
- Fixed an issue with the display of checkbox property attributes in detailed search conditions.
- Corrected an issue where email addresses added in the feedback email field were not reflected.
- Fixed a "TypeError" JSON error occurring during harvests.
- Resolved an issue preventing PDF conversion for content files stored in object storage.
- Adjusted custom report aggregation to include the current day.
- Corrected custom sort functionality for unspecified items in ascending/descending order.
- Changed the display of open access dates from UTC to local time.
- Fixed server error interruptions during imports.
- Resolved display issues with index name changes.
- Fixed an issue where non-breaking spaces in index names prevented detailed search screens from displaying.
- Corrected index aggregation logic to improve handling of large numbers of indexes.
- Resolved an issue preventing activity lock release.
- Corrected inconsistencies in index affiliation between item editing and item display screens.
- Fixed an issue where the "Publication Date" shown by the Information button in item detail screens did not reflect the file attribute information.
- Updated item detail screens to accept YYYY and YYYY-MM formats for the "Cite as" display.
- Resolved an issue where incomplete item information was retained after activity exit in the index selection screen during individual item registration.
- Fixed a non-functional ItemType sort option in the item list.
- Enabled numeric sorting for "ID" in item lists.
- Resolved an issue where automatic thumbnail adjustment in item lists was not functioning correctly.
- Adjusted item version ranking to reflect cumulative views across all versions.
- Updated item type edit screens to hide items marked as hidden from item lists and "Cite as" display.
- Corrected debug logs appearing in web container logs.
- Fixed partial OAuth2 functionality issues in SWORDv3.
- Corrected display issues of hidden title readings in title, ranking, and item list.
- Resolved a CNRI handle assignment issue caused by a CNRI server error.
- Fixed an issue where items with only English titles did not display the title in "Cite as".
- Updated the Admin > Web Design > Widget screen to enable ID-based searches.
- Resolved an issue where two activities were generated for a single item.
- Fixed an issue where "Item Link" information was not carried over during "Upgrade Version".
- Resolved an issue where items could link to themselves when linked with the "Item Link" action.
- Fixed a persistent loading issue in the item type edit screen.
- Resolved an issue where Publish Status did not display in item detail screens after login.

[v1.0.7] https://github.com/RCOSDP/weko/compare/v0.9.6...v1.0.7
[v1.0.7a] https://github.com/RCOSDP/weko/compare/v1.0.7...v1.0.7a
[v1.0.7a2] https://github.com/RCOSDP/weko/compare/v1.0.7a...v1.0.7a2
[v1.0.7b] https://github.com/RCOSDP/weko/compare/v1.0.7a2...v1.0.7b
[v1.0.8] https://github.com/RCOSDP/weko/compare/v1.0.7b...v1.0.8
[v1.0.8a] https://github.com/RCOSDP/weko/compare/v1.0.8...v1.0.8a