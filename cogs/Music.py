import asyncio
import datetime
import discord
import humanize
import itertools
import math
import random
import dropbox
import re
import wavelink
import time
import json
import youtube_dl
import lyricsgenius
import os

from utils import checks
from collections import deque
from discord.ext import commands
from typing import Union, Optional
from functools import partial
from utils.checks import music_check
from utils.translate import get_text
from utils.default import commandExtra, groupExtra
from utils.paginator import Pages
from youtube_dl import YoutubeDL
from db import tokens

RURL = re.compile(r'https?:\/\/(?:www\.)?.+')


class Track(wavelink.Track): 
    __slots__ = ('requester', 'channel', 'message')

    def __init__(self, id_, info, *, ctx=None):
        super(Track, self).__init__(id_, info)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.message = ctx.message

    @property
    def is_dead(self):
        return self.dead


class Player(wavelink.Player):

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot], guild_id: int, node: wavelink.Node):
        super(Player, self).__init__(bot, guild_id, node)

        self.queue = asyncio.Queue()
        self.next_event = asyncio.Event()

        self.volume = 40
        self.dj = None
        self.controller_message = None
        self.reaction_task = None
        self.updating = False
        self.inactive = False
        self.loop = 0

        self.pauses = set()
        self.resumes = set()
        self.stops = set()
        self.shuffles = set()
        self.skips = set()
        self.repeats = set()

        self.eq = 'Flat'

        bot.loop.create_task(self.player_loop())

    @property
    def entries(self):
        return list(self.queue._queue)

    async def player_loop(self):
        await self.bot.wait_until_ready()

        await self.set_preq('Flat')
        # We can do any pre loop prep here...
        await self.set_volume(self.volume)

        while True:
            self.next_event.clear()

            self.inactive = False

            song = await self.queue.get()
            if not song:
                continue

            self.current = song
            self.paused = False

            await self.play(song)


            # Wait for TrackEnd event to set our event...
            await self.next_event.wait()

            if self.loop != 0:
                if self.loop == 1:
                    self.queue._queue.appendleft(song)

                else:
                    await self.queue.put(song)

            # Clear votes...
            self.pauses.clear()
            self.resumes.clear()
            self.stops.clear()
            self.shuffles.clear()
            self.skips.clear()
            self.repeats.clear()


    async def song_info_page(self, ctx):
        track = self.current

        loop = asyncio.get_event_loop()

        ydl_opts = {
                'format': 'bestaudio',
                'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',}],
            }

        ytdl = YoutubeDL(ydl_opts)
        to_run = partial(ytdl.extract_info, url=f"ytsearch:{track.uri}", download=False)

        tdata = await loop.run_in_executor(None, to_run)
 
        if 'entries' in tdata:
            # take first item from a playlist
            data = tdata['entries'][0]

        uploader_name = data['uploader']
        uploader_link = data['uploader_url']
        date_year = data['upload_date'][:4]
        date_month = data['upload_date'][4:][:2]
        date_day = data['upload_date'][6:]
        creator = data['creator']
        title = data['alt_title']
        thumbnail = data['thumbnail']
        description = data['description']
        categories = ', '.join(data['categories'])
        tags = ', '.join(data['tags'])
        views = data['view_count']
        likes = data['like_count']
        dislikes = data['dislike_count']
        average_rating = data['average_rating']
        song_url = data['webpage_url']

        song_info_embed = discord.Embed(color=self.bot.embed_color)
        song_info_embed.set_thumbnail(url=thumbnail)

        song_title = f"{creator} - {title}"
        if song_title == "None - None":
            song_title = track.title

        song_info_embed.title = song_title
        song_info_embed.url = song_url

        if len(description) > 2048:
            description = description[:2040] + "..."

        song_info_embed.description = description +"\n⠀"
        song_info_embed.add_field(name=get_text(ctx.guild, 'music', 'music.controller.other'),
                                  value=f"**{get_text(ctx.guild, 'music', 'music.controller.categories')}**\n{categories}\n\n**{get_text(ctx.guild, 'music', 'music.controller.tags')}**\n{tags}\n\n👀 {get_text(ctx.guild, 'music', 'music.controller.views')} {views:,}\n<:upvote:596577438461591562> {get_text(ctx.guild, 'music', 'music.controller.likes')} {likes:,}\n<:downvote:596577438952062977> {get_text(ctx.guild, 'music', 'music.controller.dislikes')} {dislikes:,}\n⭐ {get_text(ctx.guild, 'music', 'music.controller.rating')} {average_rating}")
        song_info_embed.add_field(name=get_text(ctx.guild, 'music', 'music.controller.upload_info'),
                                  value=f"{get_text(ctx.guild, 'music', 'music.controller.uploader')} [{uploader_name}]({uploader_link})\n{get_text(ctx.guild, 'music', 'music.controller.upload_date')} {date_month}/{date_day}/{date_year}\n⠀")

        return song_info_embed


    async def info_page(self, ctx):
        info_embed = discord.Embed(color=self.bot.embed_color)
        info_embed.title = get_text(ctx.guild, 'music', 'music.controller.cpi')

        description = f"<:now_playing:606282731411734548> • **{get_text(ctx.guild, 'music', 'music.cpi.main')}**\n"
        description += f"> {get_text(ctx.guild, 'music', 'music.cpi.main_desc')}\n\n"

        description += f"<:song_info:606282731428773946> • **{get_text(ctx.guild, 'music', 'music.cpi.song_info')}**\n"
        description += f"> {get_text(ctx.guild, 'music', 'music.cpi.song_info_desc')}\n\n"

        description += f"<:karaoke:609172781472677888> • **{get_text(ctx.guild, 'music', 'music.cpi.lyrics')}**\n"
        description += f"> {get_text(ctx.guild, 'music', 'music.cpi.lyrics_desc')}\n\n"

        description += f"<:music_download:606285629038526464> • **{get_text(ctx.guild, 'music', 'music.cpi.mp3')}**\n"
        description += f"> {get_text(ctx.guild, 'music', 'music.cpi.mp3_desc')}\n\n" 

        description += f"<:delete:606282780183232550> • **{get_text(ctx.guild, 'music', 'music.cpi.delete')}**\n"
        description += f"> {get_text(ctx.guild, 'music', 'music.cpi.delete_desc')}\n\n"

        description += f"<:paginator_info:609172845880279062> • **{get_text(ctx.guild, 'music', 'music.cpi.info')}**\n"
        description += f"> {get_text(ctx.guild, 'music', 'music.cpi.info_desc')}"

        info_embed.description = description
                                 
        return info_embed

    async def download_song(self, ctx):
        track = self.current
        loop = asyncio.get_event_loop()

        ydl_opts = {
                'outtmpl': '{}.%(ext)s'.format(ctx.author.id),
                'format': 'worst',
                'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',}],
            }

        ytdl = YoutubeDL(ydl_opts)
        to_run = partial(ytdl.extract_info, url=f"ytsearch:{track.uri}")

        tdata = await loop.run_in_executor(None, to_run)

        if 'entries' in tdata:
            # take first item from a playlist
            data = tdata['entries'][0]
            try:
                song_title = data['creator'] + " - " + data['alt_title']
            except TypeError:
                song_title = track.title

        def file_download():
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                f = ydl.download([data['url']])
                #f = ydl.download([track['info']['uri']])

        await self.bot.loop.run_in_executor(None, file_download)

        download_embed = discord.Embed(color=self.bot.embed_color)
        download_embed.title = get_text(ctx.guild, 'music', 'music.controller.mp3_title')
        filepath = f"/home/dutchy/Charles/{ctx.author.id}.mp3"
        targetfile = f"/mp3_files/{song_title}.mp3"

        d = dropbox.Dropbox(tokens.DROPBOX)

        with open(filepath, "rb") as f:
            meta = d.files_upload(f.read(), targetfile, mode=dropbox.files.WriteMode("overwrite"))

        link = d.sharing_create_shared_link(targetfile)
        url = link.url
        dl_url = re.sub(r"\?dl\=0", "?dl=1", url)

        os.remove(f"/home/dutchy/Charles/{ctx.author.id}.mp3")

        download_embed.add_field(name=get_text(ctx.guild, 'music', 'music.controller.mp3_downloaded'),
                                 value=f"{song_title}\n[{get_text(ctx.guild, 'music', 'music.controller.mp3_link')}]({dl_url})")

        return download_embed

    async def lyrics_page(self, ctx):

        track = self.current
        loop = asyncio.get_event_loop()

        ydl_opts = {
                'format': 'worst',
                'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',}],
            }

        ytdl = YoutubeDL(ydl_opts)
        to_run = partial(ytdl.extract_info, url=f"ytsearch:{track.uri}", download=False)

        tdata = await loop.run_in_executor(None, to_run)
 
        if 'entries' in tdata:
            # take first item from a playlist
            data = tdata['entries'][0]

        creator = data['creator']
        title = data['alt_title']

        song_title = f"{creator} - {title}"

        genius = lyricsgenius.Genius(tokens.LYRICSGENIUS)
        song = genius.search_song(song_title)

        lyric_embed=discord.Embed(color=self.bot.embed_color,
                                  title=get_text(ctx.guild, 'music', 'music.controller.lyrics').format(song_title))


        #TODO:
        #if len(song.lyrics) > 3072:
        #    lyric_embed.description=song.lyrics[:2048]
        #    lyric_embed.add_field(name="\u200b", value=song.lyrics[2048:-1024])
        #    lyric_embed.add_field(name="\u200b", value=song.lyrics[-1024:1024])

        #    return lyric_embed
        #elif len(song.lyrics) > 2048:
        #    lyric_embed.description=song.lyrics[:2048]
        #    lyric_embed.add_field(name="\u200b", value=song.lyrics[:-1024])

        #    return lyric_embed
        #else:
        #    lyric_embed.description=song.lyrics

        lyric_embed.description=song.lyrics[:2045] + "..."

        return lyric_embed


