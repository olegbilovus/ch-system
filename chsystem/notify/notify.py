import requests
import os

import setup
import logs
import database

timer_db = database.Timer()
subscriber_db = database.Subscriber()
notifyWebhook_db = database.NotifyWebhook()

logger = logs.get_logger('Notify', token=os.getenv('LOGTAIL_NOTIFY'))

USERNAME = 'Notifier'

logger.info('Check')
webhooks = notifyWebhook_db.get_all()

for clan_id, webhook in webhooks:
    timers = timer_db.get_notify_data_by_clan_id(clan_id)
    for timer_id, timer, boss_name in timers:
        subscribers = subscriber_db.get_discord_ids_by_timer_id_clan_id(timer_id)
        msg = f'{boss_name} due in {timer}m '
        for discord_id, in subscribers:
            msg += f'<@{discord_id}>'

        res = requests.post(webhook, data={'username': USERNAME, 'content': msg})
        logger.info(f'response: {res.status_code}, sent: {msg}')

timer_db.close()
logger.info('Finish check')
