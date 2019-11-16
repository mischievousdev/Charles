import discord
import aiohttp
import os
import mtranslate
import json
import textwrap

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from functools import partial
from discord.ext import commands
from utils.default import commandExtra
from utils.translate import get_text

class Images(commands.Cog, name="Images"):
    def __init__(self, bot):
        self.bot = bot
        self.icon = "<:charlesArtist:615429245749166100>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615429245749166100.png"

    async def __get_image(self, ctx, user=None):
        if user:
            try:
                u = await commands.UserConverter().convert(ctx, user)
                if u.is_avatar_animated():
                    return str(u.avatar_url_as(format="gif"))
                else:
                    return str(u.avatar_url_as(format="png"))
            except Exception:
                try:
                    e = await commands.EmojiConverter().convert(ctx, user)
                    return str(e.url)
                except Exception:
                    try:
                        e = await commands.PartialEmojiConverter().convert(ctx, user)
                        return str(e.url)
                    except Exception:
                        return str(user.strip("<>"))


        await ctx.trigger_typing()

        message = ctx.message

        if len(message.attachments) > 0:
            return message.attachments[0].url

        def check(m):
            return m.channel == message.channel and m.author == message.author

        try:
            await ctx.send(get_text(ctx.guild, "images", "images.send_image"))
            x = await self.bot.wait_for('message', check=check, timeout=15)
        except:
            return await ctx.send(get_text(ctx.guild, "images", "images.timeout"))

        if not len(x.attachments) >= 1:
            return await ctx.send(get_text(ctx.guild, "images", "images.none_found"))

        return x.attachments[0].url

    def _ytkids(self, im, message):
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype('roboto.ttf', size=25)
        (x, y) = (30, 430)
        color = 'rgb(255, 255, 255)'
        draw.text((x, y), message, fill=color, font=font)

        return im

    @commandExtra(category="Funny")
    async def ytkids(self, ctx, *, message):
        if len(message) > 40:
            message = message[:37] + "..."

        with open('db/images/yt_kids.png', 'rb') as f:
            im = Image.open(BytesIO(f.read())).convert("RGBA")

        thing = partial(self._ytkids, im, message)

        img = await self.bot.loop.run_in_executor(None, thing)

        buffer = BytesIO()
        img.save(buffer, 'png')
        buffer.seek(0)

        f = discord.File(fp=buffer, filename='ytkids.png')
        await ctx.send(embed=discord.Embed(color=self.bot.embed_color).set_image(url="attachment://ytkids.png"), file=f)
        img.close()

    @commandExtra(category="Funny")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def caption(self, ctx, user = None):
        """Caption an image"""
        img = await self.__get_image(ctx, user)
        if not isinstance(img, str):
            return img
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "Content": img,
            "Type": "CaptionRequest"
        }
        url = "https://captionbot.azurewebsites.net/api/messages"
        try:
            async with aiohttp.ClientSession() as cs:
                async with cs.post(url, headers=headers, json=payload) as r:
                    data = await r.text()

            with open(f'db/guilds/{str(ctx.guild.id)}.json', "r") as f:
                jdata = json.load(f)

            lang_code = str(jdata["Guild_Info"]["Language"]).lower()

            result = mtranslate.translate(str(data), lang_code, "en")

            em = discord.Embed(color=self.bot.embed_color, title=result)
            em.set_image(url=img)
            await ctx.send(embed=em)
        except:
            await ctx.send(get_text(ctx.guild, "images", "images.data_fail"))

    @commandExtra(category="Animals")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def cat(self, ctx):
        """ Posts a random cat """
        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://nekos.life/api/v2/img/meow') as r:
                r = await r.json()
        await ctx.send(embed=discord.Embed(color=self.bot.embed_color).set_image(url=r['url']))



    @commandExtra(category="Animals")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def dog(self, ctx):
        """ Posts a random dog """
        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://random.dog/woof.json') as r:
                r = await r.json()

        if r['url'].endswith( ".mp4"):
        	return await ctx.send(r['url'])
        await ctx.send(embed=discord.Embed(color=self.bot.embed_color).set_image(url=r['url']))

    @commandExtra(category="Animals")
    @commands.cooldown(rate=1, per=1.5, type=commands.BucketType.user)
    async def duck(self, ctx):
        """ Posts a random duck """
        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://random-d.uk/api/v1/random') as r:
                r = await r.json()
        await ctx.send(embed=discord.Embed(color=self.bot.embed_color).set_image(url=r['url']))

    @commandExtra(category="Nsfw") 
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def phcomment(self, ctx, *, comment: commands.clean_content(fix_channel_mentions=True, use_nicknames=True, escape_markdown=True)):
        """PronHub Comment Image"""
        await ctx.trigger_typing()
        comment = comment.replace("&", "%26")
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f"https://nekobot.xyz/api/imagegen?type=phcomment"
                              f"&image={ctx.author.avatar_url_as(format='png')}"
                              f"&text={comment}&username={ctx.author.name}") as r:
                res = await r.json()
        if not res["success"]:
            return await ctx.send(get_text(ctx.guild, "images", "images.image_fail"))
        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=res["message"])
        await ctx.send(embed=embed)

    @commandExtra(category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tweet(self, ctx, username: str, *, text: str):
        """Tweet as someone."""
        await ctx.trigger_typing()
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://nekobot.xyz/api/imagegen?type=tweet"
                              "&username=%s"
                              "&text=%s" % (username, text,)) as r:
                res = await r.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=res["message"])
        await ctx.send(embed=embed)

    @commandExtra(category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clyde(self, ctx, *, text: str):
        """Make clyde say something"""
        await ctx.trigger_typing()
        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://nekobot.xyz/api/imagegen?type=clyde&text=%s" % text) as r:
                res = await r.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=res["message"])
        await ctx.send(embed=embed)

    @commandExtra(category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def threats(self, ctx, user):
        """Biggest threats to society"""
        img = await self.__get_image(ctx, user)
        await ctx.trigger_typing()
        if not isinstance(img, str):
            return img

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://nekobot.xyz/api/imagegen?type=threats&url=%s" % img) as r:
                res = await r.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=res["message"])
        await ctx.send(embed=embed)


    @commandExtra(category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deepfry(self, ctx, user = None):
        """Deepfry a user"""
        img = await self.__get_image(ctx, user)
        await ctx.trigger_typing()
        if not isinstance(img, str):
            return img

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://nekobot.xyz/api/imagegen?type=deepfry&image=%s" % img) as r:
                res = await r.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=res["message"])
        await ctx.send(embed=embed)


    @commandExtra(category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def magik(self, ctx, user = None, intensity:int=5):
        """Magikify a member"""
        img = await self.__get_image(ctx, user)
        await ctx.trigger_typing()
        if not isinstance(img, str):
            return img

        async with aiohttp.ClientSession() as cs:
            async with cs.get(f"https://nekobot.xyz/api/imagegen?type=magik&image={img}&intensity={intensity}") as r:
                res = await r.json()

        embed = discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=res["message"])
        await ctx.send(embed=embed)

    @commandExtra(hidden=True, category="Hidden")
    async def rainbowline(self, ctx):
        e=discord.Embed(color=0x36393E)
        e.set_image(url="https://cdn.discordapp.com/attachments/537583728948674580/538691432719056926/1273.gif")
        await ctx.send(embed=e)


def setup(bot):
	bot.add_cog(Images(bot))
