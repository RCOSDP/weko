def test_request_signposting(app):
    with app.test_client() as client:
        pid, record = test_records[0]
        url = url_for("weko_signpostingserver.request_signposting",recid="1")
        res = client.head(
            url
        )

        result = res.headers["Link"]
        
        data = {} # 出てきてほしいデータの形式
        
        assert result == data