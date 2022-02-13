import pytest

from weko_records_ui.views import escape_newline, escape_str, \
    json_string_escape, remove_weko2_special_character2


def test_escape_newline():
    assert escape_newline(r"\\n") == "<br/>"
    assert escape_newline(r"\\r\\n") == "<br/>"
    assert escape_newline('&lt;br&gt;') == "<br/>"
    assert escape_newline('&lt;br/&gt;') == "<br/>"


def test_json_string_escape():
    # https://datatracker.ietf.org/doc/html/rfc8259#section-7
    assert json_string_escape('"') == '\\"'
    assert json_string_escape("\b") == "\\b"
    assert json_string_escape("\f") == "\\f"
    assert json_string_escape("\n") == "\\n"
    assert json_string_escape("\r\n") == "\\r\\n"
    assert json_string_escape("\\n") == "\\\\n"
    assert json_string_escape("\\\n") == "\\\\\\n"
    assert json_string_escape("\r") == "\\r"
    assert json_string_escape("\t") == "\\t"
    assert json_string_escape(" ") == " "
    assert json_string_escape("&EMPTY&") == "&EMPTY&"


def test_escape_str():
    assert escape_str("&EMPTY&") == ""
    assert escape_newline(r"\\n") == "<br/>"
    assert escape_newline(r"\\r\\n") == "<br/>"
    assert escape_newline('&lt;br&gt;') == "<br/>"
    assert escape_newline('&lt;br/&gt;') == "<br/>"


def test_remove_weko2_special_character2():
    assert remove_weko2_special_character2("&EMPTY&") == ""
    assert remove_weko2_special_character2("\n") == "\n"
    assert remove_weko2_special_character2(
        "HELLO,&EMPTY&WORLD") == "HELLO,WORLD"
    assert remove_weko2_special_character2(
        ",&EMPTY&") == ""
