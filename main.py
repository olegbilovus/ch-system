from threading import Thread
from replit import db

import os
import time
import discord
import commands
import server
import utils
import routine

BOTS_NAMES = [os.getenv('BOT1'), os.getenv('BOT2')]

client = discord.Client()
chain = commands.reset_timer(commands.set_timer_2(commands.default()))


@client.event
async def on_ready():
	routine.delete_logs()
	utils.status(False)
	utils.logger('BOT: logged')


@client.event
async def on_message(message):
	if db['429']:
		utils.status(True)
		time.sleep(utils._429)
		utils.status(False)
		return

	if message.author == client.user or message.channel.name != 'timer_bot' or str(
	    message.author) in BOTS_NAMES:
		return

	utils.logger(f'{message.author.display_name}: {message.content}')
	msg = utils.Message(message.content.lower().split(' '), message.author)

	global chain
	try:
		msg_to_send = chain.send(msg)
	except Exception as e:
		chain = commands.reset_timer(commands.set_timer_2(commands.default()))
		logger(str(e))

	utils.logger(msg_to_send)


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
