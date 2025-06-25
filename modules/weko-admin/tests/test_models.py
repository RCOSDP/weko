
import pytest
from datetime import datetime
from mock import patch
from sqlalchemy.exc import SQLAlchemyError

from weko_admin.models import (
    SessionLifetime,
    SearchManagement,
    AdminLangSettings,
    ApiCertificate,
    StatisticUnit,
    StatisticTarget,
    LogAnalysisRestrictedIpAddress,
    LogAnalysisRestrictedCrawlerList,
    BillingPermission,
    StatisticsEmail,
    RankingSettings,
    FeedbackMailSetting,
    AdminSettings,
    SiteInfo,
    FeedbackMailHistory,
    FeedbackMailFailed,
    FacetSearchSetting
)
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp

#class SessionLifetime(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSessionLifetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestSessionLifetime:
#    def lifetime(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSessionLifetime::test_lifetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_lifetime(self):
        session_lifetime = SessionLifetime()
        session_lifetime.lifetime = 200
        assert session_lifetime.lifetime == 200
#    def create(self, lifetime=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSessionLifetime::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        # lifetime is None
        session_lifetime = SessionLifetime()
        session_lifetime = session_lifetime.create()
        SessionLifetime.query.filter_by().first().lifetime == 30
        
        SessionLifetime.query.delete()
        db.session.commit()
        
        session_lifetime = SessionLifetime()
        session_lifetime = session_lifetime.create(200)
        assert SessionLifetime.query.filter_by().first().lifetime == 200
        
        # raise exception
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            session_lifetime = SessionLifetime()
            with pytest.raises(BaseException):
                session_lifetime = session_lifetime.create(100)
                assert SessionLifetime.query.filter_by().first().lifetime == 200
                
#    def get_validtime(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSessionLifetime::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_validtime(self, session_lifetime):
        session_lifetime = SessionLifetime.get_validtime()
        session_lifetime.lifetime == 100
        
#    def is_anonymous(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSessionLifetime::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_is_anonymous(self):
        session_lifetime = SessionLifetime()
        assert session_lifetime.is_anonymous == False


#class SearchManagement(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSearchManagement -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestSearchManagement:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSearchManagement::test_null_data -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_null_data(self, db):
        sm = SearchManagement(
            default_dis_num=10
        )
        db.session.add(sm)
        db.session.commit()
        result = SearchManagement.query.first()
        assert result.sort_setting == {}
        assert result.search_conditions == {}
        assert result.search_setting_all == {}

#    default_dis_num = db.Column(db.Integer, nullable=False, default=20)
#    default_dis_sort_index = db.Column(db.Text, nullable=True, default="")
#    default_dis_sort_keyword = db.Column(db.Text, nullable=True, default="")
#        default=lambda: dict(),
#        default=lambda: dict(),
#        default=lambda: dict(),
#        default=lambda: dict(),
#        default=lambda: dict(),
#    create_date = db.Column(db.DateTime, default=datetime.now)

#    def create(cls, data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSearchManagement::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        data = {
            "dlt_dis_num_selected":20,
            "dlt_index_sort_selected":"controlnumber_asc",
            "dlt_keyword_sort_selected":"createdate_desc",
            "sort_option":{},
            "detail_condition":{},
            "display_control":{},
            "init_disp_setting":{}
        }
        SearchManagement.create(data)
        result = SearchManagement.query.filter_by().first()
        assert result.default_dis_num == 20
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                SearchManagement.create(data)

#    def get(cls):

#    def update(cls, id, data):

#class AdminLangSettings(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminLangSettings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestAdminLangSettings:
#    def parse_result(cls, in_result):

#    def load_lang(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminLangSettings::test_load_lang -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_load_lang(self, language_setting):
        test = [
            {
                "lang_code": "zh",
                "lang_name": "中文",
                "is_registered": False,
                "sequence": 0
            },
            {
                "lang_code": "en",
                "lang_name": "English",
                "is_registered": True,
                "sequence": 1
            },
            {
                "lang_code": "ja",
                "lang_name": "日本語",
                "is_registered": True,
                "sequence": 2
            }
        ]
        result = AdminLangSettings.load_lang()
        assert result == test

