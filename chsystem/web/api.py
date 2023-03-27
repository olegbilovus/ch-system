import os
import uuid
from datetime import datetime
from secrets import token_hex

import bcrypt
import requests

from models import User

_HOST = os.getenv('HOST')


def check_str_chars(obj):
    objs = str(obj).split(' ')
    for o in objs:
        if len(o) > 0 and not o.isalnum():
            return True

    return False


def postgrest_sanitize(fun):
    def wrapper_fun(*args, **kwargs):
        for arg in args[1:]:
            if check_str_chars(arg):
                return
        for k, v in kwargs.items():
            if check_str_chars(k) or check_str_chars(v):
                return
        return fun(*args, **kwargs)

    return wrapper_fun


class Api:

    def __init__(self, cert_f, key_f, cf_client_id, cf_client_secret, url):
        self.session = requests.Session()
        self.session.cert = (cert_f, key_f)
        self.session.headers.update({'CF-Access-Client-Id': cf_client_id, 'CF-Access-Client-Secret': cf_client_secret})
        self.url = url

    def check_valid_conn(self) -> bool:
        res = self.session.get(self.url)
        return res.status_code < 400

    def get_servers_names(self):
        return self.session.get(f'{self.url}/server?select=id,name&order=name').json()

    @postgrest_sanitize
    def login(self, username, password, serverid, clan) -> User | None:
        # The login is divided in multiple steps to avoid making complex query when the user does not exist
        user = self.session.get(f'{self.url}/webprofile?username=eq.{username}').json()
        if user and bcrypt.checkpw(bytes(password, 'utf-8'), bytes(user[0]['hash_pw'], 'utf-8')):
            user = user[0]
            user_data = self.session.get(f'{self.url}/userprofile?id=eq.{user["userprofileid"]}').json()[0]
            if user_data['serverid'] == serverid:
                clan_data = self.session.get(f'{self.url}/clan?id=eq.{user_data["clanid"]}').json()[0]
                if clan_data['name'] == clan:
                    user_session = User(id=str(uuid.uuid4()), sessionid=token_hex(64), username=username,
                                        userprofileid=user_data['id'],
                                        name=user_data['name'], role=user_data['role'],
                                        clanid=user_data['clanid'], serverid=user_data['serverid'],
                                        change_pw=user['change_pw'],
                                        creation=datetime.utcnow(), lastuse=datetime.utcnow(), host=_HOST)

                    res = self.session.post(f'{self.url}/websession',
                                            json={'id': user_session.id, 'sessionid': user_session.sessionid,
                                                  'userprofileid': user_session.userprofileid,
                                                  'host': user_session.host})
                    if res.status_code == 201:
                        return user_session

    @postgrest_sanitize
    def delete_session(self, sessionid) -> bool:
        res = self.session.delete(f'{self.url}/websession?sessionid=eq.{sessionid}')
        return res.status_code == 204

    @postgrest_sanitize
    def get_user_by_sessionid(self, sessionid) -> User | None:
        exists = self.session.get(f'{self.url}/websession?sessionid=eq.{sessionid}&select=sessionid').json()
        if exists:
            data = self.session.get(
                f'{self.url}/websession?sessionid=eq.{sessionid}&select=*,userprofile(name,serverid,clanid,role,webprofile(username,change_pw))').json()[
                0]
            return User(id=data['id'], sessionid=data['sessionid'], userprofileid=data['userprofileid'],
                        creation=data['creation'], lastuse=data['lastuse'],
                        username=data['userprofile']['webprofile']['username'],
                        change_pw=data['userprofile']['webprofile']['change_pw'],
                        clanid=data['userprofile']['clanid'],
                        serverid=data['userprofile']['serverid'], name=data['userprofile']['name'],
                        role=data['userprofile']['role'])

    @postgrest_sanitize
    def get_user_sessions(self, userprofileid) -> list[User]:
        data = self.session.get(
            f'{self.url}/websession?userprofileid=eq.{userprofileid}&select=id,creation,lastuse,host').json()
        return [User(id=d['id'], creation=d['creation'], lastuse=d['lastuse'], host=d['host']) for d in data]

    @postgrest_sanitize
    def get_session_by_id(self, _id) -> User | None:
        data = self.session.get(
            f'{self.url}/websession?id=eq.{_id}&select=sessionid,userprofile(id,clanid,role)').json()
        if data:
            data = data[0]
            return User(id=_id, sessionid=data['sessionid'], userprofileid=data['userprofile']['id'],
                        clanid=data['userprofile']['clanid'], role=data['userprofile']['role'])

    @postgrest_sanitize
    def session_used(self, sessionid):
        res = self.session.patch(f'{self.url}/websession?sessionid=eq.{sessionid}', json={'lastuse': datetime.utcnow().isoformat()})

        return res.status_code == 204
