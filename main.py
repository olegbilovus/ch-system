import multiprocessing
import os
import commands
from datetime import datetime

import discord
from replit import db

import notify
import routine
import server
import utils

client = discord.Client()


@client.event
async def on_ready():
    print(f'BOT: logged at {datetime.now()}')
    for boss in utils.BOSSES:
        db[boss] = utils.get_timer(boss)


@client.event
async def on_message(message):
    if message.author == client.user or message.channel.name != 'timer-bot':
        return

    msg = utils.Message(message.content.split(' '), message.author.mention,
                        message.author.id)
    chain = commands.get_all(
        commands.reset_timer(
            commands.set_timer(
                commands.get_boss(
                    commands.sub_boss(commands.unsub_boss(
                        commands.default()))))))
    msg_to_send = chain.send(msg)
    await message.channel.send(msg_to_send)


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
