import discord
import traceback
import json
import aiohttp
import os

from discord.ext import commands
from discord.ext.commands import errors
from datetime import datetime
from utils.translate import get_text
from utils.default import commandsPlus, GroupPlus
from db import tokens

class Events(commands.Cog, name="Events"):
    def __init__(self, bot):
        self.bot = bot
        self.icon = ""
        self.big_icon = ""
    
################################################################################################

    def placeholder_replacer(self, emb_dict, member):
        for thing in emb_dict:
            if isinstance(emb_dict[thing], str):
                emb_dict[thing] = emb_dict[thing].replace("{{member.name}}", member.name)
                emb_dict[thing] = emb_dict[thing].replace("{{member.mention}}", member.mention)
                emb_dict[thing] = emb_dict[thing].replace("{{member.fullname}}", str(member))
                emb_dict[thing] = emb_dict[thing].replace("{{member.count}}", f"{sum(1 for m in member.guild.members if not m.bot)}")
                emb_dict[thing] = emb_dict[thing].replace("{{member.fullcount}}", str(member.guild.member_count))
                emb_dict[thing] = emb_dict[thing].replace("{{server.name}}", member.guild.name)
                emb_dict[thing] = emb_dict[thing].replace("{{server.owner}}", self.bot.get_user(member.guild.owner_id).name)
        return emb_dict
    
################################################################################################

    async def bot_check(self, ctx):
        with open("db/botblocked.json", "r") as f:
            data = json.load(f)
        if ctx.author.id in data["BLOCKED_USERS"]:
            emb = discord.Embed(color=0xFF7070, title="You attempted to use a command, but my owner has blocked you from using my commands. If you think you should be unblocked, contact Dutchy#6127")
            emb.set_author(name="Permission Error!")
            await ctx.send(embed=emb)
        else:
            return True

################################################################################################

    @commands.Cog.listener()
    async def on_command(self, ctx):
        print(f"{ctx.guild.name} | {ctx.author} > {ctx.message.content}")

################################################################################################

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command.parent:
            cmd = f'{ctx.command.parent} {ctx.command.name}'
        else:
            cmd = ctx.command.name

        if ctx.command.cog_name == "YTT":
            return

        if not cmd in self.bot.cmdUsage:
            self.bot.cmdUsage[cmd] = 1
        else:
            self.bot.cmdUsage[cmd] += 1

        if not str(ctx.author.id) in self.bot.cmdUsers:
            self.bot.cmdUsers[str(ctx.author.id)] = 1
        else:
            self.bot.cmdUsers[str(ctx.author.id)] += 1

        if not str(ctx.guild.id) in self.bot.guildUsage:
            self.bot.guildUsage[str(ctx.guild.id)] = 1
        else:
            self.bot.guildUsage[str(ctx.guild.id)] += 1
    