#    def create(cls, lang_code, lang_name, is_registered, sequence, is_active):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminLangSettings::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self,db):
        AdminLangSettings.create(
            lang_code="en",
            lang_name="English",
            is_registered=True,
            sequence=1,
            is_active=True
        )
        result = AdminLangSettings.query.filter_by().first()
        assert result.lang_code == "en"
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AdminLangSettings.create(
                    lang_code="en",
                    lang_name="English",
                    is_registered=True,
                    sequence=1,
                    is_active=True
                )

#    def update_lang(cls, lang_code=None, lang_name=None, is_registered=None,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminLangSettings::test_update_lang -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_lang(self, language_setting):
        AdminLangSettings.update_lang(
            lang_code="en",
            lang_name="english",
            is_registered=False,
            sequence=3,
            is_active=False
        )
        
        lang = AdminLangSettings.query.filter_by(lang_code="en").one()
        assert lang.lang_name == "english"
        assert lang.is_registered == False
        assert lang.sequence == 3
        assert lang.is_active == False
        
        AdminLangSettings.update_lang(
            lang_code="ja"
        )
        lang = AdminLangSettings.query.filter_by(lang_code="ja").one()
        assert lang.lang_name == "日本語"
        assert lang.is_registered == True
        assert lang.sequence == 2
        assert lang.is_active == True

#    def get_registered_language(cls):

#    def get_active_language(cls):


#class ApiCertificate(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestApiCertificate -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestApiCertificate:
#    def select_all(cls):

#    def select_by_api_code(cls, api_code):

#    def update_cert_data(cls, api_code, cert_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestApiCertificate::test_update_cert_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_cert_data(self, db):
        result = ApiCertificate.update_cert_data("crf","test.test@test.org")
        assert result == False
        
        api = ApiCertificate(
            api_code="crf",
            api_name="CrossRef",
            cert_data="test.test@test.org"
        )
        db.session.add(api)
        db.session.commit()
        
        result = ApiCertificate.update_cert_data("crf","new.test@test.org")
        assert result == True
        ac = ApiCertificate.query.filter_by(api_code="crf").one()
        assert ac.cert_data == "new.test@test.org"
        
        with patch("weko_admin.models.db.session.commit", side_effect=Exception("test_error")):
            result = ApiCertificate.update_cert_data("crf","new.test@test.org")
            assert result == False

#    def insert_new_api_cert(cls, api_code, api_name, cert_data=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestApiCertificate::test_insert_new_api_cert -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_insert_new_api_cert(self,db):
        result = ApiCertificate.insert_new_api_cert(
            api_code="test_api",
            api_name="Test API",
            cert_data="test.test@test.org"
        )
        assert result == True
        ac = ApiCertificate.query.filter_by(api_code="test_api").one()
        assert ac.api_name == "Test API"
        assert ac.cert_data == "test.test@test.org"
        
        result = ApiCertificate.insert_new_api_cert(
            api_code=None,
            api_name=None,
            cert_data=None
        )
        assert result == False

#    def update_api_cert(cls, api_code, api_name, cert_data):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestApiCertificate::test_update_api_cert -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_api_cert(self, db):
        # not exist api cert
        result = ApiCertificate.update_api_cert("test_api","Test API","test.test@test.org")
        assert result == False
        
        api = ApiCertificate(
            api_code="test_api",
            api_name="CrossRef",
            cert_data="test.test@test.org"
        )
        db.session.add(api)
        db.session.commit()
        
        result = ApiCertificate.update_api_cert("test_api","Test API","test.cert@test.org")
        assert result == True
        ac = ApiCertificate.query.filter_by(api_code="test_api").one()
        assert ac.api_name == "Test API"
        assert ac.cert_data == "test.cert@test.org"
        
        with patch("weko_admin.models.db.session.commit",side_effect=Exception("test_error")):
            result = ApiCertificate.update_api_cert("test_api","Test API","test.cert@test.org")
            assert result == False

#class StatisticUnit(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStatisticUnit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestStatisticUnit:
#    def get_all_stats_report_unit(cls):

#    def create(cls, unit_id, unit_name):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStatisticUnit::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        StatisticUnit.create("1","Day")
        su = StatisticUnit.query.filter_by().first()
        assert su.unit_id == "1"
        assert su.unit_name == "Day"
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                StatisticUnit.create("2","Week")
        
#class StatisticTarget(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStatisticTarget -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestStatisticTarget:
#    def get_all_stats_report_target(cls):

#    def get_target_by_id(cls, target_id):

