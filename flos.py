import js2py
import os
from bs4 import BeautifulSoup as bs
from utils import logger
import requests


class Session:
    headers = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
    }

    DOMAIN = os.getenv('DOMAIN')
    URL = os.getenv('URL')
    URL2 = os.getenv('URL2')

    BOSSES_ID = {
        '110': '18',
        '115': '19',
        '120': '20',
        '125': '21',
        '130': '22',
        '140': '23',
        '155': '1',
        '160': '2',
        '165': '3',
        '170': '4',
        '180': '5',
        '185': '6',
        '190': '7',
        '195': '8',
        '200': '9',
        '205': '10',
        '210': '11',
        '215': '12',
        'aggy': '13',
        'mord': '15',
        'hrung': '14',
        'necro': '16',
        'prot': '24',
        'gele': '38',
        'bt': '39',
        'dino': '40'
    }

    def __init__(self, user, passw, clan):
        self.session = requests.Session()
        self.payload = {
            'user': user,
            'pass': passw,
            'clan': clan,
            'commit': 'login'
        }

    def login(self):
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

    def reset_boss(self, boss):
        res = self.session.get(Session.URL2 + Session.BOSSES_ID[boss],
                               headers=Session.headers)
        logger(f'Flos.reset: boss:{boss} success:{res.text}')
        if res.text != '1':
            self.login()
