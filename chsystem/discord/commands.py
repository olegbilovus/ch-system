import time
from functools import wraps

import database
from utils import time_remaining, days_hours_mins_to_mins, minutes_to_dhm

clan_discord_db = database.ClanDiscord()
timer_db = database.Timer()


class Message:
    def __init__(self, content, author):
        msg_splitted = content.lower().split(' ')
        self.cmd = msg_splitted[0]
        self.args = msg_splitted[1:]
        self.length = len(content)
        self.author_mention = author.mention
        self.author_id = author.id
        self.author_rag = str(author)
        self.guild_id = author.guild.id


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


@start_chain
def soon(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        message = yield msg_to_send
        if message.cmd == 'soon':
            clan_id = clan_discord_db.get_by_discord_guild_id(message.guild_id)[0]
            timers_data = timer_db.get_by_clan_id_order_by_type(clan_id)
            if len(timers_data) == 0:
                msg_to_send['msg'] = f'Your clan has no timers set'
            else:
                timers_data = filter(lambda x: time_remaining(x[2]) > -15, timers_data)
                msg = ''
                prev_type = ''
                for boss_name, _type, timer in timers_data:
                    if _type != prev_type:
                        msg += f'{_type.upper()}\n'
                        prev_type = _type
                    msg += f'{boss_name}: {minutes_to_dhm(time_remaining(timer))}\n'

                msg_to_send['msg'] = msg
        elif successor is not None:
            msg_to_send = successor.send(message)


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
                        timer_set = current_time_in_minutes + days_hours_mins_to_mins(msg.args[1:])
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
                timer_set = current_time_in_minutes + timer_data[1] - 2
                timer_db.update(timer_data[0], timer_set)
                msg_to_send['msg'] = f'{msg.cmd} has been reset'

        elif successor is not None:
            msg_to_send = successor.send(msg)
