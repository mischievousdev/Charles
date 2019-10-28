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
        self.guild_post.start()

        self.icon = ""
        self.big_icon = ""

    def cog_unload(self):
        self.guild_post.cancel()

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):

        channel = self.bot.get_channel(562784997962940476)
        user = self.bot.get_user(int(data['user']))
        await channel.send(f"{user} has voted!")

    @tasks.loop(hours=1)
    async def guild_post(self):
        await self.bot.dblpy.post_guild_count()

    @commands.Cog.listener()
    async def on_guild_post(self):
        channel = self.bot.get_channel(562784997962940476)
        await channel.send("Guild count posted to DBL.")

def setup(bot):
    bot.add_cog(DiscordBotsOrgAPI(bot))
