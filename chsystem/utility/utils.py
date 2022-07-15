import time


def time_remaining(_timer):
    return _timer - (round(time.time()) // 60)


def days_hours_mins_to_mins(array_values):
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
