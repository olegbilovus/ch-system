import os
import logging
import requests

import psycopg2

from datetime import datetime

logging.basicConfig(format='%(levelname)s %(asctime)s - %(message)s', level=logging.INFO)


class Database:
    db_url = os.getenv('DB_URL')
    db_uri = os.getenv('DB_URI')
    conn = psycopg2.connect(db_uri)
    cur = conn.cursor()

    def __init__(self):
        self.update_url()

    def update_url(self, force=False):
        res = requests.get(self.db_url, data={'update': '1' if force else '0'})
        if res.status_code == 200:
            os.putenv('DB_URI', res.text)
            self.db_uri = res.text
            logging.info('Got DB_URL')
            self.conn = psycopg2.connect(self.db_uri)
            self.cur = self.conn.cursor()
        else:
            logging.error('ERROR DB_URL')
            self.db_uri = None
            self.conn = None
            self.cur = None


class Server(Database):

    def retrieve_all(self):
        self.cur.execute('SELECT * FROM server')
        return self.cur.fetchall()


class Clan(Database):

    def get_by_id(self, clan_id):
        self.cur.execute('SELECT * FROM clan WHERE id = %s', (clan_id,))
        return self.cur.fetchone()

    def get_by_name_and_server(self, clan_name, server_id):
        self.cur.execute('SELECT * FROM clan WHERE name = %s AND serverid = %s', (clan_name, server_id))
        return self.cur.fetchone()

    def create(self, clan_name, server_id):
        self.cur.execute('INSERT INTO clan (name, serverid) VALUES (%s, %s)', (clan_name, server_id))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, clan_id, clan_name, server_id):
        self.cur.execute('UPDATE clan SET name = %s, serverid = %s WHERE id = %s', (clan_name, server_id, clan_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, clan_id):
        self.cur.execute('DELETE FROM clan WHERE id = %s', (clan_id,))
        self.conn.commit()
        return self.cur.fetchone()
