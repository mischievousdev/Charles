import json
import discord


from discord.ext import commands
from utils.config import Config
config = Config()
#from cogs.dbl import DiscordBotsOrgAPI

class owner_only(commands.CommandError):
    pass

class dev_only(commands.CommandError):
    pass

class support_only(commands.CommandError):
    pass

class not_nsfw_channel(commands.CommandError):
    pass

class not_guild_owner(commands.CommandError):
    pass

class no_permission(commands.CommandError):
    pass

class music_error(commands.CommandError):
    pass

def music_check(no_channel=False, bot_no_channel=False, same_channel=False, not_playing=False, no_tracks_skip=False, seekable=False, no_tracks_shuffle=False, no_tracks_clear=False, no_tracks_remove=False, no_tracks_move=False):
    async def predicate(ctx):
        if no_channel == True:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send(f'You must be in a voice channel to use this command.')
                return False

        if bot_no_channel == True:
            if not ctx.player.is_connected:
                await ctx.send(f'I am not connected to any voice channels.')
                return False

        if same_channel == True:
            if not ctx.player.channel_id == ctx.author.voice.channel.id:
                await ctx.send(f'You must be in the same voice channel as me to use this command.')
                return False

        if not_playing == True:
            if not ctx.player.current:
                await ctx.send('No tracks currently playing.')
                return False

        if no_tracks_skip == True:
            if len(list(ctx.player.queue._queue)) <= 0:
                await ctx.send('There are no tracks in the queue to skip too.')
                return False

        #if seekable == True:
        #    if not ctx.player.current.is_seekable:
        #        await ctx.send('This track is not seekable.')
        #        return False

        if no_tracks_shuffle == True:
            if len(list(ctx.player.queue._queue)) <= 0:
                await ctx.send('Add more tracks to the queue to enable queue track shuffling.')
                return False

        #if no_tracks_clear == True:
        #    if len(list(ctx.player.queue._queue)) <= 0:
        #        await ctx.send('Add more tracks to the queue to enable queue clearing.')
        #        return False

        #if no_tracks_remove == True:
        #    if len(list(ctx.player.queue._queue)) <= 0:
        #        await ctx.send('Add more tracks to the queue to enable queue track removing.')
        #        return False

        #if no_tracks_move == True:
        #    if ctx.player.queue.qsize() <= 0:
        #        await ctx.send('Add more tracks to the queue to enable queue track moving.')
        #        return False

        return True

    return commands.check(predicate)

def has_voted():
    async def predicate(ctx):
        check = await ctx.bot.dblpy.get_user_vote(ctx.author.id)
        if check == True:
            return True
        if check == False:
            e = discord.Embed(color=0xFF7070, title="You have not voted!", description="This command is vote locked. to use this command, please [vote here](https://discordbots.org/bot/505532526257766411/vote).")
            await ctx.send(embed=e)
            return False
        return True
    return commands.check(predicate)

def testcommand():
    async def predicate(ctx):
        with open('db/TestCMD_Allow.json', 'r') as f:
            data = json.load(f)
        testing_ids = list(data['ALLOWED'])
        if not ctx.author.id in testing_ids:
            erroremb=discord.Embed(description="<:warn:620414236010741783> **Permission Error:** This is a testing command!\n\nyou attempted to use a command, but it was a testing command. This command is not ready for release. [Join the support server](https://discord.gg/wZSH7pz) and watch the Announcements channel, when this command will be released for public use you'll read it there.", color=0xFF7070)
            await ctx.send(embed=erroremb)
            return False
        else:
            return True
    return commands.check(predicate)

def is_owner():
    def predicate(ctx):
        if ctx.author.id == config.owner_id:
            return True
        else:
            raise owner_only
    return commands.check(predicate)

def is_support():
    async def predicate(ctx):
        if ctx.author.id in config.support_ids or ctx.author.id == config.owner_id:
            return True
        else:
            raise support_only
    return commands.check(predicate)

def is_admin():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {'administrator': True})
    return commands.check(pred)

def is_mod():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {'manage_guild': True})
    return commands.check(pred)

def is_nsfw_channel():
    def predicate(ctx):
        if not isinstance(ctx.channel, discord.DMChannel) and ctx.channel.is_nsfw():
            return True
        else:
            raise not_nsfw_channel
    return commands.check(predicate)

def is_guild_owner():
    def predicate(ctx):
        if ctx.author.id == ctx.guild.owner_id:
            return True
        else:
            raise not_guild_owner
    return commands.check(predicate)

def server_mod_or_perms(**permissions):
    def predicate(ctx):
        if not ctx.guild:
            return True
        mod_role_name = read_data_entry(ctx.guild.id, "mod-role")
        mod = discord.utils.get(ctx.author.roles, name=mod_role_name)
        if mod or permissions and all(getattr(ctx.channel.permissions_for(ctx.author), name, None) == value for name, value in permissions.items()):
            return True
        else:
            raise no_permission
    return commands.check(predicate)

def has_permissions(**permissions):
    def predicate(ctx):
        if all(getattr(ctx.channel.permissions_for(ctx.author), name, None) == value for name, value in permissions.items()):
            return True
        else:
            raise no_permission
    return commands.check(predicate)

def needs_embed(ctx):
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return True
    if ctx.channel.permissions_for(ctx.guild.me).embed_links:
        return True
    raise exceptions.EmbedError
