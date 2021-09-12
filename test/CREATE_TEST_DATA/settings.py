# author
AUTHOR_LIMIT = 30000


# event
COUNTRYS = ['JP', 'US', None]
USERS = [
    {
        'id': 'guest',
        'role': 'guest'
    },
    {
        'id': '1',
        'role': 'System Administrator'
    },
    {
        'id': '2',
        'role': 'Repository Administrator'
    },
    {
        'id': '3',
        'role': 'Contributor'
    },
    {
        'id': '4',
        'role': ''
    },
    {
        'id': '5',
        'role': 'Community Administrator'
    }
]

TOP_VIEW_LIMIT = 10000
SEARCH_LIMIT = 10000
RECORD_VIEW_LIMIT = 10000
FILE_LIMIT = 10000

# widget
PAGE_LIMIT = 100
FREE_DESCRIPTION_LIMIT = 100
ACCESS_COUNTER_LIMIT = 100
NOTICE_LIMIT = 100
NEW_ARRIVALS_LIMIT = 100
MAIN_CONTENTS_LIMIT = 1
MENU_LIMIT = 100
HEADER_LIMIT = 1
FOOTER_LIMIT = 1

widget_insert_obj = {
    "repository_id": "Root Index",
    "is_enabled": True,
    "is_deleted": False,
    "locked": False,
    "locked_by_user": None,
    "multiLangSetting": {
        "en": {}
    }
}

free_description_settings = {
	"label_text_color": "#333333",
	"label_color": "#F5F5F5",
	"label_enable": True,
	"theme": "default",
	"border_style": "solid",
	"background_color": "#FFFFFF",
	"frame_border_color": "#DDDDDD"
}

access_counter_settings = {
	"preceding_message": "None",
	"label_text_color": "#333333",
	"label_color": "#F5F5F5",
	"label_enable": True,
	"other_message": "None",
	"theme": "default",
	"border_style": "solid",
	"background_color": "#FFFFFF",
	"frame_border_color": "#DDDDDD",
	"access_counter": "0",
	"following_message": "None"
}

notice_settings = {
	"label_text_color": "#333333",
	"label_color": "#F5F5F5",
	"label_enable": True,
	"theme": "default",
	"hide_the_rest": "None",
	"border_style": "solid",
	"background_color": "#FFFFFF",
	"frame_border_color": "#DDDDDD",
	"read_more": "None"
}

new_arrivals_settings = {
	"rss_feed": False,
	"label_text_color": "#333333",
	"label_color": "#F5F5F5",
	"label_enable": True,
	"theme": "default",
	"border_style": "solid",
	"new_dates": "5",
	"background_color": "#FFFFFF",
	"frame_border_color": "#DDDDDD",
	"display_result": "5"
}

main_contents_settings = {
	"label_text_color": "#333333",
	"label_color": "#F5F5F5",
	"label_enable": True,
	"theme": "default",
	"border_style": "solid",
	"background_color": "#FFFFFF",
	"frame_border_color": "#DDDDDD"
}

menu_settings = {
	"background_color": "#FFFFFF",
	"menu_active_color": "#000000",
	"menu_default_color": "#000000",
	"border_style": "solid",
	"menu_show_pages": ["0"],
	"theme": "default",
	"menu_active_bg_color": "#ffffff",
	"label_enable": True,
	"menu_bg_color": "#ffffff",
	"label_text_color": "#333333",
	"label_color": "#F5F5F5",
	"frame_border_color": "#DDDDDD",
	"menu_orientation": "horizontal"
}

header_settings = {
	"fixedHeaderTextColor": "#808080",
	"fixedHeaderBackgroundColor": "#FFFFFF",
	"background_color": "#3D7FA1",
	"label_enable": False,
	"theme": "simple"
}

footer_settings = {
	"background_color": "#3D7FA1",
	"label_enable": False,
	"theme": "simple"
}
