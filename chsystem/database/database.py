import os
import logging
import requests

import psycopg2

logging.basicConfig(format='%(levelname)s %(asctime)s - %(message)s', level=logging.INFO)


class Database:
    db_url = os.getenv('DB_URL')
    db_uri = os.getenv('DB_URI')
    conn = None
    cur = None

    def __init__(self, uri=None, url=None):
        self.update_url(uri, url)

    def update_url(self, uri=None, url=None, force=False):
        if uri is None and Database.db_uri is None:
            res = requests.get(Database.db_url if url is None else url, data={'update': '1' if force else '0'})
            if res.status_code == 200:
                os.putenv('DB_URI', res.text)
                Database.db_uri = res.text
                logging.info('Got DB_URL')
            else:
                logging.error('ERROR DB_URL')
                Database.db_uri = None
                self.conn = None
                self.cur = None
        else:
            Database.db_uri = uri if uri is not None else Database.db_uri
            Database.db_url = url if url is not None else Database.db_url

        self.conn = psycopg2.connect(Database.db_uri)
        self.cur = self.conn.cursor()
        self.cur.execute('SELECT version()')
        logging.info(self.cur.fetchone())


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
