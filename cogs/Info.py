import discord
import asyncio
import aiohttp
import psutil
import platform
import pathlib
import inspect
import time
import os
import codecs
import json
import humanize
import sys


from discord.ext import commands
from utils import default
from datetime import datetime
from collections import Counter
from utils.translate import get_text
from utils.default import commandExtra, groupExtra

class info(commands.Cog, name='Info'):
    def __init__(self, bot):
        self.bot = bot
        self.icon = "<:charlesInfo:615429388644777994>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615429388644777994.png"
        self.process = psutil.Process(os.getpid())

    async def bot_check(self, ctx):
        if not ctx.guild:
            return True

        file_name= "db/global_disable.json"
        cmd = self.bot.get_command(ctx.command.name)
        with open(file_name, "r") as f:
            data = json.load(f)
        
        if ctx.command.parent:
            if ctx.command.parent in data:
                if data[str(ctx.command.parent)]:
                    await ctx.send(get_text(ctx.guild, "events", "events.cmd_global_disabled").format(str(data[str(ctx.command.parent)])))
                    return False

            if f"{ctx.command.parent}_{ctx.command.name}" in data:                    
                if data[str(f"{ctx.command.parent}_{ctx.command.name}")]:
                    await ctx.send(get_text(ctx.guild, "events", "events.subcmd_global_disabled").format(str(data[str(f'{ctx.command.parent}_{ctx.command.name}')])))
                    return False

            if not ctx.command.parent in data or f"{ctx.command.parent}_{ctx.command.name}" not in data:
                return True

        else:
            if ctx.command.name in data:
                if data[str(ctx.command.name)]:
                    await ctx.send(get_text(ctx.guild, "events", "events.cmd_global_disabled").format(str(data[str(ctx.command.name)])))
                    return False

            if not ctx.command.name in data:
                return True

    def paginate(text: str):
        '''Simple generator that paginates text.'''
        last = 0
        pages = []
        for curr in range(0, len(text)):
            if curr % 1980 == 0:
                pages.append(text[last:curr])
                last = curr
                appd_index = curr
        if appd_index != len(text) - 1:
            pages.append(text[last:curr])
        return list(filter(lambda a: a != '', pages))

    @commandExtra(aliases=['source'], category="Bot Info")
    async def sourcecode(self, ctx, *, command=None):
        '''Get the source code for any command.'''
        source_url = 'https://github.com/iDutchy/Charles'
        if command is None:
            return await ctx.send(source_url)

        cmd = self.bot.get_command(command)
        if cmd is None:
            return await ctx.send("This command doesn't exist!")
        
        if cmd.cog_name.lower() == "test":
            return await ctx.send("This is a testing command. I can not show you the source of this command yet.")
        
        try:
            source = inspect.getsource(cmd.callback)
        except AttributeError:
            return await ctx.send(f"Could not find command `{command}`.")
        if len(source) + 8 <= 2000:
            await ctx.send(f'```py\n{source}\n```')
        else:
            branch = 'master'
            obj = self.bot.get_command(command.replace('.', ' '))

            # since we found the command we're looking for, presumably anyway, let's
            # try to access the code itself
            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

            lines, firstlineno = inspect.getsourcelines(src)
            location = module.replace('.', '/') + '.py'

            final_url = f'<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
            await ctx.send(f"Source was too long to post on discord, so here's the url to the source on GitHub:\n{final_url}")

    @groupExtra(invoke_without_command=True, category="Server Info")
    async def guildsettings(self, ctx):
        e = discord.Embed(color=self.bot.embed_color)
        e.set_author(icon_url=ctx.guild.icon_url,
                     name=get_text(ctx.guild, 'info', 'info.guildinfo.title').format(ctx.guild.name))

        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        logs  = f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['MessageEdit']['Toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.edit_msg')}\n"
        logs += f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['MessageDelete']['Toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.del_msg')}\n"
        logs += f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['Moderation']['Toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.mod')}\n"
        logs += f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['MemberJoin']['Toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.m_join')}\n"
        logs += f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['MemberUpdate']['Toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.m_update')}"

        e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.logs'), value=logs)

        settings  = f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['Join_Role']['toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.joinrole')}\n"
        settings += f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['Welcome_Msg']['toggle'] == 'disabled' and data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.welcome')}\n"
        settings += f"{'<:slide_no:522874184720842768>' if data['Guild_Logs']['Leave_Msg']['toggle'] == 'disabled' else '<:slide_yes:522874186042048522>'} {get_text(ctx.guild, 'info', 'info.guildinfo.leave')}"

        e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.settings'), value=settings)

        customized  = f"{get_text(ctx.guild, 'info', 'info.guildinfo.emb_col')} {data['Guild_Info']['Embed_Color']}\n"
        customized += f"{get_text(ctx.guild, 'info', 'info.guildinfo.lang')} {data['Guild_Info']['Language']}"

        e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.cust_set'), value=customized)

        #e.add_field(name="Disabled Commands:", value="None")

        if data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == "enabled":
            welcome_msg = get_text(ctx.guild, 'info', 'info.guildinfo.welc_msg_emb')
        else:
            welcome_msg = data['Guild_Logs']['Welcome_Msg']['msg']

        if data['Guild_Logs']['Leave_Msg']['embedtoggle'] == "enabled":
            leave_msg = get_text(ctx.guild, 'info', 'info.guildinfo.leav_msg_emb')
        else:
            leave_msg = data['Guild_Logs']['Leave_Msg']['msg']

        if not data['Guild_Logs']['Welcome_Msg']['toggle'] == 'disabled' or data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == 'enabled':
            e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.welc_msg'), value=welcome_msg, inline=False)
        else:
            e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.welc_msg'),
                        value=get_text(ctx.guild, 'info', 'info.guildinfo.welc_disabled'),
                        inline=False)

        if not data['Guild_Logs']['Leave_Msg']['toggle'] == 'disabled' or data['Guild_Logs']['Leave_Msg']['embedtoggle'] == 'enabled':
            e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.leav_msg'), value=leave_msg, inline=False)
        else:
            e.add_field(name=get_text(ctx.guild, 'info', 'info.guildinfo.leav_msg'),
                        value=get_text(ctx.guild, 'info', 'info.guildinfo.leav_disabled'),
                        inline=False)


        await ctx.send(embed=e)

    @guildsettings.command()
    async def welcomemsg(self, ctx):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data["Guild_Logs"]["Leave_Msg"]["embedtoggle"] == "disabled":
            return

        emb_dict = data["Guild_Logs"]["Welcome_Msg"]["embedmsg"]

        await ctx.send(embed=discord.Embed.from_dict(emb_dict))

    @guildsettings.command()
    async def leavemsg(self, ctx):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data["Guild_Logs"]["Leave_Msg"]["embedtoggle"] == "disabled":
            return

        emb_dict = data["Guild_Logs"]["Leave_Msg"]["embedmsg"]

        await ctx.send(embed=discord.Embed.from_dict(emb_dict))

    @commandExtra(category="Bot Info", aliases=['cloc', 'lc'])
    async def linecount(self, ctx):
        pylines = 0
        pyfiles = 0
        txtlines = 0
        txtfiles = 0
        pngfiles = 0
        jpgfiles = 0
        jsonlines = 0
        jsonfiles = 0
        for path, subdirs, files in os.walk('.'):
            for name in files:
                    if name.endswith('.py'):
                        pyfiles += 1
                        with codecs.open('./' + str(pathlib.PurePath(path, name)), 'r', 'utf-8') as f:
                            for i, l in enumerate(f):
                                if l.strip().startswith('#') or len(l.strip()) is 0:  # skip commented lines.
                                    pass
                                else:
                                    pylines += 1
                    if name.endswith('.txt'):
                        txtfiles += 1
                        with codecs.open('./' + str(pathlib.PurePath(path, name)), 'r', 'utf-8') as f:
                            for i, l in enumerate(f):
                                if l.strip().startswith('#') or len(l.strip()) is 0:  # skip commented lines.
                                    pass
                                else:
                                    txtlines += 1
                    if name.endswith('.json'):
                        jsonfiles += 1
                        with codecs.open('./' + str(pathlib.PurePath(path, name)), 'r', 'utf-8') as f:
                            for i, l in enumerate(f):
                                jsonlines += 1
                    if name.lower().endswith('.png'):
                        pngfiles += 1
                    if name.lower().endswith('.jpg'):
                        jpgfiles += 1


        countmsg   = "```ml\n"
        countmsg  += "File Type: | File Count: | Line Count:\n"
        countmsg  += "-----------+-------------+-------------\n"
        countmsg += f"Python     | {pyfiles}{' '*int(11-len(str(pyfiles)))} | {pylines:,}\n"
        countmsg += f"JSON       | {jsonfiles}{' '*int(11-len(str(jsonfiles)))} | {jsonlines:,}\n"
        countmsg  += "```"

        othermsg   = "```ml\n"
        othermsg  += "File Type: | File Count: | Line Count:\n"
        othermsg  += "-----------+-------------+-------------\n"
        othermsg += f"Txt        | {txtfiles}{' '*int(11-len(str(txtfiles)))} | {txtlines:,}\n"
        othermsg += f"Png        | {pngfiles}{' '*int(11-len(str(pngfiles)))} | N/A\n"
        othermsg += f"Jpg        | {jpgfiles}{' '*int(11-len(str(jpgfiles)))} | N/A\n"
        othermsg += "```"
        await ctx.send(f'**Total coding lines count:**\n{countmsg}\n**Other files line count:**\n{othermsg}')

    @commandExtra(category="User Info")
    async def credits(self, ctx):
        embed = discord.Embed(color=self.bot.embed_color, title=get_text(ctx.guild, 'info', 'info.credits_thanks'))
        
        akna = self.bot.get_user(214128381762076672)     # Translator - Vietnamese
        andreas = self.bot.get_user(177856006775242753)  # Translator - Norwegian
        sylt = self.bot.get_user(144112966176997376)     # Translator - Norwegian
        foxbell = self.bot.get_user(264195450859552779)  # Translator - Spanish
        lilo = self.bot.get_user(516280857468731395)     # Translator - Russian
        dutchy = self.bot.get_user(171539705043615744)   # Translator - Dutch
        impa = self.bot.get_user(219896976110649344)     # Translator - Dutch
        roma = self.bot.get_user(269156684155453451)     # Translator - French
        



        trdesc = f"- **{andreas}** (Norwegian)\n"
        trdesc += f"- **{sylt}** (Norwegian)\n"
        trdesc += f"- **{akna}** (Vietnamese)\n"
        trdesc += f"- **{foxbell}** (Spanish)\n"
        trdesc += f"- **{lilo}** (Russian)\n"
        trdesc += f"- **{dutchy}** (Dutch, English)\n"
        trdesc += f"- **{impa}** (Dutch)\n"
        trdesc += f"- **{roma}** (French)"

        embed.add_field(name=f"__**{get_text(ctx.guild, 'info', 'info.credits.translators')}:**__\n\n", value=trdesc)

        badesc = "- **GuardeYard#5824** \n"
        badesc += "⠀⠀ட <:instagram:595712748088721409> @trashygarbagebin"

        embed.add_field(name=f"__**{get_text(ctx.guild, 'info', 'info.credits.bot_artist')}:**__\n\n", value=badesc)

        await ctx.send(embed=embed)

    @commandExtra(category="Bot Info")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def system(self, ctx):
        """Get Bot System Info"""
        try:
            cpu_per = psutil.cpu_percent()
            cores = psutil.cpu_count()
            memory = psutil.virtual_memory().total >> 20
            mem_usage = psutil.virtual_memory().used >> 20
            storage_free = psutil.disk_usage('/').free >> 30
            em = discord.Embed(color=self.bot.embed_color, title=get_text(ctx.guild, 'info', 'info.system_info'),
                               description=f"{get_text(ctx.guild, 'info', 'info.system_os')} : **{platform.platform()}**\n"
                                           f"{get_text(ctx.guild, 'info', 'info.system_cores')} : **{cores}**\n"
                                           f"{get_text(ctx.guild, 'info', 'info.system_cpu')} : **{cpu_per}%**\n"
                                           f"{get_text(ctx.guild, 'info', 'info.system_ram')} : **{mem_usage}/{memory} MB** ({int(memory - mem_usage)}MB {get_text(ctx.guild, 'info', 'info.system_free')})\n"
                                           f"{get_text(ctx.guild, 'info', 'info.system_storage')} : **{storage_free} GB {get_text(ctx.guild, 'info', 'info.system_free')}**")
            await ctx.send(embed=em)
        except Exception as e:
            await ctx.send(get_text(ctx.guild, 'info', 'info.system_error'))

    @commandExtra(category="User Info")
    @commands.guild_only()
    async def joindate(self, ctx, *, user: discord.Member = None):
        """ Check when a user joined the current server """
        if user is None:
            user = ctx.author

        embed = discord.Embed(colour=self.bot.embed_color)
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = get_text(ctx.guild, 'info', 'info.join_date').format(user, ctx.guild.name, default.date(user.joined_at))
        await ctx.send(embed=embed) 



    @commandExtra(category="Server Info", aliases=['server'])
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """ Check info about current server """
        if ctx.invoked_subcommand is None:
            findbots = sum(1 for member in ctx.guild.members if member.bot)

            roles = ""

            for role in ctx.guild.roles:
                if not role.name == "@everyone":
                    roles += role.mention + ", "

            embed = discord.Embed(color=self.bot.embed_color)
            if ctx.guild.icon_url:
                embed.set_thumbnail(url=ctx.guild.icon_url)
            else:
                embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_name'), value=ctx.guild.name, inline=True)
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_id'), value=ctx.guild.id, inline=True)
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_members'), value=f"{sum(1 for member in ctx.guild.members if not member.bot)} (+{sum(1 for member in ctx.guild.members if member.bot)} {get_text(ctx.guild, 'info', 'info.server_bots')})", inline=True)
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_owner'), value=ctx.guild.owner, inline=True)
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_region'), value=ctx.guild.region, inline=True)
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.created'), value=default.date(ctx.guild.created_at), inline=True)
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_verification'), value=str(ctx.guild.verification_level).capitalize())
           
            info = []
            features = set(ctx.guild.features)
            all_features = {
                'PARTNERED': get_text(ctx.guild, 'info', 'info.features.partnered'),
                'VERIFIED': get_text(ctx.guild, 'info', 'info.features.verified'),
                'INVITE_SPLASH': get_text(ctx.guild, 'info', 'info.features.splash'),
                'VANITY_URL': get_text(ctx.guild, 'info', 'info.features.vanity'),
                'MORE_EMOJI': get_text(ctx.guild, 'info', 'info.features.emoji'),
                'ANIMATED_ICON': get_text(ctx.guild, 'info', 'info.features.animated'),
                'BANNER': get_text(ctx.guild, 'info', 'info.features.banner')
            }

            for feature, label in all_features.items():
                if feature in features:
                    info.append(label)

            if info:
                embed.add_field(name=get_text(ctx.guild, 'info', 'info.features'), value=',\n'.join(info))


            def next_level_calc(ctx):
                if str(ctx.guild.premium_tier) == "0":
                    count = int(2 - ctx.guild.premium_subscription_count)
                    txt = get_text(ctx.guild, 'info', 'info.next_level_in').format(count)
                    #if ctx.author.is_on_mobile():
                    return txt
                    #centered = "⠀"*int(25 - len(txt)/2) + txt 
                    #return centered

                if str(ctx.guild.premium_tier) == "1":
                    count = int(15 - ctx.guild.premium_subscription_count)
                    txt = get_text(ctx.guild, 'info', 'info.next_level_in').format(count)
                    #if ctx.author.is_on_mobile():
                    return txt
                    #centered = "⠀"*int(25 - len(txt)/2) + txt
                    #return centered

                if str(ctx.guild.premium_tier) == "2":
                    count = int(30 - ctx.guild.premium_subscription_count)
                    txt = get_text(ctx.guild, 'info', 'info.next_level_in').format(count)
                    #if ctx.author.is_on_mobile():
                    return txt
                    #centered = "⠀"*int(25 - len(txt)/2) + txt
                    #return centered

                if str(ctx.guild.premium_tier) == "3":
                    txt = get_text(ctx.guild, 'info', 'info.max_level')
                    #if ctx.author.is_on_mobile():
                    return txt
                    #centered = "⠀"*int(25 - len(txt)/2) + txt
                    #return centered

            if not ctx.author.is_on_mobile():
                if ctx.guild.premium_subscription_count is not None:
                    boostmsg = get_text(ctx.guild, 'info', 'info.boost_count').format('⠀'*int(9), ctx.guild.premium_subscription_count)
                    boostmsg += "\n`{0}{1}`\n".format('\U00002588'*(int(ctx.guild.premium_subscription_count if ctx.guild.premium_subscription_count <= 30 else 30)), '⠀'*(30-(int(round(ctx.guild.premium_subscription_count)))))
                    boostmsg += "`⠀|⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀|⠀⠀⠀⠀⠀⠀  ⠀⠀⠀⠀⠀⠀|`\n"
                    boostmsg += "Lvl 1⠀⠀⠀⠀⠀⠀⠀⠀Lvl 2⠀⠀⠀⠀⠀⠀⠀⠀⠀Lvl 3\n"
                    boostmsg += "{0}".format(next_level_calc(ctx))

                    last_boost = max(ctx.guild.members, key=lambda m: m.premium_since or ctx.guild.created_at)
                    if last_boost.premium_since is not None:
                        boosts = f"{get_text(ctx.guild, 'info', 'info.last_boost')} {last_boost} ({humanize.naturaltime(last_boost.premium_since)})"
                        #centered = "⠀"*int(27 - len(boosts)/2) + boosts
                        boostmsg += f"\n{boosts}"

                    embed.add_field(name=get_text(ctx.guild, 'info', 'info.boosts'), value=boostmsg)
                else:
                    embed.add_field(name=get_text(ctx.guild, 'info', 'info.boosts'), value=f"{'⠀'*18} {get_text(ctx.guild, 'info', 'info.no_boosts')} \n`{'⠀'*50}`\n⠀|  ⠀⠀⠀⠀⠀|  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀|\nLvl 1⠀⠀⠀Lvl 2⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Lvl 3\n{'⠀'*14}Next level in 2 boosts') #.format('⠀'*21, '⠀'*50, '⠀'*14)")
            else:
                if ctx.guild.premium_subscription_count is not None:

                    last_boost = max(ctx.guild.members, key=lambda m: m.premium_since or ctx.guild.created_at)
                    boosts = f"{get_text(ctx.guild, 'info', 'info.last_boost')} {last_boost} ({humanize.naturaltime(last_boost.premium_since)})"

                    embed.add_field(name=get_text(ctx.guild, 'info', 'info.boosts'), value=f"{get_text(ctx.guild, 'info', 'info.boosts')}: {ctx.guild.premium_subscription_count}\n"
                                                         f"{get_text(ctx.guild, 'info', 'info.boost_level')} {ctx.guild.premium_tier}\n"
                                                         f"{next_level_calc(ctx)}"
                                                         f"\n{boosts if last_boost.premium_since is not None else ''}")

            embed.add_field(name=get_text(ctx.guild, 'info', 'info.server_roles').format(int(len(ctx.guild.roles) -1)), value=roles[:-2])
            await ctx.send(content=f"<:info:603362826358095922> {get_text(ctx.guild, 'info', 'info.info_about').format(ctx.guild.name)}", embed=embed)

    @commandExtra(category="User Info", aliases=['user'])
    @commands.guild_only()
    async def userinfo(self, ctx, *, user: discord.Member = None):
        """ Get user information """
        if user is None:
            user = ctx.author

        embed = discord.Embed(colour=self.bot.embed_color)
        shared = str(len([i for i in ctx.bot.guilds if i.get_member(user.id)]))


        embed.add_field(name=get_text(ctx.guild, 'info', 'info.name'), value=user, inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.nick'), value=user.nick if hasattr(user, "nick") else get_text(ctx.guild, 'info', 'info.none'), inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.acc_created'), value=default.date(user.created_at), inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.user_id'), value=user.id)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.bot'), value=user.bot)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.joined_server'), value=default.date(user.joined_at), inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.shared'), value=shared)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.avatar'), value=f"[{get_text(ctx.guild, 'info', 'info.click')}]({user.avatar_url})")

        acknowledgements = []

        supportguild = self.bot.get_guild(514232441498763279)

        if user == self.bot.get_user(self.bot.owner_id):
            owner = "<:owner:621436626257838090> " + get_text(ctx.guild, 'info', 'info.acknowledgements.owner')
            acknowledgements.append(owner)

        translator_role = supportguild.get_role(592319743692898326)
        if user in supportguild.members:
            if user in translator_role.members:
                translator = "<:google_tr:621435195102461952> " + get_text(ctx.guild, 'info', 'info.acknowledgements.translator')
                acknowledgements.append(translator)

        bughunter_role = supportguild.get_role(521132262587236364)
        if user in supportguild.members:
            if user in bughunter_role.members:
                bughunter = "<:bughunter:633796873144238090> Bug Hunter"
                acknowledgements.append(bughunter)

        embed.add_field(name=get_text(ctx.guild, 'info', 'info.status'), value=f"**{get_text(ctx.guild, 'info', 'info.status.mobile')}:** {user.mobile_status}\n**{get_text(ctx.guild, 'info', 'info.status.desktop')}:** {user.desktop_status}\n**{get_text(ctx.guild, 'info', 'info.status.web')}:** {user.web_status}")
        if acknowledgements:
            embed.add_field(name=get_text(ctx.guild, 'info', 'info.acknowledgements'), value="\n".join(acknowledgements))

        embed.set_thumbnail(url=user.avatar_url_as(static_format='png'))

        userroles = []
        for role in user.roles:
            userroles.append(role.id)

        userroles = userroles[::-1][:-1]

        embed.add_field(
            name=get_text(ctx.guild, 'info', 'info.roles'),
            value=', '.join([f"<@&{x}>" for x in userroles]) if len(user.roles) > 1 else get_text(ctx.guild, 'info', 'info.none'),
            inline=False
        )

        await ctx.send(content="<:info:603362826358095922> " + get_text(ctx.guild, 'info', 'info.info_about').format(user), embed=embed)



    @commandExtra(category="Bot Info")
    async def ping(self, ctx):
        """ Pong! """
        before = time.monotonic()
        message = await ctx.send("Pong")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"\U0001f3d3 Pong   |   {int(ping)}ms")



    @commandExtra(category="Bot Info")
    async def support(self, ctx):
        """ Get an invite to our support server! """
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != 514232441498763279:
            return await ctx.send(embed=discord.Embed(color=self.bot.embed_color).set_author(name=get_text(ctx.guild, 'info', 'info.support'), icon_url=self.bot.get_guild(514232441498763279).icon_url, url="https://discord.gg/wZSH7pz"))

        await ctx.send(get_text(ctx.guild, 'info', 'info.is_support').format(ctx.author.name) + " :wink:")


    @commandExtra(category="Bot Info", aliases=['botinfo', 'info'])
    @commands.guild_only()
    async def about(self, ctx):
        """ About the bot """
        ramUsage = self.process.memory_full_info().rss / 1024**2
        unique_members = set(self.bot.get_all_members())
        unique_online = sum(1 for m in unique_members if m.status is discord.Status.online)
        unique_offline = sum(1 for m in unique_members if m.status is discord.Status.offline)
        unique_idle = sum(1 for m in unique_members if m.status is discord.Status.idle)
        unique_dnd = sum(1 for m in unique_members if m.status is discord.Status.dnd)
        channel_types = Counter(type(c) for c in self.bot.get_all_channels())
        voice = channel_types[discord.channel.VoiceChannel]
        text = channel_types[discord.channel.TextChannel]

        with open("db/config.json", "r") as f:
            data = json.load(f)

        embed = discord.Embed(colour=self.bot.embed_color)
        #embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.set_author(icon_url=self.bot.user.avatar_url, name=f"{self.bot.user.name}#{self.bot.user.discriminator} | {data['BOT_VERSION']}")
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.dev'), value='Dutchy#6127', inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.lib'), value="[Discord.py](https://github.com/Rapptz/discord.py)")
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.cmd_load'), value=len([x.name for x in self.bot.commands]), inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.servers'), value=len(self.bot.guilds))
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.system_ram'), value=f"{ramUsage:.2f} MB", inline=True)
        #embed.add_field(name="Commands run", value=self.bot.cmd_count)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.last_boot'), value=default.timeago(datetime.utcnow() - self.bot.uptime), inline=True)
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.users'), value=f"<:online:313956277808005120>⠀{unique_online} \n"
                            f"<:offline:313956277237710868>⠀{unique_offline} \n"
                            f"<:away:313956277220802560>⠀{unique_idle} \n"
                            f"<:dnd:313956276893646850>⠀{unique_dnd} \n"
                            f"**~~------------------~~**\n"
                            f"{get_text(ctx.guild, 'info', 'info.total')}:⠀{len(unique_members)}\n")
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.chan'), value=f"<:channel:585783907841212418> {text}\n<:voice:585783907673440266> {voice}")
        embed.add_field(name=get_text(ctx.guild, 'info', 'info.created'), value=f"{default.date(self.bot.user.created_at)}\n({default.timeago(datetime.utcnow() - self.bot.user.created_at)})")
        await ctx.send(embed=embed)

    @commandExtra(category="Bot Info", aliases=['joinme', 'botinvite'])
    async def invite(self, ctx):
        """ Invite me to your server """
        await ctx.send(embed=discord.Embed(color=self.bot.embed_color).set_author(name=get_text(ctx.guild, 'info', 'info.inv'), url="https://discordapp.com/api/oauth2/authorize?client_id=505532526257766411&permissions=1609952598&scope=bot", icon_url=self.bot.get_guild(514232441498763279).icon_url))

    @commandExtra(category="Bot Info")
    async def vote(self, ctx):
        embed = discord.Embed(color=self.bot.embed_color).set_author(name=get_text(ctx.guild, 'info', 'info.vote'), url="https://discordbots.org/bot/505532526257766411/vote", icon_url=self.bot.get_guild(514232441498763279).icon_url)
        await ctx.send(embed=embed)

    @commandExtra(category="User Info", aliases=['avy'])
    async def avatar(self, ctx, user : discord.User=None):
        em=discord.Embed(color=self.bot.embed_color)
        em.set_image(url=(user if user is not None else ctx.author).avatar_url)

        bot_artist = self.bot.get_user(299899233924939776)

        if user is self.bot.user:
            em.set_footer(text=get_text(ctx.guild, 'info', 'info.bot_avy').format(str("GuardeYard#5824")))

        await ctx.send(embed=em)

    @commandExtra(category="Bot Info")
    async def suggest(self, ctx, *, suggestion : str):
        schan = self.bot.get_channel(531628986573258784)

        # Build the suggestion embed
        semb = discord.Embed(color=0xf0c92d,
            title=ctx.author.id,
            description=f"__**New suggestion!**__\n\nFrom: {ctx.author}\nSubmitted in: {ctx.guild.name}"
        )
        semb.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        semb.add_field(name="SUGGESTION:",
            value=f"```fix\n{suggestion}```"
        )
        semb.set_footer(text=ctx.author.id)

        smsg = await schan.send(embed=semb)

        await smsg.add_reaction(':upvote:274492025678856192')
        await smsg.add_reaction(':downvote:274492025720537088')

        newsmsg = smsg.embeds[0]
        newsmsg.set_footer(text=smsg.id)
        await smsg.edit(embed=newsmsg)


        # Build the thanks embed
        tyemb = discord.Embed(color=self.bot.embed_color)
        tyemb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        support_hyperlink = str(f"[{get_text(ctx.guild, 'info', 'info.support_server')}](https://discord.gg/wZSH7pz)")

        tyemb.add_field(name=f"<:thanks:465678993576689665> {get_text(ctx.guild, 'info', 'info.thanks')}",
            value=get_text(ctx.guild, 'info', 'info.submit').format(ctx.author.display_name, support_hyperlink) + ":smile:"
        )
        tyemb.add_field(name=get_text(ctx.guild, 'info', 'info.suggestion'), value=f"```fix\n{suggestion}```")

        await ctx.send(embed=tyemb)
        await ctx.message.delete()

    @commandExtra(category="Bot Info")
    async def feedback(self, ctx, *, feedback : str):
        schan = self.bot.get_channel(531629029812600855)

        # Build the suggestion embed
        femb = discord.Embed(color=0x95fb55,
            title="New Feedback!",
            description=f"Feedback received from {ctx.author.name}, submitted in {ctx.guild.name}."
        )
        femb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        femb.add_field(name="FEEDBACK:",
            value=f"```fix\n{feedback}```"
        )

        await schan.send(embed=femb)


        # Build the thanks embed
        tyemb = discord.Embed(color=self.bot.embed_color)
        tyemb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        tyemb.add_field(name="<:thanks:465678993576689665> Thank you!",
            value=get_text(ctx.guild, 'info', 'info.feedback')
        )

        await ctx.send(embed=tyemb)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(info(bot))
