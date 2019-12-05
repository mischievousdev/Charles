import discord
import asyncio
import random
import aiohttp
import os
import json

from discord.ext import commands
from datetime import datetime
from PIL import Image
from io import BytesIO
from utils.default import commandExtra, groupExtra
from utils.translate import get_text

class Fun(commands.Cog, name='Fun'):
    def __init__(self, bot):
        self.bot = bot
        self.icon = "<:charlesClown:615429008745693184>"
        self.big_icon = "https://cdn.discordapp.com/emojis/615429008745693184.png"

    @commandExtra(category="Games", hidden=True)
    async def wtp(self, ctx):
        poke_id = random.randint(1, 802)

        # Check if we've already had this pokemon
        if os.path.exists(f'db/images/pokemon/bw/{str(poke_id)}.png'):
            # Good, then we dont need to make the image again!
            file_bw = discord.File(fp=f'db/images/pokemon/bw/{str(poke_id)}.png', filename="wtp.png")

        else:
            # Crap, haven't had this one before...

            # Open the background
            with open("db/images/pokemon/wtp_bg.png", "rb") as f:
                bg_img_bw = Image.open(BytesIO(f.read()))

            # Background width/height
            bg_w, bg_h = bg_img_bw.size

            # Open the pokemon image
            with open(f"db/images/pokemon/{str(poke_id)}.png", "rb") as f:
                poke_img_bw = Image.open(BytesIO(f.read()))

            # Pokemon width/height
            poke_w, poke_h = poke_img_bw.size

            # Resize it so it looks better
            poke_img_bw = poke_img_bw.resize((poke_w*2, poke_h*2))

            # Now let's make it blue
            pix = poke_img_bw.load()
            for y in range(poke_img_bw.size[1]):
                for x in range(poke_img_bw.size[0]):
                    if pix[x, y] == (0, 0, 0 ,0):
                        continue
                    else:
                        pix[x, y] = (3, 80, 126)

            # Now calculate where to paste it
            paste_w = int((bg_w - poke_w) / 8)
            paste_h = int((bg_h - poke_h) / 4)

            # Now we can paste it
            bg_img_bw.paste(poke_img_bw, (paste_w, paste_h), poke_img_bw)

            # Save it for later so we dont need to make this image again
            bg_img_bw.save(f'db/images/pokemon/bw/{str(poke_id)}.png')

            buf_bw = BytesIO()
            bg_img_bw.save(buf_bw, "png")
            buf_bw.seek(0)
            bg_img_bw.close()

            # Now we got our file
            file_bw = discord.File(fp=buf_bw, filename="wtp.png")

        if os.path.exists(f'db/images/pokemon/col/{str(poke_id)}.png'):
            # Good, then we dont need to make the image again!
            file_col = discord.File(fp=f'db/images/pokemon/col/{str(poke_id)}.png', filename="wtp.png")

        else:
            # Open the background
            with open("db/images/pokemon/wtp_bg.png", "rb") as f:
                bg_img_col = Image.open(BytesIO(f.read()))

            # Background width/height
            bg_w, bg_h = bg_img_col.size

            # Open the pokemon image
            with open(f"db/images/pokemon/{str(poke_id)}.png", "rb") as f:
                poke_img_col = Image.open(BytesIO(f.read()))

            # Pokemon width/height
            poke_w, poke_h = poke_img_col.size

            # Resize it so it looks better
            poke_img_col = poke_img_col.resize((poke_w*2, poke_h*2))

            # Now calculate where to paste it
            paste_w = int((bg_w - poke_w) / 8)
            paste_h = int((bg_h - poke_h) / 4)

            # Now we can paste it
            bg_img_col.paste(poke_img_col, (paste_w, paste_h), poke_img_col)

            # Save it for later so we dont need to make this image again
            bg_img_col.save(f'db/images/pokemon/col/{str(poke_id)}.png')

            buf_col = BytesIO()
            bg_img_col.save(buf_col, "png")
            buf_col.seek(0)
            bg_img_col.close()

            # Now we got our file
            file_col = discord.File(fp=buf_col, filename="wtp.png")


        with open("db/pokemon.json", "r") as f:
            data = json.load(f)

        attempts = 0

        emb = discord.Embed(color=self.bot.embed_color)
        emb.description = get_text(ctx.guild, 'fun', 'fun.wtp.guess')
        emb.set_author(icon_url="https://cdn.discordapp.com/attachments/562784997962940476/631940950704259082/pokeball-logo-DC23868CA1-seeklogo.com.png",
                       name=get_text(ctx.guild, 'fun', 'fun.wtp.wtp'))
        emb.set_image(url="attachment://wtp.png")
        emb.set_footer(text=get_text(ctx.guild, 'fun', 'fun.wtp.footer').format(str("cancel")))
        msg = await ctx.send(content=get_text(ctx.guild, 'fun', 'fun.wtp.attempts').format(str(attempts)),
                             embed=emb,
                             file=file_bw)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        while attempts != 3:

            try:

                attempt = await self.bot.wait_for('message', check=check, timeout=30.0)

                if attempt.content.lower() == "cancel" or attempt.content.lower() == "'cancel'":
                    emb.description = get_text(ctx.guild, 'fun', 'fun.wtp.gave_up') + f" {str(data[str(poke_id)]).title()}"
                    emb.set_footer(text=discord.Embed.Empty)
                    await msg.delete()
                    attempts = 3
                    return await ctx.send(embed=emb, file=file_col)

                elif attempt.content.lower() == str(data[str(poke_id)]).lower():
                    emb.description = get_text(ctx.guild, 'fun', 'fun.wtp.correct').format(str(data[str(poke_id)]).title())
                    emb.set_footer(text=discord.Embed.Empty)
                    await msg.delete()
                    attempts = 3
                    return await ctx.send(embed=emb, file=file_col)

                elif attempt.content.lower() != str(data[str(poke_id)]).lower():
                    attempts += 1
                    await msg.edit(content=get_text(ctx.guild, 'fun', 'fun.wtp.attempts').format(str(attempts)))
                    #msg = await ctx.send(embed=emb, file=file_bw)

            except asyncio.TimeoutError:
                attempts = 3
                emb.description = get_text(ctx.guild, 'fun', 'fun.wtp.timeout') + f" {str(data[str(poke_id)]).title()}"
                await msg.delete()
                return await ctx.send(embed=emb, file=file_col)

            else:
                if attempts == 3:
                    try:
                        emb.description = get_text(ctx.guild, 'fun', 'fun.wtp.tma') + f" {str(data[str(poke_id)]).title()}"
                        await msg.delete()
                        return await ctx.send(embed=emb, file=file_col)
                    except asyncio.TimeoutError:
                        pass

    @commandExtra(category="Random", invoke_without_command=True)
    async def fact(self, ctx, choice=None):
        facts = ['koala', 'dog', 'cat', 'panda', 'fox', 'bird', 'racoon', 'kangaroo', 'elephant', 'whale', 'giraffe']
        if not choice.lower() in facts:
            return await ctx.send(f"You can get a random fact from the following animals:\n\n`{'` | `'.join(facts)}`\n\nUse the command like: `{ctx.prefix}fact animal`")

        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'https://some-random-api.ml/facts/{choice.lower()}') as r:
                res = await r.json()
                await ctx.send(res['fact'])

    @commandExtra(category="Funny")
    async def dadjoke(self, ctx):
        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://icanhazdadjoke.com/', headers={"Accept": "application/json"}) as r:
                res = await r.json()
                await ctx.send(res['joke'])

    @commandExtra(category="Random", aliases=['pokemon'])
    async def pokedex(self, ctx, *, pokemon):
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'https://some-random-api.ml/pokedex?pokemon={pokemon}') as r:
                res = await r.json()

        e = discord.Embed(color=self.bot.embed_color)
        e.title = f"{res['name']} (#{res['id']})"
        desc = f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.type')}:** {', '.join(res['type'])}\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.species')}:** {', '.join(res['species'])}\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.abilities')}:** {', '.join(res['abilities'])}\n\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.height')}:** {res['height']}\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.weight')}:** {res['weight']}\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.gender')}:** {' / '.join(res['gender'])}\n\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.exp')}:** {res['base_experience']}\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.egg')}:** {', '.join(res['egg_groups'])}\n\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.evo_stage')}:** {res['family']['evolutionStage']}\n"
        desc += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.evo_line')}:** {', '.join(res['family']['evolutionLine'])}"
        e.description = desc

        stats = f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.hp')}:** {res['stats']['hp']}\n"
        stats += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.atk')}:** {res['stats']['attack']}\n"
        def_fix = get_text(ctx.guild, 'fun', "fun.pokemon.'def")
        stats += f"**{def_fix}:** {res['stats']['defense']}\n"
        stats += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.sp_atk')}:** {res['stats']['sp_atk']}\n"
        stats += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.sp_def')}:** {res['stats']['sp_def']}\n"
        stats += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.speed')}:** {res['stats']['speed']}\n"
        stats += f"**{get_text(ctx.guild, 'fun', 'fun.pokemon.total')}:** {res['stats']['total']}"

        e.add_field(name=f"{get_text(ctx.guild, 'fun', 'fun.pokemon.stats')}:", value=stats)
           
        try:
            e.set_thumbnail(url=f"http://play.pokemonshowdown.com/sprites/xyani/{res['name']}.gif")
        except Exception:
            e.set_thumbnail(url=f"http://play.pokemonshowdown.com/sprites/xyani-shiny/{res['name']}.gif")
        e.set_footer(text=res['description'])

        await ctx.send(embed=e)

    @commandExtra(name="10s", category="Games")
    async def ten_sec(self, ctx):
        emb = discord.Embed(color=self.bot.embed_color, description=get_text(ctx.guild, 'fun', "fun.10s"))
        emb.set_author(icon_url=ctx.author.avatar_url, name=ctx.author)
        msg = await ctx.send(embed=emb)
        await msg.add_reaction('👍🏻')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '👍🏻'

        reaction, user = await self.bot.wait_for('reaction_add', check=check)
        begin = msg.created_at
        end = datetime.utcnow()
        final = end - begin
        result = f'{final.seconds}.'+f'{final.microseconds}'[:2]

        new_emb = msg.embeds[0]
        new_emb.description = get_text(ctx.guild, 'fun', "fun.10s_result").format(result)
        await msg.edit(embed=new_emb)


    @commandExtra(category="Funny")
    @commands.cooldown(rate=1, per=30, type=commands.BucketType.user)
    async def hack(self, ctx, user: discord.User):
        msg1 = await ctx.send(f"Hacking {user.display_name}'s IP-Address... <a:Smooth_Loading:470313388782911489>")
        await asyncio.sleep(3)
        newmsg1 = f"Found {user.display_name}'s IP-Address! <:tick:528774982067814441>"
        await msg1.edit(content=newmsg1)
        await asyncio.sleep(1)
        msg2 = await ctx.send(f"Locating {user.display_name}... <a:Smooth_Loading:470313388782911489>")
        await asyncio.sleep(3)
        newmsg2 = f"Found {user.display_name}'s location! <:tick:528774982067814441>"
        await msg2.edit(content=newmsg2)
        await asyncio.sleep(1)
        msg3 = await ctx.send(f"Scanning through {user.display_name}'s files... <a:Smooth_Loading:470313388782911489>")
        await asyncio.sleep(3)
        newmsg3 = f"Scanned all of {user.display_name}'s files! <:tick:528774982067814441>"
        await msg3.edit(content=newmsg3)
        await asyncio.sleep(1)
        msg4 = await ctx.send("Searching for useful information... <a:Smooth_Loading:470313388782911489>")
        await asyncio.sleep(3)
        newmsg4 = "Completed! <:tick:528774982067814441>"
        await msg4.edit(content=newmsg4)
        await asyncio.sleep(1)
        msg5 = await ctx.send("Loading search result... <a:Smooth_Loading:470313388782911489>")
        await asyncio.sleep(3)
        newmsg5 = "Here's what I found:"
        await msg5.edit(content=newmsg5)
        await asyncio.sleep(1)

        hackimg = random.choice([
            "https://cdn.discordapp.com/attachments/528778876839788555/528782200955600897/hack1.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782214792478740/hack2.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782227191103489/hack3.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782230391357450/hack4.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782235059486722/hack5.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782239581077514/hack6.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782246392627210/hack7.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782249567584257/hack8.jpg",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782254160347157/hack9.png",
            "https://cdn.discordapp.com/attachments/528778876839788555/528782260242219018/hack10.jpg"
        ])

