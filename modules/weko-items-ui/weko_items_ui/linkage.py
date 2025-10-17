
import functools
import re
from flask_babelex import gettext as _
from time import sleep
from flask import current_app
import jwt
from datetime import datetime, timezone,timedelta
import requests
import urllib
import json

from weko_admin.models import AdminSettings

class Researchmap:

    def __init__(self) -> None:
        self.token = ""

    @staticmethod
    def create_access_token(encoded_jwt , type):
        """
            POST https://api.researchmap.jp/oauth2/token
        Host: xxxxxx.example.com
        Content-Type: application/x-www-form-urlencoded
        {
        “grant_type”=”urn:ietf:params:oauth:grant-type:jwt-bearer”,
        “assertion”="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        “scope”=”profile read”,
        “version”=”2”
        }
        """
        host = current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_HOST"] # type: ignore
        base_url=current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_BASE_URL"] # type: ignore


        token_api_url = base_url+"/oauth2/token"
        grant_type = "urn:ietf:params:oauth:grant-type:jwt-bearer"
        assertion = encoded_jwt
        if type == 'get':
            scope = "read achievements"
        elif type == 'post':
            scope = "write achievements" # researchers
        else:
            scope = ''
        version = "2"

        headers = { "Host": host,
                    "Content-Type": "application/x-www-form-urlencoded" }
        params = {
                    "grant_type": grant_type,
                    "assertion": assertion,
                    "scope": scope,
                    "version": version
                }
        params = urllib.parse.urlencode(params) # type: ignore

        response = requests.post(url=token_api_url, headers=headers, data=params)
        res :str = response.text
        return json.loads(res).get("access_token" ,'')
    

    @staticmethod
    def create_jwt():
        base_url=current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_BASE_URL"] # type: ignore
        
        # settings_json = AdminSettings.get(current_app.config.get('WEKO_ADMIN_SETTINGS_RESEARCHMAP_LINKAGE_SETTINGS') )
        settings_json = AdminSettings.get('researchmap_linkage_settings' , False) 
        if not settings_json:
            raise Exception(_('Nothing API keys'))

        client_id = settings_json.get("researchmap_cidkey_contents" , '') # type: ignore
        key = settings_json.get("researchmap_pkey_contents" , '') # type: ignore

        if not client_id or not key:
            raise Exception(_('Nothing API keys'))

        payload_data = {
            "iss": client_id,
            "aud": base_url + "/oauth2/token",
            "sub": 0,
            "exp": int((datetime.now(tz=timezone.utc) + timedelta(minutes=10)).timestamp()),
            "iat": int((datetime.now(tz=timezone.utc) - timedelta(seconds=1)).timestamp())
        }
        algorithm="RS256"

        jwt_jsonstr = jwt.encode(payload=payload_data,key=key,algorithm=algorithm,headers={'header':{'alg':'RS256' ,'typ' :'JWT'}})

        return jwt_jsonstr 
    
    
    @staticmethod
    def get_reseacher(token , parmalink:str , achievement_type:str , achievement_id:str):
        base_url=current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_BASE_URL"] # type: ignore
        response = requests.get('{}/{}/{}/{}'.format(base_url, parmalink , achievement_type,  achievement_id).encode()
                                , headers={"Authorization": "Bearer "+token+""
                                    ,"Accept": "application/ld+json,application/json,*/*;q=0.1"
                                    ,"Accept-Encoding": "gzip"}
        )
        return response


    @staticmethod
    def post_achievement_datas(token ,body:str):
        base_url=current_app.config["WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_BASE_URL"] # type: ignore

        response = requests.post(base_url + "/_bulk" #+ "?check=1"
                                , headers={"Authorization": "Bearer "+token+""
                                    ,"Accept": "application/ld+json,application/json,*/*;q=0.1"
                                    ,"Accept-Encoding": "gzip"
                                    ,"Content-Type": "application/json"}
                                , data=body
                                )

        return response


    def get_token(self , type):
        if self.token == "":
            self.token = Researchmap.create_access_token(Researchmap.create_jwt() ,type)

        return self.token


    def get_data(self, parmalink , achievement_type , achievement_id):
        if not re.match('^[0-9a-zA-Z -/:-@\[-~]{3,20}$', parmalink) \
            or re.match('^(?=.*[\%|\#|\<|\>|\+|\¥|\"|\'|\&|\?|\=|\~|\:|\;|\,|\@|\$|\^|\||\]|\[|\!|\(|\)|\*|\/]).*$', parmalink) :# % # < > + ¥ " ' & ? = ~ : ; , @ $ ^ | ] [ ! ( ) * / を含む場合エラー
            raise Exception(_('Invalid parmalink'))
        if not re.match('^[0-9]+$', achievement_id) :
            raise Exception(_('Invalid achievement id'))


        def __get():
            token = self.get_token('get')
            return Researchmap.get_reseacher(token , parmalink , achievement_type , achievement_id)

        return self.retry(functools.partial(__get))


    def post_data(self ,jsons):
        def __post():
            token = self.get_token('post')
            return Researchmap.post_achievement_datas(token ,jsons)

        return self.retry(functools.partial(__post))


    def get_result(self ,url):
        def __get():
            token = self.get_token('post')
            response = requests.get(url
                            , headers={"Authorization": "Bearer "+token+""
                                ,"Accept": "application/ld+json,application/json,*/*;q=0.1"
                                ,"Accept-Encoding": "gzip"})
            current_app.logger.debug(response.text)
            if response.status_code == 200 and json.loads(response.text.splitlines()[0]).get('code' , '') == 102:
                sleep(10) # 10 seconds waiting
                return __get()
            else :
                return response
        
        return self.retry(functools.partial(__get))


    def retry(self ,func :functools.partial):
        
        retry_count = 0 
        CONST_RETRY_MAX = current_app.config['WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_RETRY_MAX'] # type: ignore

        def __can_end(response):
            return response.status_code == 200 or response.status_code == 404 or retry_count >= CONST_RETRY_MAX

        def __recovery(response):
            if response.status_code == 401 and json.loads(response.text.splitlines()[0]).get("error") == "invalid_token" :
                self.token = ""

        response = func()
        current_app.logger.debug(response.status_code)
        current_app.logger.debug(response.text)
        while not __can_end(response) :
            retry_count = retry_count + 1 
            current_app.logger.debug("retry start {}".format(retry_count))
            __recovery(response)
            response = func()
            current_app.logger.debug(response.status_code)
            current_app.logger.debug(response.text)

        return response.text
