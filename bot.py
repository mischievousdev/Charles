# IMPORTS
import discord
import asyncio
import datetime
import json
import aiohttp
import andesite
import os

#///////////////////////////////////////////#
#// KEEP LOGS FIRST SO SHIT DOESN'T BREAK //#
#///////////////////////////////////////////#
from utils.logger import log
log.init()

from utils import permissions
from cogs.Music import Player
from db import tokens

from discord.ext import commands


async def get_prefix(bot, message):
    if not message.guild:
        custom_prefix = ""

        return custom_prefix

    else:
        try:
            with open(f"db/guilds/{str(message.guild.id)}.json", "r") as f:
                data = json.load(f)    


            custom_prefix = data["Guild_Info"]["Prefix"]

        except FileNotFoundError:
            custom_prefix = "c?"


        return custom_prefix

BOT_EXTENSIONS = [
    'cogs.Help',
    'cogs.Owner',
    'cogs.Jishaku',
    'cogs.Fun',
    'cogs.Music',
    'cogs.Events',
    'cogs.Info',
    'cogs.Moderation',
    'cogs.Settings',
    'cogs.dbl',
    'cogs.Utility',
    'cogs.Test',
    'cogs.Images',
    'cogs.Ytt'
]

print('[CONNECT] Logging in...')
#bot = Bot(command_prefix=get_prefix, case_insensitive=True)

class Charles(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, reconnect=True, case_insensitive=True)

        # Bot vars
        self.embed_color = 0xFE8000
        self.cmdUsage = {}
        self.cmdUsers = {}
        self.guildUsage = {}
        self.loop = asyncio.get_event_loop()
        self.andesite = andesite.Client(self)
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Loading the extensions
        for extension in BOT_EXTENSIONS:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'[WARNING] Could not load extension {extension}: {e}')

    @property
    def owner(self):
        return self.get_user(self.owner_id)
    

    async def on_message(self, msg):
        if not self.is_ready() or msg.author.bot or not permissions.can_send(msg):
            return

        await self.process_commands(msg)

    async def on_ready(self):
        print(f'[CONNECT] Logged in as:\n{self.user} (ID: {self.user.id})\n')

        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

    def run(self):
        loop = self.loop
        try:
            loop.run_until_complete(self.bot_start())
        except KeyboardInterrupt:
            loop.run_until_complete(self.bot_logout())


    async def bot_logout(self):
        await super().logout()
        #await self.session.close()

    async def bot_start(self):
        await self.login(tokens.BOT)
        await self.connect()

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=MyContext)

class MyContext(commands.Context):

    @property
    def player(self):
        return self.bot.wavelink.get_player(self.guild.id, cls=Player)



#@bot.event
#async def on_connect():
#    for extension in BOT_EXTENSIONS:
#        try:
#            bot.load_extension(extension)
#        except Exception as e:
#            print(f'[WARNING] Could not load extension {extension}: {e}')

Charles().run()