#    def create(cls, target_id, target_name, target_unit):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStatisticTarget::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        StatisticTarget.create(
            target_id="1",
            target_name="Item registration report",
            target_unit="1,2,3,5"
        )
        st = StatisticTarget.query.filter_by(target_id="1").one()
        assert st.target_name == "Item registration report"
        assert st.target_unit == "1,2,3,5"
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                StatisticTarget.create(
                    target_id="2",
                    target_name="Item registration report",
                    target_unit="1,2,3,5"
                )

#class LogAnalysisRestrictedIpAddress(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedIpAddress -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestLogAnalysisRestrictedIpAddress:
#    def get_all(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedIpAddress::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all(self,restricted_ip_addr):
        result = LogAnalysisRestrictedIpAddress.get_all()
        assert result[0].ip_address == "123.456.789.012"
        
        with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
            mock_query.return_value.all.side_effect=Exception("test_error")
            with pytest.raises(Exception):
                result = LogAnalysisRestrictedIpAddress.get_all()

#    def update_table(cls, ip_addresses):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedIpAddress::test_update_table -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_table(self,restricted_ip_addr):
        ip_addresses = [
            "123.456.789.012",
            "987.654.321.098"
        ]
        LogAnalysisRestrictedIpAddress.update_table(ip_addresses)
        ips = LogAnalysisRestrictedIpAddress.query.all()
        assert [ip.ip_address for ip in ips] == ip_addresses
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                LogAnalysisRestrictedIpAddress.update_table(ip_addresses)

#    def __iter__(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedIpAddress::test_iter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_iter(self,restricted_ip_addr):
        ip = LogAnalysisRestrictedIpAddress.query.filter_by(id=1).one()
        for data in ip:
            assert data[0] == "ip_address"
            assert data[1] == "123.456.789.012"
            
            
