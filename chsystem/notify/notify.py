import requests
import os
import time

import setup
import logs
import database
from utils import time_remaining, dhm_to_minutes, minutes_to_dhm

timer_db = database.Timer()
subscriber_db = database.Subscriber()
clan_discord_db = database.ClanDiscord()

logger = logs.get_logger('Notify', token=os.getenv(
    'LOGTAIL_NOTIFY'), stdout_r=True, stderr_r=True, file=True)

USERNAME = 'Notifier'

logger.info('Check')
webhooks = clan_discord_db.get_all_notify_webhooks()

for clan_id, webhook, discord_guild_id in webhooks:
    timers_data = timer_db.get_notify_data_by_clan_id(clan_id)
    timers_data = filter(
        lambda x: 0 <= time_remaining(x[1]) <= 10, timers_data)
    for timer_id, timer, boss_name in timers_data:
        subscribers = subscriber_db.get_discord_ids_by_timer_id_clan_id(
            timer_id)
        msg = f'{boss_name} due in {minutes_to_dhm(time_remaining(timer))}'

        for discord_id, in subscribers:
            msg += f'<@{discord_id}>'

        res = requests.post(
            webhook, data={'username': USERNAME, 'content': msg})
        logger.info(
            f'GuildID: {discord_guild_id}, ClanID: {clan_id}, response: {res.status_code}, sent: {msg}')

timer_db.close()
logger.info('Finish check')