################################################################################################

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        if isinstance(err, errors.MissingRequiredArgument):
            await ctx.send_help(ctx.command)

        elif isinstance(err, errors.BadArgument):
            await ctx.send_help(ctx.command)

        elif isinstance(err, errors.CommandInvokeError):
            err = err.original

            _traceback = traceback.format_tb(err.__traceback__)
            _traceback = ''.join(_traceback)
            error = ('```sh\n{2}{0}: {3}\n```').format(type(err).__name__, ctx.message.content, _traceback, err)

            errorlog = self.bot.get_channel(522855838881284100)
            logemb=discord.Embed(title="Coding Error", color=0xFF7070)
            if ctx.command.parent:
                cmd = f"{ctx.command.parent} {ctx.command.name}"
            else:
                cmd = ctx.command.name
            logemb.add_field(name="Server Info", value=f"**Server:** {ctx.guild.name}\n**Server ID:** {ctx.guild.id}\n**Channel:** {ctx.channel.name}\n**Channel ID:** {ctx.channel.id}")
            logemb.add_field(name="Command Info", value=f"**Invoked by:** {ctx.author}\n**Author ID:** {ctx.author.id}\n**Command:** {cmd}\n**Prefix:** {ctx.prefix}")
            logemb.add_field(name="Full command message", value=ctx.message.clean_content)
            logemb.add_field(name="__**Error:**__", value=error)
            await errorlog.send(embed=logemb)

            errormsg=discord.Embed(color=0xFF7070,
                                   title="<:warn:620414236010741783> " + get_text(ctx.guild, "events", "events.oce_ic_title"),
                                   description=get_text(ctx.guild, "events", "events.oce_ic").format(type(err).__name__, err))
            await ctx.send(embed=errormsg)

        elif isinstance(err, errors.MissingPermissions):
            errormsg=discord.Embed(color=0xFF7070,
                                   title="<:warn:620414236010741783> " + get_text(ctx.guild, "events", "events.oce_no_title"),
                                   description=get_text(ctx.guild, "events", "events.oce_user_no_perms"))
            await ctx.send(embed=errormsg)

        elif isinstance(err, errors.BotMissingPermissions):
            errormsg=discord.Embed(color=0xFF7070,
                                   title="<:warn:620414236010741783> " + get_text(ctx.guild, "events", "events.oce_no_title"),
                                   description=get_text(ctx.guild, "events", "events.oce_bot_no_perms") + f"\n\n{err}")
            await ctx.send(embed=errormsg)

        elif isinstance(err, errors.CommandOnCooldown):
            retry_after = f"{err.retry_after:.0f}"
            cdem=discord.Embed(color=0xf89a16,
                               title="<a:timing:522948753368416277> " + get_text(ctx.guild, "events", "events.oce_coc_title"),
                               description=get_text(ctx.guild, "events", "events.oce_coc_help").format(str(retry_after)))
            await ctx.send(embed=cdem)

            logchan = self.bot.get_channel(530458521125257217)
            await logchan.send(f"{ctx.author} attempted to use a command while on cooldown.\n\nMake this message fancy someday soon mkay?")

        elif isinstance(err, errors.CommandNotFound):
            pass

        elif isinstance(err, errors.NotOwner):
            errormsg=discord.Embed(color=0xFF7070,
                                   title="<:warn:620414236010741783> " + get_text(ctx.guild, "events", "events.oce_no_title"),
                                   description=get_text(ctx.guild, "events", "events.oce_no_help"))
            await ctx.send(embed=errormsg)

        elif isinstance(err, errors.CheckFailure):
            pass

        elif isinstance(err.original, discord.Forbidden):
            errormsg=discord.Embed(color=0xFF7070,
                                   title="<:warn:620414236010741783> " + get_text(ctx.guild, "events", "events.oce_no_title"),
                                   description=get_text(ctx.guild, "events", "events.oce_user_no_perms"))
            await ctx.send(embed=errormsg)

