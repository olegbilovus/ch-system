import time
from functools import wraps
import psycopg2
from tabulate import tabulate

import database
from utils import time_remaining, dhm_to_minutes, minutes_to_dhm

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
        msg_to_send['msg'] = None


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
            clan_id = clan_discord_db.get_by_discord_guild_id(msg.guild_id)[0]
            timers_data = timer_db.get_by_clan_id_order_by_type(clan_id)
            if len(timers_data) == 0:
                msg_to_send['msg'] = f'Your clan has no timers set'
            else:
                timers_data = filter(lambda x: time_remaining(x[2]) > -15, timers_data)
                data = []
                prev_type = ''
                for boss_name, _type, timer in timers_data:
                    if _type != prev_type:
                        data.append({_type: []})
                        prev_type = _type
                    data[-1][_type].append([boss_name, minutes_to_dhm(time_remaining(timer))])

                if len(msg.args) == 1 and msg.args[0] == '-t':
                    msg_to_send['msg'] = soon_tabulate(data)
                elif len(msg.args) == 2 and msg.args[0] == '-t':
                    msg_to_send['msg'] = soon_tabulate(data, msg.args[1])
                else:
                    tmp = ''
                    for coll in data:
                        prev_type = ''
                        for _type, timers in coll.items():
                            for timer in timers:
                                if _type != prev_type:
                                    tmp += f'{_type}\n'
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
                msg_to_send['msg'] = f'{msg.author_mention} Usage: set <boss> <days>d <hours>h <minutes>m'
            else:
                boss = msg.args[0]
                timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
                if timer_data is None:
                    msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
                else:
                    try:
                        current_time_in_minutes = round(time.time()) // 60
                        timer_set = current_time_in_minutes + dhm_to_minutes(msg.args[1:])
                        timer_db.update(timer_data[0], timer_set)
                        msg_to_send['msg'] = f'{boss} will spawn in {" ".join(msg.args[1:])}'
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
                current_time_in_minutes = round(time.time()) // 60
                timer_set = current_time_in_minutes + timer_data[1]
                timer_db.update(timer_data[0], timer_set)
                msg_to_send['msg'] = f'{msg.cmd} has been reset'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def sub(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'sub':
            boss = msg.args[0]
            timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
            if timer_data is None:
                msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
            else:
                discord_id = discord_id_db.get_by_discord_id(msg.author_id)
                if discord_id is None:
                    clan_id = timer_data[2]
                    user_name = msg.author_tag.split('#')[0]
                    user_profile = user_profile_db.get_by_name_and_clan_id(user_name, clan_id)
                    if user_profile is None:
                        server_id = clan_db.get_server_id_by_clan_id(timer_data[2])
                        user_profile = user_profile_db.insert(user_name, server_id, clan_id, 0, None)
                        msg.logger.info(f'Created user profile for {msg.author_tag}',
                                        extra={'user_profile_id': user_profile[0]})

                    discord_id = discord_id_db.insert(user_profile[0], msg.author_id, msg.author_tag)
                    msg.logger.info(f'Created discordID for {msg.author_tag}')

                try:
                    subscriber_db.insert(discord_id[0], timer_data[0])
                    msg_to_send['msg'] = f'{msg.author_mention} You are now subscribed to {boss}'
                except psycopg2.IntegrityError:
                    msg_to_send['msg'] = f'{msg.author_mention} You are already subscribed to {boss}'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def unsub(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'unsub':
            boss = msg.args[0]
            timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
            if timer_data is None:
                msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
            else:
                discord_id = discord_id_db.get_by_discord_id(msg.author_id)
                if discord_id is None:
                    msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to {boss}'
                else:
                    res = subscriber_db.delete(discord_id[0], timer_data[0])
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
            discord_id = discord_id_db.get_by_discord_id(msg.author_id)
            if discord_id is None:
                msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to any bosses'
            else:
                subscribers = subscriber_db.get_bosses_subscribed_by_user_id(discord_id[0])
                if len(subscribers) == 0:
                    msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to any bosses'
                else:
                    bosses_str = '\n'.join(boss for boss, in subscribers)
                    msg_to_send[
                        'msg'] = f'{msg.author_mention} You are subscribed to the following bosses:\n{bosses_str}'

        elif successor is not None:
            msg_to_send = successor.send(msg)
