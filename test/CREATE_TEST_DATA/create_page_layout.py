from weko_gridlayout.models import WidgetDesignPage, WidgetDesignPageMultiLangData, \
    WidgetDesignSetting, WidgetItem
from weko_gridlayout.services import WidgetItemServices
from invenio_db import db
from datetime import datetime
import settings
import copy

widget_type_list = ['Free description', 'Access counter', 'Notice', 'New arrivals', 'Menu']

def main():
    create_pages()
    create_widgets()
    update_pages()


def create_pages():
    page_limit = settings.PAGE_LIMIT \
        if settings.PAGE_LIMIT > len(widget_type_list) else len(widget_type_list)
    for i in range(page_limit):
        WidgetDesignPage.create_or_update(
            'Root Index',
            'Test Page {0:04d}'.format(i + 1),
            '/page/{0:04d}'.format(i + 1),
            ''
            )


def create_widgets():
    def _create(limit, widget_type, data, description=None):
        limit = limit if limit > 0 else 1
        if widget_type == 'Menu':
            pages =  WidgetDesignPage.query.order_by(WidgetDesignPage.title).all()
            for i in pages:
                data['menu_show_pages'].append(i.id)
        for i in range(limit):
            insert_obj = copy.deepcopy(settings.widget_insert_obj)
            insert_obj['widget_type'] = widget_type
            insert_obj['settings'] = data
            insert_obj['multiLangSetting']['en']['label'] = '{0} {1:05d}'.format(widget_type, i + 1)
            if description and 'description' in description:
                description['description'] = description['description'].format(i + 1)
            insert_obj['multiLangSetting']['en']['description'] = description
            WidgetItemServices.create(insert_obj)

    _create(settings.FREE_DESCRIPTION_LIMIT, "Free description",
            copy.deepcopy(settings.free_description_settings),
            {'description': '<p>Free description {0:05d} test<br></p>'})
    _create(settings.ACCESS_COUNTER_LIMIT, "Access counter",
            copy.deepcopy(settings.access_counter_settings),
            {'access_counter': '0'})
    _create(settings.NOTICE_LIMIT, "Notice",
            copy.deepcopy(settings.notice_settings),
            {'description': '<p>Notice {0:05d} test<br></p>'})
    _create(settings.NEW_ARRIVALS_LIMIT, "New arrivals",
            copy.deepcopy(settings.new_arrivals_settings))
    _create(settings.MAIN_CONTENTS_LIMIT, "Main contents",
            copy.deepcopy(settings.main_contents_settings))
    _create(settings.MENU_LIMIT, "Menu",
            copy.deepcopy(settings.menu_settings))
    _create(settings.HEADER_LIMIT, "Header",
            copy.deepcopy(settings.header_settings),
            {'description': '<p>Header {0:05d} test<br></p>'})
    _create(settings.FOOTER_LIMIT, "Footer",
            copy.deepcopy(settings.footer_settings),
            {'description': '<p>Footer {0:05d} test<br></p>'})


def update_pages():
    page_count = 1
    for widget_type in widget_type_list:
        widget_item_list = WidgetItem.query.filter_by(
            repository_id='Root Index', is_enabled=True,
            is_deleted=False, widget_type=widget_type
        ).all()
        limit = len(widget_item_list)

        page_settings = []
        x = 0
        y = 0
        counter = 0
        while counter < limit:
            for j in range(6):
                widget = widget_item_list[counter]
                item = copy.deepcopy(widget.settings)
                item["x"] = x
                item["y"] = y
                item["height"] = 6
                item["width"] = 2
                item["id"] = "Root Index"
                item["widget_id"] = widget.widget_id
                item["name"] = "{0} {1:05d}".format(widget_type, counter + 1)
                item["read_more"] = None
                item["type"] = widget_type
                item["multiLangSetting"] = {
                    "en": {
                        "label": "{0} {1:05d}".format(widget_type, counter + 1),
                        "description": None
                    }
                }
                if widget_type == "Access counter":
                    item["created_date"] = datetime.utcnow().strftime("%Y-%m-%d")
                    item["multiLangSetting"]["en"]["description"] = {
                        "access_counter": "0"
                    }
                elif widget_type in ["Free description", "Notice"]:
                    item["created_date"] = datetime.utcnow().strftime("%Y-%m-%d")
                    item["multiLangSetting"]["en"]["description"] = {
                        "description": "<p>{0} {1:05d} test<br></p>".format(widget_type, counter + 1)
                    }
                page_settings.append(item)
                x += 2
                counter += 1
                if counter == limit:
                    break
            x = 0
            y += 6
        page = WidgetDesignPage.get_by_url('/page/{0:04d}'.format(page_count))
        WidgetDesignPage.update_settings(page.id, page_settings)
        page_count += 1
    
if __name__ == '__main__':
    main()
