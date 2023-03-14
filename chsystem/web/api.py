import requests

ROLES = ['Recruit', 'Clansman', 'Guardian', 'General', 'Admin']
ROLES_COLORS = ['#f1c21b', '#e67f22', '#3398dc', '#9a59b5', '#1abc9b']


class Api:
    def __init__(self, cert_f, key_f, cf_client_id, cf_client_secret, url):
        self.session = requests.Session()
        self.session.cert = (cert_f, key_f)
        self.session.headers.update({'CF-Access-Client-Id': cf_client_id, 'CF-Access-Client-Secret': cf_client_secret})
        self.url = url

    def check_valid_conn(self):
        res = self.session.get(self.url)
        return res.status_code < 400
