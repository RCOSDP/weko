from mock import patch

from weko_admin.errors import get_this_message

def test_get_this_message():
    restricted_error_msg = {"key" : "","content" : {"ja" : {"content" : "このデータは利用できません（権限がないため）。"},"en":{"content" : "This data is not available for this user"}}}
    #test No.4(W2023-22 3-5)
    with patch("flask_babelex.get_locale", return_value = "en"):
        with patch("weko_admin.utils.get_restricted_access", return_value = restricted_error_msg):
            result = get_this_message()
            assert result == restricted_error_msg['content']['en']['content']

    #test No.5(W2023-22 3-5)
    with patch("flask_babelex.get_locale", return_value = "ja"):
        with patch("weko_admin.utils.get_restricted_access", return_value = restricted_error_msg):
            result = get_this_message()
            assert result == restricted_error_msg['content']['ja']['content']