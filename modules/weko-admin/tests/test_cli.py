
import click
from click.testing import CliRunner
from mock import patch

from weko_authors.models import AuthorsPrefixSettings,AuthorsAffiliationSettings

from weko_admin.cli import (
    init_lifetime,
    insert_lang_to_db,
    save_api_certification,
    update_api_certification,
    save_report_unit,
    save_report_target,
    add_billing_user,
    toggle_active_billing_user,
    create_settings,
    create_default_settings,
    create_default_affiliation_settings,
    insert_facet_search_to_db,
    update_attribute_mapping
)
from weko_admin.models import AdminLangSettings,ApiCertificate,StatisticUnit,\
                            StatisticTarget,BillingPermission,AdminSettings,FacetSearchSetting
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp


#def lifetime():
#def init_lifetime(minutes):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_init_lifetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_init_lifetime(script_info,session_lifetime):
    runner = CliRunner()
    result = runner.invoke(init_lifetime, ["50"],obj=script_info)
    assert result.exit_code == 0
    assert result.output =="SessionLifetime has been initialised. lifetime=50 minutes\n"
    with patch("weko_admin.cli.SessionLifetime.get_validtime",return_value=None):
        result = runner.invoke(init_lifetime, ["50"],obj=script_info)
        assert result.exit_code == 0
        assert result.output =="SessionLifetime has been initialised. lifetime=50 minutes\n"

