from setup import setup

setup()
import os
import discord

import logs
import database
import commands
from utils import PREFIX
import threading
import keep_alive

logger = logs.get_logger('DiscordBot', token=os.getenv('LOGTAIL_DISCORD'), other_loggers=['discord'], stdout_r=True,
                         stderr_r=True, file=True)

logger.info(f'Starting DiscordBot {discord.version_info}')

clan_discord_db = database.ClanDiscord()
discord_id_db = database.DiscordID()
clan_db = database.Clan()
user_profile_db = database.UserProfile()


def get_chain_commands():
    return commands.security_check(commands.soon(commands.set_timer(commands.sub(commands.unsub(commands.sublist(
        commands.init_timers(commands.copy_copyforce(commands.help_commands(
            commands.bosslist(commands.role(commands.timer(commands.reset_timer(commands.default())))))))))))))


class DiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmds = get_chain_commands().send
        self._connected = False

    async def on_ready(self):
        logger.info(f'Logged on as {self.user}')
        guilds_db = [guild_id[0] for guild_id in clan_discord_db.get_all_guild_ids()]

        for guild in self.guilds:
            if guild.id not in guilds_db:
                logger.critical(f'Guild {guild.name} joined but not in database, leaving.',
                                extra={'discord_guild_id': guild.id})
                await guild.leave()
            else:
                logger.info(f'Found guild {guild.name}', extra={'discord_guild_id': guild.id})
        logger.info('DiscordBot ready')

    async def on_message(self, message):
        if message.author.bot or not message.content.startswith(PREFIX) or message.guild is None:
            return
        extra_log = {
            'discord_id': message.author.id,
            'discord_guild_id': message.guild.id,
            'discord_guild_name': message.guild.name,
            'discord_channel_id': message.channel.id,
            'discord_channel_name': message.channel.name,
        }
        logger.info(f'Message from {message.author}: {message.content}', extra=extra_log)

        msg_received = commands.Message(message.content[1:], message.author, logger)
        try:
            msg_to_send = self.cmds(msg_received)
        except StopIteration as e:
            logger.exception(e, extra=extra_log)
            self.cmds = get_chain_commands().send
            return

        if msg_to_send['msg'] is not None:
            if msg_to_send['private']:
                await message.author.send(msg_to_send['msg'])
                logger.info(f'Sent private message to {message.author}')
            else:
                await message.channel.send(msg_to_send['msg'])
                logger.info(
                    f'Sent message to channel: {message.channel}')
        else:
            logger.warning(f'No command found for {message.content}')

    async def on_connect(self):
        self._connected = True
        logger.info('Connected')

    async def on_disconnect(self):
        self._connected = False
        logger.info('Disconnected')

    async def on_guild_join(self, guild):
        logger.warning(f'Joined guild {guild.name}', extra={'discord_guild_id': guild.id})
        if clan_discord_db.get_by_discord_guild_id(guild.id) is None:
            logger.critical(f'Guild {guild.name} joined but not in database, leaving.')
            await guild.leave()

    async def on_guild_remove(self, guild):
        logger.warning(f'Left GuildID: {guild.id}, Guild name: {guild.name}')
        clan_discord = clan_discord_db.get_by_discord_guild_id(guild.id)
        if clan_discord is not None:
            clan = clan_db.delete(clan_discord[0])
            logger.critical(f'Deleted clan_id: {clan[0]}, name:{clan[1]}, server_id:{clan[2]}')
        else:
            logger.critical(f'Guild {guild.name} left but not in database')

    async def on_guild_update(self, before, after):
        if before.name != after.name:
            logger.warning(f'GuildID:{before.id}, {before.name} renamed to {after.name}')

    async def on_member_remove(self, member):
        if member.bot:
            return
        logger.warning(f'Member {member.name} left from GuildID: {member.guild.id}, Guild name: {member.guild.name}',
                       extra={'discord_tag': str(member), 'discord_id': member.id})
        discord_id = discord_id_db.get_by_discord_id(member.id)
        if discord_id is not None:
            user_profile = user_profile_db.delete(discord_id[0])
            logger.warning(f'Deleted user_id: {user_profile[0]}, discord_id:{member.id}, name: {member.name}')
        else:
            logger.warning(f'Member {member.name} left but not in database')


if os.getenv('KEEP_ALIVE') == '1':
    threading.Thread(target=keep_alive.run, daemon=True)

client = DiscordBot(intents=discord.Intents.all(), status=discord.Status.online,
                    activity=discord.Activity(type=discord.ActivityType.playing, name='Celtic Heroes'))
client.run(os.getenv('DISCORD_TOKEN'))