################################################################################################

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Check if we didnt blacklist the guild
        logchannel = self.bot.get_channel(520047388950396928)

        with open('db/guild_blacklist.json', 'r') as f:
            d = json.load(f)

        if guild.id in d["Blacklist"]:
            e = discord.Embed(color=0xff6047, title="Attempted Invite", description=f"A blacklisted guild ({guild.name}) attempted to invite me.")
            e.set_thumbnail(url=guild.icon_url)
            await logchannel.send(embed=e)
            return await guild.leave()
        
        # Let's create their command enable/disable file
        file_name = "db/cmd_checks/" + str(guild.id) + ".json"
        new_file = open(file_name, "w+")
        new_file.write("{}")
        new_file.close()

        # And their database
        guild_db = open(f"db/guilds/{str(guild.id)}.json", "w+")
        guild_db.write('{}')
        guild_db.close()


        with open(f"db/guilds/{str(guild.id)}.json", "r") as f:
            data = json.load(f)

        data["Guild_Info"] = {}
        data["Guild_Logs"] = {}
        data["Economy"] = {}
        data["RR"] = {}

        with open(f"db/guilds/{str(guild.id)}.json", "w") as f:
            data = json.dump(data, f, indent=4)

        with open(f"db/guilds/{str(guild.id)}.json", "r") as f:
            data = json.load(f)

        module_dict = {}
        for c in self.bot.cogs.values():
            cats = []
            for cmd in c.walk_commands():
                if isinstance(cmd, commandsPlus) or isinstance(cmd, GroupPlus):
                    cats.append(cmd.category)
            cd = {}
            cats = list(set(cats))
            for cat in cats:
                cd[cat] = True
            module_dict[c.qualified_name] = {"Toggle": True, "Categories": cd}

        # Have to build the base first!
        data["Guild_Info"]["Name"] = guild.name
        data["Guild_Info"]["ID"] = guild.id
        data["Guild_Info"]["Owner_Tag"] = f"{guild.owner.name}#{guild.owner.discriminator}"
        data["Guild_Info"]["Owner_ID"] = guild.owner_id
        data["Guild_Info"]["Language"] = "EN"
        data["Guild_Info"]["Embed_Color"] = "0x307EC4"
        data["Guild_Info"]["Prefix"] = ["c?"]
        data["Guild_Info"]["Modules"] = module_dict
        data["Guild_Logs"]["Moderation"] = {}
        data["Guild_Logs"]["MessageEdit"] = {}
        data["Guild_Logs"]["MessageDelete"] = {}
        data["Guild_Logs"]["MemberJoin"] = {}
        data["Guild_Logs"]["MemberUpdate"] = {}
        data["Guild_Logs"]["Welcome_Msg"] = {}
        data["Guild_Logs"]["Leave_Msg"] = {}
        data["Guild_Logs"]["Join_Role"] = {}
        data["Economy"]["StartBal"] = 100
        data["Economy"]["Users"] = {}
        data["Economy"]["Settings"] = {}

        with open(f"db/guilds/{str(guild.id)}.json", "w") as f:
            data = json.dump(data, f, indent=4)

        with open(f"db/guilds/{str(guild.id)}.json", "r") as f:
            data = json.load(f)

        # Now we can put more data in the base
        data["Guild_Logs"]["Moderation"]["Toggle"] = "disabled"
        data["Guild_Logs"]["Moderation"]["Channel"] = "None"
        data["Guild_Logs"]["MessageEdit"]["Toggle"] = "disabled"
        data["Guild_Logs"]["MessageEdit"]["Channel"] = "None"
        data["Guild_Logs"]["MessageDelete"]["Toggle"] = "disabled"
        data["Guild_Logs"]["MessageDelete"]["Channel"] = "None"
        data["Guild_Logs"]["MemberJoin"]["Toggle"] = "disabled"
        data["Guild_Logs"]["MemberJoin"]["Channel"] = "None"
        data["Guild_Logs"]["MemberUpdate"]["Toggle"] = "disabled"
        data["Guild_Logs"]["MemberUpdate"]["channel"] = "None"
        data["Guild_Logs"]["Welcome_Msg"]["toggle"] = "disabled"
        data["Guild_Logs"]["Welcome_Msg"]["Delete_After"] = None
        data["Guild_Logs"]["Welcome_Msg"]["embedtoggle"] = "disabled"
        data["Guild_Logs"]["Welcome_Msg"]["channel"] = "None"
        data["Guild_Logs"]["Welcome_Msg"]["msg"] = "Welcome to {{server.name}}, {{member.metion}}!"
        data["Guild_Logs"]["Welcome_Msg"]["embedmsg"] = {}
        data["Guild_Logs"]["Leave_Msg"]["toggle"] = "disabled"
        data["Guild_Logs"]["Leave_Msg"]["Delete_After"] = None
        data["Guild_Logs"]["Leave_Msg"]["embedtoggle"] = "disabled"
        data["Guild_Logs"]["Leave_Msg"]["channel"] = "None"
        data["Guild_Logs"]["Leave_Msg"]["msg"] = "{{member.name}} has left the server..."
        data["Guild_Logs"]["Leave_Msg"]["embedmsg"] = {}
        data["Guild_Logs"]["Join_Role"]["toggle"] = "disabled"
        data["Guild_Logs"]["Join_Role"]["humanrole"] = "none"
        data["Guild_Logs"]["Join_Role"]["botrole"] = "none"
        data["Economy"]["Settings"]["Daily-Min"] = 10
        data["Economy"]["Settings"]["Daily-Max"] = 250
        

        with open(f"db/guilds/{str(guild.id)}.json", "w") as f:
            data = json.dump(data, f, indent=4)

        # Send the join message
        try:
            to_send = sorted([chan for chan in guild.channels if chan.permissions_for(guild.me).send_messages and isinstance(chan, discord.TextChannel)], key=lambda x: x.position)[0]
        except IndexError:
            pass
        else:
            if to_send.permissions_for(guild.me).embed_links: # We can embed!
                e = discord.Embed(color=0x307EC4, title="Thank you for adding me!")
                e.description = "Thank you for adding me to your server! I will do my best to make your work here as easy as possible. If you want to follow all changes made to me, [join my support server by clicking here!](https://discord.gg/wZSH7pz)"
                tips = ">>> **Prefix:** My default prefix is `c?`, but you can add a new prefix by doing `c?add-prefix <prefix>` or remove one by doing `c?remove-prefix <prefix>`\n\n"
                tips += "**Embed Color:** You can change my embed color by using the `c?set-color <color hex>` command! (Also try the `c?randomcolor` command to find a random color!)\n\n"
                tips += "**Command Settings:** You can enable and disable commands by using my `c?enable-command <command>` or `c?disable-command <command>` command!\n\n"
                tips += "**Language:** Did you know I am a multi-language bot? You can set my language by doing `c?set-language [language name]`! If you do not provide a language name, I will show you a list of available languages."
                e.add_field(name="Tips:", value=tips)
                await to_send.send(embed=e)
            else: # We were invited without embed perms...
                msg = "Thank you for adding me to your server! I will do my best to make your work here as easy as possible.\n"
                msg += "If you want to follow all changes made to me, join my support server by clicking on this link: <https://discord.gg/wZSH7pz>.\n\n"
                msg += "__**Tips:**__\n"
                msg += ">>> **Prefix:** My default prefix is `c?`, but you can add a new prefix by doing `c?add-prefix <prefix>` or remove one by doing `c?remove-prefix <prefix>`\n\n"
                msg += "**Embed Color:** You can change my embed color by using the `c?set-color <color hex>` command! (Also try the `c?randomcolor` command to find a random color!)\n\n"
                msg += "**Command Settings:** You can enable and disable commands by using my `c?enable-command <command>` or `c?disable-command <command>` command!\n\n"
                msg += "**Language:** Did you know I am a multi-language bot? You can set my language by doing `c?set-language [language name]`! If you do not provide a language name, I will show you a list of available languages."
                await to_send.send(msg)

        # Log the join
        members = len(guild.members)
        tch = len(guild.text_channels)
        vch = len(guild.voice_channels)
        owner = str(guild.owner)
        all = ""
        for emoji in guild.emojis:
            if discord.emoji:
                all += str(emoji)

        e=discord.Embed(title="Joined a new guild!", color=0x307EC4)
        e.set_thumbnail(url=guild.icon_url)
        e.description=f"**Guild name:** {guild.name}\n**Guild owner:** {owner}\n**Guild ID:** {guild.id}\n\n{members} members\n{tch} text channels\n{vch} voice channels\n\n__**Custom emoji:**__\n{all}"
        await logchannel.send(embed=e)

        # Post guild count to DEL
        async with aiohttp.ClientSession() as cs: 
            await cs.post('https://discordextremelist.xyz/api/bot/505532526257766411', headers={"Authorization": tokens.DEL}, data={"guildCount": len(self.bot.guilds)})

