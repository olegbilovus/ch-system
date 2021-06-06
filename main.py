from threading import Thread
from replit import db

import os
import time
import webhook
import discord
import commands
import server
import utils

client = discord.Client()
chain = commands.get_all(
    commands.reset_timer(
        commands.get_boss(
            commands.when_boss(commands.set_timer(commands.default())))))


@client.event
async def on_ready():
	utils.status(False)
	utils.logger('BOT: logged')


@client.event
async def on_message(message):
	if db['429']:
		utils.status(True)
		time.sleep(utils._429)
		utils.status(False)
		return

	if message.author == client.user or message.channel.name != 'timer-bot' or webhook.USERNAME in str(
	    message.author):
		return
	utils.logger(f'{message.author}: {message.content}')
	msg = utils.Message(message.content.split(' '), message.author)
	global chain
	msg_to_send = chain.send(msg)
	try:
		if msg_to_send['msg'] is not None:
			if msg_to_send['type'] == 'all':
				await message.channel.send(msg_to_send['msg'])
			elif msg_to_send['type'] == 'dm':
				await message.author.send(msg_to_send['msg'])
	except discord.errors.HTTPException as e:
		message_error = str(e)
		utils.logger(message_error)
		if '429' in message_error:
			utils.status(True)
			time.sleep(utils._429)
			utils.status(False)


server_s = Thread(target=server.run)
server_s.start()

try:
	client.run(os.getenv('TOKEN'))
except discord.errors.HTTPException as e:
	message_error = str(e)
	utils.logger(message_error)
	if '429' in message_error:
		utils.status(True)
		time.sleep(utils._429)
		utils.status(False)
