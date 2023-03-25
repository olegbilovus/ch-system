import bcrypt
import requests


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

    def check_valid_conn(self):
        res = self.session.get(self.url)
        return res.status_code < 400

    @postgrest_sanitize
    def login(self, username, password, serverid, clan):
        user = self.session.get(f'{self.url}/webprofile?username=eq.{username}').json()[0]
        if user and bcrypt.checkpw(bytes(password, 'utf-8'), bytes(user['hash_pw'], 'utf-8')):
            user_data = self.session.get(f'{self.url}/userprofile?id=eq.{user["userprofileid"]}').json()[0]
            if user_data['serverid'] == serverid:
                clan_data = self.session.get(f'{self.url}/clan?id=eq.{user_data["clanid"]}').json()[0]
                if clan_data['name'] == clan:
                    data = {
                        'userprofileid': user_data['id'],
                        'name': user_data['name'],
                        'role': user_data['role'],
                        'clanid': user_data['clanid'],
                        'serverid': user_data['serverid'],
                        'change_pw': user['change_pw']
                    }
                    return data

    @postgrest_sanitize
    def get_by_userprofileid(self, userprofileid):
        user_data = self.session.get(
            f'{self.url}/webprofile?userprofileid=eq.{userprofileid}&select=username,change_pw,userprofile(name,role,clanid,serverid)').json()[
            0]
        data = {
            'username': user_data['username'],
            'name': user_data['userprofile']['name'],
            'role': user_data['userprofile']['role'],
            'clanid': user_data['userprofile']['clanid'],
            'serverid': user_data['userprofile']['serverid'],
            'change_pw': user_data['change_pw']
        }
        return data

    def get_servers_names(self):
        return self.session.get(f'{self.url}/server?select=id,name&order=name').json()