################################################################################################

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logchannel = self.bot.get_channel(520047388950396928)

        members = len(guild.members)

        e=discord.Embed(title="Left a guild...", color=0x307EC4)
        e.set_thumbnail(url=guild.icon_url)
        e.description=f"**Guild name:** {guild.name}\n{members} members"
        await logchannel.send(embed=e)

        # Remove their database files
        os.remove(f'db/cmd_checks/{str(guild.id)}.json')
        os.remove(f'db/guilds/{str(guild.id)}.json')

        # Post guild count to DEL
        async with aiohttp.ClientSession() as cs:
            await cs.post('https://discordextremelist.xyz/api/bot/505532526257766411', headers={"Authorization": tokens.DEL}, data={"guildCount": len(self.bot.guilds)})

################################################################################################

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author is self.bot.user:
            return

        # We dont want to listen to commands
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        # Check if user is blacklisted from our dms
        blacklisteddms = [514849447646199819, 514609909556314123] # TODO: store in file and use command to (un)block people
        if not message.guild and message.author.id in blacklisteddms:
            blockeddm=discord.Embed(description="<:banhammer:523695899726053377> **BANNED!**", color=0xff1414)
            blockeddm.set_footer(text="You have been blocked from my dm's. If you want to appeal your ban, contact my owner! | Dutchy#6127")
            return await message.author.send(embed=blockeddm)

        # Something happens in DMs
        if message.guild is None:

            # They tried to use a command with default prefix
            if message.content.lower().startswith("c?"):
                return await message.author.send("Hey there! In my DMs you can use commands without a prefix :)")

            # They sent an actual message to the bot!
            logchannel = self.bot.get_channel(520042138264797185)
            msgembed = discord.Embed(title="New DM:", description=message.content, color=0x0a97f5)
            msgembed.set_author(name=message.author, icon_url=message.author.avatar_url)
            if message.attachments:
                attachment_url = message.attachments[0].url
                msgembed.set_image(url=attachment_url)
            msgembed.set_footer(text=f"User ID: {message.author.id}")
            await logchannel.send(embed=msgembed)

        # We were mentioned, let's log that too
        if self.bot.user.mentioned_in(message) and message.mention_everyone is False:
            mentionlog = self.bot.get_channel(520042178513207297)
            msgembed = discord.Embed(title="New Mention:", description=message.content, color=0x0a97f5)
            msgembed.set_author(name=message.author, icon_url=message.author.avatar_url)
            msgembed.add_field(name="Mention Info:", value=f"From server: {message.author.guild}\nServer ID: {message.author.guild.id}\n\nSent by: {message.author.name}\nUser ID: {message.author.id}\n\nSent in: #{message.channel.name}")
            msgembed.set_footer(text=f"Channel ID: {message.channel.id}")
            return await mentionlog.send(embed=msgembed)

