from weko_sitemap.tasks import link_success_handler,link_error_handler,update_sitemap
# def link_success_handler(retval):
def test_link_success_handler(app):
    with app.test_request_context():
        assert link_success_handler([])==""
    
# def link_error_handler(request, exc, traceback):
def test_link_error_handler():
    assert link_error_handler([],"","")==""

# def update_sitemap(start_time=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
def test_update_sitemap(app):
    with app.test_request_context():
        assert update_sitemap()==""