#class LogAnalysisRestrictedCrawlerList(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedCrawlerList -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestLogAnalysisRestrictedCrawlerList:
#    def get_all(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedCrawlerList::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all(self,log_crawler_list):
        test = [
            "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_ip_blacklist.txt",
            "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_useragent.txt"
        ]
        result = LogAnalysisRestrictedCrawlerList.get_all()
        assert [crawler.list_url for crawler in result] == test
        
        with patch("weko_admin.models.asc", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                result = LogAnalysisRestrictedCrawlerList.get_all()

#    def get_all_active(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedCrawlerList::test_get_all_active -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all_active(self, db, log_crawler_list):
        crawler3 = LogAnalysisRestrictedCrawlerList(
            list_url="https://not_active",
            is_active=False
        )
        db.session.add(crawler3)
        db.session.commit()
        
        test = [
            "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_ip_blacklist.txt",
            "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_useragent.txt"
        ]
        result = LogAnalysisRestrictedCrawlerList.get_all_active()
        assert [crawler.list_url for crawler in result] == test
        
        with patch("weko_admin.models.func.length", side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                result = LogAnalysisRestrictedCrawlerList.get_all_active()

#    def add_list(cls, crawler_lists):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedCrawlerList::test_add_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_add_list(self, db):
        data = [
            "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_ip_blacklist.txt",
            "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_useragent.txt"
        ]
        LogAnalysisRestrictedCrawlerList.add_list(data)
        result = LogAnalysisRestrictedCrawlerList.query.all()
        assert [crawler.list_url for crawler in result] == data
        
        with patch("weko_admin.models.db.session.commit",side_effect=Exception("test_error")):
            with pytest.raises(Exception):
                LogAnalysisRestrictedCrawlerList.add_list(data)

#    def update_or_insert_list(cls, crawler_list):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedCrawlerList::test_update_or_insert_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_or_insert_list(self,log_crawler_list):
        data = [
            {"list_url":"https://bitbucket.org/niijp/jairo-crawler-list/raw/master/new_Crawler-List_ip_blacklist.txt","id":1,"is_active":False},
            {"list_url":"https://new_crawler","id":3}
        ]
        LogAnalysisRestrictedCrawlerList.update_or_insert_list(data)
        crawler1 = LogAnalysisRestrictedCrawlerList.query.filter_by(id=1).one()
        assert crawler1.list_url == "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/new_Crawler-List_ip_blacklist.txt"
        assert crawler1.is_active == False
        crawler3 = LogAnalysisRestrictedCrawlerList.query.filter_by(id=3).one()
        assert crawler3.list_url == "https://new_crawler"
        assert crawler3.is_active == True
        
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                LogAnalysisRestrictedCrawlerList.update_or_insert_list(data)

#    def __iter__(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestLogAnalysisRestrictedCrawlerList::test_iter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_iter(self, log_crawler_list):
        crawler1 = LogAnalysisRestrictedCrawlerList.query.filter_by(id=1).one()
        for data in crawler1:
            assert data[0] == "list_url"
            assert data[1] == "https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_ip_blacklist.txt"


#class BillingPermission(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestBillingPermission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestBillingPermission:

#    def create(cls, user_id, is_active=True):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestBillingPermission::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        BillingPermission.create(1, True)
        assert BillingPermission.query.filter_by(user_id=1).one()
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                BillingPermission.create(1, True)

#    def activation(cls, user_id, is_active):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestBillingPermission::test_activation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_activation(self, billing_permissions):
        # exist permission
        BillingPermission.activation(1,False)
        result = BillingPermission.query.filter_by(user_id=1).one()
        assert result.is_active == False
        
        # not exist permission
        BillingPermission.activation(3,True)
        assert BillingPermission.query.filter_by(user_id=3).one()
        # raise exception
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                BillingPermission.activation(1, True)

#    def get_billing_information_by_id(cls, user_id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestBillingPermission::test_get_billing_information_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_billing_information_by_id(self, billing_permissions):
        result = BillingPermission.get_billing_information_by_id(1)
        assert result.is_active == True
        
        with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
            mock_query.return_value.\
                filter_by.return_value.\
                one_or_none.side_effect = Exception("test_error")
            with pytest.raises(Exception):
                result = BillingPermission.get_billing_information_by_id(1)



#class StatisticsEmail(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStaticsEmail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestStaticsEmail:
#    def insert_email_address(cls, email_address):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStaticsEmail::test_insert_email_address -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_insert_email_address(self, db):
        StatisticsEmail.insert_email_address("test.address@test.org")
        result = StatisticsEmail.query.filter_by(id=1).one()
        assert result.email_address == "test.address@test.org"
        
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                StatisticsEmail.insert_email_address("test.address@test.org")
        
#    def get_all_emails(cls):

#    def get_all(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStaticsEmail::test_get_all_emails -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all_emails(self,statistic_email_addrs):
        result = StatisticsEmail.get_all()
        assert [data.email_address for data in result] == ["test.taro@test.org"]

        with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
            mock_query.return_value.\
                all.side_effect = Exception("test_error")
            with pytest.raises(Exception):
                result = StatisticsEmail.get_all()

    
#    def delete_all_row(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestStaticsEmail::test_delete_all_row -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete_all_row(self, statistic_email_addrs):
        StatisticsEmail.delete_all_row()
        result = StatisticsEmail.query.filter_by(id=1).one_or_none()
        assert result is None
        
        with patch("weko_admin.models.db.session.commit",side_effect=Exception("test_error")):
            with pytest.raises(Exception) as e:
                StatisticsEmail.delete_all_row()
                assert str(e) == "test_error"

#class RankingSettings(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestRankingSettings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestRankingSettings:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestRankingSettings::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_null_data(self, db):
        rs = RankingSettings(
            is_show=True,
            new_item_period=14,
            statistical_period=365,
            display_rank=10
        )
        db.session.add(rs)
        db.session.commit()
        result = RankingSettings.query.first()
        assert result.rankings == {}
        
#    def get(cls, id=0):

#    def update(cls, id=0, data=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestRankingSettings::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update(self,ranking_settings):
        # update
        data = RankingSettings()
        data.is_show = False
        data.new_item_period=10
        data.statistical_period=182
        data.display_rank=5
        data.rankings={"new_items":False,"most_reviewed_items":False,"most_downloaded_items":False,"most_searched_keywords":False,"created_most_items_user":False}
        RankingSettings.update(id=0,data=data)
        result = RankingSettings.query.filter_by(id=0).one()
        assert result.is_show == False
        assert data.new_item_period == 10
        
        # create
        data = RankingSettings()
        data.is_show = True
        data.new_item_period=12
        data.statistical_period=100
        data.display_rank=10
        data.rankings={"new_items":True,"most_reviewed_items":True,"most_downloaded_items":False,"most_searched_keywords":False,"created_most_items_user":False}
        RankingSettings.update(id=1,data=data)
        result = RankingSettings.query.filter_by(id=1).one()
        assert result
        assert result.new_item_period == 12
        
        # raise exception
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException) as e:
                RankingSettings.update(id=0,data=data)
        
#    def delete(cls, id=0):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestRankingSettings::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete(self, ranking_settings):
        RankingSettings.delete(id=0)
        assert RankingSettings.query.filter_by(id=0).one_or_none() is None
        
        # raise exception
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException) as e:
                RankingSettings.delete(id=0)
                assert str(e) == "test_error"


