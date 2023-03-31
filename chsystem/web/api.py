import os
from datetime import datetime
from secrets import token_hex

import bcrypt
import requests
from utils import get_current_time_minutes, TIMER_OFFSET

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
                    user_session = User(id=token_hex(16), sessionid=token_hex(64), username=username,
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
    def delete_session_by_id(self, _id) -> bool:
        res = self.session.delete(f'{self.url}/websession?id=eq.{_id}')
        return res.status_code == 204

    @postgrest_sanitize
    def get_user_by_sessionid(self, sessionid) -> User | None:
        exists = self.session.get(f'{self.url}/websession?sessionid=eq.{sessionid}&select=sessionid')
        if exists.status_code == 200 and exists.json():
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
            f'{self.url}/websession?userprofileid=eq.{userprofileid}&select=id,creation,lastuse,host&order=lastuse').json()
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
        res = self.session.patch(f'{self.url}/websession?sessionid=eq.{sessionid}',
                                 json={'lastuse': datetime.utcnow().isoformat()})

        return res.status_code == 204

    @postgrest_sanitize
    def get_timers_type_by_clanid(self, clanid):
        types = self.session.get(f'{self.url}/timer?clanid=eq.{clanid}&select=type&order=type').json()
        data = []
        prev_type = ''
        for t in types:
            timer_type = t['type']
            if timer_type != prev_type:
                data.append(timer_type)
                prev_type = timer_type

        return data

    @postgrest_sanitize
    def get_timers_by_clanid_type(self, clanid, _type):
        return self.session.get(
            f'{self.url}/timer?clanid=eq.{clanid}&type=eq.{_type}&select=bossname,timer&order=bossname').json()

    @postgrest_sanitize
    def set_timer_by_clanid_bossname(self, clanid, bossname, timer):
        res = self.session.patch(f'{self.url}/timer?clanid=eq.{clanid}&bossname=eq.{bossname}', json={'timer': timer})

        return res.status_code == 204

    @postgrest_sanitize
    def reset_timer_by_clanid_bossname(self, clanid, bossname):
        boss_data = self.session.get(
            f'{self.url}/timer?clanid=eq.{clanid}&bossname=eq.{bossname}&select=respawntimeminutes').json()
        if boss_data:
            respawn_time_minutes = boss_data[0]['respawntimeminutes']
            current_time_in_minutes = get_current_time_minutes()
            timer = current_time_in_minutes + respawn_time_minutes - TIMER_OFFSET
            res = self.set_timer_by_clanid_bossname(clanid, bossname, timer)

            if res:
                return {'timer': timer}

    @postgrest_sanitize
    def change_pw(self, userprofileid, oldpw, newpw):
        user = self.session.get(f'{self.url}/webprofile?userprofileid=eq.{userprofileid}').json()
        if user and bcrypt.checkpw(bytes(oldpw, 'utf-8'), bytes(user[0]['hash_pw'], 'utf-8')):
            res = self.session.patch(f'{self.url}/webprofile?userprofileid=eq.{userprofileid}',
                                     json={'hash_pw': bcrypt.hashpw(bytes(newpw, 'utf-8'), bcrypt.gensalt()).decode(
                                         "utf-8")})
            return res.status_code == 204

        return False
