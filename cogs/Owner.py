import discord
import json
import io # Eval
import textwrap # Eval
import traceback # Eval
import math
import humanize
import copy # sudo
import aiohttp

from discord.ext import commands
from typing import Union
from utils import default, jsonedit
from contextlib import redirect_stdout # Eval
from utils.default import commandExtra, groupExtra

from jishaku.exception_handling import ReplResponseReactor
from jishaku.paginators import PaginatorInterface, WrappedPaginator
from jishaku.shell import ShellReader


class Owner(commands.Cog, name="Owner", command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.icon = "<:charles:619310144467107861>"
        self.big_icon = "https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.png?size=1024"

    async def cog_check(self, ctx: commands.Context):
        """
        Local check, makes all commands in this cog owner-only
        """
        if not await ctx.bot.is_owner(ctx.author):
            return False
        return True

    async def bot_check(self, ctx):
        if not ctx.guild:
            self.bot.embed_color = 0xFE8000
            return True

        else:
            try:
                with open(f"db/guilds/{ctx.guild.id}.json", "r")  as f:
                    data = json.load(f)

                col = data["Guild_Info"]["Embed_Color"]

                self.bot.embed_color = discord.Color(int(col, 16))
                return True
            except FileNotFoundError:
                self.bot.embed_color = 0xFE8000
                return True

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commandExtra(category="Other", name='git')
    async def git(self, ctx: commands.Context, pull_push, *, commit_msg=None):
        """
        Executes git statements in the system shell.

        This uses the system shell as defined in $SHELL, or `/bin/bash` otherwise.
        Execution can be cancelled by closing the paginator.
        """
        if pull_push == "push":
            shellcmd = f'sudo git add .&&sudo git commit -m "{commit_msg}"&&sudo git push'
        if pull_push == "pull":
            shellcmd = 'sudo git pull'
        if pull_push not in ['pull', 'push']: 
            return await ctx.send("Invalid option given")

        async with ReplResponseReactor(ctx.message):
            paginator = WrappedPaginator(prefix="```sh", max_size=1985)
            paginator.add_line(f"$ git {pull_push}\n")

            interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
            self.bot.loop.create_task(interface.send_to(ctx))

            if commit_msg is None:
                commit_msg = "File changes"

            with ShellReader(shellcmd) as reader:
                async for line in reader:
                    if interface.closed:
                        return
                    await interface.add_line(line)

    @commandExtra(category="Other")
    async def setnews(self, ctx, m_id:int, *, news:str):
        with open('db/config.json', 'r') as f:
            data = json.load(f)

        data["NEWS"]["ID"] = m_id
        data["NEWS"]["MESSAGE"] = news

        with open('db/config.json', 'w') as f:
            json.dump(data, f, indent=4)

        await ctx.send(f"Bot news has been set to: ```css\n{news}```")

    @commandExtra(category="Other")
    async def getinv(self, ctx, guild : int):
        guildid = self.bot.get_guild(guild)
        guildinvs = await guildid.invites()
        pager = commands.Paginator()
        for Invite in guildinvs:
            pager.add_line(Invite.url)
        for page in pager.pages:
            await ctx.send(page)

    @commandExtra(category="Other")
    async def createinv(self, ctx, channel : int):
        channelid = self.bot.get_channel(channel)
        InviteURL = await channelid.create_invite(max_uses=1)
        await ctx.send(InviteURL)

    @commandExtra(name="global-disable", category="Bot Settings")
    async def disablecmd(self, ctx, command, *, reason):
        """Disable the given command. A few important main commands have been blocked from disabling for obvious reasons"""
        file_name= "db/global_disable.json"
        cant_disable = ["help", "jishaku", "disable-command", "enable-command"]
        cmd = self.bot.get_command(command)

        with open(file_name, "r") as f:
            data = json.load(f)

        if cmd.parent:
            if str(f"{cmd.parent}_{cmd.name}") in data:
                return await ctx.send("This subcommand is already globally disabled!")
        else:
            if str(cmd.name) in data:
                return await ctx.send("This command is already globally disabled!")

        if cmd.name in cant_disable:
            return await ctx.send("Not going to disable that command, that'd be really stupid...")

        if cmd.parent:
            data[f"{cmd.parent}_{cmd.name}"] = reason

        else:
            data[str(cmd.name)] = reason

        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)

        if cmd.parent:
            await ctx.send(f"{cmd.parent} {cmd.name} has been globally disabled for **{reason}**!")
        else:
            await ctx.send(f"{cmd.name} has been globally disabled for **{reason}**!")

    @commandExtra(name="global-enable", category="Bot Settings")
    async def enablecmd(self, ctx, *, command):
        """Enables a disabled command"""
        file_name= "db/global_disable.json"
        cmd = self.bot.get_command(command)

        with open(file_name, "r") as f:
            data = json.load(f)

        if cmd.parent:
            if not str(f"{cmd.parent}_{cmd.name}") in data:
                return await ctx.send("This subcommand is already enabled!")
        else:
            if not str(cmd.name) in data:
                return await ctx.send("This command is already enabled!")
            
        if cmd.parent:
            data.pop(f"{cmd.parent}_{cmd.name}")

        else:
            data.pop(str(cmd.name))

        with open(file_name, "w") as f:
            json.dump(data, f, indent=4)

        if cmd.parent:
            await ctx.send(f"{cmd.parent} {cmd.name} has been re-enabled!")

        else:
            await ctx.send(f"{cmd.name} has been re-enabled!")

    @groupExtra(category="Bot Settings")
    async def change(self, ctx):
        """`change playing <new status>` - Change playing status

        `change username <new name>` - Change bot username

        `change nickname <new nickname>` - Change bot nickname

        `change avatar <url>` - Change bot avatar"""
        if ctx.invoked_subcommand is None:
            pass

    @change.command(name="playing")
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        try:
            await self.bot.change_presence(
                activity=discord.Game(type=0, name=playing),
                status=discord.Status.online
            )
            # jsonedit.change_value("files/config.json", "playing", playing)
            await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="listening")
    async def change_listening(self, ctx, *, listening: str):
        """ Change playing status. """
        try:
            await bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening,
                    name=listening)
                )
            # jsonedit.change_value("files/config.json", "playing", playing)
            await ctx.send(f"Successfully changed listening status to **{listening}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="watching")
    async def change_watching(self, ctx, *, watching: str):
        """ Change playing status. """
        try:
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.watching,
                    name=watching)
                )
            # jsonedit.change_value("files/config.json", "playing", playing)
            await ctx.send(f"Successfully changed watching status to **{watching}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="nickname")
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                await ctx.send("Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)



    @change.command(name="avatar")
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None

        try:
            async with aiohttp.ClientSession() as c:
                async with c.get(url) as f:
                    bio = await f.read()
            await self.bot.user.edit(avatar=bio)
            await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a useable image")
        except discord.HTTPException as err:
            await ctx.send(err)
        except TypeError:
            await ctx.send("You need to either provide an image URL or upload one with the command")

    @commandExtra(category="Owner Only")
    async def reboot(self, ctx):
        """ Reboot the bot """
        await ctx.message.add_reaction('a:Gears_Loading:470313276832743425')
        embed=discord.Embed(title="Rebooting...", color=0xfdac2b, timestamp=datetime.datetime.utcnow())
        channel = self.bot.get_channel(514959099235008513)
        await channel.send(embed=embed)
        await asyncio.sleep(1)
        await self.bot.logout()

    @commandExtra(category="Messages")
    async def msg(self, ctx, channel : int, *, message : str):
        """Send a message to a channel (use ChannelID) in any server the bot is in"""
        msgchannel = self.bot.get_channel(channel)
        await msgchannel.send(message)
        await ctx.message.delete()

    @commandExtra(category="Owner Only")
    async def sudo(self, ctx, who: Union[discord.Member, discord.User], *, command: str):
        """Run a command as another user."""
        msg = copy.copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)

    @commandExtra(aliases=['edit'], category="Messages")
    @commands.guild_only()
    async def editmessage(self, ctx, id:int, *, newmsg:str):
        """Edits a message sent by the bot"""
        try:
            msg = await ctx.channel.fetch_message(id)
        except discord.errors.NotFound:
            return await ctx.send("Couldn't find a message with an ID of `{}` in this channel".format(id))
        if msg.author != self.bot.user:
            return await ctx.send("That message was not sent by me")
        await msg.edit(content=newmsg)
        await ctx.message.delete()


    @commandExtra(category="Messages")
    async def dm(self, ctx, id:int, *, msg:str):
        """DMs a user"""
        user = self.bot.get_user(id)
        if not user:
            await ctx.send("Could not find any user with an ID of `{}`".format(id))


        try:
            await user.send(msg)

            logchannel = self.bot.get_channel(520042138264797185)
            logembed = discord.Embed(title=f"DM to {user}", description=msg, color=0x39e326)
            await logchannel.send(embed=logembed)
            await ctx.message.delete()

        except discord.errors.Forbidden:
            await ctx.author.send("Sorry bro, I can't send messages to that person...")
            await ctx.message.delete()

    @commandExtra(aliases=['slist', 'serverlist'], category="Other")
    async def guildlist(self, ctx, page:int=1):
        """List the guilds I am in."""
        guild_list = []
        for guild in self.bot.guilds:
            guild_list.append(guild)

        guild_count = len(self.bot.guilds)
        items_per_page = 10
        pages = math.ceil(guild_count / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        guilds_list = '' # Let's list the songs
        for guild in guild_list[start:end]:
            guilds_list += f'**{guild.name}** ({guild.id})\n**Joined:** {humanize.naturaltime(guild.get_member(self.bot.user.id).joined_at)}\n> **●▬▬▬▬▬▬▬▬๑۩۩๑▬▬▬▬▬▬▬▬●**\n'

        embed = discord.Embed(color=self.bot.embed_color, title="Guilds I'm in:", description=guilds_list)
        embed.set_footer(text=f"Viewing page {page}/{pages}")

        await ctx.send(embed=embed)

    @commandExtra(category="Suggestions")
    async def suggestdeny(self, ctx, message_id, *, reason = None):
        if reason is None:
            reason = "No reason given"


        channel = self.bot.get_channel(531628986573258784)
        message = await channel.fetch_message(id=message_id)
        embed = message.embeds[0]

        # Send message to the user first before we edit out the user ID
        author = self.bot.get_user(int(embed.title))
        
        e=discord.Embed(color=0xc22727)
        e.description = f"Your suggestion has been denied by {ctx.author}\n\n**Reason:**\n{reason}"
        e.add_field(name="Info", value="For more info, [join the support server](https://discord.gg/wZSH7pz)!")
        e.add_field(name="Your denied suggestion:", value=embed.description)
        await author.send(embed=e)


        up = self.bot.get_emoji(':upvote:274492025678856192')
        down = self.bot.get_emoji(':downvote:274492025720537088')

        up_count = {up.count for up in message.reactions}
        up_total = len(up_count)-1

        down_count = {down.count for down in message.reactions}
        down_total = len(down_count)-1

        # Edit embed after sending a message to the user
        embed.color = 0xc22727
        embed.title = f"Suggestion Denied"
        embed.description = f"Suggestion has been denied by {ctx.author}\n\n**Reason:**\n{reason}"
        embed.set_footer(text=f"Vote results: ⠀ 👍 {up_total} ⠀⠀|⠀⠀ 👎 {down_total}")


        await message.clear_reactions()
        await message.edit(embed=embed)
        await ctx.message.delete()



    @commandExtra(category="Suggestions")
    async def suggestapprove(self, ctx, message_id, *, note = None):
        if note is None:
            note = "No extra notes provided"
        
        channel = ctx.channel
        message = await channel.fetch_message(id=message_id)
        embed = message.embeds[0]

        # Send message to the user first before we edit out the user ID
        author = self.bot.get_user(int(embed.title))

        e=discord.Embed(color=0x34ab22)
        e.description = f"Your suggestion has been approved by {ctx.author}\n\n**Extra note:**\n{note}"
        e.add_field(name="Info", value="To see the progress of your suggestion, [join the support server](https://discord.gg/wZSH7pz)!")
        e.add_field(name="Your approved suggestion:", value=embed.description)
        await author.send(embed=e)


        up = self.bot.get_emoji(':upvote:274492025678856192')
        down = self.bot.get_emoji(':downvote:274492025720537088')

        up_count = {up.count for up in message.reactions}
        up_total = len(up_count)-1

        down_count = {down.count for down in message.reactions}
        down_total = len(down_count)-1


        embed.color = 0x34ab22
        embed.title = f"Suggestion Approved"
        embed.description = f"Suggestion has been approved by {ctx.author}\n\n**Extra Note:**\n{note}"
        embed.set_footer(text=f"Vote results: ⠀ 👍 {up_total} ⠀⠀|⠀⠀ 👎 {down_total}")
        await message.clear_reactions()
        await message.edit(embed=embed)
        await ctx.message.delete()

    @commandExtra(name='eval', category="Owner Only")
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')


#   configuration edits
#--------------------------------------------------------------------
    
    @groupExtra(name="configedit",
                aliases=["botedit"],
                category="Bot Settings")
    async def configedit(self, ctx):
        """Change an important value of the bot in the `config.json` file."""
        msg = "Please choose what you wish to update:\n"
        msg += "```json\n"
        msg += "{\n"
        msg += '    "botversion": "Version the bot is",\n'
        msg += '    "supportinvite": "Update the invite link for the support server"\n'
        msg += "}```"

        if ctx.invoked_subcommand is None:
            await ctx.send(msg)
    
#------------------------------

    @configedit.command(name="botversion")
    async def botversion(self, ctx, *, version):
        """Change the version of the bot."""

        jsonedit.change_value("db/config.json", "BOT_VERSION", f"v{version}")

        await ctx.send(f"Succesfully updated my version to {version}!")

#------------------------------

    @configedit.command(name="supportinvite")
    async def supportinvite(self, ctx, *, invite):
        """Change the invite link to the support server."""

        jsonedit.change_value("db/config.json", "SUPPORT_INVITE", invite)

        await ctx.send(f"Succesfully updated the invitation to the support server to {invite}!")

#--------------------------------------------------------------------

    @commandExtra(name="botblock",
                  aliases=["commandblock", "blacklist"],
                  category="Settings")
    async def botblock(self, ctx, *, user : discord.User):
        """Block an user from using any of my commands"""

        with open("db/botblocked.json", "r") as f:
            data = json.load(f)

        data["BLOCKED_USERS"].append(user.id)

        with open("db/botblocked.json", "w") as f:
            json.dump(data, f)

        await ctx.send(f"Succesfully blocked {user} from using my commands!")

#------------------------------

    @commandExtra(name="botunblock",
                  aliases=["commandunblock", "whitelist"],
                  category="Settings")
    async def botunblock(self, ctx, *, user : discord.User):
        """Remove an user's block to allow them to use my commands again"""
        with open("db/botblocked.json", "r") as f:
            data = json.load(f)

        data["BLOCKED_USERS"].remove(user.id)

        with open("db/botblocked.json", "w") as f:
            json.dump(data, f)
        
        await ctx.send(f"Succesfully unblocked {user} from their command block!")

#--------------------------------------------------------------------

    @commandExtra(aliases=['l'], category="Extension Management")
    async def load(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.load_extension(f"{name}")
        except Exception as e:
            return await ctx.send(f"```diff\n- {e}```")
        await ctx.send(f"Loaded extension **{name}.py**")

#------------------------------

    @commandExtra(aliases=['r'], category="Extension Management")
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        self.bot.reload_extension(f"{name}")
        await ctx.send(f"Reloaded extension **{name}.py**")
    
#------------------------------

    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, discord.errors.ExtensionAlreadyLoaded):
            await ctx.send("Extension has already been loaded!")
        elif isinstance(error, discord.errors.ExtensionNotFound):
            await ctx.send("Could not find that extension...")

#------------------------------

    @commandExtra(aliases=['u'], category="Extension Management")
    async def unload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.unload_extension(f"{name}")
        except Exception as e:
            return await ctx.send(f"```diff\n- {e}```")
        await ctx.send(f"Unloaded extension **{name}.py**")

def setup(bot):
    bot.add_cog(Owner(bot))