#class FeedbackMailSetting(db.Model, Timestamp):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailSetting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestFeedbackMailSetting:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailSetting::test_null_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_null_data(self, db):
        fms = FeedbackMailSetting(
            account_author="1",
            is_sending_feedback=True
        )
        db.session.add(fms)
        db.session.commit()
        
        result = FeedbackMailSetting.query.first()
        assert result.manual_mail == {}

#    def create(cls, account_author, manual_mail,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailSetting::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        result = FeedbackMailSetting.create(
            account_author="1,2",
            manual_mail={"email":["test.manual1@test.org","test.manual2@test.org"]},
            is_sending_feedback=True,
            root_url="http://test_server"
        )
        assert result == True
        res = FeedbackMailSetting.query.filter_by(id=1).one()
        assert res.account_author == "1,2"
        
        # raise exception
        with patch("weko_admin.models.db.session.commit",side_effect=BaseException("test_error")):
            result = FeedbackMailSetting.create(
                account_author="1,2",
                manual_mail={"email":["test.manual1@test.org","test.manual2@test.org"]},
                is_sending_feedback=True,
                root_url="http://test_server"
            )
            assert result == False
            

#    def get_all_feedback_email_setting(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailSetting::test_get_all_feedback_email_setting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all_feedback_email_setting(self,feedback_mail_settings):
        result = FeedbackMailSetting.get_all_feedback_email_setting()
        assert result[0].manual_mail=={"email":["test.manual1@test.org","test.manual2@test.org"]}
        
        with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
            mock_query.return_value.\
                all.side_effect = Exception("test_error")
            result = FeedbackMailSetting.get_all_feedback_email_setting()
            assert result == []


#    def update(cls, account_author,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailSetting::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update(self,feedback_mail_settings):
        result = FeedbackMailSetting.update(
            account_author="1",
            manual_mail={"email":[]},
            is_sending_feedback=False,
            root_url="http://test_server2"
        )
        assert result == True
        res = FeedbackMailSetting.query.filter_by(id=1).one()
        assert res.account_author == "1"
        assert res.manual_mail == {"email":[]}
        
        # raise exception
        with patch("weko_admin.models.db.session.commit", side_effect=Exception("test_error")):
            result = FeedbackMailSetting.update(
                account_author="1",
                manual_mail={"email":[]},
                is_sending_feedback=False,
                root_url="http://test_server2"
            )
            assert result == False
        
#    def delete(cls, id=1):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailSetting::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete(self, feedback_mail_settings):
        result = FeedbackMailSetting.delete()
        assert result == True
        res = FeedbackMailSetting.query.filter_by(id=1).one_or_none()
        assert res is None
        
        # raise exception
        with patch("weko_admin.models.db.session.commit", side_effect=Exception("test_error")):
            result = FeedbackMailSetting.delete()
            assert result == False


#class AdminSettings(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminSettings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestAdminSettings:
    def test_null_data(self, db):
        ass = AdminSettings(
            name="test_setting"
        )
        db.session.add(ass)
        db.session.commit()
        
        result = AdminSettings.query.first()
        assert result.settings == {}

#    class Dict2Obj(object):
#        def __init__(self, data):
#    def _get_count():

#    def get(cls, name, dict_to_object=True):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminSettings::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get(self,admin_settings):
        result = AdminSettings.get("storage_check_settings",True)
        assert result.day == 0
        assert result.cycle == "weekly"
        
        result = AdminSettings.get("storage_check_settings",False)
        assert result == {"day": 0, "cycle": "weekly", "threshold_rate": 80}
        
        result = AdminSettings.get("not_exist_setting")
        assert result == None
        
        with patch("weko_admin.models.AdminSettings.Dict2Obj.__init__", side_effect=Exception("test_error")):
            result = AdminSettings.get("storage_check_settings",True)
            assert result == None

