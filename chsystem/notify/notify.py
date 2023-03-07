import requests
import os
import argparse

import setup
import logs
import database
from utils import time_remaining, minutes_to_dhm
from queue import Queue
from threading import Thread
import time

timer_db = database.Timer()
subscriber_db = database.Subscriber()
clan_discord_db = database.ClanDiscord()

logger = logs.get_logger('Notify', token=os.getenv('LOGTAIL_NOTIFY'), stdout_r=True, stderr_r=True, file=True)

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('--broadcast', help='Broadcast message', type=str)
args = parser.parse_args()

OPTIMAL_THREADS = os.cpu_count() + 4
jobs = Queue()


def request_worker(jobs_queue, log):
    while True:
        webh, content, usern, clanid = jobs_queue.get()
        try:
            res = requests.post(webh, data={'username': usern, 'content': content})
            if res.status_code >= 400:
                log.error(f'Failed to send message to ClanID: {clanid}, response: {res.status_code}, send: {content}')
            else:
                log.info(f'Sent message to ClanID: {clanid}, response: {res.status_code}, send: {content}')
        except requests.exceptions.RequestException as e:
            log.error(e)

        jobs_queue.task_done()


def do_work(jobs_queue, log):
    threads = OPTIMAL_THREADS if jobs_queue.qsize() > OPTIMAL_THREADS else jobs_queue.qsize()
    logger.info(f'Starting {threads} threads')
    for _ in range(threads):
        t = Thread(target=request_worker, args=(jobs_queue, log))
        t.daemon = True
        t.start()

    jobs_queue.join()
    logger.info('Work done')


if not args.broadcast:
    username = 'Notifier'

    while True:
        logger.info('Check')
        webhooks = clan_discord_db.get_all_notify_webhooks()

        for clan_id, webhook, discord_guild_id in webhooks:
            timers_data = timer_db.get_notify_data_by_clan_id(clan_id)
            for timer_id, timer, boss_name in timers_data:
                subscribers = subscriber_db.get_discord_ids_by_timer_id_clan_id(timer_id)
                msg = f'{boss_name} due in {minutes_to_dhm(time_remaining(timer))} '

                for discord_id, in subscribers:
                    msg += f'<@{discord_id}>'

                jobs.put((webhook, msg, username, clan_id))

        do_work(jobs, logger)
        logger.info('Finish check')

        time.sleep(300)

elif args.broadcast:
    username = 'Broadcaster'

    logger.info('Broadcast')
    webhooks = clan_discord_db.get_all_notify_webhooks()

    for clan_id, webhook, discord_guild_id in webhooks:
        jobs.put((webhook, args.broadcast, username, clan_id))

    do_work(jobs, logger)
    logger.info('Finish broadcast')

timer_db.close()