class PlayerToo(Player):
    def __init__(self, bot):
        self.bot = bot
        Player.__init__()

    def is_playing(self):
        """ Returns the player's track state. """
        if not self.is_connected:
            return False

        if not self.last_position:
            return False

        if self.last_position > 0 and self.last_position < self.current.duration:
            return True

        return False


    def position(self):
        if not PlayerToo.is_playing:
            return 0

        if self.paused:
            return min(self.last_position, self.current.duration)

        difference = (time.time() * 1000) - self.last_update
        return min(self.last_position + difference, self.current.duration)

    async def main_page(self, ctx):

        track = self.current

        if track.is_stream:
            duration = '🔴 ' + get_text(ctx.guild, "music", "music.np.live")
        else:
            duration = str(datetime.timedelta(milliseconds=int(track.length)))

        dur_txt = get_text(ctx.guild, "music", "music.np.duration")
        vol_txt = get_text(ctx.guild, "music", "music.np.volume")
        eq_txt = get_text(ctx.guild, 'music', 'music.np.eq')
        dj_txt = get_text(ctx.guild, 'music', 'music.np.dj')
        loop_txt = get_text(ctx.guild, 'music', 'music.np.loop')
        position = str(datetime.datetime.utcfromtimestamp(PlayerToo.position(self)/1000).strftime("%H:%M:%S"))
        dur_time = f"{position}/{duration}"
        spaces_dur = 15 - len(dur_txt)
        spaces_vol = 15 - len(vol_txt)
        spaces_eq = 15 - len(eq_txt)
        spaces_dj = 15 - len(dj_txt)
        spaces_loop = 15 - len(loop_txt)

        desc = "```ini\n"
        desc += f'[{dur_txt}]:' + ' '*int(spaces_dur) + dur_time
        desc += f'\n[{vol_txt}]:' + ' '*int(spaces_vol) + f"{self.volume}%\n"

        if self.loop == 0:
            loop_opt = str(get_text(ctx.guild, 'music', 'music.np.loop_disabled'))
        if self.loop == 1:
            loop_opt = str(get_text(ctx.guild, 'music', 'music.np.loop_current'))
        if self.loop == 2:
            loop_opt = str(get_text(ctx.guild, 'music', 'music.np.loop_all'))

        desc += f"[{loop_txt}]:" + ' '*int(spaces_loop) + f"{loop_opt}\n"
        desc += f'[{eq_txt}]:' + ' '*int(spaces_eq) + f"{self.eq}\n"
        desc += f'[{dj_txt}]:' + ' '*int(spaces_dj) + f"{self.dj}```"

        main_embed = discord.Embed(color=self.bot.embed_color,
                              title=track.title,
                              url=track.uri,
                              description=desc)

        if len(self.entries) > 0:
            more = get_text(ctx.guild, "music", "music.np.more")
            data = '\n'.join(f'**-** `{t.title[0:45]}{"..." if len(t.title) > 45 else ""}`\n{f"*+ {int(len(self.entries) -1)} {more}*" if self.entries != 0 else ""}'
                             for t in itertools.islice([e for e in self.entries if not e.is_dead], 0, 1, None))
            main_embed.add_field(name=get_text(ctx.guild, 'music', 'music.np.up_next'),
                                 value=data, inline=False)

        main_embed.set_author(name=get_text(ctx.guild, "music", "music.np.now_playing"),
                              icon_url="https://cdn.discordapp.com/emojis/587796324267720704.gif")
        main_embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.uri[32:]}/maxresdefault.jpg")
        main_embed.set_footer(text=get_text(ctx.guild, 'music', 'music.np.requester').format(track.requester))

        return main_embed