#    def update(cls, name, settings, id=None):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminSettings::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update(self,admin_settings):
        # update
        AdminSettings.update(
            name="storage_check_settings",
            settings={}
        )
        result = AdminSettings.query.filter_by(name="storage_check_settings").one()
        assert result.settings == {}
        
        # create
        AdminSettings.update(
            name="new_setting",
            settings={"key":"value"},
            id=10
        )
        result = AdminSettings.query.filter_by(id=10).one()
        assert result.name=="new_setting"
        assert result.settings=={"key":"value"}
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                AdminSettings.update(
                    name="storage_check_settings",
                    settings={}
                )
        

#    def delete(cls, name):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestAdminSettings::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete(self, admin_settings):
        AdminSettings.delete("storage_check_settings")
        result = AdminSettings.query.filter_by(name="storage_check_settings").one_or_none()
        assert result is None
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException) as e:
                AdminSettings.delete("items_display_settings")
                assert str(e) == "test_error"
                result = AdminSettings.query.filter_by(name="items_display_settings").one_or_none()
                assert result is not None

#class SiteInfo(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSiteInfo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestSiteInfo:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSiteInfo::test_null_data -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_null_data(self, db):
        si = SiteInfo(
            site_name=None,
            notify=None
        )
        db.session.add(si)
        db.session.commit()
        
        result = SiteInfo.query.first()
        assert result.site_name == {}
        assert result.notify == {}
#    def get(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSiteInfo::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get(self, db, site_info):
        # exist data
        result = SiteInfo.get()
        assert result.copy_right == "test_copy_right1"

        # not exist data
        SiteInfo.query.delete()
        db.session.commit()
        result = SiteInfo.get()
        assert result == {}
        
        # raise exception
        
        with patch("weko_admin.models.db.session.begin_nested",side_effect=SQLAlchemyError):
            result = SiteInfo.get()
            assert result == {}
        with patch("weko_admin.models.db.session.begin_nested",side_effect=Exception("test_error")):
            result = SiteInfo.get()
            assert result == {}
        
        
#    def update(cls, site_info):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestSiteInfo::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update(self, app, site_info, mocker):
        mocker.patch("invenio_files_rest.utils.update_ogp_image", side_effect=lambda x,y:"{}".format(x) if x != "false" else None)
        with app.test_request_context():
            # udpate
            # update_ogp_image is None
            data = {
                "site_name":[
                    {"index":"test_index1","name":"test_name1","language":"en"},
                    {"index":"test_index2","name":"test_name2","language":"ja"},
                ],
                "notify":[
                    {"notify_name":"test_notify1","language":"en"},
                    {"notify_name":"test_notify2","language":"ja"}
                ],
                "copy_right":"new_copyright","description":"this is new description","keyword":"test new keyword","favicon":"test,favicon",
                "favicon_name":"test favicon","google_tracking_id_user":"test_tracking",
                "ogp_image":"false"
            }
            result = SiteInfo.update(data)
            assert result.site_name == [{"index":"test_index1","name":"test_name1","language":"en"},{"index":"test_index2","name":"test_name2","language":"ja"}]
            assert result.ogp_image == "/var/tmp/test_dir"
            assert result.ogp_image_name == "test ogp image name1"

            # update_ogp_image is not None
            data = {
                "site_name":[
                    {"index":"test_index1","name":"test_name1","language":"en"},
                    {"index":"test_index2","name":"test_name2","language":"ja"},
                ],
                "notify":[
                    {"notify_name":"test_notify1","language":"en"},
                    {"notify_name":"test_notify2","language":"ja"}
                ],
                "copy_right":"new_copyright","description":"this is new description","keyword":"test new keyword","favicon":"test,favicon",
                "favicon_name":"test favicon","google_tracking_id_user":"test_tracking",
                "ogp_image":"/var/tmp/new_dir",
                "ogp_image_name":"new ogp image name"
            }
            result = SiteInfo.update(data)
            assert result.site_name == [{"index":"test_index1","name":"test_name1","language":"en"},{"index":"test_index2","name":"test_name2","language":"ja"}]
            assert result.ogp_image == "/var/tmp/new_dir"
            assert result.ogp_image_name == "new ogp image name"

            # create
            SiteInfo.query.delete()
            data = {
                "site_name":[
                    {"index":"new_index1","name":"new_name1","language":"en"},
                    {"index":"new_index2","name":"new_name2","language":"ja"},
                ],
                "notify":[
                    {"notify_name":"new_notify1","language":"en"},
                    {"notify_name":"new_notify2","language":"ja"}
                ],
                "copy_right":"new_copyright","description":"this is new description","keyword":"test new keyword","favicon":"test,favicon",
                "favicon_name":"test favicon","google_tracking_id_user":"",
                "ogp_image":""
            }
            result = SiteInfo.update(data)
            assert result.site_name == [{"index":"new_index1","name":"new_name1","language":"en"},{"index":"new_index2","name":"new_name2","language":"ja"}]
            assert result.ogp_image == None
            assert result.ogp_image_name == None
            assert result.google_tracking_id_user == ""

            # raise Exception
            with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
                with pytest.raises(BaseException):
                    SiteInfo.update(data)


