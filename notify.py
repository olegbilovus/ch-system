import os
import time
import discord
import utils
from datetime import datetime
from replit import db

client = discord.Client()


async def notify():
    channel = client.get_channel(int(db['notify']))
    guild = client.get_guild(int(db['guild']))
    while True:
        print(f'NOTIFIER: check at {datetime.now()}')
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
                            subs_mention = []
                            for sub_id in subs_id:
                                try:
                                    user = await guild.fetch_member(int(sub_id))
                                    subs_mention.append(user.mention)
                                except discord.errors.NotFound:
                                    subs_id.remove(sub_id)
                            msg = f'{boss} due in {utils.minutes_to_dhm(timer)} {" ".join(subs_mention)}'
                            db[key] = subs_id
                        else:
                            raise IndexError
                    except (KeyError, IndexError):
                        msg = f'{boss} due in {utils.minutes_to_dhm(timer)}'
                    await channel.send(msg)
                    print(f'NOTIFIER: {boss} sent at {datetime.now()}')
        time.sleep(300)


@client.event
async def on_ready():
    print(f'NOTIFIER: ready at {datetime.now()}')
    await notify()


def start_notifier():
    client.run(os.getenv('TOKEN'))
