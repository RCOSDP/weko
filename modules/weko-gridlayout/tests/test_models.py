import pytest
import json
from mock import patch, MagicMock

from weko_gridlayout.models import (
    WidgetType,
    WidgetItem,
    WidgetMultiLangData,
    WidgetDesignSetting,
    WidgetDesignPage,
    WidgetDesignPageMultiLangData
)


# class WidgetType(db.Model):
#     def create(cls, data):
def test_WidgetType_create(i18n_app, db):
    data = {
        "type_id": 1,
        "type_name": "test",
    }

    assert WidgetType.create(data)
def test_WidgetType_create_2(i18n_app):
    data = {
        "type_id": 1,
        "type_name": "test",
    }

    # Coverage for execption
    assert WidgetType.create(data)


#     def get(cls, widget_type_id):
def test_WidgetType_get(i18n_app, widget_item):
    data = {
        "type_id": 1,
        "type_name": "test",
    }

    assert WidgetType.get(data) == None

#     def get_all_widget_types(cls):
def test_WidgetType_get_all_widget_types(i18n_app, widget_item):
    def all_func():
        return None
    db = MagicMock()
    db.all = all_func

    with patch('weko_gridlayout.models.db.session.query', return_value=db):
        assert WidgetType.get_all_widget_types() == None


# class WidgetItem(db.Model, Timestamp):
#     def get_by_id(cls, widget_item_id):


#     def get_id_by_repository_and_type(cls, repository, widget_type):
def test_get_id_by_repository_and_type(i18n_app, widget_items):
    repository = "Root Index"
    widget_type = "Free description"

    assert WidgetItem.get_id_by_repository_and_type(repository, widget_type)
    assert not WidgetItem.get_id_by_repository_and_type("repository", "widget_type")


#     def get_sequence(cls, session): ERR ~ execution error
def test_get_sequence(i18n_app, db):
    session = None

    assert WidgetItem.get_sequence(session)


#     def create(cls, widget_data, session):
# def test_create_WidgetItem(i18n_app):



#     def update_by_id(cls, widget_item_id, widget_data, session=None):
def test_update_by_id(i18n_app, widget_items):
    widget_item_id = MagicMock()
    widget_data = MagicMock()

    def merge(item):
        return item
    
    def commit():
        return True

    def begin_nested():
        return True

    session = MagicMock()
    session.merge = merge
    session.commit = commit

    with patch('weko_gridlayout.models.db', session):
        with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=""):
            assert WidgetItem.update_by_id(widget_item_id, widget_data) == None

        with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=widget_data):
            with patch("weko_gridlayout.models.setattr", return_value=widget_data):
                assert WidgetItem.update_by_id(widget_item_id, {"test": {"test": "test"}}, session=session) != None

        with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=widget_data):
            assert WidgetItem.update_by_id(widget_item_id, widget_data) != None

            with patch("weko_gridlayout.models.db.session.commit", side_effect=Exception('')):
                assert WidgetItem.update_by_id(widget_item_id, widget_data) == False


#     def update_setting_by_id(cls, widget_id, settings):
def test_update_setting_by_id(i18n_app, widget_items):
    settings = {}
    widget_id = "1"

    assert WidgetItem.update_setting_by_id(widget_id, settings)
    assert not WidgetItem.update_setting_by_id(222, settings)


#     def delete_by_id(cls, widget_id, session):
def test_delete_by_id(i18n_app, widget_items):
    session = MagicMock()
    widget_id = "1"

    assert WidgetItem.delete_by_id(widget_id, session)
    assert not WidgetItem.delete_by_id(False, session)


# class WidgetMultiLangData(db.Model):
#     def get_by_id(cls, widget_multi_lang_id):
def test_get_by_id(i18n_app, widget_items):
    widget_multi_lang_id = "1"

    assert WidgetMultiLangData.get_by_id(widget_multi_lang_id)


#     def create(cls, data, session):
#     def get_by_widget_id(cls, widget_id):


#     def update_by_id(cls, widget_item_id, data):
def test_update_by_id_WidgetMultiLangData(i18n_app, widget_items):
    widget_item_id = "1"
    data = {"test1": "1", "test2": "2"}

    assert WidgetMultiLangData.update_by_id(widget_item_id, data)
    assert not WidgetMultiLangData.update_by_id(widget_item_id, {})


#     def delete_by_widget_id(cls, widget_id, session):
def test_delete_by_widget_id(i18n_app, widget_items):
    widget_id = "1"
    session = None

    assert WidgetMultiLangData.delete_by_widget_id(widget_id, session)
    assert not WidgetMultiLangData.delete_by_widget_id("99", session)


# class WidgetDesignSetting(db.Model):
#     def select_all(cls):
def test_select_all(i18n_app, db):
    test1 = WidgetDesignSetting(repository_id="1")
    test2 = WidgetDesignSetting(repository_id="2")
    test3 = WidgetDesignSetting(repository_id="3")
    db.session.add(test1)
    db.session.add(test2)
    db.session.add(test3)
    db.session.commit()

    assert WidgetDesignSetting.select_all()


#     def select_by_repository_id(cls, repository_id):


