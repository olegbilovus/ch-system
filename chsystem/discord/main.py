import os
import time
import commands
import discord
import requests
import utils
import routine
import keep_alive

from threading import Thread
from replit import db

BOTS_NAMES = os.getenv('BOTS').split(',')
CHANNELS = os.getenv('CHANNELS').split(',')
API_URL2 = os.getenv('API_URL2')
LOGIN_API2 = {'user_id': os.getenv('USER_ID'), 'api_key': os.getenv('API_KEY')}

client = discord.Client(intents=discord.Intents.all())
chain = commands.copy(commands.get_all(
    commands.reset_timer(commands.set_timer_2(commands.default()))))


@client.event
async def on_ready():
    routine.delete_logs()
    utils.status(False)
    utils.logger('BOT: logged')


@client.event
async def on_message(message):
    if db['429']:
        utils.status(True)
        os.system('kill 1')
        utils.status(False)
        return

    if message.author == client.user or message.channel.name not in CHANNELS or str(
            message.author) in BOTS_NAMES:
        return

    utils.logger(f'{message.author.display_name}: {message.content}')
    msg = utils.Message(message.content.lower().split(' '), message.author)
    msg_to_send = None
    global chain
    try:
        msg_to_send = chain.send(msg)
        await message.channel.send(msg_to_send['msg'])
    except Exception as e:
        chain = commands.copy(commands.get_all(commands.reset_timer(
            commands.set_timer_2(commands.default()))))
        utils.logger(str(e))

    utils.logger(msg_to_send)


@client.event
async def on_member_remove(member):
    utils.logger(f'{member} has left the server')
    session = requests.Session()
    session.post(f'{API_URL2}/login', data=LOGIN_API2)
    res = session.post(f'{API_URL2}/user/delete',
                       json={'user_id': str(member.id)})
    if res.status_code == 200:
        utils.logger(f'{member} deleted')


server_s = Thread(target=keep_alive.run)
server_s.start()

try:
    client.run(os.getenv('TOKEN'))
except discord.errors.HTTPException as ex:
    message_error = str(ex)
    utils.logger(message_error)
    if '429' in message_error:
        utils.status(True)
        time.sleep(utils._429)
        utils.status(False)
