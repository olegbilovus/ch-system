import os
import requests
import psycopg2

import logs

from datetime import datetime, timezone

logger = logs.get_logger('Database', token=os.getenv('LOGTAIL_DATABASE'))


class Database:
    _shared_state = {
        'conn': None,
        'cur': None,
        'db_uri': os.getenv('DB_URI'),
        'db_url': os.getenv('DB_URL')
    }

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared_state
        return obj

    def __init__(self, uri=None, url=None):
        if self.conn is None:
            self.update_url(uri, url)

    def update_url(self, uri=None, url=None, force=False):
        if uri is None and self.db_uri is None:
            res = requests.get(self.db_url if url is None else url, data={'update': '1' if force else '0'})
            if res.status_code == 200:
                os.putenv('DB_URI', res.text)
                self.db_uri = res.text
                logger.info('Got DB_URL')
            else:
                logger.error('ERROR DB_URL')
                self.db_uri = None
                self.conn = None
                self.cur = None
        else:
            self.db_uri = uri if uri is not None else self.db_uri
            self.db_url = url if url is not None else self.db_url

        if self.conn is None:
            self.conn = psycopg2.connect(self.db_uri)
            self.cur = self.conn.cursor()
            self.cur.execute('SELECT version()')
            logger.info(self.cur.fetchone())

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            self.cur = None


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


class NotifyWebhook(Database):
    def get_all(self):
        self.cur.execute('SELECT * FROM notifywebhook')
        return self.cur.fetchall()

    def get_by_clan_id(self, clan_id):
        self.cur.execute('SELECT * FROM notifywebhook WHERE clanid = %s', (clan_id,))
        return self.cur.fetchone()

    def create(self, clan_id, notify_webhook):
        self.cur.execute('INSERT INTO notifywebhook (clanid, notifywebhook) VALUES (%s, %s)',
                         (clan_id, notify_webhook))
        self.conn.commit()
        return self.cur.fetchone()

    def update(self, clan_id, notify_webhook):
        self.cur.execute('UPDATE notifywebhook SET notifywebhook = %s WHERE clanid = %s',
                         (notify_webhook, clan_id))
        self.conn.commit()
        return self.cur.fetchone()

    def delete(self, clan_id):
        self.cur.execute('DELETE FROM notifywebhook WHERE clanid = %s', (clan_id,))
        self.conn.commit()
        return self.cur.fetchone()


class Timer(Database):

    def get_notify_data_by_clan_id(self, clan_id):
        current_time = datetime.now(timezone.utc)
        self.cur.execute(
            'SELECT id, timer, bossname FROM timer WHERE clanid = %s AND timer.timer - %s >= 0 AND timer.timer - %s <= 10',
            (clan_id, current_time, current_time))
        return self.cur.fetchall()

    def get_by_clan_id(self, clan_id):
        self.cur.execute('SELECT * FROM timer WHERE clanid = %s', (clan_id,))
        return self.cur.fetchall()

    def get_by_clan_id_and_boss_name(self, clan_id, boss_name):
        self.cur.execute('SELECT * FROM timer WHERE clanid = %s AND bossName = %s', (clan_id, boss_name))
        return self.cur.fetchone()

    def get_by_clan_id_and_timer_id(self, clan_id, timer_id):
        self.cur.execute('SELECT * FROM timer WHERE clanid = %s AND id = %s', (clan_id, timer_id))
        return self.cur.fetchone()

    def create(self, boss_name, boss_type, timer, clan_id):
        self.cur.execute('INSERT INTO timer (bossName, type, timer, clanid) VALUES (%s, %s, %s, %s)',
                         (boss_name, boss_type, timer, clan_id))
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


class Subscriber(Database):
    def get_by_user_id(self, user_id):
        self.cur.execute('SELECT * FROM subscriber WHERE userprofileid = %s', (user_id,))
        return self.cur.fetchone()

    def get_discord_ids_by_timer_id_clan_id(self, timer_id):
        self.cur.execute(
            'SELECT discordid FROM subscriber, discordid WHERE timerid = %s AND subscriber.userprofileid = discordid.userprofileid',
            (timer_id,))
        return self.cur.fetchall()

    def create(self, user_id, timer_id, discord_id, clan_id):
        self.cur.execute('INSERT INTO subscriber (userprofileid, timerid, clanid) VALUES (%s, %s, %s)',
                         (user_id, timer_id, discord_id, clan_id))
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
