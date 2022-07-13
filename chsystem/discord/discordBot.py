import setup
import os
import discord

import logs
import database

logger = logs.get_logger('DiscordBot', token=os.getenv('LOGTAIL_DISCORD'), other_loggers=['discord'], stdout_r=True,
                         stderr_r=True)

logger.info(f'Starting DiscordBot {discord.version_info}')

clan_discord_db = database.ClanDiscord()
discord_id_db = database.DiscordID()
clan_db = database.Clan()
user_profile_db = database.UserProfile()


class DiscordBot(discord.Client):
    async def on_ready(self):
        logger.info(f'Logged on as {self.user}')

    async def on_message(self, message):
        if message.author.bot:
            return
        logger.info(f'Message from {message.author}: {message.content}')

    async def on_disconnect(self):
        logger.error(f'Disconnected')

    async def on_guild_join(self, guild):
        logger.warning(f'Joined guild {guild.name}')
        if clan_discord_db.get_by_discord_guild_id(guild.id) is None:
            logger.critical(f'Guild {guild.name} joined but not in database, leaving.')
            await guild.leave()

    async def on_guild_remove(self, guild):
        logger.warning(f'Left guild {guild.name}, {guild.id}')
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
        logger.warning(f'Member {member.name} left from GuildID: {member.guild.id}, Guild name: {member.guild.name}')
        discord_id = discord_id_db.get_by_discord_id(member.id)
        if discord_id is not None:
            user_profile = user_profile_db.delete(discord_id[0])
            logger.warning(f'Deleted user_id: {user_profile[0]}, discord_id:{user_profile[1]}')

    async def on_error(self, event_method, *args, **kwargs):
        logger.error(f'Error in {event_method}:\n{args}\n{kwargs}')


client = DiscordBot(intents=discord.Intents.all(), status=discord.Status.online,
                    activity=discord.Activity(type=discord.ActivityType.playing, name='Celtic Heroes'))
client.run(os.getenv('DISCORD_TOKEN'))
