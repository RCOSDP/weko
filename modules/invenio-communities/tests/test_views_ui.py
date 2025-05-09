
from flask import make_response,render_template,url_for
from mock import patch
from weko_index_tree.models import Index
from invenio_accounts.testutils import create_test_user
from invenio_communities.models import Community
from invenio_communities.views.ui import (
    pass_community,
    permission_required,
    generic_item,
    dbsession_clean
)

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

# def sanitize_html(value):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_sanitize_html -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_sanitize_html(app):
    text = '<script><a href="https://google.com"><p>test_url</p></a></script>'
    result = app.jinja_env.filters["sanitize_html"](text)
    assert result == '<a href="https://google.com"><p>test_url</p></a>'


# def pass_community(f):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_pass_community -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_pass_community(app,db,communities,mocker):
    result = pass_community(lambda x:x)(community_id="comm1")
    assert result.id == "comm1"

    mock_abort = mocker.patch("invenio_communities.views.ui.abort",return_value=make_response())
    result = pass_community(lambda x:x)(community_id="not_exist_comm")
    mock_abort.assert_called_with(404)


# def permission_required(action):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_permission_required -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_permission_required(app,db,users,mocker):

    index = Index()
    db.session.add(index)
    db.session.commit()
    comm0 = Community.create(community_id='comm1', role_id=3,
                             id_user=1, title='Title1',
                             description='Description1',
                             root_node_id=1,
                             group_id=1)
    db.session.commit()

    with app.test_client() as client:
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            client.get("/")
            result = permission_required("community-edit")(lambda x: x)(community=comm0)
            assert result.id == "comm1"

        with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
            client.get("/")
            mock_abort = mocker.patch("invenio_communities.views.ui.abort",return_value=make_response())
            result = permission_required("community-edit")(lambda x: x)(community=comm0)
            mock_abort.assert_called_with(403)

# def format_item(item, template, name='item'):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_format_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_format_item(app,mocker):
    template_value = app.jinja_env.from_string("test_value: {{ name }}")
    mocker.patch("invenio_communities.utils.current_app.jinja_env.get_or_select_template",return_value=template_value)
    item = "test_item"
    template = "test_template"
    name = "name"
    result = app.jinja_env.filters["format_item"](item,template,name)
    assert result == "test_value: test_item"

# def mycommunities_ctx():
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_mycommunities_ctx -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_mycommunities_ctx(app,db,users):
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm0 = Community.create(community_id='comm1', role_id=2,
                             id_user=2, title='Title1',
                             description='Description1',
                             root_node_id=1,
                             group_id=1)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        result = app.jinja_env.filters["mycommunities_ctx"]()
        assert "mycommunities" in result
        assert result["mycommunities"][0].id == "comm1"

