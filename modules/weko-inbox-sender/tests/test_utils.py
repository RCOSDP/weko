#
# from flask import request
# from weko_inbox_sender.utils import \
#     get_recid_p, get_records_pid, get_record_permalink, inbox_url
#
#
# def test_get_recid_p1(test_pid):
#     # 正常系
#     assert get_recid_p("1.1") == "1"
#
#
# def test_get_recid_p2(test_pid):
#     # 存在しないrecid
#     assert get_recid_p("5.1") == "1"
#
#
# def test_get_recid_p3(test_pid):
#     # 親を持たないrecid
#     assert get_recid_p("1") == "1"
#
#
# def test_get_recid_p4(test_pid):
#     # 該当の子が存在しないrecid
#     assert get_recid_p("1.2") == "1"
#
#
# def test_get_records_pid1(test_pid):
#     # 子を持つrecidのuuid
#     assert get_records_pid("1") == test_pid[1][1]
#
#
# def test_get_records_pid2(test_pid):
#     # 子を持たないrecidのuuid
#     assert get_records_pid("5") == "1"
#
#
# def test_get_records_pid3(test_pid):
#     # 1.1意向を持たないrecid
#     assert get_records_pid("2") == test_pid[2][1]
#
#
# def test_get_record_permalink1(app, test_pid):
#     # doiを持つレコード
#     with app.test_request_context("/"):
#         print(test_pid[0][0].object_uuid)
#         print(test_pid[3][0].object_uuid)
#         print(test_pid[4][0].object_uuid)
#         assert get_record_permalink("1") == 'https://doi.org'
#
#
# def test_get_record_permalink2(app, test_pid):
#     # doiを持たないレコード
#     with app.test_request_context('/'):
#         host_url = request.host_url
#         assert get_record_permalink("2") == host_url+'records/2'
#
# # TODO: get_record_permalinkのexceptエラー。というかexceptが返ってきても返していいの？
#
# def test_inbox_url1(app):
#     # 置換する
#     url = "https://localhost/inbox/xxx-aaa-bbb"
#     result = inbox_url(url)
#
#     assert result == "https://nginx:443/inbox/xxx-aaa-bbb"
#
# def test_inbox_url2(app):
#     # 置換しない
#     url = "https://example.com/inbox/xxx-aaa-bbb"
#     result = inbox_url(url)
#
#     assert result == "https://example.com/inbox/xxx-aaa-bbb"
#
# def test_inbox_url3(app):
#     # 引数なし
#     result = inbox_url()
#
#     assert result == "https://nginx:443/inbox"
