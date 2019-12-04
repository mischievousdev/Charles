import discord
import asyncio
import aiohttp
import random
import secrets
import shlex
import json
import re
import io
import zlib
import os
import mtranslate
import lxml.etree as etree

from discord.ext import commands
from utils import default, checks, permissions
from utils import Nullify
from utils import FuzzySearch
from utils import cache
from utils.default import commandExtra, groupExtra, commandsPlus, GroupPlus
from utils.testing import changePNGColor
from utils.translate import get_text


class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode('utf-8')

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b''
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b'\n')
            while pos != -1:
                yield buf[:pos].decode('utf-8')
                buf = buf[pos + 1:]
                pos = buf.find(b'\n')


def to_keycap(c):
    return '\N{KEYCAP TEN}' if c == 10 else str(c) + '\u20e3'

class utility(commands.Cog, name="Utility"):
    def __init__(self, bot, language_file = "db/Languages.json"):
        self.bot = bot
        self.icon = "<:charlesWorker:615429082397671424>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615429082397671424.png"
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

        #// FOR TRANSLATE \\#
        if os.path.exists(language_file):
            f = open(language_file,'r')
            filedata = f.read()
            f.close()
            self.languages = json.loads(filedata)
        else:
            self.languages = []
            print("No {}!".format(language_file))

    async def bot_check(self, ctx):
        if ctx.author == self.bot.owner:
            return True

        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            d = json.load(f)

        if ctx.command.name == "help":
            return True

        if d["Guild_Info"]["Modules"][ctx.command.cog_name]["Toggle"] == False:
            return False

        if isinstance(ctx.command, commandsPlus) or isinstance(ctx.command, GroupPlus):
            if d["Guild_Info"]["Modules"][ctx.command.cog_name]["Categories"][ctx.command.category] == False:
                return False
            else:
                return True

        else:
            return True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open(f'db/guilds/{payload.guild_id}.json', 'r') as f:
            d = json.load(f)

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if str(payload.message_id) in d["RR"]:
            if str(payload.emoji) in d["RR"][str(payload.message_id)]:
                role = guild.get_role(d["RR"][str(payload.message_id)][str(payload.emoji)])
                await user.add_roles(role) 

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        with open(f'db/guilds/{payload.guild_id}.json', 'r') as f:
            d = json.load(f)

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if str(payload.message_id) in d["RR"]:
            if str(payload.emoji) in d["RR"][str(payload.message_id)]:
                role = guild.get_role(d["RR"][str(payload.message_id)][str(payload.emoji)])
                await user.remove_roles(role) 

    @commands.has_permissions(manage_messages=True, manage_roles=True)
    @commandExtra(aliases=['reactionrole', 'rr'], category="Utility")
    async def reactionroles(self, ctx):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as r:
            d = json.load(r)

        embed_opt = False

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Do you want to use an existing message or do you want me to make a new one? `new` | `existing`")

        msg_opt = False
        check1 = False
        while check1 != True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)

                if msg.content.lower() == "new":
                    await ctx.send("Ok, I'll make a new one!", delete_after=5)
                    msg_opt = True
                    check1 = True
                elif msg.content.lower() == "existing":
                    await ctx.send("Alright, let's use an existing message.", delete_after=5)
                    check1 = True
                else:
                    await ctx.send("Invalid option given, please try again.", delete_after=5)

            except asyncio.TimeoutError:
                return await ctx.send("Timed out, cancelling command.")

        if msg_opt == True:
            await ctx.send("Do you want it in an embed? `yes` | `no`\n\n*if you choose for embed, the roles will be mentions as they don't ping in an embed. In a normal message it will be the role name.*")

            check2 = False
            while check2 != True:
                try:
                    embed = await self.bot.wait_for('message', check=check, timeout=60)

                    if embed.content.lower() == "yes":
                        await ctx.send("Ok, great!", delete_after=5)
                        embed_opt = True
                        check2 = True
                    elif embed.content.lower() == "no":
                        await ctx.send("Alright, normal message it is.", delete_after=5)
                        check2 = True
                    else:
                        await ctx.send("Invalid option given, please try again.", delete_after=5)

                except asyncio.TimeoutError:
                    return await ctx.send("Timed out, cancelling command.")
        else:
            pass

        done = False
        emoji_check = False
        role_check = True

        emoji_dict = {}
        addmsg = ""

        while done != True:
            try:
                if len(emoji_dict) == 20:
                    done = True
                else:
                    await ctx.send(f"Please send **one** emoji you want to use! {addmsg}")
                    emoji_check = False
                    role_check = True
                    emoji_msg = await self.bot.wait_for('message', check=check, timeout=60)

                if emoji_msg.content.lower() == "cancel" and len(emoji_dict) >= 1:
                    await ctx.send("Alright, so that's all set up now.", delete_after=5)
                    done = True

                if emoji_msg.content in emoji_dict.keys():
                    await ctx.send("Already using that emoji for reaction roles in this message!", delete_after=5)
                    emoji_check = True


                if done != True and emoji_check != True and role_check != False:
                    try:
                        await emoji_msg.add_reaction(str(emoji_msg.content))
                        await ctx.send("Ok, let's use that emoji!", delete_after=5)

                        try:
                            await ctx.send("Now please send the role name/mention/id for the role you want to set for that emoji.")
                            role_msg = await self.bot.wait_for('message', check=check, timeout=60)

                            role = await commands.RoleConverter().convert(ctx, role_msg.content)

                            if role.id in emoji_dict.values():
                                await ctx.send("Already using that role for reaction roles in this message, please try again.", delete_after=5)
                                role_check = False

                            if role_check != False:
                                if role.position >= ctx.guild.me.top_role.position:
                                    await ctx.send("I could not set that as a reaction role. The position of that role is higher than or equal to my top role!", delete_after=5)
                                else:
                                    await ctx.send(f"The role `{role.name}` has been set as reaction role for {str(emoji_msg.content)}")
                                    emoji_dict[str(emoji_msg.content)] = role.id

                                    if addmsg == "":
                                        addmsg += "Say `cancel` if you're done"

                        except asyncio.TimeoutError:
                            return await ctx.send("Timed out, cancelling command.")

                        except Exception:
                            await ctx.send("I could not find that role. Restarting...", delete_after=5)

                    except Exception:
                        await ctx.send("I could not find that emoji, make sure I am in the same server this emoji is from!", delete_after=5)

            except asyncio.TimeoutError:
                return await ctx.send("Timed out, cancelling command.")

        total = ""
        for k, v in emoji_dict.items():
            total += f"{k} | <@&{v}>\n"

        await ctx.send(content="Here's the result:", embed=discord.Embed(color=0x36393E, description=total))

        await asyncio.sleep(2)

        if msg_opt == True:

            await ctx.send("Please send the channel mention/ID/name where you want the message to be.")
            check3 = False
            while check3 != True:
                try:
                    chan_msg = await self.bot.wait_for('message', check=check, timeout=60)
                    channel = await commands.TextChannelConverter().convert(ctx, chan_msg.content)
                    
                    if channel != None:
                        if channel.permissions_for(ctx.guild.me).send_messages == True:
                            await ctx.send(f"Alright, message will be sent to {channel.mention}!", delete_after=5)
                            check3 = True
                        else:
                            await ctx.send("I do not have permissions to send messages in that channel.", delete_after=5)
                    else:
                        await ctx.send("I could not find that channel.", delete_after=5)

                except asyncio.TimeoutError:
                    return await ctx.send("Timed out, cancelling command.")

                except Exception:
                    await ctx.send("I could not find that channel, please try again.", delete_after=5)

            if embed_opt == True:

                await ctx.send("If you want to set a custom title for the embed, please say it now. Say \"None\" to set it to the default title (\"Reaction Roles\").")
                try:
                    title_msg = await self.bot.wait_for('message', check=check, timeout=60)
                    if title_msg.content.lower() == "none":
                        title = "Reaction Roles"
                    else:
                        title = title_msg.content
                except asyncio.TimeoutError:
                    return await ctx.send("Timed out, cancelling command.")

                e = discord.Embed(color=self.bot.embed_color, title=title)
                e.set_footer(text="React with an emoji to get the corresponding role!")
                e.description = total
                rrmsg = await channel.send(embed=e)
                for k in emoji_dict.keys():
                    await rrmsg.add_reaction(k)

            elif embed_opt == False:
                msg = "React with an emoji to get the corresponding role!\n\n"
                for k, v in emoji_dict.items():
                    msg += f"{k} | {ctx.guild.get_role(v).name}\n"
                rrmsg = await channel.send(msg)
                for k in emoji_dict.keys():
                    await rrmsg.add_reaction(k)

        elif msg_opt == False:
            await ctx.send("Please send the **channel ID/mention/name** of the channel the message is in you want to use for these reaction roles!")
            check4 = False
            while check4 != True:
                try:
                    chan_msg = await self.bot.wait_for('message', check=check, timeout=60)
                    channel = await commands.TextChannelConverter().convert(ctx, chan_msg.content)
                    
                    if channel != None:
                        await ctx.send(f"Alright, message will be fetched from {channel.mention}!", delete_after=5)
                        check4 = True
                    else:
                        await ctx.send("I could not find that channel.", delete_after=5)

                except asyncio.TimeoutError:
                    return await ctx.send("Timed out, cancelling command.")

                except Exception:
                    await ctx.send("I could not find that channel, please try again.", delete_after=5)

            await ctx.send("Now please send the **message ID** from the message you want to use for reaction roles!")
            check5 = False
            while check5 != True:
                try:
                    message_msg = await self.bot.wait_for('message', check=check, timeout=60)
                    rrmsg = await channel.fetch_message(int(message_msg.content))
                    
                    if rrmsg != None:
                        if str(rrmsg.id) in d["RR"]:
                            await ctx.send("I can not use that message for reaction roles as it already is being used for reaction roles!", delete_after=5)
                        else:
                            await ctx.send(f"Alright, I will use that message for reaction roles!", delete_after=5)
                            check5 = True
                    else:
                        await ctx.send(f"I could not find that message in {channel.mention}...", delete_after=5)

                except asyncio.TimeoutError:
                    return await ctx.send("Timed out, cancelling command.")

                except Exception:
                    await ctx.send("I could not find that message, please try again.", delete_after=5)

            for k in emoji_dict.keys():
                await rrmsg.add_reaction(k)

        await ctx.send("Everything has been set up, reaction roles are now set up!")
        d["RR"][str(rrmsg.id)] = emoji_dict

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as r:
            json.dump(d, r, indent=4)

    @commandExtra(category="Utility")
    async def tinyurl(self, ctx, *, link: str):
        '''Makes a link shorter using the tinyurl api'''
        url = link.strip("<>")
        url = 'http://tinyurl.com/api-create.php?url=' + url
        async with self.session.get(url) as resp:
            new = await resp.text()
        emb = discord.Embed(color=discord.Color.blurple())
        emb.add_field(name=get_text(ctx.guild, "utility", "utility.tu_original"), value=link, inline=False)
        emb.add_field(name=get_text(ctx.guild, "utility", "utility.tu_short"), value=new, inline=False)
        emb.set_footer(text=get_text(ctx.guild, "utility", "utility.tu_ref"), icon_url='http://cr-api.com/static/img/branding/cr-api-logo.png')
        await ctx.send(embed=emb)
        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            pass

    @commandExtra(category="Colors")
    async def randomcolor(self, ctx):
        r = lambda: random.randint(0,255)
        color = f"{f'{r():x}':0>2}{f'{r():x}':0>2}{f'{r():x}':0>2}"

        embed=discord.Embed(color=discord.Color(int(f"0x{color}", 16)))

        embed.add_field(name="Hex", value=f"#{color}")

        changePNGColor("db/images/circle.png", "#FFFFFF", f"#{color}")

        lv = len(color)
        rgb_color = tuple(int(color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        embed.add_field(name="RGB", value=rgb_color, inline=False)

        f = discord.File(f"db/images/{color}.png", filename="image.png")
        embed.set_thumbnail(url="attachment://image.png")
        info_cmd = f"{ctx.prefix}colorinfo #{color}"
        embed.set_footer(text=get_text(ctx.guild, "utility", "utility.random_col").format(str(info_cmd)))

        await ctx.send(file=f, embed=embed)
        os.remove(f"db/images/{color}.png")

    @commandExtra(category="Colors")
    async def colorinfo(self, ctx, color):
        color = color.strip('#')

        changePNGColor("db/images/normal-circle.png", "#FFFFFF", f"#{color}")

        embed=discord.Embed()

        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'http://thecolorapi.com/id?hex={color}') as r:
                res = await r.json()

                hex = res['hex']['value']
                rgb = f"({res['rgb']['r']}, {res['rgb']['g']}, {res['rgb']['b']})"
                hsl = f"({res['hsl']['h']}, {res['hsl']['s']}%, {res['hsl']['l']}%)"
                hsv = f"({res['hsv']['h']}, {res['hsv']['s']}%, {res['hsv']['v']}%)"
                name = res['name']['value']
                cmyk = f"({res['cmyk']['c']}, {res['cmyk']['m']}, {res['cmyk']['y']}, {res['cmyk']['k']})"
                xyz = f"({res['XYZ']['X']}, {res['XYZ']['Y']}, {res['XYZ']['Z']})"

        f = discord.File(f"db/images/{color}.png", filename="image.png")
        embed.set_thumbnail(url="attachment://image.png")

        embed.title = name
        embed.color = discord.Color(int(f"0x{color}", 16))
        embed.add_field(name="Hex", value=hex)
        embed.add_field(name="rgb", value=rgb)
        embed.add_field(name="cmyk", value=cmyk)
        embed.add_field(name="hsv", value=hsv)
        embed.add_field(name="hsl", value=hsl)
        embed.add_field(name="XYZ", value=xyz)

        await ctx.send(embed=embed, file=f)
        os.remove(f"db/images/{color}.png")

    @commands.is_nsfw()
    @commandExtra(category="Utility") 
    @commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
    async def urban(self, ctx, *, search: str):
        """ Find the 'best' definition to your words """

        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'http://api.urbandictionary.com/v0/define?term={search}') as r:
                url = await r.json()

        if url is None:
            return await ctx.send(get_text(ctx.guild, "utility", "utility.ud_broken"))

        count = len(url['list'])
        if count == 0:
            return await ctx.send(get_text(ctx.guild, "utility", "utility.ud_none"))
        result = url['list'][random.randint(0, count - 1)]

        definition = result['definition']
        if len(definition) >= 1000:
                definition = definition[:1000]
                definition = definition.rsplit(' ', 1)[0]
                definition += '...'

        with open(f'db/guilds/{str(ctx.guild.id)}.json', "r") as f:
            jdata = json.load(f)

        lang_code = str(jdata["Guild_Info"]["Language"]).lower()

        definition = mtranslate.translate(str(definition), lang_code, "en")
        example = mtranslate.translate(str(result['example']), lang_code, "en")

        embed = discord.Embed(colour=self.bot.embed_color, description=f"**{result['word']}**\n*by: {result['author']}*")
        embed.add_field(name=get_text(ctx.guild, "utility", "utility.ud_definition"), value=definition, inline=False)
        embed.add_field(name=get_text(ctx.guild, "utility", "utility.ud_example"), value=example, inline=False)
        embed.set_footer(text=f"\U0001f44d {result['thumbs_up']} | \U0001f44e {result['thumbs_down']}")

        await ctx.send(embed=embed)

    @commandExtra(category="Utility")
    async def password(self, ctx):
        """ Generates a random password string for you """
        if hasattr(ctx, 'guild') and ctx.guild is not None:
            await ctx.send(get_text(ctx.guild, "utility", "utility.pw_confirm").format(ctx.author.name))
        await ctx.author.send(f"\U0001f381 " + get_text(ctx.guild, "utility", "utility.pw").format(secrets.token_urlsafe(18))) 



    @commandExtra(category="Polls")
    async def poll(self, ctx, *, questions_and_choices: str):
        """
        delimit questions and answers by either | or ,
        supports up to 10 choices
        """
        if "|" in questions_and_choices:
            delimiter = "|"
        elif "," in questions_and_choices:
            delimiter = ","
        else:
            delimiter = None
        if delimiter is not None:
            questions_and_choices = questions_and_choices.split(delimiter)
        else:
            questions_and_choices = shlex.split(questions_and_choices)

        if len(questions_and_choices) < 3:
            return await ctx.send(get_text(ctx.guild, "utility", "utility.poll_short"))
        elif len(questions_and_choices) > 11:
            return await ctx.send(get_text(ctx.guild, "utility", "utility.poll_long"))

        question = questions_and_choices[0]
        choices = [(f"`{e}.`", v)
                   for e, v in enumerate(questions_and_choices[1:], 1)]
        reactions = [(to_keycap(e), v)
                     for e, v in enumerate(questions_and_choices[1:], 1)]

        try:
            await ctx.message.delete()
        except:
            pass

        answer = '\n'.join('%s %s' % t for t in choices)

        embed = discord.Embed(color=self.bot.embed_color, title=question.replace("@", "@\u200b"), description=answer.replace("@", "@\u200b"))
        embed.set_author(icon_url=ctx.author.avatar_url, name=get_text(ctx.guild, "utility", "utility.poll_by").format(ctx.author)) 
        poll = await ctx.send(embed=embed)
        for emoji, _ in reactions:
            await poll.add_reaction(emoji)

    @commandExtra(category="Polls")
    async def strawpoll(self, ctx, *, question_and_choices: str=None):
        """
        Usage: !strawpoll my question | answer a | answer b | answer c\nAt least two answers required.
        """
        if "|" in question_and_choices:
            delimiter = "|"
        else:
            delimiter = ","
        question_and_choices = question_and_choices.split(delimiter)
        if len(question_and_choices) == 1: 
            return await ctx.send(get_text(ctx.guild, "utility", "utility.spoll_short"))
        elif len(question_and_choices) >= 31:
            return await ctx.send(get_text(ctx.guild, "utility", "utility.spoll_long"))
        question, *choices = question_and_choices
        choices = [x.lstrip() for x in choices]
        print(choices)
        header = {"Content-Type": "application/json"}
        payload = {
            "title": question,
            "options": choices,
            "multi": False
        }
        print(payload)
        async with self.session.post("https://www.strawpoll.me/api/v2/polls", headers=header, json=payload) as r:
            data = await r.json()
        print(data)
        link = "http://www.strawpoll.me/" + str(data["id"])

        embed=discord.Embed(color=self.bot.embed_color, title=question, description=get_text(ctx.guild, "utility", "utility.spoll_link").format(link))
        embed.set_footer(icon_url="https://cdn.discordapp.com/attachments/562784997962940476/611338971468923113/20190815_012238.png", text=get_text(ctx.guild, "utility", "utility.spoll_ref"))
        await ctx.send(embed=embed)



    @commandExtra(category="Utility")
    async def hastebin(self, ctx, *, code):
        '''Hastebin-ify your code!'''
        if code.startswith('```') and code.endswith('```'):
            code = code[3:-3]
        else:
            code = code.strip('` \n')
        async with aiohttp.ClientSession() as cs:
            async with cs.post("https://hastebin.com/documents", data=code) as resp:
                data = await resp.json()
                key = data['key']
        embed = discord.Embed(color=self.bot.embed_color, title=get_text(ctx.guild, "utility", "utility.hb_upload"), description=f"https://hastebin.com/{key}") 
        embed.set_footer(icon_url="https://cdn.discordapp.com/attachments/562784997962940476/611010770603343872/twitter_400x400.png", text=get_text(ctx.guild, "utility", "utility.hb_ref"))
        await ctx.send(embed=embed)

    @commandExtra(category="Utility", aliases=['translate'])
    async def tr(self, ctx, *, translate):
        """Translate some stuff!  Takes a phrase, the from language identifier (optional), and the to language identifier.
        To see a number of potential language identifiers, use the langlist command.

        If you do not specify the from language, Google translate will attempt to automatically determine it."""

        # Check if we're suppressing @here and @everyone mentions
        suppress = True

        word_list = translate.split(" ")

        if len(word_list) < 2:
            return await ctx.send(embed=discord.Embed(title=get_text(ctx.guild, "utility", "utility.tr_error"),description=get_text(ctx.guild, "utility", "utility.tr_notfound"),color=self.bot.embed_color))

        lang = word_list[len(word_list)-1]
        from_lang = word_list[len(word_list)-2] if len(word_list) >= 3 else "auto"

        # Get the from language
        from_lang_back = [ x for x in self.languages if x["code"].lower() == from_lang.lower() ]
        from_lang_code = from_lang_back[0]["code"] if len(from_lang_back) else "auto"
        from_lang_name = from_lang_back[0]["name"] if len(from_lang_back) else get_text(ctx.guild, "utility", "utility.tr_auto")
        # Get the to language
        lang_back = [ x for x in self.languages if x["code"].lower() == lang.lower() ]
        lang_code = lang_back[0]["code"] if len(lang_back) else None
        lang_name = lang_back[0]["name"] if len(lang_back) else None

        # Translate all but our language codes
        if len(word_list) > 2 and word_list[len(word_list)-2].lower() == from_lang_code.lower():
            trans = " ".join(word_list[:-2])
        else:
            trans = " ".join(word_list[:-1])
        
        if not lang_code:
            return await ctx.send(embed=discord.Embed(title=get_text(ctx.guild, "utility", "utility.tr_error"),description=get_text(ctx.guild, "utility", "utility.tr_notfound"),color=self.bot.embed_color))

        result = mtranslate.translate(trans, lang_code, from_lang_code)
        
        if not result:
            return await ctx.send(embed=discord.Embed(title=get_text(ctx.guild, "utility", "utility.tr_error"),description=get_text(ctx.guild, "utility", "utility.tr_notrans"),color=self.bot.embed_color))
        
        if result == trans:
                # We got back what we put in...
                return await ctx.send(embed=discord.Embed(title=get_text(ctx.guild, "utility", "utility.tr_error"), description=get_text(ctx.guild, "utility", "utility.tr_sametrans"), color=self.bot.embed_color))


        # Check for suppress
        if suppress:
            result = Nullify.clean(result)

        embed=discord.Embed(color=self.bot.embed_color, title=f"{from_lang_name} --> {lang_name}", description=result)
        embed.set_footer(icon_url="https://cdn.discordapp.com/attachments/562784997962940476/611346692549378068/gtr.png", text=get_text(ctx.guild, "utility", "utility.tr_ref"))

        await ctx.send(embed=embed)


    def parse_object_inv(self, stream, url):
        # key: URL
        # n.b.: key doesn't have `discord` or `discord.ext.commands` namespaces
        result = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != '# Sphinx inventory version 2':
            raise RuntimeError('Invalid objects.inv file version.')

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if 'zlib' not in line:
            raise RuntimeError('Invalid objects.inv file, not z-lib compatible.')

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(':')
            if directive == 'py:module' and name in result:
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue

            # Most documentation pages have a label
            if directive == 'std:doc':
                subdirective = 'label'

            if location.endswith('$'):
                location = location[:-1] + name

            key = name if dispname == '-' else dispname
            prefix = f'{subdirective}:' if domain == 'std' else ''

            if projname == 'discord.py':
                key = key.replace('discord.ext.commands.', '').replace('discord.', '')

            result[f'{prefix}{key}'] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            sub = cache[key] = {}
            async with self.session.get(page + '/objects.inv') as resp:
                if resp.status != 200:
                    raise RuntimeError('Cannot build rtfm lookup table, try again later.')

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, ctx, key, obj):
        page_types = {
            'latest': 'https://discordpy.readthedocs.io/en/latest',
            'python': 'https://docs.python.org/3'
        }

        if obj is None:
            await ctx.send(page_types[key])
            return

        if not hasattr(self, '_rtfm_cache'):
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        obj = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)

        if key == 'latest':
            pit_of_success_helpers = {
                'vc': 'VoiceClient',
                'msg': 'Message',
                'color': 'Colour',
                'perm': 'Permissions',
                'channel': 'TextChannel',
                'chan': 'TextChannel',
            }

            # point the abc.Messageable types properly:
            q = obj.lower()
            for name in dir(discord.abc.Messageable):
                if name[0] == '_':
                    continue
                if q == name:
                    obj = f'abc.Messageable.{name}'
                    break

            def replace(o):
                return pit_of_success_helpers.get(o.group(1), '')

            pattern = re.compile('|'.join(fr'(?:^({k})$|({k})\.)' for k in pit_of_success_helpers.keys()))
            obj = pattern.sub(replace, obj)

        cache = list(self._rtfm_cache[key].items())
        def transform(tup):
            return tup[0]

        matches = FuzzySearch.finder(obj, cache, key=lambda t: t[0], lazy=False)[:15]

        e = discord.Embed(colour=self.bot.embed_color)
        if len(matches) == 0:
            return await ctx.send('Could not find anything. Sorry.')

        e.title = "Documentation search results:"
        e.set_author(icon_url=ctx.author.avatar_url, name=ctx.author.display_name)
        e.description = '\n'.join(f'[{key}]({url})' for key, url in matches)
        await ctx.send(embed=e)

    @commands.is_owner()
    @groupExtra(aliases=['rtd'], invoke_without_command=True, hidden=True, category="Hidden")
    async def rtfm(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a discord.py entity.

        Events, objects, and functions are all supported through a
        a cruddy fuzzy algorithm.
        """
        await self.do_rtfm(ctx, 'latest', obj)

    @rtfm.command(name='python', aliases=['py'])
    async def rtfm_python(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a Python entity."""
        await self.do_rtfm(ctx, 'python', obj)

    @commandExtra(category="Fonts", name='aesthetics', aliases=['ae'])
    async def _aesthetics(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        aesthetic_space = '\u3000'
        aesthetic_punctuation = "§½！\"＃¤％＆／（）＝？`´＠£＄€｛［］｝＼＾¨~＇＊＜＞|，．－＿："
        aesthetic_lowercase = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ１２３４５６７８９０"
        aesthetic_uppercase = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += aesthetic_lowercase[alphabet[letter]]
                elif letter in uppercase_alphabet:
                    returnthis += aesthetic_uppercase[uppercase_alphabet[letter]]
                elif letter in punctuation:
                    returnthis += aesthetic_punctuation[punctuation[letter]]
                elif letter == space:
                    returnthis += aesthetic_space
                else:
                    returnthis += letter
        await ctx.send(returnthis)

    @commandExtra(category="Fonts", name='fraktur')
    async def _fraktur(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        uppercase_fraktur = "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"
        lowercase_fraktur = "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷1234567890"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += lowercase_fraktur[alphabet[letter]]
                elif letter in uppercase_alphabet:
                    returnthis += uppercase_fraktur[uppercase_alphabet[letter]]
                elif letter == space:
                    returnthis += " "
                else:
                    returnthis += letter
        await ctx.send(returnthis)

    @commandExtra(category="Fonts", name='boldfaktur')
    async def _boldfaktur(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        uppercase_boldfraktur = "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅"
        lowercase_boldfraktur = "𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟1234567890"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += lowercase_boldfraktur[alphabet[letter]]
                elif letter in uppercase_alphabet:
                    returnthis += uppercase_boldfraktur[uppercase_alphabet[letter]]
                elif letter == space:
                    returnthis += " "
                else:
                    returnthis += letter
        await ctx.send(returnthis)

    @commandExtra(category="Fonts", name='fancy', aliases=['ff'])
    async def _fancy(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        fancy_lowercase = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫𝟢"
        fancy_uppercase ="𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += fancy_lowercase[alphabet[letter]]
                elif letter in uppercase_alphabet:
                    returnthis += fancy_uppercase[uppercase_alphabet[letter]]
                elif letter == space:
                    returnthis += " "
                else:
                    returnthis += letter
        await ctx.send(returnthis)

    @commandExtra(category="Fonts", name='boldfancy', aliases=['bf'])
    async def _bold_fancy(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        bold_fancy_lowercase = "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃1234567890"
        bold_fancy_uppercase = "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += bold_fancy_lowercase[alphabet[letter]]
                elif letter in uppercase_alphabet:
                    returnthis += bold_fancy_uppercase[uppercase_alphabet[letter]]
                elif letter == space:
                    returnthis += " "
                else:
                    returnthis += letter
        await ctx.send(returnthis)

    @commandExtra(category="Fonts", name='double', aliases=['ds'])
    async def _doublestruck(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        double_uppercase = "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
        double_lowercase = "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡𝟘"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += double_lowercase[alphabet[letter]]
                elif letter in uppercase_alphabet:
                    returnthis += double_uppercase[uppercase_alphabet[letter]]
                elif letter == space:
                    returnthis += " "
                else:
                    returnthis += letter
        await ctx.send(returnthis)

    @commandExtra(category="Fonts", name='smallcaps', aliases=['sc'])
    async def _smallcaps(self, ctx, *, sentence: str):
        returnthis = ""

        alphabet = dict(zip("abcdefghijklmnopqrstuvwxyz1234567890", range(0, 36)))
        uppercase_alphabet = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(0, 26)))
        punctuation = dict(zip("§½!\"#¤%&/()=?`´@£$€{[]}\\^¨~'*<>|,.-_:", range(0, 37)))
        space = " "
        smallcaps_alphabet = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ1234567890"

        for word in sentence:
            for letter in word:
                if letter in alphabet:
                    returnthis += smallcaps_alphabet[alphabet[letter]]
                else:
                    returnthis += letter
        await ctx.send(returnthis)

def setup(bot):
    bot.add_cog(utility(bot))
