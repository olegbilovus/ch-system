import json
import time

PREFIX = '.'
TIMER_OFFSET = 0


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
        else:
            raise ValueError

    to_return = days * 1440 + hours * 60 + minutes - TIMER_OFFSET

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


def get_default_timers_data():
    data = []
    for boss in _BOSSES_DATA:
        data.append((boss['name'], boss['type'], boss['respawn'], boss['window']))

    return data


# Need to find an alternative solution. Loading as a JSON file from other modules have some issues with finding the file
_BOSSES_DATA = [
    {
        "name": "170",
        "type": "DL",
        "respawn": 78,
        "window": 3
    },
    {
        "name": "mord",
        "type": "MIDS",
        "respawn": 1440,
        "window": 1440
    },
    {
        "name": "bt",
        "type": "EGS",
        "respawn": 2160,
        "window": 2160
    },
    {
        "name": "dino",
        "type": "EGS",
        "respawn": 2160,
        "window": 2160
    },
    {
        "name": "prot",
        "type": "EGS",
        "respawn": 1080,
        "window": 120
    },
    {
        "name": "hrung",
        "type": "MIDS",
        "respawn": 1440,
        "window": 1440
    },
    {
        "name": "aggy",
        "type": "MIDS",
        "respawn": 1440,
        "window": 1440
    },
    {
        "name": "necro",
        "type": "MIDS",
        "respawn": 1440,
        "window": 1440
    },
    {
        "name": "gele",
        "type": "EGS",
        "respawn": 2160,
        "window": 2160
    },
    {
        "name": "north",
        "type": "RINGS",
        "respawn": 215,
        "window": 50
    },
    {
        "name": "lir",
        "type": "VORTEX",
        "respawn": 110,
        "window": 20
    },
    {
        "name": "center",
        "type": "RINGS",
        "respawn": 215,
        "window": 50
    },
    {
        "name": "155",
        "type": "DL",
        "respawn": 63,
        "window": 3
    },
    {
        "name": "190",
        "type": "EDL",
        "respawn": 81,
        "window": 3
    },
    {
        "name": "195",
        "type": "EDL",
        "respawn": 89,
        "window": 4
    },
    {
        "name": "165",
        "type": "DL",
        "respawn": 73,
        "window": 3
    },
    {
        "name": "205",
        "type": "EDL",
        "respawn": 117,
        "window": 4
    },
    {
        "name": "grom",
        "type": "FROZEN",
        "respawn": 48,
        "window": 3
    },
    {
        "name": "chained",
        "type": "FROZEN",
        "respawn": 43,
        "window": 3
    },
    {
        "name": "eye",
        "type": "FROZEN",
        "respawn": 28,
        "window": 3
    },
    {
        "name": "swampie",
        "type": "FROZEN",
        "respawn": 33,
        "window": 3
    },
    {
        "name": "200",
        "type": "EDL",
        "respawn": 108,
        "window": 5
    },
    {
        "name": "woody",
        "type": "FROZEN",
        "respawn": 38,
        "window": 3
    },
    {
        "name": "185",
        "type": "EDL",
        "respawn": 72,
        "window": 3
    },
    {
        "name": "pyrus",
        "type": "FROZEN",
        "respawn": 58,
        "window": 3
    },
    {
        "name": "south",
        "type": "RINGS",
        "respawn": 215,
        "window": 50
    },
    {
        "name": "east",
        "type": "RINGS",
        "respawn": 215,
        "window": 50
    },
    {
        "name": "fingals",
        "type": "VORTEX",
        "respawn": 110,
        "window": 20
    },
    {
        "name": "carrow",
        "type": "VORTEX",
        "respawn": 110,
        "window": 20
    },
    {
        "name": "180",
        "type": "DL",
        "respawn": 88,
        "window": 3
    },
    {
        "name": "215",
        "type": "EDL",
        "respawn": 134,
        "window": 5
    },
    {
        "name": "210",
        "type": "EDL",
        "respawn": 125,
        "window": 5
    },
    {
        "name": "160",
        "type": "DL",
        "respawn": 68,
        "window": 3
    }
]
