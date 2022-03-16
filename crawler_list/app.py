import redis
import requests

from flask import Flask
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine ,Column, Integer, String, Boolean, asc
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from redis import RedisError, sentinel
from simplekv.memory.redisstore import RedisStore

Base = declarative_base()
app = Flask(__name__)

class saveCrawlerList:

    def put_crawler(self):
        app.logger.info("start put crawler")
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
            app.logger.info("Set to redis crawler List:"+str(restricted_agent_list))

    def redis_connection(self):
        try:
            if app.config["REDIS_TYPE"] == 'redis':
                self.connection = RedisStore(redis.StrictRedis(app.config['REDIS_HOST'],port = app.config['REDIS_PORT'],db = app.config["REDIS_DB"]))
            elif app.config["REDIS_TYPE"] == 'redissentinel':
                self.connection = sentinel.Sentinel(app.config["SENTINEL_HOST"])
                self.master = RedisStore(self.connection.master_for(app.config["SENTINEL_HOST"],db = app.config["REDIS_DB"]))
        except RedisError as err:
            error_str = "Error while connecting to redis : " + str(err)
            app.logger.error(error_str)


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
            app.logger.debug(ex)
            all = []
            raise
        return all

if __name__ == "__main__":
    app.run(debug=True)
    app.config.from_pyfile('instance.cfg')

    redis_driver = saveCrawlerList()

    engine = create_engine(app.config["DB_HOST"])
    session = sessionmaker(engine)

    redis_driver.put_crawler()
    
    