#def language():
#def insert_lang_to_db(
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_insert_lang_to_db -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_insert_lang_to_db(db,script_info):
    runner = CliRunner()
    result = runner.invoke(insert_lang_to_db,["zh","中文","3"],obj=script_info)
    assert result.exit_code == 0
    setting = AdminLangSettings.query.filter_by(lang_code="zh").one_or_none()
    assert setting.sequence == 3
    assert result.output == "insert language success\n"
    with patch("weko_admin.cli.AdminLangSettings.create",side_effect=Exception("test_error")):
        result = runner.invoke(insert_lang_to_db,["zh","中文","3"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"

#def cert():
#def save_api_certification(api_code, api_name, cert_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_save_api_certification -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_api_certification(db,script_info):
    runner = CliRunner()
    result = runner.invoke(save_api_certification,["crf","CrossRef","test.test@test.org"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert cert success\n"
    assert ApiCertificate.query.filter_by(api_code="crf").one_or_none().api_name == "CrossRef"
    
    with patch("weko_admin.cli.ApiCertificate.insert_new_api_cert",return_value=False):
        result = runner.invoke(save_api_certification,["crf","CrossRef","test.test@test.org"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "insert cert failed\n"


#def update_api_certification(api_code, api_name, cert_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_update_api_certification -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_api_certification(script_info,api_certificate):
    runner = CliRunner()
    result = runner.invoke(update_api_certification,["crf","new_name","new_data"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "update cert success\n"
    assert ApiCertificate.query.filter_by(api_code="crf").one_or_none().api_name == "new_name"
    
    with patch("weko_admin.cli.ApiCertificate.update_api_cert",return_value=False):
        result = runner.invoke(update_api_certification,["crf","CrossRef","test.test@test.org"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "update cert failed\n"


#def report():
#def save_report_unit(unit_id, unit_name):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_save_report_unit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_report_unit(db,script_info):
    runner = CliRunner()
    result = runner.invoke(save_report_unit,["1","Day"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert report unit success\n"
    assert StatisticUnit.query.filter_by(unit_id=1).one_or_none().unit_name== "Day"
    
    with patch("weko_admin.cli.StatisticUnit.create",side_effect=Exception("test_error")):
        result = runner.invoke(save_report_unit,["1","Day"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"


#def save_report_target(target_id, target_name, target_unit):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_save_report_target -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_save_report_target(db,script_info):
    runner = CliRunner()
    result = runner.invoke(save_report_target,["1","new_target","1,2,4"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert report target success\n"
    assert StatisticTarget.query.filter_by(target_id=1).one_or_none().target_name== "new_target"
    
    with patch("weko_admin.cli.StatisticTarget.create",side_effect=Exception("test_error")):
        result = runner.invoke(save_report_target,["1","new_target","1,2,4"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"


#def billing():
#def add_billing_user(user_id, active):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_add_billing_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_add_billing_user(db,script_info):
    runner = CliRunner()
    result = runner.invoke(add_billing_user,["1"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert billing user success\n"
    assert BillingPermission.query.filter_by(user_id=1).one_or_none().is_active == False

    with patch("weko_admin.cli.BillingPermission.create",side_effect=Exception("test_error")):
        result = runner.invoke(add_billing_user,["1"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"


#def toggle_active_billing_user(user_id, active):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_toggle_active_billing_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_toggle_active_billing_user(db,billing_permissions,script_info):
    runner = CliRunner()
    result = runner.invoke(toggle_active_billing_user,["2","--active"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "active billing user success\n"
    assert BillingPermission.query.filter_by(user_id=2).one_or_none().is_active== True

    result = runner.invoke(toggle_active_billing_user,["1"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "deactive billing user success\n"
    assert BillingPermission.query.filter_by(user_id=1).one_or_none().is_active== False
    
    with patch("weko_admin.cli.BillingPermission.activation",side_effect=Exception("test_error")):
        result = runner.invoke(toggle_active_billing_user,["1"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"


#def admin_settings():
#def create_settings(id, name, settings):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_create_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_create_settings(db,script_info):
    runner = CliRunner()
    result = runner.invoke(create_settings,["1","default_properties_settings",'{"show_flag":True}'],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert setting success\n"
    assert AdminSettings.query.filter_by(id=1).one_or_none().name== "default_properties_settings"
    
    with patch("weko_admin.cli.AdminSettings.update",side_effect=Exception("test_error")):
        result = runner.invoke(create_settings,["1","default_properties_settings",'{"show_flag":True}'],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"


#def authors_prefix():
#def create_default_settings(name, scheme, url):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_create_default_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_create_default_settings(db, script_info):
    runner = CliRunner()
    result = runner.invoke(create_default_settings,["ORCID","ORCID","https://orcid.org/##"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert setting success\n"
    assert AuthorsPrefixSettings.query.filter_by(name="ORCID").one_or_none().url== "https://orcid.org/##"
    
    with patch("weko_admin.cli.AuthorsPrefixSettings.create",side_effect=Exception("test_error")):
        result = runner.invoke(create_default_settings,["ORCID","ORCID","https://orcid.org/##"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"


#def authors_affiliation():
#def create_default_affiliation_settings(name, scheme, url):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_create_default_affiliation_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_create_default_affiliation_settings(db,script_info):
    runner = CliRunner()
    result = runner.invoke(create_default_affiliation_settings,["ISNI","ISNI","https://www.isni.org/isni/##"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert setting success\n"
    assert AuthorsAffiliationSettings.query.filter_by(name="ISNI").one_or_none().url== "https://www.isni.org/isni/##"
    
    with patch("weko_admin.cli.AuthorsAffiliationSettings.create",side_effect=Exception("test_error")):
        result = runner.invoke(create_default_affiliation_settings,["ISNI","ISNI","https://www.isni.org/isni/##"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"

#def facet_search_setting():
#def insert_facet_search_to_db(name_en, name_jp, mapping, aggregations, active):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_insert_facet_search_to_db -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_insert_facet_search_to_db(db, script_info):
    runner = CliRunner()
    result = runner.invoke(insert_facet_search_to_db,["Data Language","データの言語","language","[]","True","SelectBox","1","True","OR"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert facet search\n"
    assert FacetSearchSetting.query.filter_by(name_en="Data Language").one_or_none().active== True
    
    result = runner.invoke(insert_facet_search_to_db,["Distributor","配布者","contributor.contributorName","[{'agg_value': 'Distributor', 'agg_mapping': 'contributor.@attributes.contributorType'}]","True","CheckboxList","2","True","OR"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert facet search\n"
    assert FacetSearchSetting.query.filter_by(name_en="Distributor").one_or_none().active== True
    
    result = runner.invoke(insert_facet_search_to_db,["Temporal","時間的範囲","temporal","[]","True","RangeSlider","3","True","AND"],obj=script_info)
    assert result.exit_code == 0
    assert result.output == "insert facet search\n"
    assert FacetSearchSetting.query.filter_by(name_en="Temporal").one_or_none().active== True
    
    
    result = runner.invoke(insert_facet_search_to_db,["Topic","トピック","subject.value","[]","True","SelectBox","4","False"],obj=script_info)
    assert result.exit_code == 2
    assert 'Usage: create [OPTIONS] NAME_EN NAME_JP MAPPING AGGREGATIONS ACTIVE UI_TYPE' in result.output
    assert FacetSearchSetting.query.filter_by(name_en="Topic").one_or_none()==None
    
    with patch("weko_admin.cli.FacetSearchSetting.create",side_effect=Exception("test_error")):
        result = runner.invoke(insert_facet_search_to_db,["Data Language","データの言語","language","[]","True","SelectBox","1","True","OR"],obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"

#def admin_settings():
#def update_attribute_mapping(shib_eppn, shib_role_authority_name, shib_mail, shib_user_name):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_cli.py::test_update_attribute_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_update_attribute_mapping(db, script_info):
    runner = CliRunner()

    try:
        db.session.add(AdminSettings(
            id=9,
            name="attribute_mapping",
            settings='{"shib_eppn": "eduPersonPrincipalName", "shib_mail": "mail", "shib_user_name": "displayName", "shib_role_authority_name": "eduPersonAffiliation"}'
        ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise
    finally:
        db.session.remove()

    # テスト用引数をオプション形式で定義
    args = [
        '--shib_eppn', 'o',
        '--shib_role_authority_name', None,
        '--shib_mail', 'o',
        '--shib_user_name', None
    ]
        
    result = runner.invoke(update_attribute_mapping, args=args, obj=script_info)

    assert result.exit_code == 0  
    assert result.output.strip() == "Mapping and update were successful."

    with patch("weko_admin.cli.AdminSettings.update",side_effect=Exception("test_error")):
        result = runner.invoke(update_attribute_mapping, args=args, obj=script_info)
        assert result.exit_code == 0
        assert result.output == "test_error\n"