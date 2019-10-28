import discord
import json

from discord.ext import commands
from utils.default import commandExtra, groupExtra
from utils.translate import get_text

class GuildSettings(commands.Cog, name="Settings"):
    def __init__(self, bot):
        self.bot = bot
        self.icon = "<:charlesSetting:615429320311046145>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615429320311046145.png"


    async def bot_check(self, ctx):
        if not ctx.guild:
            return True

        file_name= "db/cmd_checks/" + str(ctx.guild.id) + ".json"
        cmd = self.bot.get_command(ctx.command.name)
        try:
            with open(file_name, "r") as f:
                data = json.load(f)
            
            if ctx.command.parent:
                if ctx.command.parent in data:
                    if data[str(ctx.command.parent)] == "disabled":
                        await ctx.send(get_text(ctx.guild, "events", "events.cmd_disabled"))
                        return False

                if f"{ctx.command.parent}_{ctx.command.name}" in data:
                    if data[str(f"{ctx.command.parent}_{ctx.command.name}")] == "disabled":
                        await ctx.send(get_text(ctx.guild, "events", "events.subcmd_disabled"))
                        return False

                if not ctx.command.parent in data or f"{ctx.command.parent}_{ctx.command.name}" not in data:
                    return True

            else:
                if ctx.command.name in data:
                    if data[str(ctx.command.name)] == "disabled":
                        await ctx.send(get_text(ctx.guild, "events", "events.cmd_disabled"))
                        return False

                if not ctx.command.name in data:
                    return True

        except FileNotFoundError:
            return False

    @commands.has_permissions(administrator=True)
    @groupExtra(category="Settings")
    async def joinrole(self, ctx):
        pass

    @joinrole.command(name="toggle")
    async def role_toggle(self, ctx):
        toggle_set = False
        with open(f"db/guilds/{ctx.guild.id}.json", "r") as f:
            data = json.load(f)

        if data["Guild_Logs"]["Join_Role"]["humanrole"] == "none" and data["Guild_Logs"]["Join_Role"]["botrole"] == "none":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.none_set'))

        if data["Guild_Logs"]["Join_Role"]["toggle"] == "disabled":
            data["Guild_Logs"]["Join_Role"]["toggle"] = "enabled"
            toggle_set = True

        elif data["Guild_Logs"]["Join_Role"]["toggle"] == "enabled":
            data["Guild_Logs"]["Join_Role"]["toggle"] = "disabled"
            toggle_set = False

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            data = json.dump(data, f, indent=4)

        if toggle_set == True:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.enabled'))
        else:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.disabled'))

    @joinrole.command()
    async def bots(self, ctx, role:discord.Role):

        if role.position == ctx.guild.me.top_role.position or role.position > ctx.guild.me.top_role.position:
            img = discord.File(fp='db/images/role_position.PNG', filename='Role_Position.png')
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.toprole').format(role.name), file=img)

        with open(f"db/guilds/{ctx.guild.id}.json", "r") as f:
            data = json.load(f)

        data["Guild_Logs"]["Join_Role"]["botrole"] = role.id

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.bots') + f" `{role.name}`")

    @joinrole.command()
    async def humans(self, ctx, role:discord.Role):

        if role.position == ctx.guild.me.top_role.position or role.position > ctx.guild.me.top_role.position:
            img = discord.File(fp='db/images/role_position.PNG', filename='Role_Position.png')
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.toprole').format(role.name), file=img)

        with open(f"db/guilds/{ctx.guild.id}.json", "r") as f:
            data = json.load(f)

        data["Guild_Logs"]["Join_Role"]["humanrole"] = role.id

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.joinrole.humans') + f" `{role.name}`")

    @commands.has_permissions(administrator=True)
    @groupExtra(category="Welcoming/Leaving Messages")
    async def leaving(self, ctx):
        pass

    @leaving.command()
    async def msg(self, ctx, *, message):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Leave_Msg']['embedtoggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.emb_no_msg'))

        data['Guild_Logs']['Leave_Msg']['msg'] = message

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.msg') + f" ```\n{message}```")

    @leaving.command()
    async def embedmsg(self, ctx, *, message):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Leave_Msg']['toggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.msg_no_emb'))

        d = json.loads(message)

        data['Guild_Logs']['Leave_Msg']['embedmsg'] = d

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        e = discord.Embed.from_dict(d)

        await ctx.send(content=get_text(ctx.guild, 'settings', 'settings.leaving.embmsg'), embed=e)

    @leaving.command()
    async def toggle(self, ctx):
        toggle_set = False
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Leave_Msg']['embedtoggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.emb_is_toggled'))

        if data['Guild_Logs']['Leave_Msg']['channel'] == "None":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.no_chan'))

        if data['Guild_Logs']['Leave_Msg']['toggle'] == "disabled":
            toggle_set = True
            data['Guild_Logs']['Leave_Msg']['toggle'] = "enabled"
        elif data['Guild_Logs']['Leave_Msg']['toggle'] == "enabled":
            toggle_set = False
            data['Guild_Logs']['Leave_Msg']['toggle'] = "disabled"

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        if toggle_set == True:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.toggle_enable'))
        else:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.toggle_disable'))

    @leaving.command()
    async def embedtoggle(self, ctx):
        toggle_set = False
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Leave_Msg']['channel'] == "None":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.no_chan'))

        if data['Guild_Logs']['Leave_Msg']['toggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.msg_is_toggled'))

        if data['Guild_Logs']['Leave_Msg']['embedmsg'] == {}:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.emb_not_set'))

        if data['Guild_Logs']['Leave_Msg']['embedtoggle'] == "disabled":
            toggle_set = True
            data['Guild_Logs']['Leave_Msg']['embedtoggle'] = "enabled"
        elif data['Guild_Logs']['Leave_Msg']['embedtoggle'] == "enabled":
            toggle_set = False
            data['Guild_Logs']['Leave_Msg']['embedtoggle'] = "disabled"

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        if toggle_set == True:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.embtoggle_enable'))
        else:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.embtoggle_disable'))

    @leaving.command()
    async def channel(self, ctx, channel:discord.TextChannel):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        data['Guild_Logs']['Leave_Msg']['channel'] = channel.id

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.leaving.chan_set') + f" {channel.mention}")

    @commands.has_permissions(administrator=True)
    @groupExtra(category="Welcoming/Leaving Messages")
    async def welcoming(self, ctx):
        pass

    @welcoming.command(name="msg")
    async def _msg(self, ctx, *, message):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.emb_no_msg'))

        data['Guild_Logs']['Welcome_Msg']['msg'] = message

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.msg') + f" ```\n{message}```")

    @welcoming.command(name="embedmsg")
    async def _embedmsg(self, ctx, *, message):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Welcome_Msg']['toggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.msg_no_emb'))

        d = json.loads(message)

        data['Guild_Logs']['Welcome_Msg']['embedmsg'] = d

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        e = discord.Embed.from_dict(d)

        await ctx.send(content=get_text(ctx.guild, 'settings', 'settings.welcoming.embmsg'), embed=e)

    @welcoming.command(name="toggle")
    async def _toggle(self, ctx):
        toggle_set = False
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)


        if data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.emb_is_toggled'))

        if data['Guild_Logs']['Welcome_Msg']['channel'] == "None":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.no_chan'))

        if data['Guild_Logs']['Welcome_Msg']['toggle'] == "disabled":
            toggle_set = True
            data['Guild_Logs']['Welcome_Msg']['toggle'] = "enabled"
        elif data['Guild_Logs']['Welcome_Msg']['toggle'] == "enabled":
            toggle_set = False
            data['Guild_Logs']['Welcome_Msg']['toggle'] = "disabled"

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        if toggle_set == True:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.toggle_enable'))
        else:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.toggle_disable'))

    @welcoming.command(name="embedtoggle")
    async def _embedtoggle(self, ctx):
        toggle_set = False
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if data['Guild_Logs']['Welcome_Msg']['channel'] == "None":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.no_chan'))

        if data['Guild_Logs']['Welcome_Msg']['toggle'] == "enabled":
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.msg_is_toggled'))

        if data['Guild_Logs']['Welcome_Msg']['embedmsg'] == {}:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.emb_not_set'))

        if data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == "disabled":
            toggle_set = True
            data['Guild_Logs']['Welcome_Msg']['embedtoggle'] = "enabled"
        elif data['Guild_Logs']['Welcome_Msg']['embedtoggle'] == "enabled":
            toggle_set = False
            data['Guild_Logs']['Welcome_Msg']['embedtoggle'] = "disabled"

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        if toggle_set == True:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.embtoggle_enable'))
        else:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.embtoggle_disable'))

    @welcoming.command(name="channel")
    async def _channel(self, ctx, channel:discord.TextChannel):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        data['Guild_Logs']['Welcome_Msg']['channel'] = channel.id

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.welcoming.chan_set') + f" {channel.mention}")

    @commandExtra(category="Settings", name="guild-logs")
    async def guild_logs(self, ctx):
        file_name= "db/guilds/" + str(ctx.guild.id) + ".json"
        with open(file_name, "r") as f:
            data = json.load(f)

        emb = discord.Embed(color=self.bot.embed_color, title="Log settings:")

        disabled = str(get_text(ctx.guild, "settings", "settings.disabled"))
        enabled = str(get_text(ctx.guild, "settings", "settings.enabled"))

        moderation = str(get_text(ctx.guild, "settings", "settings.mod"))
        msg_edit = str(get_text(ctx.guild, "settings", "settings.msg_edit"))
        msg_del = str(get_text(ctx.guild, "settings", "settings.msg_del"))
        join = str(get_text(ctx.guild, "settings", "settings.join"))
        mupdate = str(get_text(ctx.guild, "settings", "settings.mupdate"))

        if data["Guild_Logs"]["Moderation"]["Toggle"] == "disabled":
            emb.add_field(name=moderation, value=f"```prolog\n{disabled}```")
        elif data["Guild_Logs"]["Moderation"]["Toggle"] == "enabled":
            emb.add_field(name=moderation, value=f"```css\n{enabled}```")

        if data["Guild_Logs"]["MessageEdit"]["Toggle"] == "disabled":
            emb.add_field(name=msg_edit, value=f"```prolog\n{disabled}```")
        elif data["Guild_Logs"]["MessageEdit"]["Toggle"] == "enabled":
            emb.add_field(name=msg_edit, value=f"```css\n{enabled}```")

        if data["Guild_Logs"]["MessageDelete"]["Toggle"] == "disabled":
            emb.add_field(name=msg_del, value=f"```prolog\n{disabled}```")
        elif data["Guild_Logs"]["MessageDelete"]["Toggle"] == "enabled":
            emb.add_field(name=msg_del, value=f"```css\n{enabled}```")

        if data["Guild_Logs"]["MemberJoin"]["Toggle"] == "disabled":
            emb.add_field(name=join, value=f"```prolog\n{disabled}```")
        elif data["Guild_Logs"]["MemberJoin"]["Toggle"] == "enabled":
            emb.add_field(name=join, value=f"```css\n{enabled}```")

        if data["Guild_Logs"]["MemberUpdate"]["Toggle"] == "disabled":
            emb.add_field(name=mupdate, value=f"```prolog\n{disabled}```")
        elif data["Guild_Logs"]["MemberUpdate"]["Toggle"] == "enabled":
            emb.add_field(name=mupdate, value=f"```css\n{enabled}```")

        await ctx.send(embed=emb)

    @commands.has_permissions(administrator=True)
    @commandExtra(name='set-color', category="Settings")
    async def embed_color(self, ctx, color):
        with open(f"db/guilds/{ctx.guild.id}.json", "r") as f:
            data = json.load(f)

        color = color.replace('#', '0x')

        data["Guild_Info"]["Embed_Color"] = color

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            json.dump(data, f)

        e = discord.Embed(color=discord.Color(int(color, 16)),
                          title=get_text(ctx.guild, "settings", "settings.emb_col"))

        await ctx.send(embed=e)

    @commands.has_permissions(administrator=True)
    @commandExtra(name="set-language",
                  aliases=['set-lang'],
                  category="Settings")
    async def set_language(self, ctx, *, language=None):

        languages = ['norwegian', 'dutch', 'english', 'spanish', 'vietnamese', 'russian']

        language_txt = get_text(ctx.guild, "settings", "settings.lang_txt")
        trans_txt = get_text(ctx.guild, "settings", "settings.translated")

        lang_list = "```ini\n"
        lang_list += f"{language_txt}{' '*int(15-len(language_txt))}| % {trans_txt}\n"
        lang_list += f"---------------+----{'-'*int(len(trans_txt))}\n"
        lang_list += "Norwegian      | [16.41%]\n"
        lang_list += "English        | [100%]\n"
        lang_list += "Dutch          | [41.61%]\n"
        #lang_list += "German         | [XXX]\n"
        #lang_list += "Danish         | [XXX]\n"
        #lang_list += "Italian        | [XXX]\n"
        lang_list += "French         | [24.78%]\n"
        lang_list += "Spanish        | [69.99%]\n"
        lang_list += "Vietnamese     | [75.44%]\n"
        lang_list += "Russian        | [15.49%]"
        #lang_list += "Serbian        | [XXX]"
        lang_list += "```"


        if language is None or language.lower() not in languages:
            e = discord.Embed(color=self.bot.embed_color,
                              title=get_text(ctx.guild, "settings", "settings.invalid_lang"),
                              description=get_text(ctx.guild, "settings", "settings.invalid_lang_desc"))
            e.add_field(name=get_text(ctx.guild, "settings", "settings.lang_available"),
                        value=lang_list)
            e.set_footer(text=get_text(ctx.guild, "settings", "settings.lang_help"))
            return await ctx.send(embed=e)

        if language.lower() == "norwegian":
            option = "NO"

        elif language.lower() == "dutch":
            option = "NL"

        elif language.lower() == "english":
            option = "EN"

        #elif language.lower() == "german":
        #    option = "DE"

        #elif language.lower() == "danish":
        #    option = "DA"

        #elif language.lower() == "italian":
        #    option = "IT"

        elif language.lower() == "french":
            option = "FR"

        elif language.lower() == "spanish":
            option = "ES"

        elif language.lower() == "vietnamese":
            option = "VI"

        elif language.lower() == "russian":
            option = "RU"

        file_name= "db/guilds/" + str(ctx.guild.id) + ".json"
        with open(file_name, "r") as f:
            data = json.load(f)

        data['Guild_Info']['Language'] = option

        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, "settings", "settings.lang_set").format(language.capitalize()))

    @commands.has_permissions(administrator=True)
    @commandExtra(name="disable-command",
                      aliases=["disablecmd", "disable-cmd"],
                      category="Settings")
    async def disablecmd(self, ctx, *, command):
        """Disable the given command. A few important main commands have been blocked from disabling for obvious reasons"""
        file_name= "db/cmd_checks/" + str(ctx.guild.id) + ".json"
        cant_disable = ["help", "jishaku", "disable-command", "enable-command"]
        cmd = self.bot.get_command(command)

        with open(file_name, "r") as f:
            data = json.load(f)

        if cmd.parent:
            if str(f"{cmd.parent}_{cmd.name}") in data:
                if data[str(f"{cmd.parent}_{cmd.name}")] == "disabled":
                    return await ctx.send(get_text(ctx.guild, "settings", "settings.subcmd_isdisabled"))
        else:
            if str(cmd.name) in data:
                if data[str(cmd.name)] == "disabled":
                    return await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_isdisabled"))

        if cmd.name in cant_disable:
            return await ctx.send(get_text(ctx.guild, "settings", "settings.no_disable"))

        if cmd.parent:
            data[f"{cmd.parent}_{cmd.name}"] = "disabled"

        else:
            data[str(cmd.name)] = "disabled"

        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)

        if cmd.parent:
            cmd = f"{cmd.parent} {cmd.name}"
            await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_disabled").format(cmd))
        else:
            await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_disabled").format(cmd.name))

    @commands.has_permissions(administrator=True)
    @commandExtra(name="enable-command",
                  aliases=["enablecmd", "enable-cmd"],
                  category="Settings")
    async def enablecmd(self, ctx, *, command):
        """Enables a disabled command"""
        file_name= "db/cmd_checks/" + str(ctx.guild.id) + ".json"
        cmd = self.bot.get_command(command)

        with open(file_name, "r") as f:
            data = json.load(f)

        if cmd.parent:
            if not str(f"{cmd.parent}_{cmd.name}") in data:
                return await ctx.send(get_text(ctx.guild, "settings", "settings.subcmd_isenabled"))
        else:
            if not str(cmd.name) in data:
                return await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_isenabled"))
            
        if cmd.parent:
            data.pop(f"{cmd.parent}_{cmd.name}")

        else:
            data.pop(str(cmd.name))

        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)

        if cmd.parent:
            cmd = f"{cmd.parent} {cmd.name}"
            await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_enabled").format(cmd))

        else:
            await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_enabled").format(cmd.name))

    @commands.has_permissions(administrator=True)
    @commandExtra(name="remove-prefix",
                  aliases=["rem-prefix", "del-prefix"],
                  category="Prefix")
    async def remove_prefix(self, ctx, prefix):
        """Remove a custom prefix from the list"""

        with open(f"db/guilds/{str(ctx.guild.id)}.json", "r") as f:
            data = json.load(f)

        if len(data["Guild_Info"]["Prefix"]) == 1:
            return await ctx.send(get_text(ctx.guild, "settings", "settings.one_pre"))

        data["Guild_Info"]["Prefix"].remove(prefix)

        with open(f"db/guilds/{str(ctx.guild.id)}.json", "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, "settings", "settings.pre_remove").format(prefix))

    @commands.has_permissions(administrator=True)
    @commandExtra(name="add-prefix",
                  aliases=["set-prefix"],
                  category="Prefix")
    async def add_prefix(self, ctx, prefix):

        with open(f"db/guilds/{str(ctx.guild.id)}.json", "r") as f:
            data = json.load(f)

        if not prefix in data["Guild_Info"]["Prefix"]:
            data["Guild_Info"]["Prefix"].append(prefix)
        else:
            return await ctx.send(get_text(ctx.guild, "settings", "settings.pre_isadded"))

        with open(f"db/guilds/{str(ctx.guild.id)}.json", "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, "settings", "settings.pre_add").format(prefix))

    @commandExtra(name="prefixes",
                  category="Prefix")
    async def prefixes(self, ctx):
        """Tells you which prefix(es) this server uses"""
        with open(f"db/guilds/{str(ctx.guild.id)}.json", "r") as f:
            data = json.load(f)

        if len(data["Guild_Info"]["Prefix"]) == 1:
            pre = '`, `'.join(data["Guild_Info"]["Prefix"])
            return await ctx.send(get_text(ctx.guild, "settings", "settings.prefix").format(pre))
        
        if len(data["Guild_Info"]["Prefix"]) >= 1:
            pre = '`, `'.join(data["Guild_Info"]["Prefix"])
            return await ctx.send(get_text(ctx.guild, "settings", "settings.prefixes").format(pre))

    @commands.has_permissions(administrator=True)
    @commandExtra(category="Settings")
    async def logchannel(self, ctx, option = None, *, channel: discord.TextChannel = None):

        options = ["MemberJoin", "MemberUpdate", "MessageEdit", "MessageDelete", "Moderation"]
        optionsmsg = "```asciidoc\n"
        optionsmsg += f'MemberJoin    :: {get_text(ctx.guild, "settings", "settings.log_join")}\n'
        optionsmsg += f'MemberUpdate  :: {get_text(ctx.guild, "settings", "settings.log_update")}\n'
        optionsmsg += f'MessageEdit   :: {get_text(ctx.guild, "settings", "settings.log_edit")}\n'
        optionsmsg += f'MessageDelete :: {get_text(ctx.guild, "settings", "settings.log_delete")}\n'
        optionsmsg += f'Moderation    :: {get_text(ctx.guild, "settings", "settings.log_mod")}'
        optionsmsg += "```"

        if not option in options or option is None:
            e = discord.Embed(color=self.bot.embed_color,
                              title=get_text(ctx.guild, "settings", "settings.invalid_opt"),
                              description=optionsmsg)
            e.set_footer(text=get_text(ctx.guild, "settings", "settings.invalid_opt_note"))
            return await ctx.send(embed=e)

        with open(f"db/guilds/{ctx.guild.id}.json", "r") as f:
            data = json.load(f)

        if channel is None:
            data["Guild_Logs"][option]["Toggle"] = "disabled"
            data["Guild_Logs"][option]["Channel"] = "None"
        
        if channel is not None:
            data["Guild_Logs"][option]["Toggle"] = "enabled"
            data["Guild_Logs"][option]["Channel"] = int(channel.id)

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            json.dump(data, f, indent=4)
        
        if channel is None:
            await ctx.send(get_text(ctx.guild, "settings", "settings.log_disabled").format(option))

        if channel is not None:
            await ctx.send(get_text(ctx.guild, "settings", "settings.log_set").format(option, channel.mention))

def setup(bot):
    bot.add_cog(GuildSettings(bot))
