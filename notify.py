import discord
import os
import time
from datetime import datetime
from replit import db
import utils


async def notify():
    channel = client.get_channel(int(db['notify']))
    while True:
        print(f'Notify check at {datetime.now()}')
        for key in db.keys():
            if key.endswith('sub'):
                boss = key.split('sub')[0]
                timer = utils.get_timer(boss)
                if timer != None:
                    timer2 = utils.minutes_sub(int(timer))
                    if timer2 <= 10 and timer2 >= 0:
                        subs = db[key]
                        msg = f'{boss} due in {utils.minutes_to_dhm(timer)} {" ".join(subs)}'
                        await channel.send(msg)
                        print(f'Notify sent at {datetime.now()}')

        time.sleep(300)


client = discord.Client()


@client.event
async def on_ready():
    print(f'Notify ready at {datetime.now()}')
    await notify()


def start_notifier():
    client.run(os.getenv('TOKEN'))