#        ##shared_guilds = list([i for i in ctx.bot.guilds if i.get_member(user.id)])
#        ##guild_pick = random.choice(shared_guilds)
#        ##for guild in guild_pick:
#        for channel in ctx.guild.text_channels:
#            async for message in channel.history():
#                if message.author == user:
#                    if message.attachments:
#                        hackimg = message.attachments[0].url


        embed=discord.Embed(color=self.bot.embed_color)
        embed.set_image(url=hackimg)
        await ctx.send(embed=embed)


    @commandExtra(category="Funny")
    async def shoot(self, ctx, member: discord.User):
        """Allows the user to shoot a person of choice."""
        if member == self.bot.user:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811533029310466/525813424849158145/gun_dodge1.gif",
                "https://cdn.discordapp.com/attachments/525811533029310466/525813428519043082/gun_dodge2.gif",
                "https://cdn.discordapp.com/attachments/525811533029310466/525813412022976526/gun_dodge3.gif",
                "https://media.tenor.com/images/d0e49e6b1e3c2be4a73583b578bf3071/tenor.gif",
                "https://media.tenor.com/images/a8acf57b2653f46b914d9326f1f57568/tenor.gif",
                "https://media.tenor.com/images/4fbed315a9af5603f72a778fcf88d0b0/tenor.gif",
                "https://media.tenor.com/images/8d4e163b51fba8f0f65d2a6684f31920/tenor.gif",
                "https://media.tenor.com/images/0a14cac741d74d10bdc3dd1a69c23f58/tenor.gif",
                "https://media.tenor.com/images/658d08bea28ab2d7dd2ba062022139f1/tenor.gif",
                "https://media.tenor.com/images/ffa17c3325025301091c97beaacbe590/tenor.gif",
                "https://media.tenor.com/images/fd8ec6555604a86a90fe4af1734c48ac/tenor.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.shoot_bot").format(ctx.author.name)

        elif member == ctx.author:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811505568940032/525813015090823186/gun_suicide1.gif",
                "https://cdn.discordapp.com/attachments/525811505568940032/525812994467430400/gun_suicide2.gif",
                "https://cdn.discordapp.com/attachments/525811505568940032/525813015967432754/gun_suicide3.gif",
                "https://cdn.discordapp.com/attachments/525811505568940032/525813011483590658/gun_suicide4.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.shoot_self").format(ctx.author.name)

        else:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811461830737940/525812284220768256/gun_shooting1.gif",
                "https://cdn.discordapp.com/attachments/525811461830737940/525812297902325761/gun_shooting2.gif",
                "https://cdn.discordapp.com/attachments/525811461830737940/525812347512815637/gun_shooting3.gif",
                "https://cdn.discordapp.com/attachments/525811461830737940/525812321201946624/gun_shooting4.gif",
                "https://cdn.discordapp.com/attachments/525811461830737940/525812334892154891/gun_shooting5.gif",
                "https://cdn.discordapp.com/attachments/525811461830737940/525812345864192000/gun_shooting6.gif",
                "https://cdn.discordapp.com/attachments/525811461830737940/525812346535542794/gun_shooting7.gif",
                "https://tenor.com/view/shooting-cat-gif-5266895",
                "https://media.tenor.com/images/d08da0153edb0797eeb0b9a07a6af556/tenor.gif",
                "https://tenor.com/view/shooting-the-office-gif-5266899",
                "https://tenor.com/view/ricky-berwick-toy-gun-shoot-nerf-gun-playing-gif-13811086",
                "https://tenor.com/view/wreck-it-ralph-wedding-day-kill-it-kill-it-dead-shoot-gif-3551541"
            ])
            message = get_text(ctx.guild, 'fun', "fun.shoot_user").format(ctx.author.name, member.name)

        #Building the embed
        e=discord.Embed(color=self.bot.embed_color, title=message)
        e.set_image(url=gif)
        await ctx.send(embed=e)



    @commandExtra(category="Funny")
    async def stab(self, ctx, member: discord.User):
        """Allows the user to stab a person of choice."""
        if member == self.bot.user:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811657138503711/525814558246567947/stab_dodge1.gif",
                "https://cdn.discordapp.com/attachments/525811657138503711/525814572817317908/stab_dodge3.gif",
                "https://cdn.discordapp.com/attachments/525811657138503711/525814639477391361/stab_dodge4.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.stab_bot").format(ctx.author.name)

        elif member == ctx.author:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811633814110228/525814228112638003/stab_suicide1.gif",
                "https://cdn.discordapp.com/attachments/525811633814110228/525814208886079493/stab_suicide2.gif",
                "https://cdn.discordapp.com/attachments/525811633814110228/525814245250695186/stab_suicide3.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.stab_self").format(ctx.author.name)

        else:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811569930666005/525813812796850178/stab_stabbing1.gif",
                "https://cdn.discordapp.com/attachments/525811569930666005/525813818467549214/stab_stabbing2.gif",
                "https://cdn.discordapp.com/attachments/525811569930666005/525813828932337713/stab_stabbing3.gif",
                "https://cdn.discordapp.com/attachments/525811569930666005/525813819969372180/stab_stabbing4.gif",
                "https://tenor.com/view/excel-saga-stabby-stab-stab-fustrated-anime-gif-14178229"
            ])
            message = get_text(ctx.guild, 'fun', "fun.stab_user").format(ctx.author.name, member.name)

        #Building the embed
        e=discord.Embed(color=self.bot.embed_color, title=message)
        e.set_image(url=gif)
        await ctx.send(embed=e)



    @commandExtra(category="Funny")
    async def punch(self, ctx, member: discord.User):
        """Allows the user to punch a person of choice."""
        if member == self.bot.user:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525812014233157672/525816632526766100/punch_dodge1.gif",
                "https://cdn.discordapp.com/attachments/525812014233157672/525816695328079893/punch_dodge2.gif",
                "https://cdn.discordapp.com/attachments/525812014233157672/525816503032086606/punch_dodge3.gif",
                "https://cdn.discordapp.com/attachments/525812014233157672/525816511877873684/punch_dodge4.gif",
                "https://cdn.discordapp.com/attachments/525812014233157672/525816515392569344/punch_dodge5.gif",
                "https://media.tenor.com/images/b0e87d7aabccc565a1bbeb722aab1873/tenor.gif",
                "https://media.tenor.com/images/05940e79a78c49e1e2983bbec9b98dfb/tenor.gif",
                "https://media.tenor.com/images/b0d9b40af89c07b520d586bbe954272a/tenor.gif",
                "https://media.tenor.com/images/6fc1642780557b27e0d22229bd627dc1/tenor.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.punch_bot").format(ctx.author.name)

        elif member == ctx.author:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811976509718548/525816120117035038/punch_self1.gif",
                "https://cdn.discordapp.com/attachments/525811976509718548/525816132586962945/punch_self2.gif",
                "https://cdn.discordapp.com/attachments/525811976509718548/525816117990785036/punch_self3.gif",
                "https://media.tenor.com/images/d946b87f8bee98e41d60c03a3a238a6a/tenor.gif",
                "https://media.tenor.com/images/0e7dee41bd53917512a6ed725b762bf8/tenor.gif",
                "https://media.tenor.com/images/ec48a7b31262da32d17ddc525b51e16b/tenor.gif",
                "https://media.tenor.com/images/9663698e8071ee6bd041091f4046921f/tenor.gif",
                "https://media.tenor.com/images/f38d1651dee251a3be87ccb049cc2566/tenor.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.punch_self").format(ctx.author.name)

        else:
            gif = random.choice([
                "https://cdn.discordapp.com/attachments/525811952132292610/525815546516734002/punch_punch1.gif",
                "https://cdn.discordapp.com/attachments/525811952132292610/525815548655828992/punch_punch2.gif",
                "https://cdn.discordapp.com/attachments/525811952132292610/525815669833596928/punch_punch3.gif",
                "https://cdn.discordapp.com/attachments/525811952132292610/525815716121673739/punch_punch4.gif",
                "https://cdn.discordapp.com/attachments/525811952132292610/525815743242043412/punch_punch5.gif",
                "https://media.tenor.com/images/7bd895a572947cf17996b84b9a51cc02/tenor.gif",
                "https://media.tenor.com/images/4f8828f7b42fc5e4d8fdca488776c064/tenor.gif",
                "https://media.tenor.com/images/5bf52a1335155572859dff8429873a30/tenor.gif",
                "https://media.tenor.com/images/dacabecede0ad9ca9bd5635cf3d1dd8f/tenor.gif",
                "https://media.tenor.com/images/764087f86d045bcc407ead9f284ff5e5/tenor.gif",
                "https://media.tenor.com/images/427deaa0773b8f397e11853a489ee6d2/tenor.gif",
                "https://media.tenor.com/images/88ba7356041dab0dca94bfc77e03d7f7/tenor.gif",
                "https://tenor.com/view/punch-dwarf-gif-5261161",
                "https://tenor.com/view/hulk-thor-punch-hit-nope-gif-7559294",
                "https://media.tenor.com/images/acd61f837f5961d845b62f6cec5a4ac0/tenor.gif"
            ])
            message = get_text(ctx.guild, 'fun', "fun.punch_user").format(ctx.author.name, member.name)

        #Building the embed
        e=discord.Embed(color=self.bot.embed_color, title=message)
        e.set_image(url=gif)
        await ctx.send(embed=e)

    @commandExtra(category="Random", aliases=['8ball'])
    async def eightball(self, ctx, *, question):
        """ Consult 8ball to receive an answer """
        yes = get_text(ctx.guild, 'fun', "fun.8b_yes")
        no = get_text(ctx.guild, 'fun', "fun.8b_no")
        tal = get_text(ctx.guild, 'fun', "fun.8b_tal")
        ybtj = get_text(ctx.guild, 'fun', "fun.8b_ybtj")
        ml = get_text(ctx.guild, 'fun', "fun.8b_ml")
        vd = get_text(ctx.guild, 'fun', "fun.8b_vd")
        answer = random.choice([yes, no, tal, ybtj, ml, vd])
        question = question.strip("?")
        e = discord.Embed(color=self.bot.embed_color, title=f"\U0001f3b1 {question}?", description=answer)
        await ctx.send(embed=e)

    @commandExtra(aliases=['flip', 'coin'], category="Random")
    async def coinflip(self, ctx):
        """ Coinflip! """
        heads = get_text(ctx.guild, 'fun', "fun.cf_heads")
        tails = get_text(ctx.guild, 'fun', "fun.cf_tails")
        coinsides = [heads, tails]
        await ctx.send(get_text(ctx.guild, 'fun', "fun.cf_result").format(ctx.author.name, random.choice(coinsides)))

    @commandExtra(category="Funny")
    async def reverse(self, ctx, *, text: str):
        """ !poow ,ffuts esreveR
        Everything you type after reverse will of course, be reversed
        """
        t_rev = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"{t_rev}")

    @commandExtra(category="Random")
    async def rate(self, ctx, *, thing):
        """ Rates what you desire """
        num = random.randint(0, 100)
        deci = random.randint(0, 9)

        if num == 100:
            deci = 0

        rating = f"{num}.{deci}"
        await ctx.send(get_text(ctx.guild, 'fun', "fun.rating").format(thing, rating))

    @commandExtra(aliases=['howhot', 'hot'], category="Funny")
    async def hotcalc(self, ctx, *, user: discord.Member = None):
        """ Returns a random percent for how hot is a discord user """
        owner = self.bot.get_user(171539705043615744)
        if user == owner:
            return await ctx.send(get_text(ctx.guild, 'fun', "fun.hc_owner") +  " \U0001f49e")

        bot = self.bot.get_user(505532526257766411)
        if user == bot:
            return await ctx.send(get_text(ctx.guild, 'fun', "fun.hc_bot"))

        if user is None:
            user = ctx.author

        random.seed(user.id)
        r = random.randint(1, 100)
        hot = r / 1.17

        emoji = "\U0001f494"
        if hot > 25:
            emoji = "\U0001f494"
        if hot > 50:
            emoji = "\U00002764"
        if hot > 75:
            emoji = "\U0001f49e"

        await ctx.send(get_text(ctx.guild, 'fun', "fun.hc").format(user.name, f"{hot:.2f}", emoji))

    @commandExtra(category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        """Ship OwO"""
        if user2 is None:
            user2 = ctx.message.author

        self_length = len(user1.display_name)
        first_length = round(self_length / 2)
        first_half = user1.display_name[0:first_length]
        usr_length = len(user2.display_name)
        second_length = round(usr_length / 2)
        second_half = user2.display_name[second_length:]
        finalName = first_half + second_half

        score = random.randint(0, 100)
        filled_progbar = round(score / 100 * 10)
        counter_ = '█' * filled_progbar + '‍ ‍' * (10 - filled_progbar)

        em = discord.Embed(color=self.bot.embed_color)
        em.title = f"%s + %s = {finalName} ❤" % (user1.display_name, user2.display_name,)
        em.description = f"`{counter_}` **{score}%** " + get_text(ctx.guild, 'fun', "fun.love")

        await ctx.send(embed=em)

    @commandExtra(aliases=["dick", "penis"], category="Funny")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dong(self, ctx, *, user: discord.Member=None):
        """Detects user's dong length"""
        if user is None:
            user = ctx.author
        state = random.getstate()
        random.seed(user.id)
        dong = "8{}D".format("=" * random.randint(0, 30))
        random.setstate(state)
        em = discord.Embed(title=get_text(ctx.guild, 'fun', "fun.dsize").format(user), description=dong, colour=self.bot.embed_color)
        await ctx.send(embed=em)



    @commandExtra(aliases=['fite'], category="Random")
    @commands.cooldown(1, 7, commands.BucketType.user)
    async def fight(self, ctx, user1: discord.Member, user2: discord.Member = None):
        """Fite sum1"""
        if user2 == None:
            user2 = ctx.message.author

        win = random.choice([user1, user2])
        if win == user1:
            lose = user2
        else:
            lose = user1

        await ctx.send(get_text(ctx.guild, 'fun', "fun.fight").format(win.mention, lose.mention))

def setup(bot):
    bot.add_cog(Fun(bot))
