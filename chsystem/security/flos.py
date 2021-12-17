import js2py
import os
import requests

from bs4 import BeautifulSoup as bs
from utils import logger
from replit import db


class Session:
    headers = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    }

    DOMAIN = os.getenv('DOMAIN')
    URL = os.getenv('URL')
    URL2 = os.getenv('URL2')

    def __init__(self, user, passw, clan):
        self.session = None
        self.payload = {
            'user': user,
            'pass': passw,
            'clan': clan,
            'commit': 'login'
        }

    def login(self):
        self.session = requests.session()
        req = self.session.post(Session.URL,
                                headers=Session.headers,
                                data=self.payload)
        soup = bs(req.text, 'html5lib')
        script = (soup.find('script'))
        scr = script.text
        a = (scr.split("(r)")[0][:-1] +
             "r=r.replace('document.cookie','var cookie');")
        b = (js2py.eval_js(a))
        sucuri_cloudproxy_cookie = js2py.eval_js(
            b.replace("location.", "").replace("reload();", ""))

        sucuri_uuid = sucuri_cloudproxy_cookie.split("=")[0]
        token = sucuri_cloudproxy_cookie.split("=")[1].replace(";path", "")

        self.session.cookies.set(sucuri_uuid, token, domain=Session.DOMAIN)
        logger('Flos logged')

    def get_users(self):
        logger('Flos check admins')
        res = self.session.get(Session.URL2, headers=Session.headers)
        soup = bs(res.text, 'html5lib')
        table = soup.body.table.tbody
        table_children = table.children
        users = []
        for table_child in table_children:
            tr_children = table_child.children
            if len(table_child.getText()) > 100 and tr_children:
                user = {}
                for i, tr_child in enumerate(tr_children):
                    if i == 0:
                        user['username'] = tr_child.getText()
                    elif i == 1:
                        select = tr_child.find('select')
                        user['flos_id'] = select['data-user-id']
                        user['role'] = select.option['value']
                    else:
                        break

                users.append(user)
        logger('Flos admins checked')
        db['users_flos'] = users
        return users

    def check_admins(self, users, admins):
        users_unauthorized = []
        for user in users:
            if user['role'] == '6' and user['username'] not in admins:
                users_unauthorized.append(user)

        if users_unauthorized:
            for user in users_unauthorized:
                payload = {'user_id_to_edit': user['flos_id'], 'level': 0}
                self.session.post(Session.URL2,
                                  headers=Session.headers,
                                  data=payload)
        return users_unauthorized
