import requests

import logs
import database

timer_db = database.Timer()
subscriber_db = database.Subscriber()
discordID_db = database.DiscordID()
notifyWebhook_db = database.NotifyWebhook()

logger = logs.get_logger(name='notify')

USERNAME = 'Notifier'

logger.info('Check')
webhooks = notifyWebhook_db.get_all()

for clan_id, webhook in webhooks():
    timers = timer_db.get_notify_data_by_clan_id(clan_id)
    for timer_id, timer, boss_name in timers:
        if 0 <= timer <= 10:
            subscribers = subscriber_db.get_by_timer_id(timer_id)
            msg = f'{boss_name} due in {timer}m '
            for discord_id, in subscribers:
                msg += f'<@{discord_id}>'

            res = requests.post(webhook, data={'username': USERNAME, 'content': msg})
            logger.info(f'response: {res.status_code}, sent: {msg}')

logger.info('Finish check')
