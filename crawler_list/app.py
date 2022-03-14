from flask import Flask
import redis
import sqlalchemy


app = Flask(__name__)

class saveCrawlerList:

    def getCrawlerList(crawler_list):
        f = open(crawler_list, 'r')
        list = f.readlines()
        return list

    def redis_connection():
        
        return



if __name__ == "__main__":
    app.run(debug=True)
    app.config.from_pyfile('instance.cfg')
