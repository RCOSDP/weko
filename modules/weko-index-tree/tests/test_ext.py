
from weko_index_tree.ext import WekoIndexTree, WekoIndexTreeREST

# class WekoIndexTreeREST(object):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::test_WekoIndexTree -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_WekoIndexTree(app, db):
    app.config['BASE_EDIT_TEMPLATE'] = ''
    WekoIndexTree(app)
    app.config.pop('BASE_EDIT_TEMPLATE')
    WekoIndexTree(app)

# class WekoIndexTreeREST(object):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::test_WekoIndexTreeREST -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_WekoIndexTreeREST(app, db):
    WekoIndexTreeREST()
    WekoIndexTreeREST(app)