class Music(commands.Cog, name="Music"):
    """Our main Music Cog."""

    def __init__(self, bot: Union[commands.Bot, commands.AutoShardedBot]):
        self.bot = bot
        self.icon = "<:charlesDJ:615428841888022528>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615428841888022528.png"

        self.bot.loop.create_task(self.initiate_nodes())
        self.controls = {'now_playing:606282731411734548': 'Main_Page',
                         'song_info:606282731428773946': 'Song_Info_Page',
                         'karaoke:609172781472677888': 'Lyric_Page',
                         'music_download:606285629038526464': 'Download_Song',
                         'delete:606282780183232550': 'Delete_Page',
                         'paginator_info:609172845880279062': 'Info_Page'}

        self._last_command_channel = None

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command.cog != ctx.cog:
            return

        self._last_command_channel = ctx.channel.id

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and after.channel is None:
            if member.guild.me in before.channel.members:
                if len(before.channel.members) == 1:
                    channel = member.guild.get_channel(self._last_command_channel)
                    await channel.send("Everyone left the channel, I will stop playing music.")

                    player = self.bot.wavelink.get_player(member.guild.id, cls=Player)
                    await player.destroy()


    async def initiate_nodes(self):
        nodes = {'MAIN': {'host': '127.0.0.1',
                          'port': 2333,
                          'rest_url': 'http://127.0.0.1:2333',
                          'password': "youshallnotpass",
                          'identifier': 'MAIN',
                          'region': 'eu'}}

        for n in nodes.values():
            node = await self.bot.wavelink.initiate_node(host=n['host'],
                                                         port=n['port'],
                                                         rest_uri=n['rest_url'],
                                                         password=n['password'],
                                                         identifier=n['identifier'],
                                                         region=n['region'],
                                                         secure=False)

            node.set_hook(self.event_hook)

    def event_hook(self, event):
        """Our event hook. Dispatched when an event occurs on our Node."""
        if isinstance(event, wavelink.TrackEnd):
            event.player.next_event.set()
        elif isinstance(event, wavelink.TrackException):
            print(event.error)

    def required(self, player, invoked_with):
        """Calculate required votes."""
        channel = self.bot.get_channel(int(player.channel_id))
        if invoked_with == 'stop':
            if len(channel.members) - 1 == 2:
                return 2

        return math.ceil((len(channel.members) - 1) / 2.5)

    async def has_perms(self, ctx, **perms):
        """Check whether a member has the given permissions."""
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if ctx.author.id == player.dj.id:
            return True

        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]

        if not missing:
            return True

        return False

    async def vote_check(self, ctx, command: str):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        vcc = len(self.bot.get_channel(int(player.channel_id)).members) - 1
        votes = getattr(player, command + 's', None)

        if vcc < 3 and not ctx.invoked_with == 'stop':
            votes.clear()
            return True
        else:
            votes.add(ctx.author.id)

            if len(votes) >= self.required(player, ctx.invoked_with):
                votes.clear()
                return True
        return False

    async def do_vote(self, ctx, player, command: str):
        attr = getattr(player, command + 's', None)
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if ctx.author.id in attr:
            await ctx.send(get_text(ctx.guild, 'music', 'music.vote.has_voted').format(ctx.author.mention, command), delete_after=15)
        elif await self.vote_check(ctx, command):
            await ctx.send(get_text(ctx.guild, 'music', 'music.vote.vote_passed').format(command), delete_after=20)
            to_do = getattr(self, f'do_{command}')
            await to_do(ctx)
        else:
            embed = discord.Embed(description=get_text(ctx.guild, 'music', 'music.vote.voted').format(ctx.author.mention, command))
            embed.set_footer(text=get_text(ctx.guild, 'music', 'music.vote.votes_needed').format(self.required(player, ctx.invoked_with) - len(attr)))
            await ctx.send(embed=embed, delete_after=45)

    @music_check(no_channel=True)
    @commandExtra(name='connect', aliases=['join'], category="Basic")
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to voice.

        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise discord.DiscordException(get_text(ctx.guild, 'music', 'music.no_channel'))

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if player.is_connected:
            if ctx.author.voice.channel == ctx.guild.me.voice.channel:
                return

        e = discord.Embed(color=self.bot.embed_color)
        ch = f"<:voice:585783907673440266>`{channel.name}`" 
        e.description=f"<:headphone:607011176106295327> " + get_text(ctx.guild, 'music', 'music.connected').format(ch)

        await ctx.send(embed=e, delete_after=10)
        await player.connect(channel.id)

    @music_check(no_channel=True)
    @commandExtra(name='play', aliases=['sing'], category="Basic")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def play_(self, ctx, *, query: str):
        """Queue a song or playlist for playback.

        Aliases
        ---------
            sing

        Parameters
        ------------
        query: simple, URL [Required]
            The query to search for a song. This could be a simple search term or a valid URL.
            e.g Youtube URL or Spotify Playlist URL.

        Examples
        ----------
        <prefix>play <query>
            {ctx.prefix}play What is love?
            {ctx.prefix}play https://www.youtube.com/watch?v=XfR9iY5y94s
        """
        await ctx.trigger_typing()

        await ctx.invoke(self.connect_)
        query = query.strip('<>')

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if not player.dj:
            player.dj = ctx.author

        if not RURL.match(query):
            query = f'ytsearch:{query}'

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.nothing_found'))

        if isinstance(tracks, wavelink.TrackPlaylist):
            for t in tracks.tracks:
                await player.queue.put(Track(t.id, t.info, ctx=ctx))

            embed = discord.Embed(color=self.bot.embed_color)
            embed.title = "<:music:600682025284010025> " + get_text(ctx.guild, 'music', 'music.playlist_added').format(len(tracks.tracks))
            embed.description = tracks.data["playlistInfo"]["name"]
            await ctx.send(embed=embed, delete_after=15)
        else:
            track = tracks[0]
            embed = discord.Embed(color=self.bot.embed_color)
            embed.title = "<:music:600682025284010025> " + get_text(ctx.guild, 'music', 'music.track_added')
            embed.description = f"[{track.title}]({track.uri})"
            embed.set_thumbnail(url=track.thumb)
            await ctx.send(embed=embed, delete_after=15)
            await player.queue.put(Track(track.id, track.info, ctx=ctx))

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True)
    @commandExtra(name="remove", category="Player Controls")
    async def _remove(self, ctx, index: int):
        """ Removes an item from the player's queue with the given index. """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        upcoming = list(player.entries)

        if not upcoming:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.no_queue'))

        if index > len(upcoming) or index < 1:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.invalid_index').format(len(upcoming)))

        removed = upcoming[index - 1]
        player.queue._queue.remove(removed)  # Account for 0-index.

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = "<:music:600682025284010025> " + get_text(ctx.guild, 'music', 'music.queue_remove').format(removed.title)

        await ctx.send(embed=embed, delete_after=15)

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='now_playing', aliases=['np', 'current', 'currentsong'], category="Player Information")
    async def now_playing(self, ctx):
        """Invoke the player controller.
        Aliases
        ---------
            np
            current
            currentsong
        Examples
        ----------
        <prefix>now_playing
            {ctx.prefix}np
        The player controller contains various information about the current and upcoming songs.
        
        ============================="""

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=PlayerToo)

        controller_msg = await ctx.send(embed=await PlayerToo.main_page(self=player, ctx=ctx))

        for reaction in self.controls:
            await controller_msg.add_reaction(str(reaction))

        def check(r, u):
            return u.id == ctx.author.id and r.message.id == controller_msg.id

        while controller_msg:

            react, user = await self.bot.wait_for('reaction_add', check=check)
            control = self.controls.get(str(react).strip("<:>"))

            if control == 'Main_Page':
                try:
                    await controller_msg.remove_reaction(react, user)
                except discord.errors.Forbidden:
                    pass
                await controller_msg.edit(embed=await PlayerToo.main_page(self=player, ctx=ctx))
            if control == 'Song_Info_Page':
                try:
                    await controller_msg.remove_reaction(react, user)
                except discord.errors.Forbidden:
                    pass
                await controller_msg.edit(embed=discord.Embed(color=self.bot.embed_color,
                                                              description=get_text(ctx.guild, 'music', 'music.loading_song_info') + " <a:discord_loading:587812494089912340>"))
                await controller_msg.edit(embed=await Player.song_info_page(self=player, ctx=ctx))
            if control == 'Info_Page':
                await controller_msg.edit(embed=await Player.info_page(self, ctx=ctx))
            if control == 'Delete_Page':
                await controller_msg.delete()
                try:
                    await ctx.message.delete()
                except discord.errors.Forbidden:
                    pass
            if control == 'Download_Song':
                checkmsg = await ctx.send(get_text(ctx.guild, 'music', 'music.mp3_confirm'))
                await checkmsg.add_reaction('✅')
                await checkmsg.add_reaction('❌')

                def checkmsgcheck(r, u):
                    return u.id == ctx.author.id and r.message.id == checkmsg.id

                react, user = await self.bot.wait_for('reaction_add', check=checkmsgcheck)

                if str(react) == '✅':
                    await checkmsg.delete()
                    await controller_msg.edit(embed=discord.Embed(color=self.bot.embed_color, description=get_text(ctx.guild, 'music', 'music.mp3_downloading') + " <a:discord_loading:587812494089912340>"))
                    await controller_msg.edit(embed=await Player.download_song(self=player, ctx=ctx))
                if str(react) == '❌':
                    await checkmsg.delete()
                    await controller_msg.edit(embed=discord.Embed(color=self.bot.embed_color, description=get_text(ctx.guild, 'music', 'music.mp3_cancel')))
            if control == 'Lyric_Page':
                await controller_msg.edit(embed=discord.Embed(color=self.bot.embed_color, description=get_text(ctx.guild, 'music', 'music.lyric_search') + " <a:discord_loading:587812494089912340>"))
                try:
                    await controller_msg.edit(embed=await Player.lyrics_page(self=player, ctx=ctx))
                except AttributeError:
                    await controller_msg.edit(emned=discord.Embed(color=self.bot.embed_color, description=get_text(ctx.guild, 'music', 'music.lyric_not_found')))


    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='pause', category="Player Controls")
    async def pause_(self, ctx):
        """Pause the currently playing song.
        Examples
        ----------
        <prefix>pause
            {ctx.prefix}pause
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player:
            return

        if not player.is_connected:
            await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if player.paused:
            return

        if await self.has_perms(ctx, manage_guild=True):
            embed = discord.Embed(color=self.bot.embed_color, description="<:pause:600682025661235201> " + get_text(ctx.guild, 'music', 'music.paused').format(ctx.author.mention))
            await ctx.send(embed=embed, delete_after=25)
            return await self.do_pause(ctx)

        await self.do_vote(ctx, player, 'pause')

    async def do_pause(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        player.paused = True
        await player.set_pause(True)

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='resume', category="Player Controls")
    async def resume_(self, ctx):
        """Resume a currently paused song.
        Examples
        ----------
        <prefix>resume
            {ctx.prefix}resume
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if not player.paused:
            return

        if await self.has_perms(ctx, manage_guild=True):
            embed = discord.Embed(color=self.bot.embed_color, description=f"<:play:600682025938321418> " + get_text(ctx.guild, 'music', 'music.resumed').format(ctx.author.mention))
            await ctx.send(embed=embed, delete_after=25)
            return await self.do_resume(ctx)

        await self.do_vote(ctx, player, 'resume')

    async def do_resume(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        player.resumetime = datetime.datetime.utcnow()
        await player.set_pause(False)

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='skip', category="Player Controls")
    @commands.cooldown(5, 10, commands.BucketType.user)
    async def skip_(self, ctx):
        """Skip the current song.
        Examples
        ----------
        <prefix>skip
            {ctx.prefix}skip
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if await self.has_perms(ctx, manage_guild=True):
            embed = discord.Embed(color=self.bot.embed_color, description='<:next:600682025741058059> ' + get_text(ctx.guild, 'music', 'music.skip').format(ctx.author.mention))
            await ctx.send(embed=embed, delete_after=25)
            return await self.do_skip(ctx)

        if player.current.requester.id == ctx.author.id:
            embed = discord.Embed(color=self.bot.embed_color, description=f'<:next:600682025741058059> ' + get_text(ctx.guild, 'music', 'music.skip').format(ctx.author.mention))
            await ctx.send(embed=embed, delete_after=25)
            return await self.do_skip(ctx)

        await self.do_vote(ctx, player, 'skip')

    async def do_skip(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.stop()

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True)
    @commandExtra(name='stop', category="Player Controls", aliases=["dc","disconnect"])
    @commands.cooldown(3, 30, commands.BucketType.guild)
    async def stop_(self, ctx):
        """Stop the player, disconnect and clear the queue.
        Examples
        ----------
        <prefix>stop
            {ctx.prefix}stop
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if await self.has_perms(ctx, manage_guild=True):
            embed = discord.Embed(color=self.bot.embed_color)
            embed.description = f'<:stop:600682025904766987> ' + get_text(ctx.guild, 'music', 'music.stop').format(ctx.author.mention)
            await ctx.send(embed=embed, delete_after=25)
            return await self.do_stop(ctx)

        await self.do_vote(ctx, player, 'stop')

    async def do_stop(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.destroy()

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True)
    @commandExtra(name='volume', aliases=['vol'], category="Player Controls")
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def volume_(self, ctx, *, value: int):
        """Change the player volume.
        Aliases
        ---------
            vol
        Parameters
        ------------
        value: [Required]
            The volume level you would like to set. This can be a number between 1 and 100.
        Examples
        ----------
        <prefix>volume <value>
            {ctx.prefix}volume 50
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if not 0 < value < 201:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.vol.value_error'))

        if not await self.has_perms(ctx, manage_guild=True) and player.dj.id != ctx.author.id:
            if (len(player.connected_channel.members) - 1) > 2:
                return

        if value < player.volume:
            emoji = "<:reducevolume:600682026223534080>"

        if value > player.volume:
            emoji = "<:volumeup:600682025644589069>"

        if value == player.volume:
            emoji = "<:volume:600684577106952192>"

        await player.set_volume(value)
        embed = discord.Embed(color=self.bot.embed_color)
        embed.description = f'{emoji} ' + get_text(ctx.guild, "music", "music.set_volume").format(player.volume)
        await ctx.send(embed=embed, delete_after=7)

    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='queue', aliases=['q', 'que'], category="Player Information")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def queue_(self, ctx, page: int = 1):
        """Retrieve a list of currently queued songs.
        Aliases
        ---------
            que
            q
        Examples
        ----------
        <prefix>queue
            {ctx.prefix}queue
            {ctx.prefix}q
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        upcoming = list(player.entries)

        if not upcoming:
            return await ctx.send(embed = discord.Embed(colour=self.bot.embed_color,
                                  title='<:menu:600682024558264322> ' + get_text(ctx.guild, 'music', 'music.no_queue')), delete_after=15)


        items_per_page = 10
        pages = math.ceil(len(upcoming) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(upcoming[start:end], start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = discord.Embed(colour=self.bot.embed_color,
                              title='<:menu:600682024558264322> ' + get_text(ctx.guild, "music", "music.queue"),
                              description=get_text(ctx.guild, "music", "music.queue_tracks").format(len(upcoming)) + f'\n\n{queue_list}')
        embed.set_footer(text=get_text(ctx.guild, "music", "music.queue_page").format(page, pages))

        await ctx.send(embed=embed)

    @checks.has_voted()
    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True, no_tracks_shuffle=True)
    @commandExtra(name='shuffle', aliases=['mix'], category="Player Controls")
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def shuffle_(self, ctx):
        """Shuffle the current queue.
        Aliases
        ---------
            mix
        Examples
        ----------
        <prefix>shuffle
            {ctx.prefix}shuffle
            {ctx.prefix}mix
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        if len(player.entries) < 3:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.cant_shuffle'), delete_after=10)

        if await self.has_perms(ctx, manage_guild=True):
            await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f'<:shuffle:600682026470998026> ' + get_text(ctx.guild, 'music', 'music.shuffle').format(ctx.author.mention)), delete_after=25)
            return await self.do_shuffle(ctx)

        await self.do_vote(ctx, player, 'shuffle')

    async def do_shuffle(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        random.shuffle(player.queue._queue)

    @checks.has_voted()
    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='repeat', category="Player Controls")
    async def repeat_(self, ctx):
        """Repeat the currently playing song.
        Examples
        ----------
        <prefix>repeat
            {ctx.prefix}repeat
        """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            return

        if await self.has_perms(ctx, manage_guild=True):
            await self.do_repeat(ctx)

            if player.loop == 0:
                return await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f'<:loop:600682024721711115> ' + get_text(ctx.guild, 'music', 'music.loop_stop').format(ctx.author.mention)), delete_after=9)
            elif player.loop == 1:
                return await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f'<:loop:600682024721711115> ' + get_text(ctx.guild, 'music', 'music.loop_current').format(ctx.author.mention)), delete_after=9)
            elif player.loop == 2:
                return await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f'<:loop:600682024721711115> ' + get_text(ctx.guild, 'music', 'music.loop_all').format(ctx.author.mention)), delete_after=9)

        await self.do_vote(ctx, player, 'repeat')


    async def do_repeat(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if player.loop == 0:
            player.loop = 1
        elif player.loop == 1:
            player.loop = 2
        elif player.loop == 2:
            player.loop = 0

    @checks.has_voted()
    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name='eq', category="Player Controls")
    async def set_eq(self, ctx, *, eq: str):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if eq.upper() not in player.equalizers:
            eqs = "Flat, Boost, Metal, Piano"
            return await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=get_text(ctx.guild, 'music', 'music.eq_invalid').format(eq, eqs)))

        await player.set_preq(eq)
        player.eq = eq.capitalize()
        embed = discord.Embed(color=self.bot.embed_color, description='<:equalizer:607008433081942016> ' + get_text(ctx.guild, 'music', 'music.eq_set').format(eq.capitalize()))
        await ctx.send(embed=embed, delete_after=25)

    #@checks.has_voted()
    @music_check(no_channel=True, bot_no_channel=True, same_channel=True, not_playing=True)
    @commandExtra(name="seek", category="Player Controls")
    async def seek(self, ctx, time:int):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await player.seek(int(PlayerToo.position(player)) + (time*1000))

        newpos = str(datetime.datetime.utcfromtimestamp(PlayerToo.position(player)/1000 + time).strftime("%H:%M:%S"))

        if str(time).startswith("-"):
            await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f"<:backward:600682023878656000> " + get_text(ctx.guild, 'music', 'music.pos_rew').format(ctx.author.mention, newpos)), delete_after=5)
        else:
            await ctx.send(embed=discord.Embed(color=self.bot.embed_color, description=f"<:forwards:600682023832518657> " + get_text(ctx.guild, 'music', 'music.pos_for').format(ctx.author.mention, newpos)), delete_after=5)

    #@checks.has_voted()
    @music_check(no_channel=True, bot_no_channel=True, same_channel=True)
    @commandExtra(category="Player Controls")
    async def find(self, ctx, *, query):
        """ Lists the first 10 search results from a given query. """
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not query.startswith('ytsearch:'):
            query = 'ytsearch:' + query

        tracks = await self.bot.wavelink.get_tracks(query)

        if not tracks:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.nothing_found'))

        tracklist = tracks[:10]  # First 10 results

        o = []
        for index, track in enumerate(tracklist, start=1):
            o.append(f'`{index}.` [{track.title}]({track.uri})')

        embed = discord.Embed(color=self.bot.embed_color, description="\n".join(o))
        msg = await ctx.send(content=get_text(ctx.guild, 'music', 'music.find_confirm'), embed=embed)

        def check(m):
            return ctx.author == m.author and m.content in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10')

        msgcheck = msg.embeds[0]
        desc_lines = msgcheck.description.splitlines()

        checking = await self.bot.wait_for('message', check=check)

        checkmsg = checking.content.strip('.')

        tracks = await self.bot.wavelink.get_tracks(tracklist[int(checkmsg.content)+1])
        track = tracks[0]
        await player.queue.put(Track(track.id, track.info, ctx=ctx))

        if not player.is_connected:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.bot_not_connected'))

        embed = discord.Embed(color=self.bot.embed_color)
        embed.title = "<:music:600682025284010025> " + get_text(ctx.guild, 'music', 'music.track_added')
        embed.description = f"[{track.title}]({track.uri})"
        embed.set_thumbnail(url=track.thumb)
        await ctx.send(embed=embed, delete_after=15)


    @commands.is_owner()
    @commandExtra(category="Hidden")
    async def playerinfo(self, ctx):
        """Retrieve various Node/Server/Player information."""
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        node = player.node

        used = humanize.naturalsize(node.stats.memory_used)
        total = humanize.naturalsize(node.stats.memory_allocated)
        free = humanize.naturalsize(node.stats.memory_free)
        cpu = node.stats.cpu_cores

        embed = discord.Embed(color=self.bot.embed_color, title=f'WaveLink: {wavelink.__version__}')

        fmt = f'Connected to `{len(self.bot.wavelink.nodes)}` nodes.\n' \
              f'Best available Node `{self.bot.wavelink.get_best_node().__repr__()}`\n' \
              f'`{len(self.bot.wavelink.players)}` players are distributed on nodes.\n' \
              f'`{node.stats.players}` players are distributed on server.\n' \
              f'`{node.stats.playing_players}` players are playing on server.\n\n' \
              f'Server Memory: `{used}/{total}` | `({free} free)`\n' \
              f'Server CPU: `{cpu}`\n\n' \
              f'Server Uptime: `{datetime.timedelta(milliseconds=node.stats.uptime)}`'

        embed.description = fmt
        await ctx.send(embed=embed)

    @groupExtra(aliases=['playlists', 'pl'], category="Playlists", invoke_without_command=True)
    async def playlist(self, ctx, *, user:Optional[discord.User]=None):
        if ctx.invoked_subcommand is None:

            if user is None:
                user = ctx.author

            # Check if playlist exists
            if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{user.id}.json'):
                if user != ctx.author:
                    return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.user_no_playlists'))
                return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists'))

            with open(f'db/Playlists/{user.id}.json', "r") as f: # It exists! Let's open it
                data = json.load(f)

            # Check if there are any playlists available
            if not data["Playlists"]:
                if user != ctx.author:
                    return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.user_no_playlists'))
                return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists'))

            # Let's list the playlists
            desc = ""
            for playlist in data["Playlists"]:
                desc += f"`-` {playlist} ({len(data['Playlists'][playlist])} {str(get_text(ctx.guild, 'music', 'music.pl.song')) if len(data['Playlists'][playlist]) == 1 else str(get_text(ctx.guild, 'music', 'music.pl.songs'))})\n"

            embed=discord.Embed(color=self.bot.embed_color, title=get_text(ctx.guild, 'music', 'music.pl.playlists'))
            embed.set_author(icon_url=user.avatar_url, name=str(user))
            embed.description = desc

            await ctx.send(embed=embed)


    @playlist.command()
    async def create(self, ctx, *, name):

        # Check if playlsit exists. If not, let's create
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            f = open(f"db/Playlists/{ctx.author.id}.json", "w+")
            f.write('{"Playlists": {}}')
            f.close()

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f: # It exists! Let's open it
            data = json.load(f)

        # Check if the playlist already exists
        if name in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.playlist_exists'))

        # Let's count how many playlists they have
        pl_count = 0
        for playlist in data["Playlists"]:
            pl_count += 1

        # Make sure they haven't exceeded the 15 playlists limit
        if pl_count == 10:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.playlist_limit'))

        data["Playlists"][name] = {}

        with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'music', 'music.pl.created').format(name, ctx.prefix))

    @playlist.command(name="add", aliases=['addsong'])
    async def add(self, ctx, playlist, *, song):

        # Check if playlist exists
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists'))

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f: # It exists! Let's open it
            data = json.load(f)

        # Check if we're adding the song to an existing playlist
        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_exist'))

        # Let's count the songs in the playlist
        song_count = 0
        for entry in data["Playlists"][playlist]:
            song_count += 1
            if song_count == 150:
                return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.song_limit'))

        song = song.strip('<>')
        if not RURL.match(song):
            song = f'ytsearch:{song}'

        tracks = await self.bot.wavelink.get_tracks(song)


        if isinstance(tracks, wavelink.TrackPlaylist): # Tracks result is a playlist
            if len(tracks.tracks) > (150 - song_count):
                can_add = 150 - song_count
                await ctx.send(get_text(ctx.guild, 'music', 'music.pl.limit_exceeded').format(playlist, can_add), delete_after=10)
                for t in tracks.tracks[:int(can_add)]:
                    data['Playlists'][playlist][t.title] = {"ID": t.id, "Info": t.info}
            if len(tracks.tracks) < (151 - song_count):
                for t in tracks.tracks:
                    data['Playlists'][playlist][t.title] = {"ID": t.id, "Info": t.info}
            title = tracks.data["playlistInfo"]["name"]

        else: # Tracks result can be a single song
            if tracks[0].title in data["Playlists"][playlist]:
                return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.song_is_added')) # Deny if it's already in the playlist
            t = tracks[0]
            data['Playlists'][playlist][t.title] = {"ID": t.id, "Info": t.info}
            title = t.title

        with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'music', 'music.pl.song_added').format(title, playlist))


    @music_check(no_channel=True)
    @playlist.command(aliases=['play'])
    async def start(self, ctx, *, playlist):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        await ctx.invoke(self.connect_)

        # Check if playlist exists
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists'))

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f: # It exists! Let's open it 
            data = json.load(f)

        # Check if playlist exists
        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_exist'))

        if not player.dj:
            player.dj = ctx.author # Set the dj if not done already

        for song in data["Playlists"][playlist]:
            await player.queue.put(Track(data["Playlists"][playlist][song]["ID"], data["Playlists"][playlist][song]["Info"], ctx=ctx))

        await ctx.send(get_text(ctx.guild, 'music', 'music.pl.play').format(playlist))

    @playlist.command()
    async def clear(self, ctx, *, playlist):

        # Check if playlist exists
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f: # It exists! Let's open it
            data = json.load(f)

        # Check if playlist exists
        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_exist'))

        # Let's make sure if they really want to do this
        msg = await ctx.send(get_text(ctx.guild, 'music', 'music.pl.clear_confirm').format(playlist))
        await msg.add_reaction('check:314349398811475968')
        await msg.add_reaction('xmark:314349398824058880')

        def check(r, u):
            return r.message.id == msg.id and u.id == ctx.author.id

        react, user = await self.bot.wait_for('reaction_add', check=check)

        if str(react) == "<:check:314349398811475968>": # Yep, let's delete
            data["Playlists"][playlist] = {}

            with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
                json.dump(data, f, indent=4)

            await msg.delete()
            await ctx.send(get_text(ctx.guild, 'music', 'music.pl.cleared').format(playlist))

        if str(react) == "<:xmark:314349398824058880>": # No, keep the playlist
            await msg.delete()
            await ctx.send(get_text(ctx.guild, 'music', 'music.pl.clear_cancel'))

    @playlist.command()
    async def remove(self, ctx, playlist, *, song):

        # Check if playlist exists
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        song = song.strip('<>')
        if not RURL.match(song):
            song = f"ytsearch:{song}"

        tracks = await self.bot.wavelink.get_tracks(song)

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f: # It exists! Let's open it
            data = json.load(f)

        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_exist'))

        # Check if playlist exists
        if not tracks[0].title in data["Playlists"][playlist]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.song_not_found'))

        data["Playlists"][playlist].pop(tracks[0].title) # Song removed

        with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'music', 'music.pl.song_removed').format(tracks[0].title, playlist))


    @playlist.command()
    async def delete(self, ctx, *, playlist):

        # Check if playlist exists
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f: # It exists! Let's open it
            data = json.load(f)

        # Check if playlist exists
        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_exist'))

        # Let's make sure this is really what they want
        msg = await ctx.send(get_text(ctx.guild, 'music', 'music.pl.delete_confirm').format(playlist))
        await msg.add_reaction('check:314349398811475968')
        await msg.add_reaction('xmark:314349398824058880')

        def check(r, u):
            return r.message.id == msg.id and u.id == ctx.author.id

        react, user = await self.bot.wait_for('reaction_add', check=check)

        if str(react) == "<:check:314349398811475968>": # Yep, let's remove the song
            data["Playlists"].pop(playlist)

            with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
                json.dump(data, f, indent=4)

            await msg.delete()
            await ctx.send(get_text(ctx.guild, 'music', 'music.pl.delete').format(playlist))

        if str(react) == "<:xmark:314349398824058880>": # No, keep the song
            await msg.delete()
            await ctx.send(get_text(ctx.guild, 'music', 'music.pl.delete_cancel'))

    @playlist.command()
    async def show(self, ctx, user:Optional[discord.User]=None, *, playlist):

        if user == None:
            user = ctx.author

        # Check if playlist exists
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{user.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        with open(f'db/Playlists/{user.id}.json', "r") as f:
            data = json.load(f)

        # Check if playlist exists
        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_found'))

        # Let's create the pages
        song_list = []
        for song in data["Playlists"][playlist]:
            song_list.append(song)

        queue_list = [] # Let's list the songs
        for track in song_list:
            queue_list.append(f'**[{track}]({data["Playlists"][playlist][track]["Info"]["uri"]})**')

        paginator = Pages(ctx,
                          title=f"__Showing playlist:__ {playlist}",
                          entries=queue_list,
                          per_page = 15,
                          embed_color=self.bot.embed_color,
                          show_entry_count=False,
                          author=user)

        await paginator.paginate()

    @playlist.command()
    async def clone(self, ctx, user:discord.User, playlist:str):

        # Check if author has a file
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f:
            auth_data = json.load(f)

        if len(auth_data["Playlists"]) == 10:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.playlist_limit'))

        # Check if user has a file
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{user.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        with open(f'db/Playlists/{user.id}.json', "r") as f:
            user_data = json.load(f)

        # Check if playlist exists
        if not playlist in user_data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.user_not_found').format(user.name))

        playlist_data = user_data["Playlists"][playlist]
        playlist_length = len(user_data["Playlists"][playlist])

        auth_data["Playlists"][playlist] = playlist_data

        with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
            json.dump(auth_data, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'music', 'music.pl.cloned').format(playlist, str(playlist_length), user.name))

    @playlist.command(name="shuffle")
    async def pl_shuffle(self, ctx, *, playlist):
        if not os.path.exists(f'/home/dutchy/Charles/db/Playlists/{ctx.author.id}.json'):
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.no_playlists')) 

        with open(f'db/Playlists/{ctx.author.id}.json', "r") as f:
            data = json.load(f)

        if not playlist in data["Playlists"]:
            return await ctx.send(get_text(ctx.guild, 'music', 'music.pl.not_found'))

        listdata = []
        for pl in data["Playlists"][playlist]:
            listdata.append({pl:data["Playlists"][playlist][pl]})
        random.shuffle(listdata)

        newdict = {}
        for entry in listdata:
            for k, v in entry.items():
                newdict[k] = v

        data["Playlists"][playlist] = newdict

        with open(f'db/Playlists/{ctx.author.id}.json', "w") as f:
            json.dump(data, f, indent=4)

        await ctx.send(f"Succesfully shuffled playlist `{playlist}`!")

def setup(bot):
    bot.add_cog(Music(bot))