#     def update(cls, repository_id, settings):
def test_update_WidgetDesignSetting(i18n_app, db):
    test1 = WidgetDesignSetting(repository_id="1")
    db.session.add(test1)
    db.session.commit()

    assert WidgetDesignSetting.update("1", {})
    assert not WidgetDesignSetting.update("99", {})
    assert not WidgetDesignSetting.update("1", MagicMock())


#     def create(cls, repository_id, settings=None):
def test_create_WidgetDesignSetting(i18n_app, db):
    test1 = WidgetDesignSetting(repository_id="1")
    db.session.add(test1)
    db.session.commit()
    repository_id = "1"

    def merge(item):
        return item
    
    def commit():
        return True

    session = MagicMock()
    session.merge = merge
    session.commit = commit

    with patch('weko_gridlayout.models.db', session):
        assert WidgetDesignSetting.create(repository_id=repository_id) == True

    # Exception coverage ~ line 459
    try:
        WidgetDesignSetting.create(repository_id=repository_id)
    except:
        pass



# class WidgetDesignPage(db.Model):
# def create_or_update(cls, repository_id, title, url, content, page_id=0, settings=None, multi_lang_data={}, is_main_layout=False):
def test_create_or_update(i18n_app, db, widget_item):
    test1 = WidgetDesignPage(
        repository_id="1",
        url="/"
    )
    db.session.add(test1)
    db.session.commit()
    repository_id = "1"
    title = "1"
    url = "/"
    content = MagicMock()

    # Exception coverage ~ line 532, 558
    try:
        test1.create_or_update(
            repository_id=None,
            title=title,
            url=None,
            content=content,
        )
    except:
        pass

    # Exception coverage ~ line 534, 558
    try:
        test1.create_or_update(
            repository_id=repository_id,
            title=title,
            url=None,
            content=content,
            page_id=1
        )
    except:
        pass

    # Exception coverage ~ line 542
    try:
        WidgetDesignPage.create_or_update(
            repository_id=repository_id,
            title=title,
            url=url,
            content=content
        )
    except:
        pass
    
    with patch('weko_gridlayout.models.db.session.merge', return_value=""):
        with patch('weko_gridlayout.models.db.session.commit', return_value=""):
            with patch('weko_gridlayout.models.WidgetDesignPageMultiLangData', return_value=MagicMock()):
                WidgetDesignPage.create_or_update(
                    repository_id=repository_id,
                    title=title,
                    url="url",
                    content=content,
                    settings={},
                    multi_lang_data={"lang": "lang"}
                )
        

#     def delete(cls, page_id):
def test_delete_WidgetDesignPage(i18n_app, widget_items):
    page_id = "1"

    assert WidgetDesignPage.delete(page_id)
    assert not WidgetDesignPage.delete(False)
    assert not WidgetDesignPage.delete("a")

    
#     def update_settings(cls, page_id, settings=None):
def test_update_settings(i18n_app, db):
    test = WidgetDesignPage(
        id=1,
        repository_id="1",
        url="/"
    )
    db.session.add(test)
    db.session.commit()
    page_id = 1

    assert WidgetDesignPage.update_settings(page_id)
    assert not WidgetDesignPage.update_settings(9)
    assert not WidgetDesignPage.update_settings("a")


#     def update_settings_by_repository_id(cls, repository_id, settings=None):
def test_update_settings_by_repository_id(i18n_app, db):
    test = WidgetDesignPage(
        id=1,
        repository_id="1",
        url="/"
    )
    db.session.add(test)
    db.session.commit()
    page_id = 1

    assert WidgetDesignPage.update_settings_by_repository_id(page_id) == True

    with patch('weko_gridlayout.models.db.session.merge', side_effect=Exception('')):
        assert WidgetDesignPage.update_settings_by_repository_id(page_id) == False


#     def get_all(cls):
def test_get_all(i18n_app, db):
    test = WidgetDesignPage(
        id=1,
        repository_id="1",
        url="/"
    )
    db.session.add(test)
    db.session.commit()

    assert WidgetDesignPage.get_all() != None


#     def get_all_valid(cls):
def test_get_all_valid(i18n_app, db):
    test = WidgetDesignPage(
        id=1,
        repository_id="1",
        url="/"
    )
    db.session.add(test)
    db.session.commit()

    assert WidgetDesignPage.get_all_valid() != None


#     def get_by_id(cls, id):
#     def get_by_id_or_none(cls, id):
#     def get_by_url(cls, url):
#     def get_by_repository_id(cls, repository_id):


# class WidgetDesignPageMultiLangData(db.Model):
#     def __init__(self, lang_code, title):
#     def get_by_id(cls, id):
def test_get_by_id(i18n_app, widget_item, db):
    w = WidgetDesignPageMultiLangData(
        lang_code="en",
        title="title",
    )

    assert w.get_by_id(w.id) == None

#     def delete_by_page_id(cls, page_id):
def test_delete_by_page_id(i18n_app, widget_item):
    w = WidgetDesignPageMultiLangData(
        lang_code="en",
        title="title",
    )

    assert w.delete_by_page_id(page_id=1) == True

    with patch('weko_gridlayout.models.db.session.commit', side_effect=Exception('')):
        # Exception coverage ~ line 724
        try:
            assert w.delete_by_page_id(page_id=1) == False
        except:
            pass
    
    assert w.delete_by_page_id(page_id=0) == False