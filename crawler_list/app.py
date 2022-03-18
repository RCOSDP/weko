import redis
import requests
import configparser
import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine ,Column, Integer, String, Boolean, asc
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from redis import RedisError, sentinel
from simplekv.memory.redisstore import RedisStore

Base = declarative_base()
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
config_ini.set('DEFAULT', 'DB_URI','postgresql+psycopg2://' + str(os.environ.get('INVENIO_POSTGRESQL_DBUSER')) + ':' + str(os.environ.get('INVENIO_POSTGRESQL_DBPASS'))+'@'+ str(os.environ.get('INVENIO_POSTGRESQL_HOST'))+':5432/' + str(os.environ.get('INVENIO_POSTGRESQL_DBNAME')))

class saveCrawlerList:

    def put_crawler(self):
        print("start put crawler")
        self.redis_connection()
        local_session = session()
        restricted_agent_lists = LogAnalysisRestrictedCrawlerList.get_all_active()
        local_session.close()
        for restricted_agent_list in restricted_agent_lists:
            raw_res = requests.get(restricted_agent_list.list_url).text
            if not raw_res:
                continue
            restrict_list = raw_res.split('\n')
            restrict_list = [
                agent for agent in restrict_list if not agent.startswith('#')]
            for restrict_ip in restrict_list:
                self.master.sadd(restricted_agent_list,restrict_ip)
            print("Set to redis crawler List:"+str(restricted_agent_list))

    def redis_connection(self):
        try:
            if config_ini['DEFAULT']["REDIS_TYPE"] == 'redis':
                self.connection = RedisStore(redis.StrictRedis(config_ini['DEFAULT']['REDIS_HOST'],port = config_ini['DEFAULT']['REDIS_PORT'],db = config_ini['DEFAULT']["REDIS_DB"]))
            elif config_ini['DEFAULT']["REDIS_TYPE"] == 'redissentinel':
                self.connection = sentinel.Sentinel(config_ini['DEFAULT']["SENTINEL_HOST"])
                self.master = RedisStore(self.connection.master_for(config_ini['DEFAULT']["SENTINEL_HOST"],db = config_ini['DEFAULT']["REDIS_DB"]))
        except RedisError as err:
            error_str = "Error while connecting to redis : " + str(err)
            print(error_str)


class LogAnalysisRestrictedCrawlerList(Base):
    __tablename__ = 'loganalysis_restricted_crawler_list'

    id = Column(
        Integer(),
        primary_key=True,
        autoincrement=True
    )

    list_url = Column(
        String(255),
        nullable=False
    )

    is_active = Column(
        Boolean(name='activated'),
        default=True
    )

    @classmethod
    def get_all(cls):
        """Get all crawler lists.

        :return: All crawler lists.
        """
        try:
            all = cls.query.order_by(asc(cls.id)).all()
        except Exception as ex:
            app.logger.debug(ex)
            all = []
            raise
        return all

    @classmethod
    def get_all_active(cls):
        """Get all active crawler lists.

        :return: All active crawler lists.
        """
        try:
            all = cls.query.filter(cls.is_active.is_(True)) \
                .filter(func.length(cls.list_url) > 0).all()
        except Exception as ex:
            print(ex)
            all = []
            raise
        return all

if __name__ == "__main__":

    
    redis_driver = saveCrawlerList()

    engine = create_engine(config_ini['DEFAULT']["DB_URI"])
    session = sessionmaker(engine)

    redis_driver.put_crawler()
    
    
