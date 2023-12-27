from mock import patch
from unittest.mock import MagicMock
import pytest
import io
import random
from flask import Flask, json, jsonify, session, url_for, current_app
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from weko_records_ui.captcha import ImageCaptchaEx, get_captcha_info
from captcha.image import random_color
from PIL.Image import new as createImage, Image, QUAD, BILINEAR
from PIL.ImageDraw import Draw, ImageDraw
from PIL.ImageFilter import SMOOTH


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_captcha.py::test_create_captcha_image -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records_ui/.tox/c1/tmp
def test_create_captcha_image(mocker):
    imagechan = ImageCaptchaEx(width=360, height=78)
    chars = "1a2b+4c5"
    color = (10,200,225)
    background = (240,240,240)
    with patch("weko_records_ui.captcha.random.random", return_value=0.7):
        print(type(imagechan.create_captcha_image(chars, color, background)))
        print(type(Image()))
        assert type(Image()) == type(imagechan.create_captcha_image(chars, color, background))
    with patch("weko_records_ui.captcha.random.random", return_value=0.3):
        assert type(Image()) == type(imagechan.create_captcha_image(chars, color, background))

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_captcha.py::test_generate_image -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records_ui/.tox/c1/tmp
def test_generate_image(mocker):
    imagechan = ImageCaptchaEx(width=360, height=78)
    chars = "1a2b+4c5"
    with mocker.patch("weko_records_ui.captcha.random.random", return_value=0.7):
        assert  type(Image()) == type(imagechan.generate_image(chars))

counter = 0
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_captcha.py::test_get_captcha_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records_ui/.tox/c1/tmp
def test_get_captcha_info(mocker):
    def side_effect1(one=None,two=None):
        global counter 
        counter += 1
        if counter > 2:
            return 10
        elif counter == 1:
            return 50
        elif counter == 2:
            return 30
    def side_effect2(one=None,two=None):
        global counter 
        counter += 1
        if counter > 2:
            return 10
        elif counter == 1:
            return 30
        elif counter == 2:
            return 50
    
    with patch("weko_records_ui.captcha.random.randint") as r:
        with patch("weko_records_ui.captcha.random.random", return_value=0.7):
            r.side_effect = side_effect1
            ret = get_captcha_info()
            assert type(bytes()) == type(ret["image"])
            assert type(int()) == type(ret["answer"])
            r.side_effect = side_effect2
            ret = get_captcha_info()
            assert type(bytes()) == type(ret["image"])
            assert type(int()) == type(ret["answer"])
        with patch("weko_records_ui.captcha.random.random", return_value=0.3):
            r.side_effect = side_effect1
            ret = get_captcha_info()
            assert type(bytes()) == type(ret["image"])
            assert type(int()) == type(ret["answer"])
        
