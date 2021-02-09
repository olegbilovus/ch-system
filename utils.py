from replit import db
import time

TIME_KILL = False

BOSSES = {
    '110': 30,
    '115': 35,
    '120': 40,
    '125': 45,
    '130': 50,
    '140': 55,
    '155': 60,
    '160': 65,
    '165': 70,
    '170': 80,
    '180': 90,
    '185': 75,
    '190': 85,
    '195': 95,
    '200': 105,
    '205': 115,
    '210': 125,
    '215': 135,
    'aggy': 1894,
    'mord': 2160,
    'hrung': 2160,
    'necro': 2160,
    'prot': 1190,
    'gele': 2880,
    'bt': 4320,
    'dino': 4320
}

MINUTES_IN_A_DAY = 1440
SUB_SUFFIX = 'sub'


def minutes_sub(timer):
    return timer - (round(time.time()) // 60)


def minutes_add(timer):
    return round(time.time()) // 60 + timer


def minutes_to_dhm(minutes):
    minutes = minutes_sub(minutes)
    negative = False
    if int(minutes) < 0:
        minutes *= -1
        negative = True
    days = minutes // MINUTES_IN_A_DAY
    minutes = minutes % MINUTES_IN_A_DAY
    hours = minutes // 60
    minutes = minutes % 60
    msg = f'{str(days) + "d " if days > 0 else ""}{str(hours) + "h " if hours > 0 else ""}{minutes}m'
    if not negative:
        return msg
    else:
        return '-' + msg


def get_timer(boss):
    if boss in BOSSES:
        try:
            return db[boss]
        except KeyError:
            return None
    else:
        return None


def set_timer(boss, timer):
    if boss in BOSSES:
        db[boss] = minutes_add(int(timer))
        return True
    else:
        return False


def get_subs(boss):
    if boss in BOSSES:
        subs = []
        boss_suffix = boss + SUB_SUFFIX
        try:
            subs = db[boss_suffix]
        except KeyError:
            db[boss_suffix] = subs
        return subs
    else:
        return None


def add_sub(boss, user_mention):
    subs = get_subs(boss)
    if subs != None and user_mention not in subs:
        subs.append(user_mention)
        db[boss + SUB_SUFFIX] = subs
        return True
    else:
        return False


def remove_sub(boss, user_mention):
    subs = get_subs(boss)
    if subs and user_mention in subs:
        subs.remove(user_mention)
        db[boss + SUB_SUFFIX] = subs
        return True
    else:
        return False


def usage(message):
    return f'I could not understand _{message}_\nCommands:\n__all/All/soon/Soon__: get all available timers. e.g. _all_\n__g/G/get/Get boss__: to get a boss timer. e.g. _180_\n__boss timer__: to set a specific timer to a boss in minutes. e.g. _180 56_\n__boss__: it will reset a boss timer to the default timer. e.g. _180_\n__sub/Sub boss__: subscribe to a boss, when it will be due, you will be tagged in a message on discord. e.g. _sub 180_\n__unsub/Unsub boss__: unsub from a boss to not be anymore notified when it is due. e.g. _unsub 180_'


def separator_label(category, separator='---------------------------------'):
    return separator + '\n' + category + '\n'
