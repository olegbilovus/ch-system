import datetime
from functools import wraps

import database

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


def days_hours_minutes(td):
    str_data = ''
    if td.days > 0:
        str_data += f'{td.days} days '
    hours = td.seconds // 3600
    if hours > 0:
        str_data += f'{hours} hours '
    minutes = (td.seconds % 3600) // 60
    if minutes > 0:
        str_data += f'{minutes} minutes'

    return str_data


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
                msg = ''
                prev_type = ''
                for boss_name, _type, timer in timers_data:
                    if _type != prev_type:
                        msg += f'{_type.upper()}\n'
                        prev_type = _type
                    msg += f'{boss_name}: {days_hours_minutes(timer)}\n'

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
                    timer_set = datetime.datetime.utcnow()
                    try:
                        for i in range(1, len(msg.args)):
                            if msg.args[i][-1] == 'd':
                                timer_set += datetime.timedelta(days=int(msg.args[i][:-1]))
                            elif msg.args[i][-1] == 'h':
                                timer_set += datetime.timedelta(hours=int(msg.args[i][:-1]))
                            elif msg.args[i][-1] == 'm':
                                timer_set += datetime.timedelta(minutes=int(msg.args[i][:-1]))
                            else:
                                raise ValueError

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
                timer_db.reset(timer_data[0], msg.cmd)
                msg_to_send['msg'] = f'{msg.cmd} has been reset'

        elif successor is not None:
            msg_to_send = successor.send(msg)