################################################################################################

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        if before.content == after.content:
            return

        embed=discord.Embed(title=get_text(before.guild, "events", "events.ome_msgedit"), color=0xcb5f06, timestamp=datetime.utcnow())
        embed.add_field(name=get_text(before.guild, "events", "events.ome_author"), value=f"{before.author.mention} ({before.author})", inline=True)
        embed.add_field(name=get_text(before.guild, "events", "events.ome_channel"), value=before.channel.mention, inline=True)
        embed.add_field(name=get_text(before.guild, "events", "events.ome_msg_orignal"), value=before.content, inline=False)
        embed.add_field(name=get_text(before.guild, "events", "events.ome_msg_edited"), value=after.content, inline=False)
        embed.set_footer(text=get_text(before.guild, "events", "events.ome_msgid").format(before.id))

        try:
            with open(f"db/guilds/{before.guild.id}.json", "r") as f:
                data = json.load(f)

            if data["Guild_Logs"]["MessageEdit"]["Toggle"] == "disabled":
                return

            elif data["Guild_Logs"]["MessageEdit"]["Toggle"] == "enabled":
                channel_id = int(data["Guild_Logs"]["MessageEdit"]["Channel"])
                channel = before.guild.get_channel(channel_id)

                await channel.send(embed=embed)
        except FileNotFoundError:
            return

################################################################################################

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        # Create the embed
        embed=discord.Embed(title=get_text(message.guild, "events", "events.omd_msgdel"),
                            color=0xe94e51,
                            timestamp=datetime.utcnow())

        embed.add_field(name=get_text(message.guild, "events", "events.omd_author"),
                        value=f"{message.author.mention} ({message.author})",
                        inline=True) # Message author

        embed.add_field(name=get_text(message.guild, "events", "events.omd_channel"),
                        value=message.channel.mention,
                        inline=True) # Message channel

        embed.add_field(name=get_text(message.guild, "events", "events.omd_msg_deleted"),
                        value=message.content,
                        inline=False) # Message content

        if message.attachments: # Had an attachment
            embed.set_image(url=message.attachments[0].url)

        embed.set_footer(text=f"ID: {message.id}") # Message ID

        try:
            with open(f"db/guilds/{message.guild.id}.json", "r") as f:
                data = json.load(f)

            if data["Guild_Logs"]["MessageDelete"]["Toggle"] == "disabled":
                return

            elif data["Guild_Logs"]["MessageDelete"]["Toggle"] == "enabled":
                channel_id = int(data["Guild_Logs"]["MessageDelete"]["Channel"])
                channel = message.guild.get_channel(channel_id)

                await channel.send(embed=embed)
        except FileNotFoundError:
            return