#class FeedbackMailHistory(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailHistory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestFeedbackMailHistory:
#    def get_by_id(cls, id):
#    def get_sequence(cls, session):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailHistory::test_get_sequence -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_sequence(self, db, mocker):

        class MockSession:
            def __init__(self):
                self.id = {"feedback_mail_history_id_seq":1}
            def execute(self,sequence):
                name = sequence.name
                self.id[name]+=1
                return self.id[name]
        session = MockSession()
        result = FeedbackMailHistory.get_sequence(session)
        assert result == 2
        mocker.patch("weko_admin.models.db.session.execute", side_effect=session.execute)
        result = FeedbackMailHistory.get_sequence(None)
        assert result == 3
        
#    def get_all_history(cls):

#    def create(cls,
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailHistory::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        # exist session, parent_id
        session = db.session
        FeedbackMailHistory.create(
            session=session,
            id=1,
            start_time=datetime(2022,10,1,1,2,3,45678),
            end_time=datetime(2022,10,1,2,3,4,56789),
            stats_time="2022-10",
            count=2,
            error=0,
            parent_id=1,
            is_latest=True
        )
        result = FeedbackMailHistory.query.filter_by(id=1).one()
        assert result.stats_time == "2022-10"
        assert result.parent_id == 1
        
        FeedbackMailHistory.create(
            session=None,
            id=2,
            start_time=datetime(2022,11,1,1,2,3,45678),
            end_time=datetime(2022,11,1,2,3,4,56789),
            stats_time="2022-11",
            count=2,
            error=0,
            is_latest=False
        )
        result = FeedbackMailHistory.query.filter_by(id=2).one()
        assert result.stats_time == "2022-11"
        assert result.parent_id == None
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            FeedbackMailHistory.create(
                session=None,
                id=3,
                start_time=datetime(2022,12,1,1,2,3,45678),
                end_time=datetime(2022,12,1,2,3,4,56789),
                stats_time="2022-12",
                count=2,
                error=0,
                is_latest=False
            )
            result = FeedbackMailHistory.query.filter_by(id=3).one_or_none()
            assert result is None
            
#    def update_lastest_status(cls, id, status):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailHistory::test_upate_lastest_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_upate_lastest_status(self, feedback_mail_histories):
        FeedbackMailHistory.update_lastest_status(1, False)
        result = FeedbackMailHistory.query.filter_by(id=1).one()
        assert result.is_latest == False
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                FeedbackMailHistory.update_lastest_status(1, False)


#class FeedbackMailFailed(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailFailed -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestFeedbackMailFailed:
#    def get_by_history_id(cls, history_id):

#    def get_mail_by_history_id(cls, history_id):

#    def delete_by_history_id(cls, session, history_id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailFailed::test_delete_by_history_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete_by_history_id(self, db, feedback_mail_faileds):
        session = db.session
        FeedbackMailFailed.delete_by_history_id(session,1)
        result = FeedbackMailFailed.query.filter_by(id=1).one_or_none()
        assert result is None
        
        failed1 = FeedbackMailFailed(
            history_id=1,
            author_id=1,
            mail="test.test1@test.org"
        )
        db.session.add(failed1)
        db.session.commit()
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            FeedbackMailFailed.delete_by_history_id(None,1)
            result = FeedbackMailFailed.query.filter_by(id=1).one_or_none()
            assert result is not  None

