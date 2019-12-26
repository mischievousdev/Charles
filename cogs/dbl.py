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
        c = await self.bot.fetch_channel(659606634321936417)
        await c.send("A vote test has ran succesfully!")

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        channel = await self.bot.fetch_channel(659606634321936417)
        user = await self.bot.fetch_user(int(data['user']))
        e = discord.Embed(color=0x5E82AC,
                          title="Received Upvote!",
                          description=f"New upvote received from **{user}**!")
        e.set_author(icon_url=user.avatar_url, name=str(user))
        e.set_thumbnail(url="https://cdn.discordapp.com/attachments/638902095520464908/659611283443941376/upvote.png")
        await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.dblpy.post_guild_count()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.dblpy.post_guild_count()

def setup(bot):
    bot.add_cog(DiscordBotsOrgAPI(bot))
