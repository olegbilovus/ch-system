import os
import requests
import psycopg2

import logs

logger = logs.get_logger()


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

        if self.conn is not None:
            self.conn.close()
            self.cur = None
            self.conn = None
        self.conn = psycopg2.connect(Database.db_uri)
        self.cur = self.conn.cursor()
        self.cur.execute('SELECT version()')
        logging.info(self.cur.fetchone())


class Server(Database):

    def get_all(self):
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


class UserProfile(Database):

    def get_by_clan_and_server(self, clan_id, server_id):
        self.cur.execute('SELECT * FROM userprofile WHERE clanid = %s AND serverid = %s', (clan_id, server_id))
        return self.cur.fetchall()

    def get_by_id(self, user_id):
        self.cur.execute('SELECT * FROM userprofile WHERE id = %s', (user_id,))
        return self.cur.fetchone()

    def get_by_name_and_server(self, user_name, server_id):
        self.cur.execute('SELECT * FROM userprofile WHERE name = %s AND serverid = %s', (user_name, server_id))
        return self.cur.fetchone()

    def create(self, user_name, server_id, clan_id, role, hash_pw):
        self.cur.execute(
            'INSERT INTO userprofile (name, serverid, clanid, role, hash_pw, change_pw) VALUES (%s, %s, %s, %s, %s)',
            (user_name, server_id, clan_id, role, hash_pw, True))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, user_id, user_name, server_id, clan_id, role, hash_pw, change_pw):
        self.cur.execute(
            'UPDATE userprofile SET name = %s, serverid = %s, clanid = %s, role = %s, hash_pw = %s, change_pw = %s WHERE id = %s',
            (user_name, server_id, clan_id, role, hash_pw, change_pw, user_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, user_id):
        self.cur.execute('DELETE FROM userprofile WHERE id = %s', (user_id,))
        self.conn.commit()
        return self.cur.fetchone()


class ApiKey(Database):

    def get_by_user_id(self, user_id):
        self.cur.execute('SELECT * FROM apikey WHERE userprofileid = %s', (user_id,))
        return self.cur.fetchone()

    def create(self, user_id, key):
        self.cur.execute('INSERT INTO apikey (userprofileid, key) VALUES (%s, %s)', (user_id, key))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, user_id, key):
        self.cur.execute('UPDATE apikey SET key = %s WHERE userprofileid = %s', (key, user_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, user_id):
        self.cur.execute('DELETE FROM apikey WHERE userprofileid = %s', (user_id,))
        self.conn.commit()
        return self.cur.fetchone()


class DiscordID(Database):

    def get_by_user_id(self, user_id):
        self.cur.execute('SELECT * FROM discordid WHERE userprofileid = %s', (user_id,))
        return self.cur.fetchone()

    def create(self, user_id, discord_id):
        self.cur.execute('INSERT INTO discordid (userprofileid, discordid) VALUES (%s, %s)', (user_id, discord_id))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, user_id, discord_id):
        self.cur.execute('UPDATE discordid SET discordid = %s WHERE userprofileid = %s', (discord_id, user_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, user_id):
        self.cur.execute('DELETE FROM discordid WHERE userprofileid = %s', (user_id,))
        self.conn.commit()
        return self.cur.fetchone()


class DiscordChannelID(Database):
    def get_by_clan_id(self, clan_id):
        self.cur.execute('SELECT * FROM discordchannelid WHERE clanid = %s', (clan_id,))
        return self.cur.fetchone()

    def create(self, clan_id, discord_channel_id):
        self.cur.execute('INSERT INTO discordchannelid (clanid, discordchannelid) VALUES (%s, %s)',
                         (clan_id, discord_channel_id))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, clan_id, discord_channel_id):
        self.cur.execute('UPDATE discordchannelid SET discordchannelid = %s WHERE clanid = %s',
                         (discord_channel_id, clan_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, clan_id):
        self.cur.execute('DELETE FROM discordchannelid WHERE clanid = %s', (clan_id,))
        self.conn.commit()
        return self.cur.fetchone()


class Timer(Database):

    def get_by_clan_id(self, clan_id):
        self.cur.execute('SELECT * FROM timer WHERE clanid = %s', (clan_id,))
        return self.cur.fetchone()

    def get_by_clan_id_and_boss_name(self, clan_id, boss_name):
        self.cur.execute('SELECT * FROM timer WHERE clanid = %s AND bossName = %s', (clan_id, boss_name))
        return self.cur.fetchone()

    def create(self, boss_name, boss_type, timer, server_id, clan_id):
        self.cur.execute('INSERT INTO timer (bossName, type, timer, serverid, clanid) VALUES (%s, %s, %s, %s, %s)',
                         (boss_name, boss_type, timer, server_id, clan_id))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, clan_id, boss_name, timer):
        self.cur.execute('UPDATE timer SET timer = %s WHERE clanid = %s AND bossName = %s',
                         (timer, clan_id, boss_name))
        self.conn.commit()
        return self.cur.fetchone()

    def update_bulk(self, clan_id, data: dict):
        for boss_name, timer in data.items():
            self.cur.execute('UPDATE timer SET timer = %s WHERE clanid = %s AND bossName = %s',
                             (timer, clan_id, boss_name))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, clan_id, boss_name):
        self.cur.execute('DELETE FROM timer WHERE clanid = %s AND bossName = %s', (clan_id, boss_name))
        self.conn.commit()
        return self.cur.fetchone()

    def delete_by_clan_id(self, clan_id):
        self.cur.execute('DELETE FROM timer WHERE clanid = %s', (clan_id,))
        self.conn.commit()
        return self.cur.fetchone()


class Subscriber(Database):
    def get_by_user_id(self, user_id):
        self.cur.execute('SELECT * FROM subscriber WHERE userprofileid = %s', (user_id,))
        return self.cur.fetchone()

    def get_by_timer_id(self, timer_id):
        self.cur.execute('SELECT * FROM subscriber WHERE timerid = %s', (timer_id,))
        return self.cur.fetchone()

    def create(self, user_id, timer_id):
        self.cur.execute('INSERT INTO subscriber (userprofileid, timerid) VALUES (%s, %s)', (user_id, timer_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, user_id, timer_id):
        self.cur.execute('DELETE FROM subscriber WHERE userprofileid = %s AND timerid = %s', (user_id, timer_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete_by_user_id(self, user_id):
        self.cur.execute('DELETE FROM subscriber WHERE userprofileid = %s', (user_id,))
        self.conn.commit()
        return self.cur.fetchone()