################################################################################################

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Don't listen to bots
        if before.bot:
            return

        # get the guild file
        try:
            with open(f"db/guilds/{before.guild.id}.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return

        # Logs are disabled...
        if data["Guild_Logs"]["MemberUpdate"]["Toggle"] == "disabled":
            return

        # Logs are enabled!
        elif data["Guild_Logs"]["MemberUpdate"]["Toggle"] == "enabled":
            channel_id = int(data["Guild_Logs"]["MemberUpdate"]["Channel"])
            channel = self.bot.get_channel(channel_id)

            # Nickname changed
            if before.nick != after.nick:
                e = discord.Embed(color=self.bot.embed_color,
                                  title=get_text(before.guild, "events", "events.omu_nick"),
                                  timestamp=datetime.utcnow())
                e.set_author(name=before, icon_url = before.avatar_url)
                e.description = get_text(before.guild, "events", "events.omu_msg").format(before.name, before.nick, after.nick)
                e.set_footer(text=get_text(before.guild, "events", "events.omu_id").format(before.id))
                await channel.send(embed=e)

################################################################################################

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        # Don't listen to bots
        if before.bot:
            return

        # Get all guilds as this is per user not per member
        try:
            for guild in self.bot.guilds:
                if before in guild.members:
                    with open(f"db/guilds/{guild.id}.json", "r") as f:
                        data = json.load(f)

                    # Logs are disabled...
                    if data["Guild_Logs"]["MemberUpdate"]["Toggle"] == "disabled":
                        continue

                    # Logs are enabled!
                    elif data["Guild_Logs"]["MemberUpdate"]["Toggle"] == "enabled":
                        channel_id = int(data["Guild_Logs"]["MemberUpdate"]["Channel"])
                        channel = guild.get_channel(channel_id)

                        # Avatar changed
                        if before.avatar != after.avatar:
                            e = discord.Embed(color=self.bot.embed_color,
                                              title=get_text(guild, "events", "events.ouu_avatar"),
                                              timestamp=datetime.utcnow())
                            e.set_author(name=after, icon_url=after.avatar_url)
                            e.description = get_text(guild, "events", "events.ouu_avy_msg").format(after.name)
                            e.set_thumbnail(url=after.avatar_url)
                            #e.set_image(url=before.avatar_url)
                            e.set_footer(text=get_text(guild, "events", "events.ouu_avy_id").format(after.id))
                            await channel.send(embed=e)
                            
                        # Username changed
                        if before.name != after.name:
                            e = discord.Embed(color=self.bot.embed_color, title=get_text(guild, "events", "events.ouu_username"))
                            e.set_author(name=after, icon_url=after.avatar_url)
                            e.description = get_text(guild, "events", "events.ouu_name_msg").format(before.name, after.name)
                            await channel.send(embed=e)

        except FileNotFoundError:
            return

################################################################################################

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open(f"db/guilds/{member.guild.id}.json", "r") as f:
            data = json.load(f)

        # Sending the welcoming message
        if data["Guild_Logs"]["Welcome_Msg"]["toggle"] == "enabled":

            text = str(data["Guild_Logs"]["Welcome_Msg"]["msg"])
            text = text.replace("{{member.name}}", member.name)
            text = text.replace("{{member.mention}}", member.mention)
            text = text.replace("{{server.name}}", member.guild.name)

            channel = self.bot.get_channel(int(data["Guild_Logs"]["Welcome_Msg"]["channel"]))
            if data["Guild_Logs"]["Welcome_Msg"]["Delete_After"] == None:
                await channel.send(text)
            else:
                await channel.send(text, delete_after=data["Guild_Logs"]["Welcome_Msg"]["Delete_After"])

        # Sending the embedded welcoming message
        if data["Guild_Logs"]["Welcome_Msg"]["embedtoggle"] == "enabled":
        
            emb_dict = data["Guild_Logs"]["Welcome_Msg"]["embedmsg"]
            emb_dict = self.placeholder_replacer(emb_dict, member)
            if "author" in emb_dict:
                emb_dict["author"] = self.placeholder_replacer(emb_dict["author"], member)
            if "footer" in emb_dict:
                emb_dict["footer"] = self.placeholder_replacer(emb_dict["footer"], member)
            if "fields" in emb_dict:
                for field in emb_dict["fields"]:
                    emb_dict["fields"] = self.placeholder_replacer(field["name"], member)
                    emb_dict["fields"] = self.placeholder_replacer(field["value"], member)
                    
            channel = self.bot.get_channel(int(data["Guild_Logs"]["Welcome_Msg"]["channel"]))
            if data["Guild_Logs"]["Welcome_Msg"]["Delete_After"] == None:
                await channel.send(embed=discord.Embed.from_dict(emb_dict))
            else:
                await channel.send(embed=discord.Embed.from_dict(emb_dict), delete_after=data["Guild_Logs"]["Welcome_Msg"]["Delete_After"])

        # Add a role to new members/bots
        if data["Guild_Logs"]["Join_Role"]["toggle"] == "enabled":

            # Log channel
            logchannel = self.bot.get_channel(562784997962940476)

            # Member is a bot
            if member.bot:

                try: # Try to add the botrole
                    if not data["Guild_Logs"]["Join_Role"]["botrole"] == "none":
                        role = member.guild.get_role(int(data["Guild_Logs"]["Join_Role"]["botrole"]))
                        await member.add_roles(role)

                except Exception as e: # Something went wrong...
                    await logchannel.send(e)

            # Member is not a bot
            if not member.bot:

                try: # Try to add the role
                    if not data["Guild_Logs"]["Join_Role"]["humanrole"] == "none":
                        role = member.guild.get_role(int(data["Guild_Logs"]["Join_Role"]["humanrole"]))
                        await member.add_roles(role)

                except Exception as e: # Something went wrong...
                    await logchannel.send(e)

        # Logs are disabled...
        else:
            return

################################################################################################

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        with open(f"db/guilds/{member.guild.id}.json", "r") as f:
            data = json.load(f)

        # Sending the leaving message
        if data["Guild_Logs"]["Leave_Msg"]["toggle"] == "enabled":

            text = str(data["Guild_Logs"]["Leave_Msg"]["msg"])
            text = text.replace("{{member.name}}", member.name)
            text = text.replace("{{server.name}}", member.guild.name)
            text = text.replace("{{member.fullname}}", f"{member.name}#{member.discriminator}")
            text = text.replace("{{member.count}}", str(sum(1 for m in member.guild.members if not m.bot)))
            text = text.replace("{{member.fullcount}}", member.guild.member_count)
            text = text.replace("{{server.owner}}", self.bot.get_user(member.guild.owner_id).name)

            channel = self.bot.get_channel(int(data["Guild_Logs"]["Leave_Msg"]["channel"]))
            if data["Guild_Logs"]["Leave_Msg"]["Delete_After"] == None:
                await channel.send(text)
            else:
                await channel.send(text, delete_after=data["Guild_Logs"]["Leave_Msg"]["Delete_After"])

        # Sending the embedded leaving message
        if data["Guild_Logs"]["Leave_Msg"]["embedtoggle"] == "enabled":

            emb_dict = data["Guild_Logs"]["Leave_Msg"]["embedmsg"]
            emb_dict = self.placeholder_replacer(emb_dict, member)
            if "author" in emb_dict:
                emb_dict["author"] = self.placeholder_replacer(emb_dict["author"], member)
            if "footer" in emb_dict:
                emb_dict["footer"] = self.placeholder_replacer(emb_dict["footer"], member)
            if "fields" in emb_dict:
                for field in emb_dict["fields"]:
                    emb_dict["fields"] = self.placeholder_replacer(field["name"], member)
                    emb_dict["fields"] = self.placeholder_replacer(field["value"], member)

            channel = self.bot.get_channel(int(data["Guild_Logs"]["Leave_Msg"]["channel"]))

            if data["Guild_Logs"]["Leave_Msg"]["Delete_After"] == None:
                await channel.send(embed=discord.Embed.from_dict(emb_dict))
            else:
                await channel.send(embed=discord.Embed.from_dict(emb_dict), delete_after=data["Guild_Logs"]["Leave_Msg"]["Delete_After"])

        # Logs are disabled...
        else:
            return

def setup(bot):
    bot.add_cog(Events(bot))
