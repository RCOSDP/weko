#!/bin/bash

#echo $(date +"%Y%m%d%I%M%S")
#unix_today=$(date +'%s')
#unix_today=$((unix_today+32400))
jst_ymd_today=$(date +"%Y%m%d%I%M%S")

mkdir ${jst_ymd_today}

#1.1.	toxインストール、1.2.	setuptoolsのバージョン指定まではじっしておくこと
cd /code/modules

#exit

#実行前一時停止
#read -p "Hit enter: "
<< COMMENTOUT
cd weko-admin
.tox/c1/bin/pytest --cov=weko_admin tests/test_weko_admin.py::test_role_has_access -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-admin/.tox/c1/tmp --full-trace 
echo "weko-admin完了"
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_weko_admin
COMMENTOUT

# cd ../
cd weko-groups
.tox/c1/bin/pytest --cov=weko_groups tests/test_models.py::test_group_query_by_user -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-groups/.tox/c1/tmp --full-trace 
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_group_query_by_user

.tox/c1/bin/pytest --cov=weko_groups tests/test_models.py::test_membership_search -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-groups/.tox/c1/tmp --full-trace 
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_membership_search

.tox/c1/bin/pytest --cov=weko_groups tests/test_models.py::test_group_admin_query_admins_by_group_ids -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-groups/.tox/c1/tmp --full-trace 
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_group_admin_query_admins_by_group_ids

echo "weko-groups完了"


cd ../
cd weko-items-ui
.tox/c1/bin/pytest --cov=weko_items_ui tests/test_utils.py::test__get_max_export_items -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp --full-trace 
echo "weko-items-ui完了"
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test__get_max_export_items


cd ../
cd weko-records
.tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_latest -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records/.tox/c1/tmp --full-trace 
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_itemtypes_get_latest

.tox/c1/bin/pytest --cov=weko_records tests/test_api.py::test_itemtypes_get_latest_with_item_type -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records/.tox/c1/tmp --full-trace 
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_itemtypes_get_latest_with_item_type
echo "weko_records完了"



cd ../
cd weko-records-ui
.tox/c1/bin/pytest --cov=weko_records_ui tests/test_permissions.py::test_check_user_group_permission -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp --full-trace 
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_check_user_group_permission
echo "weko-records-ui完了"



cd ../
cd weko-workflow
.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority -v -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_check_authority

.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority_action -v -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_check_authority_action

echo "weko-workflow完了"


<<COMMENTOUT
cd ../
cd invenio-communities
.tox/c1/bin/pytest --cov=invenio_communities tests/test_receivers.py::test_destroy_oaipmh_set -v -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_destroy_oaipmh_set

echo "invenio-communities完了"


cd ../
cd weko-index-tree
.tox/c1/bin/pytest --cov=weko_index_tree tests/test_tasks.py::test_update_oaiset_setting -v -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
cp -r htmlcov /code/modules/worktest/${jst_ymd_today}/test_update_oaiset_setting

echo "weko-index-tree完了"
COMMENTOUT
cd ../worktest


