import discord
import os
from replit import db

client = discord.Client()


@client.event
async def on_ready():
    print('Logged')


@client.event
async def on_message(message):
    msg = message.content.split(' ')
    if message.author != client.user and msg[0] == 'setchannelnotify':
        db['notify'] = message.channel.id
        await message.channel.send(
            f'notify channel set to {message.channel.name}')


client.run(os.getenv('TOKEN'))
