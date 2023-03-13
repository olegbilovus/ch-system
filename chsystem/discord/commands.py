from functools import wraps
import psycopg2
from tabulate import tabulate

import database
from utils import time_remaining, dhm_to_minutes, minutes_to_dhm, get_default_timers_data, PREFIX, \
    get_current_time_minutes, TIMER_OFFSET

discord_id_db = database.DiscordID()
clan_discord_db = database.ClanDiscord()
clan_db = database.Clan()
timer_db = database.Timer()
user_profile_db = database.UserProfile()
subscriber_db = database.Subscriber()

MAX_NUM_TIMERS = 50


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
        self.server_id = None
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
    while True:
        msg_to_send = {'private': False, 'msg': None}
        yield msg_to_send


@start_chain
def bosslist(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'bosslist':
            clan_id = msg.user_clan_id
            boss_names = timer_db.get_names_types_by_clan_id(clan_id)
            if len(boss_names) == 0:
                msg_to_send['msg'] = f'{msg.author_mention} Your clan has no timers'
            else:
                tmp = ''
                prev_type = ''
                for boss_name, _type in boss_names:
                    if _type != prev_type:
                        tmp += f'__**`{_type}`**__\n'
                        prev_type = _type
                    tmp += f'{boss_name}\n'
                msg_to_send['msg'] = f'{tmp} {msg.author_mention}'

        elif successor is not None:
            msg_to_send = successor.send(msg)


def soon_tabulate(data, tablefmt=None):
    msg = ''
    for coll in data:
        for _type, b_timer in coll.items():
            msg += f'```\n{tabulate(b_timer, headers=[_type, "Time"], tablefmt=tablefmt)}\n```'

    return msg


@start_chain
def soon(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'soon':
            clan_id = msg.user_clan_id
            preferred_timer_types = [t.upper() for t in msg.args] if len(msg.args) >= 1 and msg.args[
                0] != '-t' else None
            timers_data = timer_db.get_by_clan_id_order_by_type(clan_id, preferred_timer_types)

            if len(timers_data) == 0:
                msg_to_send['msg'] = 'Your clan has no timers set'
                if preferred_timer_types is not None:
                    msg_to_send['msg'] += ' for ' + ', '.join(preferred_timer_types) + ' bosses'
            else:
                data = []
                prev_type = ''
                flag_tabulate = False if len(msg.args) == 0 else msg.args[0] == '-t'
                for boss_name, _type, b_timer, window in timers_data:
                    if _type != prev_type:
                        data.append({_type: []})
                        prev_type = _type
                    minutes_timer = time_remaining(b_timer)
                    # to refactor the check for tabulate
                    if minutes_timer <= 10 and not flag_tabulate:
                        boss_name = f'__**{boss_name}**__'
                    if minutes_timer <= 0 and window > 0:
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
                            for b_timer in timers:
                                if _type != prev_type:
                                    tmp += f'__**`{_type}`**__\n'
                                    prev_type = _type
                                tmp += f'{b_timer[0]}: {b_timer[1]}\n'

                    msg_to_send['msg'] = tmp
            msg_to_send['msg'] = f'{msg_to_send["msg"]}\n{msg.author_mention}'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def set_timer(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'set':
            if not 1 < len(msg.args) < 6:
                msg_to_send['msg'] = f'{msg.author_mention} Usage: {PREFIX}set <boss> <days>d <hours>h <minutes>m [ago]'
            else:
                boss = msg.args[0]
                timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
                if timer_data is None:
                    msg_to_send['msg'] = f'{msg.author_mention} {boss} is not a valid boss'
                else:
                    try:
                        current_time_in_minutes = get_current_time_minutes()
                        if msg.args[-1] == 'ago':
                            timer_set = current_time_in_minutes + timer_data[1] - dhm_to_minutes(msg.args[1:-1])
                        else:
                            timer_set = current_time_in_minutes + dhm_to_minutes(msg.args[1:])
                        timer_db.update(timer_data[0], timer_set)
                        msg_to_send['msg'] = f'{msg.author_mention} {boss} set to {" ".join(msg.args[1:])}'
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
                timer_set = current_time_in_minutes + timer_data[1] - TIMER_OFFSET
                timer_db.update(timer_data[0], timer_set)
                msg_to_send['msg'] = f'{msg.author_mention} {msg.cmd} has been reset'

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def copy_copyforce(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'copy' or msg.cmd == 'copyforce':
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
            copyforce = msg.cmd == 'copyforce'
            for boss, t in data.items():
                timer_id = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss, timer=not copyforce)
                if timer_id is not None:
                    array_tmp = t.split(' ')
                    array_values = []
                    for i in range(0, len(array_tmp), 2):
                        array_values.append(array_tmp[i] + array_tmp[i + 1])
                    try:
                        if msg.cmd == 'copy' and timer_id[3] >= current_time - 1:
                            continue

                        b_timer = current_time + dhm_to_minutes(array_values)
                        data_send.append(timer_id[0])
                        data_send.append(b_timer)
                        bosses_copied.append(boss)
                    except ValueError:
                        pass

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
            if msg.user_role < 5:
                msg_to_send['msg'] = f'{msg.author_mention} You are not authorized to use this command'
            else:
                clan_id = msg.user_clan_id
                default_timers = get_default_timers_data()
                try:
                    timer_db.init_timers(default_timers, clan_id)
                    msg_to_send['msg'] = f'{msg.author_mention} Timers have been added'
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
            if len(msg.args) < 1:
                msg_to_send['msg'] = f'{msg.author_mention} Usage: {PREFIX}sub <boss>'
            else:
                valid_bosses = []
                not_found_bosses = []
                already_sub_bosses = []
                for boss in msg.args:
                    timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
                    if timer_data is None:
                        not_found_bosses.append(boss)
                    else:
                        try:
                            subscriber_db.insert(msg.user_profile_id, timer_data[0])
                            valid_bosses.append(boss)
                        except psycopg2.IntegrityError:
                            subscriber_db.conn.rollback()
                            already_sub_bosses.append(boss)
                msg_str = ''
                if len(valid_bosses) > 0:
                    valid_bosses = ', '.join(valid_bosses)
                    msg_str += f'{msg.author_mention} You are no longer subscribed to: {valid_bosses}\n'
                if len(not_found_bosses) > 0:
                    not_found_bosses = ', '.join(not_found_bosses)
                    msg_str += f'{msg.author_mention} The following bosses are not valid: {not_found_bosses}\n'
                if len(already_sub_bosses) > 0:
                    already_sub_bosses = ', '.join(already_sub_bosses)
                    msg_str += f'{msg.author_mention} You are not subscribed to: {already_sub_bosses}\n'

                msg_to_send['msg'] = msg_str

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
                valid_bosses = []
                not_found_bosses = []
                not_sub_bosses = []
                for boss in msg.args:
                    timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, boss)
                    if timer_data is None:
                        not_found_bosses.append(boss)
                    else:
                        res = subscriber_db.delete(msg.user_profile_id, timer_data[0])
                        if res is not None:
                            valid_bosses.append(boss)
                        else:
                            not_sub_bosses.append(boss)
                msg_str = ''
                if len(valid_bosses) > 0:
                    valid_bosses = ', '.join(valid_bosses)
                    msg_str += f'{msg.author_mention} You are now subscribed to: {valid_bosses}\n'
                if len(not_found_bosses) > 0:
                    not_found_bosses = ', '.join(not_found_bosses)
                    msg_str += f'{msg.author_mention} The following bosses are not valid: {not_found_bosses}\n'
                if len(not_sub_bosses) > 0:
                    not_sub_bosses = ', '.join(not_sub_bosses)
                    msg_str += f'{msg.author_mention} You are already subscribed to: {not_sub_bosses}\n'

                msg_to_send['msg'] = msg_str

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def sublist(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'sublist':
            boss_names = subscriber_db.get_bosses_subscribed_by_user_id(msg.user_profile_id)
            if len(boss_names) == 0:
                msg_to_send['msg'] = f'{msg.author_mention} You are not subscribed to any bosses'
            else:
                tmp = f'{msg.author_mention} You are subscribed to the following bosses:\n'
                prev_type = ''
                for boss_name, _type in boss_names:
                    if _type != prev_type:
                        tmp += f'__**`{_type}`**__\n'
                        prev_type = _type
                    tmp += f'{boss_name}\n'
                msg_to_send['msg'] = tmp

        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def role(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    usage = '{} Usage: {}role <@user> <role>'
    while True:
        msg = yield msg_to_send
        if msg.cmd == 'role':
            if msg.user_role < 4:
                msg_to_send['msg'] = f'{msg.author_mention} You are not authorized to use this command'
            else:
                if len(msg.args) != 2:
                    msg_to_send['msg'] = usage.format(msg.author_mention, PREFIX)
                else:
                    other_user_discord_id = msg.args[0][2:-1]
                    try:
                        other_user_discord_id = int(other_user_discord_id)
                        role_change = int(msg.args[1])
                        if not 0 <= role_change <= 4:
                            msg_to_send['msg'] = f'{msg.author_mention} Role has to be a number between 0 and 4'
                        else:

                            other_user_data = clan_discord_db.get_by_discord_id(other_user_discord_id)
                            if other_user_data is None:
                                msg_to_send[
                                    'msg'] = f'{msg.author_mention} the user <@{other_user_discord_id}> has not an account. To get an account he needs to use the bot once.'
                            else:
                                user_profile_db.update_role(other_user_data[3], role_change)
                                msg_to_send[
                                    'msg'] = f'{msg.author_mention} role updated from {other_user_data[2]} to {role_change}'
                    except ValueError:
                        msg_to_send['msg'] = usage.format(msg.author_mention, PREFIX)
        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def timer(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        if msg.cmd in ['timeradd', 'timeredit', 'timerdel']:
            if msg.user_role < 3:
                msg_to_send['msg'] = f'{msg.author_mention} You are not authorized to use this command'
            elif 1 <= len(msg.args) <= 4:
                flag_add = msg.cmd == 'timeradd'
                flag_edit = msg.cmd == 'timeredit'
                timer_data = timer_db.get_by_guild_id_and_boss_name(msg.guild_id, msg.args[0])
                if flag_add or flag_edit:
                    try:
                        boss_type = msg.args[1].upper()
                        respawn = int(msg.args[2])
                        window = int(msg.args[3])
                        if timer_data is not None and flag_add:
                            msg_to_send['msg'] = f'{msg.author_mention} {msg.args[0]} already exists'
                        elif timer_data is None and flag_add:
                            num_timers = timer_db.get_num_timers_by_clan_id(msg.user_clan_id)[0]
                            if num_timers < MAX_NUM_TIMERS:
                                timer_db.insert(msg.args[0], boss_type, respawn, window, msg.user_clan_id)
                                msg_to_send[
                                    'msg'] = f'{msg.author_mention} Added name: {msg.args[0]}, type: {boss_type}, respawn: {minutes_to_dhm(respawn)}, window: {minutes_to_dhm(window)}'
                            else:
                                msg_to_send[
                                    'msg'] = f'{msg.author_mention} your clan has already {MAX_NUM_TIMERS} timers, delete some to add more'
                        elif timer_data is None and flag_edit:
                            msg_to_send['msg'] = f'{msg.author_mention} {msg.args[0]} does not exists'
                        else:
                            timer_db.update_full(msg.args[0], boss_type, respawn, window, msg.user_clan_id)
                            msg_to_send[
                                'msg'] = f'{msg.author_mention} {msg.args[0]} edited to type: {boss_type}, respawn: {minutes_to_dhm(respawn)}, window: {minutes_to_dhm(window)}'
                    except (ValueError, IndexError):
                        msg_to_send[
                            'msg'] = f'{msg.author_mention} Usage: {PREFIX}{"timeradd" if flag_add else "timeredit"} <name> <type> <respawn mins> <window mins>'
                else:
                    if timer_data is None:
                        msg_to_send['msg'] = f'{msg.author_mention} {msg.args[0]} does not exists'
                    else:
                        timer_db.delete(msg.user_clan_id, msg.args[0])
                        msg_to_send['msg'] = f'{msg.author_mention} {msg.args[0]} deleted'
            else:
                msg_to_send['msg'] = f'{msg.author_mention} Use {PREFIX}help to see the usage'
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
                f'{PREFIX}**soon <boss type> <boss type> ...** - Show all available timers for specific boss\' types.\n' \
                f'\te.g: **{PREFIX}soon frozen**\n' \
                f'{PREFIX}**<boss>** - Reset a boss.\n' \
                f'{PREFIX}**set <boss> <days>d <hours>h <minutes>m [ago]** - Set a boss to a specific timer. Use **ago** at the end to set it to a relative time.\n' \
                f'\te.g.: **{PREFIX}set 215 1h 13m**\n' \
                f'{PREFIX}**sub <boss>** - Subscribe to a boss to get notified when that boss is due.\n' \
                f'{PREFIX}**unsub <boss>** - Unsubscribe from a boss.\n' \
                f'{PREFIX}**sublist** - Show all the bosses you are subscribed to.\n' \
                f'{PREFIX}**bosslist** - Get the names of the bosses available in your clan.\n' \
                f'{PREFIX}**help** - Show this message.\n' \
                f'*-- Commands which require role > 3 --*\n' \
                f'{PREFIX}**role** <@user> <role> - Change a user role, @user means to tag/mention the user. role has to be a number between 0 and 4\n' \
                f'*-- Commands which require role > 2 --*\n' \
                f'{PREFIX}**timeradd** <name> <type> <respawm mins> <window mins> - Add a timer. Name has to be one single word, respawm and window has to be in minutes. Each clan has a maximum of {MAX_NUM_TIMERS} timers.\n' \
                f'{PREFIX}**timeredit** <name> <type> <respawm mins> <window mins> - Edit a timer. Name has to be one single word, respawm and window has to be in minutes.\n' \
                f'{PREFIX}**timerdel** <name> - Delete a timer'
        elif successor is not None:
            msg_to_send = successor.send(msg)


@start_chain
def security_check(successor=None):
    msg_to_send = {'private': False, 'msg': None}
    while True:
        msg = yield msg_to_send
        user_data = clan_discord_db.get_by_discord_id(msg.author_id)
        if user_data is not None and user_data[0] != msg.guild_id:
            msg_to_send[
                'msg'] = f'{msg.author_mention} You are already registered to a different clan, please leave that server before trying to post in another server'
        elif successor is not None:
            if user_data is None:
                user_data = []
                clan_id = clan_discord_db.get_by_discord_guild_id(msg.guild_id)[0]
                user_name = msg.author_tag.split('#')[0]
                server_id = clan_db.get_server_id_by_clan_id(clan_id)
                user_profile_id = user_profile_db.insert(user_name, server_id, clan_id, 0, None)[0]
                msg.logger.info(f'Created user profile for {msg.author_tag}',
                                extra={'user_profile_id': user_profile_id})

                discord_id_db.insert(user_profile_id, msg.author_id, msg.author_tag)
                msg.logger.info(f'Created discordID for {msg.author_tag}')

                user_data.append(msg.guild_id)
                user_data.append(clan_id)
                user_data.append(0)
                user_data.append(user_profile_id)
                user_data.append(server_id)

            msg.account_discord_guild_id = user_data[0]
            msg.user_clan_id = user_data[1]
            msg.user_role = user_data[2]
            msg.discord_id_in_db = msg.author_id
            msg.user_profile_id = user_data[3]
            msg.server_id = user_data[4]

            msg_to_send = successor.send(msg)
