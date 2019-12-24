import dbl
import discord
from discord.ext import commands, tasks
from db import tokens

import asyncio


class DiscordBotsOrgAPI(commands.Cog, name="DBL"):
    """Handles interactions with the discordbots.org API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = tokens.DBL # set this to your DBL token
        self.bot.dblpy = dbl.DBLClient(self.bot, self.token, webhook_path='/dblwebhook', webhook_auth=self.token, webhook_port=5000)

        self.icon = ""
        self.big_icon = ""

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        print(data)

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        print(data)
        channel = await self.bot.fetch_channel(562784997962940476)
        user = await self.bot.fetch_user(int(data['user']))
        await channel.send(f"{str(user)} has voted!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.dblpy.post_guild_count()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.dblpy.post_guild_count()

    @commands.Cog.listener()
    async def on_guild_post(self):
        channel = await self.bot.fetch_channel(562784997962940476)
        await channel.send("Guild count posted to DBL.")

def setup(bot):
    bot.add_cog(DiscordBotsOrgAPI(bot))
