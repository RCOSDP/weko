# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
from mock import patch

from weko_gridlayout.services import WidgetItemServices


@pytest.mark.parametrize("widget_data, result_error",
                         [({}, 'Widget data is empty!'),
                          ({'multiLangSetting':''}, 'Multiple language data is empty'),
                          ({'repository_id': 'Root Index',
                            'widget_type': '',
                            'multiLangSetting':
                                {'en':
                                    {
                                        'label': 'test',
                                        'description': ''
                                    }
                                }
                            }, '')])
def test_create(db, widget_data, result_error):
    """
    Test of new widget creation.
    """
    with patch("weko_gridlayout.models.WidgetItem.get_sequence", return_value=3):
        result = WidgetItemServices.create(widget_data)
        assert result['error'] == result_error


def test_create_exception(app, db):
    """
    Test of new widget creation.
    """
    widget_data = {'multiLangSetting':
        {'en':
            {'label': 'test',
            'description': ''
            }
        }
    }
    with patch("weko_gridlayout.models.WidgetItem.get_sequence",
                side_effect=Exception("Exception")):
        result = WidgetItemServices.create(widget_data)
        assert result['error'] == "Exception"


@pytest.mark.parametrize("widget_id, widget_data, result_error",
                         [(None, None, 'Widget data is empty!'),
                          (1, None, 'Widget data is empty!'),
                          (None, {'multiLangSetting':''}, 'Widget data is empty!'),
                          (1, {'multiLangSetting':''}, 'Multiple language data is empty'),
                          (1, {'multiLangSetting':
                                {'en':
                                    {
                                        'label': 'test',
                                        'description': ''
                                    }
                                }
                            }, '')])
def test_update_by_id(db, widget_id, widget_data, result_error):
    """
    Test of widget updating by id.
    """
    result = WidgetItemServices.update_by_id(widget_id, widget_data)
    assert result['error'] == result_error


def test_update_by_id_exception(db):
    widget_data = {'multiLangSetting':
        {'en':
            {'label': 'test',
            'description': ''
            }
        }
    }
    with patch("weko_gridlayout.models.WidgetItem.update_by_id",
               side_effect=Exception("Exception")):
        result = WidgetItemServices.update_by_id(1, widget_data)
        assert result['error'] == "Exception"
