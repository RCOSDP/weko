"""Resource for weko-items-ui log messages."""

WEKO_ACCOUNTS_MESSAGE = {
    'WEKO_ITEMS_UI_SEARCH_ITEM': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1001',
        'msgstr': "Search item: {query}, result: {num}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1001',
        'msgstr': "FAILED to search item: {query}",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1002',
        'msgstr': "Search condition added.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1003',
        'msgstr': "Search condition deleted.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1004',
        'msgstr': "Items added to the search condition have been exported.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1002',
        'msgstr': "FAILED to add search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1003',
        'msgstr': "FAILED to delete search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1004',
        'msgstr': "FAILED to export items added to the search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1005',
        'msgstr': "Settings for how items are displayed have been changed.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1005',
        'msgstr': "FAILED to change faceted search settings to {set_value}.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1006',
        'msgstr': "FAILED to change item display method settings.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1006',
        'msgstr': "RSS output for items corresponding to the search results.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1007',
        'msgstr': "Failed to output RSS for the item corresponding to the search result.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1007',
        'msgstr': "RSS feeds are now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1008',
        'msgstr': "RSS document has been output.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1008',
        'msgstr': "FAILED to output RSS document.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_CHANGE_DISPLAY_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1009',
        'msgstr': "The display setting for search results has been changed to {conf_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_SAVE_INDEX_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1009',
        'msgstr': "Failed to save changes to index settings.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_ENABLE_ITEM_EXPORT': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1010',
        'msgstr': "Item export is now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_DISABLE_ITEM_EXPORT': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1011',
        'msgstr': "Item export is now disabled.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_SAVED_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1012',
        'msgstr': "Index designation saved: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_QUIT_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1013',
        'msgstr': "Index designation quitted: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_SAVE_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1010',
        'msgstr': "FAILED to save index designation: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_POPULATE_AUTO_METADATA_CROSSREF': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1014',
        'msgstr': "Metadata was automatically populated via CrossRef. Itemid: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_POPULATE_AUTO_METADATA_CINII': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1015',
        'msgstr': "Metadata was automatically populated via CiNii. Itemid: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_POPULATE_AUTO_METADATA_WEKOID': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1016',
        'msgstr': "Metadata was automatically populated via WEKOID. Itemid: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_POPULATE_AUTO_METADATA_CROSSREF': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1011',
        'msgstr': "FAILED to automatically populate metadata via CrossRef. Itemid: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_POPULATE_AUTO_METADATA_CINII': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1012',
        'msgstr': "FAILED to automatically populate metadata via CiNii. Itemid: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_POPULATE_AUTO_METADATA_WEKOID': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1013',
        'msgstr': "FAILED to automatically populate metadata via WEKOID. Itemid: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_JSON': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1017',
        'msgstr': "Selected items have been exported in json format.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_BIBTEX': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1018',
        'msgstr': "Selected items have been exported in bibtex format.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_JSON_WITH_FILE_CONTENTS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1019',
        'msgstr': "Selected items have been exported in json format with File Contents.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_BIBTEX_WITH_FILE_CONTENTS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1020',
        'msgstr': "Selected items have been exported in bibtex format with File Contents.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_EXPORT_ITEM_IN_JSON': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1014',
        'msgstr': "FAILED to export selected items in json format.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_EXPORT_ITEM_IN_BIBTEX': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1015',
        'msgstr': "FAILED to export selected items in bibtex format.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_ASSIGN_PROXY_CONTRIBUTOR': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1021',
        'msgstr': "A proxy contributor has been assigned for the item: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_ASSIGN_PROXY_CONTRIBUTOR': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1016',
        'msgstr': "Failed to assign a proxy contributor for the item.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_REGISTER_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1022',
        'msgstr': "Destination index has been registered: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_REGISTER_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1017',
        'msgstr': "FAILED to register index designation: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_SAVED_RANKING_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1023',
        'msgstr': "Ranking settings have been saved.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_SAVE_RANKING_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1018',
        'msgstr': "FAILED to save ranking settings.",
        'msglvl': 'ERROR',
    },
    'WEKO_ITEMS_UI_CREATED_RANKING_LISTS': {
        'msgid': 'WEKO_ITEMS_UI_INFO_1024',
        'msgstr': "Ranking lists have been created.",
        'msglvl': 'INFO',
    },
    'WEKO_ITEMS_UI_FAILED_CREATE_RANKING_LISTS': {
        'msgid': 'WEKO_ITEMS_UI_ERROR_1019',
        'msgstr': "FAILED to create ranking lists.",
        'msglvl': 'ERROR',
    },
}
