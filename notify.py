import os
import time
from datetime import datetime

import discord
from replit import db

import utils

client = discord.Client()


async def notify():
    channel = client.get_channel(int(db['notify']))
    while True:
        utils.logger.info(f'NOTIFIER: check at {datetime.now()}')
        for boss in utils.BOSSES:
            timer = utils.get_timer(boss)
            if timer is not None:
                minutes = utils.minutes_sub(int(timer))
                if 10 >= minutes >= 0:
                    msg = None
                    key = boss + utils.SUB_SUFFIX
                    try:
                        subs_id = db[key]
                        if subs_id:
                            msg = f'{boss} due in {utils.minutes_to_dhm(timer)} {" ".join(subs_id)}'
                        else:
                            raise IndexError
                    except (KeyError, IndexError):
                        msg = f'{boss} due in {utils.minutes_to_dhm(timer)}'
                    await channel.send(msg)
                    utils.logger.info(f'NOTIFIER: {boss} sent at {datetime.now()}')
        time.sleep(300)


@client.event
async def on_ready():
    utils.logger.info(f'NOTIFIER: ready at {datetime.now()}')
    await notify()


def start_notifier():
    client.run(os.getenv('TOKEN'))
