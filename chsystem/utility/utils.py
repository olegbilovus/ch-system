import time

PREFIX = '.'


def get_current_time_minutes():
    return round(time.time()) // 60


def time_remaining(_timer):
    return _timer - get_current_time_minutes()


def dhm_to_minutes(array_values):
    days = 0
    hours = 0
    minutes = 0
    for value in array_values:
        if len(value) > 1:
            if value[-1] == 'd':
                days = int(value[:-1])
            elif value[-1] == 'h':
                hours = int(value[:-1])
            elif value[-1] == 'm':
                minutes = int(value[:-1])
            else:
                raise ValueError

    to_return = days * 1440 + hours * 60 + minutes - 2

    return to_return


def minutes_to_dhm(minutes):
    negative = False
    if int(minutes) < 0:
        minutes *= -1
        negative = True
    days = minutes // 1440
    minutes %= 1440
    hours = minutes // 60
    minutes %= 60
    msg = f'{str(days) + "d " if days > 0 else ""}{str(hours) + "h " if hours > 0 else ""}{minutes}m'
    if not negative:
        return msg
    return '-' + msg


def get_default_timers_data(_type=None):
    bosses = {
        'eye': ('FROZEN', 30, 0),
        'swampie': ('FROZEN', 35, 0),
        'woody': ('FROZEN', 40, 0),
        'chained': ('FROZEN', 45, 0),
        'grom': ('FROZEN', 50, 0),
        'pyrus': ('FROZEN', 55, 0),
        '155': ('DL', 60, 0),
        '160': ('DL', 65, 0),
        '165': ('DL', 70, 0),
        '170': ('DL', 80, 0),
        '180': ('DL', 90, 0),
        '185': ('EDL', 75, 0),
        '190': ('EDL', 85, 0),
        '195': ('EDL', 95, 0),
        '200': ('EDL', 105, 0),
        '205': ('EDL', 115, 0),
        '210': ('EDL', 125, 0),
        '215': ('EDL', 135, 0),
        'aggy': ('MIDS', 1894, 1894),
        'mord': ('MIDS', 2160, 2160),
        'hrung': ('MIDS', 2160, 2160),
        'necro': ('MIDS', 2160, 2160),
        'prot': ('EGS', 1190, 0),
        'gele': ('EGS', 2880, 2880),
        'bt': ('EGS', 2880, 2880),
        'dino': ('EGS', 2880, 2880),
        'east': ('RINGS', 255, 0),
        'north': ('RINGS', 255, 0),
        'south': ('RINGS', 255, 0),
        'center': ('RINGS', 255, 0)
    }

    if _type is not None:
        flag = False
        data = {}
        for boss, b_data in bosses.items():
            if b_data[0] == _type:
                data[boss] = b_data
                flag = True
            elif flag:
                break

        return data

    return bosses