#    def create(cls, session, history_id, author_id, mail):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFeedbackMailFailed::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self, db):
        session = db.session
        FeedbackMailFailed.create(
            session=session,
            history_id=1,
            author_id=1,
            mail="test@test.org"
        )
        result = FeedbackMailFailed.query.filter_by(id=1).one()
        assert result
        assert result.mail == "test@test.org"
        
        with patch("weko_admin.models.db.session.commit", side_effect=BaseException("test_error")):
            FeedbackMailFailed.create(
                session=None,
                history_id=2,
                author_id=2,
                mail="test2@test.org"
            )
            result = FeedbackMailFailed.query.filter_by(id=2).one_or_none()
            assert result is None
            
#class Identifier(db.Model):
#    def __repr__(self):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::test_Identifier_repr -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_Identifier_repr(identifier):
    result = repr(identifier)
    assert result == "<Identifier 1, Repository: Root Index>"


#class FacetSearchSetting(db.Model):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
class TestFacetSearchSetting:
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting::test_null_data -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_null_data(self, db):
        fss = FacetSearchSetting(
            name_en="test_setting",
            mapping="test_mapping",
            aggregations=None,
            name_jp=None,
            active=None,
            ui_type="test_ui_type",
            display_number=1,
            is_open=None
        )
        db.session.add(fss)
        db.session.commit()
        
        result = FacetSearchSetting.query.first()
        assert result.aggregations == {}

#    def __init__(self, name_en, name_jp, mapping, aggregations, active):

#    def to_dict(self) -> dict:

#    def get_by_id(cls, id):

#    def get_all(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_all(self, facet_search_settings):
        result = FacetSearchSetting.get_all()
        assert result[0].name_en == "Data Language"
        assert result[1].name_en == "Access"

#    def get_activated_facets(cls):

#    def create(cls, faceted_search_dict):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_create(self,db):
        data = {
            "name_en":"test setting",
            "name_jp":"テスト設定",
            "mapping":"test_mapping",
            "aggregations":[],
            "active":True,
            "ui_type":"SelectBox",
            "display_number":1,
            "is_open":True
        }
        result = FacetSearchSetting.create(data)
        assert result.name_en == "test setting"
        assert result.aggregations == []
        
        with patch("weko_admin.models.db.session.commit", side_effect=Exception("test_error")):
            result = FacetSearchSetting.create(data)
            assert result == None
        
#    def delete(cls, id):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_delete(self,facet_search_settings):
        # id is None
        result = FacetSearchSetting.delete(None)
        assert result == False
        
        # id is not None
        result = FacetSearchSetting.delete(1)
        assert result == True
        
        # raise exception
        with patch("weko_admin.models.db.session.commit", side_effect=Exception("test_error")):
            result = FacetSearchSetting.delete(2)
            assert result == False
            res = FacetSearchSetting.query.filter_by(id=2).one_or_none()
            assert res is not None

#    def update_by_id(cls, id, faceted_search_dict):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting::test_update_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_update_by_id(self, facet_search_settings):
        # facet_search is None
        result = FacetSearchSetting.update_by_id(100,{})
        assert result == False
        
        # facet_search is not None
        data = {
            "name_en":"test setting",
            "name_jp":"テスト設定",
            "mapping":"test_mapping",
            "aggregations":[],
            "active":True
        }
        result = FacetSearchSetting.update_by_id(1,data)
        assert result == True
        res = FacetSearchSetting.query.filter_by(id=1).one_or_none()
        assert res.name_en == "test setting"
        assert res.name_jp == "テスト設定"
        
        # raise exception
        with patch("weko_admin.models.db.session.commit", side_effect=Exception("test_error")):
            result = FacetSearchSetting.update_by_id(2,data)
            assert result == False
            res = FacetSearchSetting.query.filter_by(id=2).one_or_none()
            assert res.name_en == "Access"
            assert res.name_jp == "アクセス制限"

#    def get_activated_facets_mapping(cls):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_models.py::TestFacetSearchSetting::test_get_activated_facets_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
    def test_get_activated_facets_mapping(self, facet_search_settings):
        test = {
            "Data Language": "language",
            "Data Type": "description.value",
            "raw_test": "test.fields.raw"
        }
        result = FacetSearchSetting.get_activated_facets_mapping()
        assert result == test
        
#    def get_by_name(cls, name_en, name_jp):

#    def get_by_mapping(cls, mapping):
