import discord
import re
import aiohttp
import asyncio
import argparse
import shlex

from io import BytesIO
from discord.ext import commands
from utils import permissions
from collections import Counter
from utils.translate import get_text
from utils.default import commandExtra, groupExtra
from utils import checks

class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class moderation(commands.Cog, name="Moderation"):
    def __init__(self, bot):
        self.bot = bot
        self.icon = "<:charlesJudge:615429146159611909>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615429146159611909.png"


    @commandExtra(category="Basic")
    @commands.guild_only()
    @checks.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None): 
        """ Kicks a user from the current server. """
        if reason is None:
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:member_remove:598208865447837709> " + get_text(ctx.guild, "moderation", "moderation.kick").format(member.name)
            await member.kick(reason=get_text(ctx.guild, "moderation", "moderation.no_reason"))

        else:
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:member_remove:598208865447837709> " + get_text(ctx.guild, "moderation", "moderation.kick_reason").format(member.name, reason)
            await member.kick(reason=reason)

        await ctx.send(embed=e, delete_after=10)

    @commandExtra(category="Basic", aliases=['nick'])
    @commands.guild_only()
    @checks.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, name: str = None):
        """ Nicknames a user from the current server. """
        await member.edit(nick=name)
        e = discord.Embed(color=self.bot.embed_color)
        e.set_author(icon_url=member.avatar_url, name=member)
        e.description = f"<:member_edit:598206376816279577> " + get_text(ctx.guild, "moderation", "moderation.nick_change").format(member.name, name)

        if name is None:
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:member_edit:598206376816279577> " + get_text(ctx.guild, "moderation", "moderation.nick_remove").format(member.name)

        await ctx.send(embed=e, delete_after=10)

    @commandExtra(category="Banning")
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """ Bans a user from the current server. """
        if reason is None:
            await ctx.guild.ban(member, reason=get_text(ctx.guild, "moderation", "moderation.no_reason"))
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:member_remove:598208865447837709> " + get_text(ctx.guild, "moderation", "moderation.ban").format(member.name)

        else:
            await ctx.guild.ban(member, reason=reason)
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:member_remove:598208865447837709> " + get_text(ctx.guild, "moderation", "moderation.ban_reason").format(member.name, reason)

        await ctx.send(embed=e, delete_after=10)

    @commandExtra(category="Banning")
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    async def massban(self, ctx, reason: str, *members):
        """ Mass bans multiple members from the server. """
        for member_id in members:
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)

        e = discord.Embed(color=self.bot.embed_color)
        e.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
        e.description = f"<:member_remove:598208865447837709> " + get_text(ctx.guild, "moderation", "moderation.massban").format(len(members), reason)
        await ctx.send(embed=e, delete_after=10)

    @commandExtra(category="Banning")
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User, *, reason: str = None):
        """ Unbans a user from the current server. """
        if reason is None:
            await ctx.guild.unban(discord.Object(id=member.id), reason=get_text(ctx.guild, "moderation", "moderation.no_reason"))
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
            e.description = f"<:member_okay:598215768760385551> " + get_text(ctx.guild, "moderation", "moderation.unban")

        else:
            await ctx.guild.unban(discord.Object(id=member.id), reason=reason)
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
            e.description = f"<:member_okay:598215768760385551> " + get_text(ctx.guild, "moderation", "moderation.unban_reason").format(reason)

        await ctx.send(embed=e, delete_after=10)

    @commandExtra(category="Basic")
    @commands.guild_only()
    @checks.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = None):
        """ Mutes a user from the current server. """
        message = []

        for role in ctx.guild.roles:
            if role.name == "Muted":
                message.append(role.id)

        try:
            therole = discord.Object(id=message[0])

        except IndexError:

            try:
                therole = await ctx.guild.create_role(name="Muted", color=discord.Color.greyple())
                for channel in ctx.guild.channels:
                    await channel.set_permissions(therole, read_messages=True, send_messages=False)
                await ctx.send(get_text(ctx.guild, "moderation", "moderation.mute.role_created"))

            except Exception:
                return await ctx.send(get_text(ctx.guild, "moderation", "moderation.mute.no_role"))

        try:
            if reason is None:
                await member.add_roles(therole, reason=get_text(ctx.guild, "moderation", "moderation.no_reason"))
                e = discord.Embed(color=self.bot.embed_color)
                e.set_author(icon_url=member.avatar_url, name=member)
                e.description = f"<:mute:598220663743840286> " + get_text(ctx.guild, "moderation", "moderation.mute").format(member.name)

            else:
                await member.add_roles(therole, reason=reason)
                e = discord.Embed(color=self.bot.embed_color)
                e.set_author(icon_url=member.avatar_url, name=member)
                e.description = f"<:mute:598220663743840286> " + get_text(ctx.guild, "moderation", "moderation.mute_reason").format(member.name, reason)

            await ctx.send(embed=e, delete_after=10)
        except Exception as e:
            await ctx.send(e)

    @commandExtra(category="Basic")
    @commands.guild_only()
    @checks.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        """ Unmutes a user from the current server. """
        message = []
        for role in ctx.guild.roles:
            if role.name == "Muted":
                message.append(role.id)
        try:
            therole = discord.Object(id=message[0])
        except IndexError:
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.unmute.no_role"))

        if reason is None:
            await member.remove_roles(therole, reason=get_text(ctx.guild, "moderation", "moderation.no_reason"))
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:unmute:598227300399579227> " + get_text(ctx.guild, "moderation", "moderation.unmute").format(member.name)

        else:
            await member.remove_roles(therole, reason=reason)
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=member.avatar_url, name=member)
            e.description = f"<:unmute:598227300399579227> " + get_text(ctx.guild, "moderation", "moderation.unmute_reason").format(member.name, reason)

        await ctx.send(embed=e, delete_after=10)


    @groupExtra(aliases=['delete', 'prune'], category="Basic")
    @commands.guild_only()
    @checks.has_permissions(manage_messages=True)
    async def purge(self, ctx):
        """Removes messages that meet a criteria.

        In order to use this command, you must have Manage Messages permissions.
        Note that the bot needs Manage Messages as well. These commands cannot
        be used in a private message.

        When the command is done doing its work, you will get a message
        detailing which users got removed and how many messages got removed.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(get_text(ctx.guild, "moderation", "moderation.purge.no_subcommand"))

    async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.purge.too_many_msg").format(limit))

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
        except discord.Forbidden as e:
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.purge.no_perm"))
        except discord.HTTPException as e:
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.error").format(e))

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        if deleted == 1:
            messages = [get_text(ctx.guild, "moderation", "moderation.purge.one_message")]
        else:
            messages = [get_text(ctx.guild, "moderation", "moderation.purge.more_messages").format(deleted)]
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'**{name}**: {count}' for name, count in spammers)

        to_send = '\n'.join(messages)

        if len(to_send) > 2000:
            await ctx.send(get_text(ctx.guild, "moderation", "moderation.purged_alot").format(deleted), delete_after=10)
        else:
            e = discord.Embed(color=self.bot.embed_color)
            e.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
            e.description = to_send
            await ctx.send(embed=e, delete_after=10)
        await ctx.message.delete()

    @purge.command()
    async def embeds(self, ctx, search=100):
        """Removes messages that have embeds in them."""
        await self.do_removal(ctx, search, lambda e: len(e.embeds))

    @purge.command()
    async def files(self, ctx, search=100):
        """Removes messages that have attachments in them."""
        await self.do_removal(ctx, search, lambda e: len(e.attachments))

    @purge.command()
    async def images(self, ctx, search=100):
        """Removes messages that have embeds or attachments."""
        await self.do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @purge.command(name='all')
    async def _remove_all(self, ctx, search=100):
        """Removes all messages."""
        await self.do_removal(ctx, search, lambda e: True)

    @purge.command()
    async def user(self, ctx, member: discord.Member, search=100):
        """Removes all messages by the member."""
        await self.do_removal(ctx, search, lambda e: e.author == member)

    @purge.command()
    async def contains(self, ctx, *, substr: str):
        """Removes all messages containing a substring.

        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.send(get_text(ctx.guild, "moderation", "moderation.purge.too_short_argument"))
        else:
            await self.do_removal(ctx, 100, lambda e: substr in e.content)

    @purge.command(name='bot')
    async def _bot(self, ctx, prefix=None, search=100):
        """Removes a bot user's messages and messages with their optional prefix."""

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))

        await self.do_removal(ctx, search, predicate)

    @purge.command(name='emoji')
    async def _emoji(self, ctx, search=100):
        """Removes all messages containing custom emoji."""
        custom_emoji = re.compile(r'<:(\w+):(\d+)>')
        def predicate(m):
            return custom_emoji.search(m.content)

        await self.do_removal(ctx, search, predicate)

    @purge.command(name='reactions')
    async def _reactions(self, ctx, search=100):
        """Removes all reactions from messages that have them."""

        if search > 2000:
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.purge.too_many_msg").format(search))

        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()

        await ctx.send(get_text(ctx.guild, "moderation", "moderation.purge_reactions").format(total_reactions))

    @purge.command()
    async def custom(self, ctx, *, args: str):
        """A more advanced purge command.

        This command uses a powerful "command line" syntax.
        Most options support multiple values to indicate 'any' match.
        If the value has spaces it must be quoted.

        The messages are only deleted if all options are met unless
        the `--or` flag is passed, in which case only if any is met.

        The following options are valid.

        `--user`: A mention or name of the user to remove.
        `--contains`: A substring to search for in the message.
        `--starts`: A substring to search if the message starts with.
        `--ends`: A substring to search if the message ends with.
        `--search`: How many messages to search. Default 100. Max 2000.
        `--after`: Messages must come after this message ID.
        `--before`: Messages must come before this message ID.

        Flag options (no arguments):

        `--bot`: Check if it's a bot user.
        `--embeds`: Check if the message has embeds.
        `--files`: Check if the message has attachments.
        `--emoji`: Check if the message has custom emoji.
        `--reactions`: Check if the message has reactions
        `--or`: Use logical OR for all options.
        `--not`: Use logical NOT for all options.
        """
        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--user', nargs='+')
        parser.add_argument('--contains', nargs='+')
        parser.add_argument('--starts', nargs='+')
        parser.add_argument('--ends', nargs='+')
        parser.add_argument('--or', action='store_true', dest='_or')
        parser.add_argument('--not', action='store_true', dest='_not')
        parser.add_argument('--emoji', action='store_true')
        parser.add_argument('--bot', action='store_const', const=lambda m: m.author.bot)
        parser.add_argument('--embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('--files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('--reactions', action='store_const', const=lambda m: len(m.reactions))
        parser.add_argument('--search', type=int, default=100)
        parser.add_argument('--after', type=int)
        parser.add_argument('--before', type=int)

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            await ctx.send(str(e))
            return

        predicates = []
        if args.bot:
            predicates.append(args.bot)

        if args.embeds:
            predicates.append(args.embeds)

        if args.files:
            predicates.append(args.files)

        if args.reactions:
            predicates.append(args.reactions)

        if args.emoji:
            custom_emoji = re.compile(r'<:(\w+):(\d+)>')
            predicates.append(lambda m: custom_emoji.search(m.content))

        if args.user:
            users = []
            converter = commands.MemberConverter()
            for u in args.user:
                try:
                    user = await converter.convert(ctx, u)
                    users.append(user)
                except Exception as e:
                    await ctx.send(str(e))
                    return

            predicates.append(lambda m: m.author in users)

        if args.contains:
            predicates.append(lambda m: any(sub in m.content for sub in args.contains))

        if args.starts:
            predicates.append(lambda m: any(m.content.startswith(s) for s in args.starts))

        if args.ends:
            predicates.append(lambda m: any(m.content.endswith(s) for s in args.ends))

        op = all if not args._or else any
        def predicate(m):
            r = op(p(m) for p in predicates)
            if args._not:
                return not r
            return r

        args.search = max(0, min(2000, args.search)) # clamp from 0-2000
        await self.do_removal(ctx, args.search, predicate, before=args.before, after=args.after)

    @commandExtra(category="Banning")
    @commands.guild_only()
    @checks.has_permissions(kick_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason: str = None):
        """Soft bans a member from the server.

        A softban is basically banning the member from the server but
        then unbanning the member as well. This allows you to essentially
        kick the member while removing their messages.

        In order for this to work, the bot must have Ban Member permissions.

        To use this command you must have Kick Members permissions.
        """
        e = discord.Embed(color=self.bot.embed_color)
        e.set_author(icon_url=member.avatar_url, name=member)

        if reason is None:
            e.description = get_text(ctx.guild, "moderation", "moderation.softban").format(member.name)
        else:
            e.description = get_text(ctx.guild, "moderation", "moderation.softban_reason").format(member.name, reason)


        obj = discord.Object(id=member.id)
        await ctx.guild.ban(obj, reason=reason)
        await ctx.guild.unban(obj, reason=reason)
        await ctx.send(embed=e)

    @commandExtra(category="Banning")
    @commands.guild_only()
    @checks.has_permissions(ban_members=True)
    async def unbanall(self, ctx):
        total_bans = len(await ctx.guild.bans()) 

        unbanned = 0

        if total_bans == 0:
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.unbanall.no_bans"))

        def check(m):
            return m.author == ctx.author

        checkmsg = await ctx.send(get_text(ctx.guild, "moderation", "moderation.unbanall_check").format(total_bans))
        yes_no = await self.bot.wait_for('message', check=check)

        if yes_no.content.upper() == get_text(ctx.guild, "moderation", "moderation.unbanall.option_yes").capitalize():
            pass
        elif yes_no.content.upper() == get_text(ctx.guild, "moderation", "moderation.unbanall.option_no").capitalize():
            return await ctx.send(get_text(ctx.guild, "moderation", "moderation.unbanall.check_no"), delete_after=15)
        else:
            return

        await checkmsg.delete()

        msg = await ctx.send(get_text(ctx.guild, "moderation", "moderation.unbanall_unbanning") + "  <a:discord_loading:587812494089912340>")
        await asyncio.sleep(3)
        for user in await ctx.guild.bans():
            await ctx.guild.unban(user.user)
            total_unbanned = unbanned + 1
            await msg.edit(content=get_text(ctx.guild, "moderation", "moderation.unbanall_count").format(total_unbanned, total_bans))

        e = discord.Embed(color=self.bot.embed_color)
        e.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
        e.description = get_text(ctx.guild, "moderation", "moderation.unbanall_done").format(total_bans)
        await msg.edit(content="\u200B", embed=e, delete_after=10)




def setup(bot):
    bot.add_cog(moderation(bot))
