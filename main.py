import multiprocessing
import os
import time
from datetime import datetime

import discord
from replit import db

import commands
import notify
import routine
import server
import utils

client = discord.Client()
chain = None


@client.event
async def on_ready():
	print(f'BOT: logged at {datetime.now()}')
	for boss in utils.BOSSES:
		db[boss] = utils.get_timer(boss)
	global chain
	chain = commands.get_all(
	    commands.reset_timer(
	        commands.get_boss(
	            commands.when_boss(
	                commands.sub_boss(
	                    commands.unsub_boss(
	                        commands.set_timer(commands.default())))))))


@client.event
async def on_message(message):
	if message.author == client.user or message.channel.name != 'timer-bot':
		return
	print(f'{message.author}: {message.content} at {datetime.now()}')
	msg = utils.Message(message.content.split(' '), message.author)
	global chain
	msg_to_send = chain.send(msg)
	try:
		if msg_to_send['type'] == 'all':
		  await message.channel.send(msg_to_send['msg'])
		elif msg_to_send['type'] == 'dm':
		  await message.author.send(msg_to_send['msg'])
	except discord.errors.HTTPException as e:
		print(e)
		time.sleep(3600)


server_s = multiprocessing.Process(target=server.run)
server_s.daemon = True
server_s.start()
notifier = multiprocessing.Process(target=notify.start_notifier)
notifier.daemon = True
notifier.start()
delete_old_timers = multiprocessing.Process(target=routine.delete_old_timers)
delete_old_timers.daemon = True
delete_old_timers.start()
client.run(os.getenv('TOKEN'))
