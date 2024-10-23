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

## [v1.0.7a] 2024-10-21
### Added
None
### Changed
Added the functionality for users to unlock activity.
### Deprecated
None
### Removed
None
### Fixed
- Fixed an issue where comments in the first index would overwrite comments in the same-level indices.
- Fixed an issue where the workflow locking feature was not working when opened in multiple tabs.
- Fixed an issue with the validation check of dissertations where the StartPage was being included incorrectly.
- Fixed an encoding range issue during Shibboleth redirection.
### Security
None

## [v1.0.9] - 2024-10-03
### Fixed
- Fixed an issue where running the script `renew_all_item_types.py` cleared the attribute information of item types. Added a tool, `replace_item_type_data.py`, to restore the cleared data to a specified date and time.
- Modified the error message "Item already DELIETED in the system" on the import screen to be displayed in Japanese.

[v1.0.9] https://github.com/RCOSDP/weko/compare/v1.0.8...v1.0.9
[v1.0.8] https://github.com/RCOSDP/weko/compare/v1.0.7...v1.0.8