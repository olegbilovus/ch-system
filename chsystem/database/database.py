import os
import requests
import psycopg2

import logs

from utils import get_current_time_minutes


class Database:
    _shared_state = {
        'conn': None,
        'db_uri': os.getenv('DB_URI'),
        'db_url': os.getenv('DB_URL'),
        'logger': logs.get_logger('Database', token=os.getenv('LOGTAIL_DATABASE'))
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
            res = requests.get(self.db_url if url is None else url, data={
                'update': '1' if force else '0'})
            if res.status_code == 200:
                os.putenv('DB_URI', res.text)
                self.db_uri = res.text
                self.logger.info('Got DB_URL')
            else:
                self.logger.error('ERROR DB_URL')
                self.db_uri = None
                self.conn = None
        else:
            self.db_uri = uri if uri is not None else self.db_uri
            self.db_url = url if url is not None else self.db_url

        if self.conn is None or force:
            self.conn = psycopg2.connect(self.db_uri)
            cur = self.conn.cursor()
            cur.execute('SELECT version()')
            self.logger.info(cur.fetchone())

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None


class Server(Database):

    def get_all(self):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM server')
        return cur.fetchall()


class Clan(Database):

    def get_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM clan WHERE id = %s', (clan_id,))
        return cur.fetchone()

    def get_server_id_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        cur.execute('SELECT serverid FROM clan WHERE id = %s', (clan_id,))
        return cur.fetchone()[0]

    def get_by_name_and_server(self, clan_name, server_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM clan WHERE name = %s AND serverid = %s', (clan_name, server_id))
        return cur.fetchone()

    def insert(self, clan_name, server_id):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO clan (name, serverid) VALUES (%s, %s) RETURNING *', (clan_name, server_id))
        self.conn.commit()
        return cur.fetchone()

    def update(self, clan_id, clan_name, server_id):
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE clan SET name = %s, serverid = %s WHERE id = %s', (clan_name, server_id, clan_id))
        self.conn.commit()

    def delete(self, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM clan WHERE id = %s RETURNING *', (clan_id,))
        self.conn.commit()
        return cur.fetchone()


class UserProfile(Database):

    def get_by_clan_and_server(self, clan_id, server_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM userprofile WHERE clanid = %s AND serverid = %s', (clan_id, server_id))
        return cur.fetchall()

    def get_by_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM userprofile WHERE id = %s', (user_id,))
        return cur.fetchone()

    def get_by_name_and_clan_id(self, user_name, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM userprofile WHERE name = %s AND clanid = %s', (user_name, clan_id))
        return cur.fetchone()

    def insert(self, user_name, server_id, clan_id, role, hash_pw):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO userprofile (name, serverid, clanid, role, hash_pw, change_pw) VALUES (%s, %s, %s, %s, %s, True) RETURNING *',
            (user_name, server_id, clan_id, role, hash_pw))
        self.conn.commit()
        return cur.fetchone()

    def update(self, user_id, user_name, server_id, clan_id, role, hash_pw, change_pw):
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE userprofile SET name = %s, serverid = %s, clanid = %s, role = %s, hash_pw = %s, change_pw = %s WHERE id = %s',
            (user_name, server_id, clan_id, role, hash_pw, change_pw, user_id))
        self.conn.commit()

    def update_role(self, user_id, role):
        cur = self.conn.cursor()
        cur.execute('UPDATE userprofile SET role = %s WHERE id = %s', (role, user_id))
        self.conn.commit()

    def delete(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM userprofile WHERE id = %s RETURNING *', (user_id,))
        self.conn.commit()
        return cur.fetchone()


class ApiKey(Database):

    def get_by_user_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM apikey WHERE userprofileid = %s', (user_id,))
        return cur.fetchone()

    def insert(self, user_id, key):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO apikey (userprofileid, key) VALUES (%s, %s) RETURNING *', (user_id, key))
        self.conn.commit()
        return cur.fetchone()

    def update(self, user_id, key):
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE apikey SET key = %s WHERE userprofileid = %s', (key, user_id))
        self.conn.commit()

    def delete(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM apikey WHERE userprofileid = %s RETURNING *', (user_id,))
        self.conn.commit()
        return cur.fetchone()


class ClanDiscord(Database):

    def get_all_guild_ids(self):
        cur = self.conn.cursor()
        cur.execute('SELECT discordguildid FROM clandiscord')
        return cur.fetchall()

    def get_all_notify_webhooks(self):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM clandiscord WHERE notifywebhook IS NOT NULL')
        return cur.fetchall()

    def get_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM clandiscord WHERE clanid = %s', (clan_id,))
        return cur.fetchone()

    def get_by_discord_guild_id(self, discord_guild_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM clandiscord WHERE discordguildid = %s', (discord_guild_id,))
        return cur.fetchone()

    def get_by_discord_id(self, discord_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT clandiscord.discordguildid, userprofile.clanid, userprofile.role, userprofile.id, userprofile.serverid FROM discordid, userprofile, clandiscord WHERE discordid = %s AND discordid.userprofileid = userprofile.id AND clandiscord.clanid = userprofile.clanid',
            (discord_id,))
        return cur.fetchone()

    def insert(self, clan_id, notify_webhook, discord_guild_id):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO clandiscord (clanid, notifywebhook, discordguildid) VALUES (%s, %s, %s) RETURNING *',
            (clan_id, notify_webhook, discord_guild_id))
        self.conn.commit()
        return cur.fetchone()

    def update(self, clan_id, notify_webhook, discord_guild_id):
        cur = self.conn.cursor()
        cur.execute('UPDATE clandiscord SET notifywebhook = %s, discordguildid = %s WHERE clanid = %s',
                    (notify_webhook, discord_guild_id, clan_id))
        self.conn.commit()

    def delete(self, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM clandiscord WHERE clanid = %s RETURNING *', (clan_id,))
        self.conn.commit()
        return cur.fetchone()


class Timer(Database):

    def get_notify_data_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        current_time = get_current_time_minutes()
        timer = current_time + 10
        cur.execute(
            "SELECT id, timer, bossname FROM timer WHERE clanid = %s AND timer >= %s AND timer <= %s",
            (clan_id, current_time, timer))
        return cur.fetchall()

    def get_by_clan_id_order_by_type(self, clan_id, preferred_types=None):
        cur = self.conn.cursor()
        timer = get_current_time_minutes() - 15
        if preferred_types is None:
            cur.execute(
                "SELECT bossname, type, timer, windowminutes FROM timer WHERE clanid = %s AND timer + windowminutes >= %s ORDER BY type, bossname",
                (clan_id, timer))
        else:
            sql_query = 'SELECT bossname, type, timer, windowminutes FROM timer WHERE clanid = %s AND timer + windowminutes >= %s AND type IN ({}) ORDER BY type, bossname'.format(
                ', '.join(['%s'] * len(preferred_types)))
            cur.execute(sql_query, (clan_id, timer, *tuple(preferred_types)))
        return cur.fetchall()

    def get_list_info_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT bossname, type, respawntimeminutes, windowminutes FROM timer WHERE clanid = %s ORDER BY type, bossname", (clan_id,))
        return cur.fetchall()

    def get_by_guild_id_and_boss_name(self, guild_id, boss_name, timer=False):
        cur = self.conn.cursor()
        if not timer:
            cur.execute(
                "SELECT timer.id, respawnTimeMinutes, timer.clanid FROM timer, clandiscord WHERE discordguildid = %s AND bossname = %s AND timer.clanid = clandiscord.clanid",
                (guild_id, boss_name))
        else:
            cur.execute(
                "SELECT timer.id, respawnTimeMinutes, timer.clanid, timer.timer FROM timer, clandiscord WHERE discordguildid = %s AND bossname = %s AND timer.clanid = clandiscord.clanid",
                (guild_id, boss_name))
        return cur.fetchone()

    def get_by_clan_id_and_timer_id(self, clan_id, timer_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM timer WHERE clanid = %s AND id = %s', (clan_id, timer_id))
        return cur.fetchone()

    def get_num_timers_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        cur.execute('SELECT count(*) as NUM FROM timer where clanid = %s', (clan_id,))
        return cur.fetchone()

    def insert(self, boss_name, boss_type, respawn_time_minutes, windowminutes, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO timer (bossName, type, respawntimeminutes, windowminutes, clanid) VALUES (%s, %s, %s, %s, %s) RETURNING *',
            (boss_name, boss_type, respawn_time_minutes, windowminutes, clan_id))
        self.conn.commit()
        return cur.fetchone()

    def update_full(self, boss_name, boss_type, respawn_time_minutes, windowminutes, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'UPDATE timer SET type = %s, respawntimeminutes = %s, windowminutes = %s WHERE clanid = %s AND bossname = %s',
            (boss_type, respawn_time_minutes, windowminutes, clan_id, boss_name))
        self.conn.commit()

    def update(self, timer_id, timer):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE timer SET timer = %s WHERE id = %s", (timer, timer_id))
        self.conn.commit()

    def update_bulk(self, data):
        cur = self.conn.cursor()
        sql = 'UPDATE timer SET timer = d.timer FROM (VALUES '
        sql += '(%s, %s), ' * (len(data) // 2)
        sql = sql[:-2]
        sql += ') AS d(id, timer) WHERE timer.id = d.id'

        cur.execute(sql, data)
        self.conn.commit()

    def init_timers(self, default_timers, clan_id):
        cur = self.conn.cursor()
        timer = get_current_time_minutes()
        # not using prepared statements because the input is safe from SQL injection
        sql = 'INSERT INTO timer (bossName, type, respawntimeminutes, windowminutes, timer, clanid) VALUES '

        for boss in default_timers:
            sql += f"('{boss[0]}', '{boss[1]}', {boss[2]}, {boss[3]}, {timer}, {clan_id}), "
        sql = sql[:-2]

        cur.execute(sql)
        self.conn.commit()

    def delete(self, clan_id, boss_name):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM timer WHERE clanid = %s AND bossName = %s RETURNING *', (clan_id, boss_name))
        self.conn.commit()
        return cur.fetchone()

    def delete_by_clan_id(self, clan_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM timer WHERE clanid = %s RETURNING *', (clan_id,))
        self.conn.commit()
        return cur.fetchall()


class DiscordID(Database):
    def get_by_user_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM discordid WHERE userprofileid = %s', (user_id,))
        return cur.fetchone()

    def get_by_discord_id(self, discord_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM discordid WHERE discordid = %s', (discord_id,))
        return cur.fetchone()

    def insert(self, user_id, discord_id, discord_tag):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO discordid (userprofileid, discordid, discordtag) VALUES (%s, %s, %s) RETURNING *',
                    (user_id, discord_id, discord_tag))
        self.conn.commit()
        return cur.fetchone()

    def update(self, user_id, discord_id, discord_tag):
        cur = self.conn.cursor()
        cur.execute('UPDATE discordid SET discordid = %s, discordtag = %s WHERE userprofileid = %s',
                    (discord_id, discord_tag, user_id))
        self.conn.commit()

    def delete(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM discordid WHERE userprofileid = %s RETURNING *', (user_id,))
        self.conn.commit()
        return cur.fetchone()


class Subscriber(Database):
    def get_by_user_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT * FROM subscriber WHERE userprofileid = %s', (user_id,))
        return cur.fetchall()

    def get_discord_ids_by_timer_id_clan_id(self, timer_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT discordid FROM subscriber, discordid WHERE timerid = %s AND subscriber.userprofileid = discordid.userprofileid',
            (timer_id,))
        return cur.fetchall()

    def get_bosses_subscribed_by_user_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT bossname, type FROM subscriber, timer WHERE subscriber.userprofileid = %s AND subscriber.timerid = timer.id ORDER BY type, bossname',
            (user_id,))
        return cur.fetchall()

    def insert(self, user_id, timer_id):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO subscriber (userprofileid, timerid) VALUES (%s, %s)',
                    (user_id, timer_id))
        self.conn.commit()

    def delete(self, user_id, timer_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM subscriber WHERE userprofileid = %s AND timerid = %s RETURNING *',
                    (user_id, timer_id))
        self.conn.commit()
        return cur.fetchone()

    def delete_by_user_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            'DELETE FROM subscriber WHERE userprofileid = %s RETURNING *', (user_id,))
        self.conn.commit()
        return cur.fetchall()