# def index():
# def view(community):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_view(client,app,db,communities,mocker):
    app.config.update(
        WEKO_INDEX_TREE_STYLE_OPTIONS={
                'id': 'weko',
                'widths': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
            },
        RECORDS_REST_SORT_OPTIONS = dict(
            records=dict(
                bestmatch=dict(
                    title='Best match',
                    fields=['_score'],
                    default_order='desc',
                    order=1,
                ),
                mostrecent=dict(
                    title='Most recent',
                    fields=['-_created'],
                    default_order='asc',
                    order=2,
                ),
            )
        ),
        THEME_FRONTPAGE_TEMPLATE = "weko_theme/frontpage.html"
        )
    mocker.patch("invenio_communities.views.ui.get_search_detail_keyword",return_value=[])

    url = url_for("invenio_communities.view",community_id="comm1")
    mock_render = mocker.patch("invenio_communities.views.ui.render_template",return_value=make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_theme/frontpage.html"
    assert kwargs["sort_option"] == {"records": {"bestmatch": {"title": "Best match", "fields": ["_score"], "default_order": "desc", "order": 1}, "mostrecent": {"title": "Most recent", "fields": ["-_created"], "default_order": "asc", "order": 2}}}
    assert kwargs["detail_condition"] == []
    assert kwargs["community_id"] == "comm1"
    assert kwargs["width"] == "3"
    assert kwargs["height"] == None
    assert kwargs["community"].id == "comm1"
    assert kwargs["display_facet_search"] == False
    assert kwargs["display_index_tree"] == True

    url = url_for("invenio_communities.view",community_id="comm1",view="weko")
    mock_render = mocker.patch("invenio_communities.views.ui.render_template",return_value=make_response())
    res = client.get(url)
    assert res.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "weko_theme/frontpage.html"
    assert kwargs["sort_option"] == {"records": {"bestmatch": {"title": "Best match", "fields": ["_score"], "default_order": "desc", "order": 1}, "mostrecent": {"title": "Most recent", "fields": ["-_created"], "default_order": "asc", "order": 2}}}
    assert kwargs["detail_condition"] == []
    assert kwargs["community_id"] == "comm1"
    assert kwargs["width"] == "3"
    assert kwargs["height"] == None
    assert kwargs["community"].id == "comm1"
    assert kwargs["display_facet_search"] == False
    assert kwargs["display_index_tree"] == True

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_content_policy -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_content_policy(client, app, db, communities, mocker):
    comm = communities[0]
    mock_render = mocker.patch("invenio_communities.views.ui.render_template",return_value=make_response())

    # valid community
    url = url_for("invenio_communities.content_policy", community_id=comm.id)
    response = client.get(url)
    assert response.status_code == 200
    args, kwargs = mock_render.call_args
    assert args[0] == "invenio_communities/content_policy.html"
    assert kwargs["community"].id == comm.id

    # invalid community
    url = url_for("invenio_communities.content_policy", community_id="invalid_id")
    response = client.get(url)
    assert response.status_code == 404

# # def detail(community):
# # def search(community):
# # def about(community):

# def generic_item(community, template, **extra_ctx):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_generic_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_generic_item(app,db,users,mocker):
    index = Index()
    db.session.add(index)
    db.session.commit()
    community = Community.create(community_id='comm1', role_id=2,
                             page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False,
                             id_user=2, title='Title1',
                             description='Description1',
                             root_node_id=1,
                             group_id=1)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        mock_render = mocker.patch("invenio_communities.views.ui.render_template",return_value=make_response())
        result = generic_item(community,"test_template.html")
        args,kwargs = mock_render.call_args

        assert args[0] == "test_template.html"
        assert kwargs["mycommunities"][0].id == "comm1"
        assert kwargs["is_owner"] == True
        assert kwargs["community"].id == "comm1"
        assert kwargs["detail"] == True

# # def new():
# # def edit(community):
# #    def read_color(scss_file, community):
# # def delete(community):
# # def curate(community):
# def community_list():
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_community_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_community_list(client,app,db,users,mocker):
    index = Index()
    db.session.add(index)
    db.session.commit()
    community = Community.create(community_id='comm1', role_id=2,
                             id_user=2, title='Title1',
                             description='Description1',
                             root_node_id=1,
                             group_id=1)
    db.session.commit()
    app.config.update(
        WEKO_THEME_DEFAULT_COMMUNITY="Root Index"
    )
    url = url_for("invenio_communities.community_list")
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        mock_render = mocker.patch("invenio_communities.views.ui.render_template",return_value=make_response())
        res = client.get(url)
        assert res.status_code == 200
        args,kwargs = mock_render.call_args
        assert args[0] == "invenio_communities/communities_list.html"
        assert kwargs["page"] == None
        assert kwargs["render_widgets"] == False
        assert kwargs["mycommunities"][0].id == "comm1"
        assert kwargs["r_from"] == 0
        assert kwargs["r_to"] == 1
        assert kwargs["r_total"] == 1
        assert kwargs["pagination"].page == 1
        assert kwargs["form"].data == {"p": None, "csrf_token": None}
        assert kwargs["title"] == "Communities"
        assert kwargs["communities"][0].id == "comm1"
        assert kwargs["featured_community"] == None
        assert kwargs["display_community"] == False

# def dbsession_clean(exception):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_views_ui.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_dbsession_clean(app, db):
    user = create_test_user(email='test@test.org')
    user1 = db.session.merge(user)
    ds = app.extensions['invenio-accounts'].datastore
    r = ds.create_role(name='superuser', description='1234')
    ds.add_role_to_user(user1, r)
    ds.commit()
    index = Index()
    db.session.add(index)
    db.session.commit()
    # exist exception
    com1 = Community(id=1,id_role=1,id_user=1,root_node_id=1,title="com1",page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False)
    db.session.add(com1)
    dbsession_clean(None)
    assert Community.query.filter_by(id=1).first().title =="com1"

    # raise Exception
    com2 = Community(id=2,id_role=1,id_user=1,root_node_id=1,title="com2",page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False)
    db.session.add(com2)
    with patch("invenio_mail.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert Community.query.filter_by(id=2).first() is None

    # not exist exception
    config3 = Community(id=3,id_role=1,id_user=1,root_node_id=1,title="com3",page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False)
    db.session.add(config3)
    dbsession_clean(Exception)
    assert Community.query.filter_by(id=3).first() is None
