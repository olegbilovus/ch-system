import discord
import os
import time
from datetime import datetime
from replit import db
import utils

client = discord.Client()


async def notify():
	channel = client.get_channel(int(db['notify']))
	guild = client.get_guild(int(db['guild']))
	while True:
		print(f'NOTIFIER: check at {datetime.now()}')
		for key in db.keys():
			if key.endswith('sub'):
				boss = key.split('sub')[0]
				timer = utils.get_timer(boss)
				if timer != None:
					timer2 = utils.minutes_sub(int(timer))
					if timer2 <= 10 and timer2 >= 0:
						subs_ids = db[key]
						subs_mentions = []
						for sub_id in subs_ids:
						  try:
						    user = await guild.fetch_member(int(sub_id))
						    subs_mentions.append(user.mention)
						  except discord.errors.NotFound:
						    subs_ids.remove(sub_id)
						msg = f'{boss} due in {utils.minutes_to_dhm(timer)} {" ".join(subs_mentions)}'
						await channel.send(msg)
						print(f'NOTIFIER: {boss} sent at {datetime.now()}')
						db[key] = subs_ids

		time.sleep(300)


@client.event
async def on_ready():
	print(f'NOTIFIER: ready at {datetime.now()}')
	await notify()


def start_notifier():
	client.run(os.getenv('TOKEN'))
