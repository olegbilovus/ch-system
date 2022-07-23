from functools import wraps
import psycopg2
from tabulate import tabulate

import database
from utils import time_remaining, dhm_to_minutes, minutes_to_dhm, get_default_timers_data, PREFIX, \
    get_current_time_minutes

discord_id_db = database.DiscordID()
clan_discord_db = database.ClanDiscord()
clan_db = database.Clan()
timer_db = database.Timer()
user_profile_db = database.UserProfile()
subscriber_db = database.Subscriber()


class Message:
    def __init__(self, content, author, logger):
        msg_splitted = content.lower().split(' ')
        self.cmd = msg_splitted[0]
        self.args = msg_splitted[1:]
        self.length = len(content)
        self.author_mention = author.mention
        self.author_id = author.id
        self.author_tag = str(author)
        self.guild_id = author.guild.id
        self.account_discord_guild_id = None
        self.user_clan_id = None
        self.user_role = None
        self.discord_id_in_db = None
        self.user_profile_id = None
        self.logger = logger


def start_chain(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        chain = f(*args, **kwargs)
        next(chain)
        return chain

    return wrapper


@start_chain
def default():
    msg_to_send = {'private': False, 'msg': None}
    while True:
        yield msg_to_send


def soon_tabulate(data, tablefmt=None):
    msg = ''
    for coll in data:
        for _type, timer in coll.items():
            msg += f'```\n{tabulate(timer, headers=[_type, "Time"], tablefmt=tablefmt)}\n```'

    return msg


@start_chain
def soon(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'soon':

            if msg.user_clan_id is None:
                clan_id = clan_discord_db.get_by_discord_guild_id(msg.guild_id)[0]
            else:
                clan_id = msg.user_clan_id

            preferred_timer_type = msg.args[0].upper() if len(msg.args) == 1 and msg.args[0] != '-t' else None
            timers_data = timer_db.get_by_clan_id_order_by_type(clan_id, preferred_timer_type)

            if len(timers_data) == 0:
                msg_to_send['msg'] = 'Your clan has no timers set'
                if preferred_timer_type is not None:
                    msg_to_send['msg'] += f' for {preferred_timer_type} bosses'
            else:
                data = []
                prev_type = ''
                flag_tabulate = msg.args[0] == '-t'
                for boss_name, _type, timer, window in timers_data:
                    if _type != prev_type:
                        data.append({_type: []})
                        prev_type = _type
                    minutes_timer = time_remaining(timer)
                    # to refactor the check for tabulate
                    if minutes_timer <= 10 and not flag_tabulate:
                        boss_name = f'__**{boss_name}**__'
                    if minutes_timer <= -15:
                        minutes_timer += window
                        data[-1][_type].append([boss_name, f'window closes in {minutes_to_dhm(minutes_timer)}'])
                    else:
                        data[-1][_type].append([boss_name, minutes_to_dhm(minutes_timer)])

                if len(msg.args) == 1 and flag_tabulate:
                    msg_to_send['msg'] = soon_tabulate(data)
                elif len(msg.args) == 2 and flag_tabulate:
                    msg_to_send['msg'] = soon_tabulate(data, msg.args[1])
                else:
                    tmp = ''
                    for coll in data:
                        prev_type = ''
                        for _type, timers in coll.items():
                            for timer in timers:
                                if _type != prev_type:
                                    tmp += f'__**`{_type}`**__\n'
                                    prev_type = _type
                                tmp += f'{timer[0]}: {timer[1]}\n'

                    msg_to_send['msg'] = tmp

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def set_timer(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'set':
            if not 1 < len(msg.args) < 5:
                msg_to_send['msg'] = f'{msg.author_mention} Usage: {PREFIX}set <boss> <days>d <hours>h <minutes>m'
            else:
                boss = msg.args[0]
                timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
                if timer_data is None:
                    msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
                else:
                    try:
                        current_time_in_minutes = get_current_time_minutes()
                        timer_set = current_time_in_minutes + dhm_to_minutes(msg.args[1:])
                        timer_db.update(timer_data[0], timer_set)
                        msg_to_send['msg'] = f'{boss} set to {" ".join(msg.args[1:])}'
                    except ValueError:
                        msg_to_send['msg'] = f'{msg.author_mention} Invalid time format'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def reset_timer(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if len(msg.args) == 0:
            timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, msg.cmd)
            if timer_data is None:
                msg_to_send['msg'] = f'{msg.author_mention} {msg.cmd} is not a valid boss to reset'
            else:
                current_time_in_minutes = get_current_time_minutes()
                timer_set = current_time_in_minutes + timer_data[1]
                timer_db.update(timer_data[0], timer_set)
                msg_to_send['msg'] = f'{msg.cmd} has been reset'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def copy(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'copy':
            content = ' '.join(msg.args)
            content = content.split('\n')

            data = {}
            bosses_copied = []
            for t in content:
                if ' in ' in t:
                    s = t.split(' in ')
                    data[s[0].lower()] = s[1][:-1].replace('minutes', 'm').replace('days', 'd').replace('hours',
                                                                                                        'h').replace(
                        ',', '').replace('.', '')

            current_time = get_current_time_minutes()
            data_send = []
            for boss, t in data.items():
                timer_id = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
                if timer_id is not None:
                    array_tmp = t.split(' ')
                    array_values = []
                    for i in range(0, len(array_tmp), 2):
                        array_values.append(array_tmp[i] + array_tmp[i + 1])

                    timer = current_time + dhm_to_minutes(array_values)
                    data_send.append(timer_id[0])
                    data_send.append(timer)
                    bosses_copied.append(boss)

            if len(data_send) > 0:
                timer_db.update_bulk(data_send)
                msg_to_send[
                    'msg'] = f'{msg.author_mention} Copied the following timers:\n {", ".join(bosses_copied)}'
            else:
                msg_to_send['msg'] = f'{msg.author_mention} No timers to copy'
        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def init_timers(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'init':
            discord_id = msg.discord_id_in_db
            if discord_id is None or msg.user_role < 4:
                msg_to_send['msg'] = f'{msg.author_mention} You are not authorized to use this command'
            else:
                clan_id = msg.user_clan_id
                _type = msg.args[0].upper() if len(msg.args) == 1 else None
                default_timers = get_default_timers_data(_type)
                if len(default_timers) == 0:
                    msg_to_send['msg'] = f'{msg.author_mention} No timers found for {_type}'
                else:
                    try:
                        timer_db.init_timers(default_timers, clan_id)
                        msg_to_send['msg'] = f'{msg.author_mention} Timers have been initialized to 0m'
                    except psycopg2.IntegrityError:
                        timer_db.conn.rollback()
                        msg_to_send['msg'] = f'{msg.author_mention} An error occurred while initializing timers'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def sub(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'sub':
            if len(msg.args) == 0:
                msg_to_send['msg'] = f'{msg.author_mention} Usage: {PREFIX}sub <boss>'
            else:
                boss = msg.args[0]
                timer_data = timer_db.get_by_guild_id_and_boss_name(
                    msg.guild_id, boss)
                if timer_data is None:
                    msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
                else:
                    discord_id = msg.discord_id_in_db
                    if discord_id is None:
                        clan_id = timer_data[2]
                        user_name = msg.author_tag.split('#')[0]
                        if msg.user_profile_id is None:
                            server_id = clan_db.get_server_id_by_clan_id(timer_data[2])
                            msg.user_profile_id = user_profile_db.insert(user_name, server_id, clan_id, 0, None)[0]
                            msg.logger.info(f'Created user profile for {msg.author_tag}',
                                            extra={'user_profile_id': msg.user_profile_id})

                        discord_id_db.insert(msg.user_profile_id, msg.author_id, msg.author_tag)
                        msg.logger.info(f'Created discordID for {msg.author_tag}')

                    try:
                        subscriber_db.insert(msg.user_profile_id, timer_data[0])
                        msg_to_send['msg'] = f'{msg.author_mention} You are now subscribed to {boss}'
                    except psycopg2.IntegrityError:
                        subscriber_db.conn.rollback()
                        msg_to_send['msg'] = f'{msg.author_mention} You are already subscribed to {boss}'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def unsub(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'unsub':
            if len(msg.args) == 0:
                msg_to_send['msg'] = f'{msg.author_mention} Usage: {PREFIX}unsub <boss>'
            else:
                boss = msg.args[0]
                timer_data = timer_db.get_by_guild_id_and_boss_name(
                    msg.guild_id, boss)
                if timer_data is None:
                    msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
                else:
                    discord_id = msg.discord_id_in_db
                    if discord_id is None:
                        msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to {boss}'
                    else:
                        res = subscriber_db.delete(msg.user_profile_id, timer_data[0])
                        if res is None:
                            msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to {boss}'
                        else:
                            msg_to_send['msg'] = f'{msg.author_mention} You are no longer subscribed to {boss}'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def sublist(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'sublist':
            discord_id = msg.discord_id_in_db
            if discord_id is None:
                msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to any bosses'
            else:
                subscribers = subscriber_db.get_bosses_subscribed_by_user_id(msg.user_profile_id)
                if len(subscribers) == 0:
                    msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to any bosses'
                else:
                    bosses_str = '\n'.join(boss for boss, in subscribers)
                    msg_to_send[
                        'msg'] = f'{msg.author_mention} You are subscribed to the following bosses:\n{bosses_str}'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def help_commands(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'help':
            msg_to_send['msg'] = \
                f'{msg.author_mention} Here are the commands I understand, use the prefix **{PREFIX}** before each command:\n' \
                f'{PREFIX}**soon** - Show all the bosses that are timed and their timer is >= -15m.\n' \
                f'{PREFIX}**soon -t** - Same as **soon** but results are showed in a tabular format.\n' \
                f'{PREFIX}**soon -t <format>** - Same as **soon -t** but you can decide the format.\n ' \
                f'\tAvailable formats can be found here in "Table format" section <https://pypi.org/project/tabulate/>.\n' \
                f'{PREFIX}**soon <boss type>** - Show all available timers of a specific boss\' type.\n' \
                f'\te.g: **{PREFIX}soon frozen**\n' \
                f'{PREFIX}**<boss>** - Reset a boss.\n' \
                f'{PREFIX}**set <boss> <days>d <hours>h <minutes>m** - Set a boss to a specific timer.\n' \
                f'\te.g.: **{PREFIX}set 215 1h 13m**\n' \
                f'{PREFIX}**sub <boss>** - Subscribe to a boss to get notified when that boss is due.\n' \
                f'{PREFIX}**unsub <boss>** - Unsubscribe from a boss.\n' \
                f'{PREFIX}**sublist** - Show all the bosses you are subscribed to.\n' \
                f'{PREFIX}**help** - Show this message.'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def security_check(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        msg_to_send = {'private': False, 'msg': None}
        user_data = clan_discord_db.get_by_discord_id(msg.author_id)
        if user_data is not None and user_data[0] != msg.guild_id:
            msg_to_send[
                'msg'] = f'{msg.author_mention} You are already registered to a different clan, please leave that server before trying to post in another server'
        elif successor is not None:
            if user_data is not None:
                msg.account_discord_guild_id = user_data[0]
                msg.user_clan_id = user_data[1]
                msg.user_role = user_data[2]
                msg.discord_id_in_db = msg.author_id
                msg.user_profile_id = user_data[3]
            msg_to_send = successor.send(msg)
