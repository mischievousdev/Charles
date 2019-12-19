import discord
import json
import asyncio
import aiohttp
import os
import datetime
import random
import re

from discord.ext import commands
from utils.default import commandExtra, groupExtra
from utils.translate import get_text

HEX = re.compile(r'^(#|0x)[A-Fa-f0-9]{6}$')

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
    @commandExtra(name="toggle-category", aliases=['toggle-cat'], category="Settings")
    async def toggle_category(self, ctx, module:str, *, category:str):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            d = json.load(f)

        if not module.title() in d["Guild_Info"]["Modules"]:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.invalid_module'))

        if module.title() in ["Owner", "Help", "DBL", "Events", "Jishaku", "Settings"]:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.no_toggle'))

        if not category.title() in d["Guild_Info"]["Modules"][module.title()]["Categories"]:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.invalid_category'))

        count = 0
        for x in d["Guild_Info"]["Modules"][module.title()]["Categories"]:
            if d["Guild_Info"]["Modules"][module.title()]["Categories"][x] == True:
                count += 1

        if count == 1 and d["Guild_Info"]["Modules"][module.title()]["Categories"][category.title()] != False:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.1_cat'))


        if d["Guild_Info"]["Modules"][module.title()]["Categories"][category.title()] == True:
            d["Guild_Info"]["Modules"][module.title()]["Categories"][category.title()] = False
            toggle = get_text(ctx.guild, 'settings', 'settings.t_off')
        elif d["Guild_Info"]["Modules"][module.title()]["Categories"][category.title()] == False:
            d["Guild_Info"]["Modules"][module.title()]["Categories"][category.title()] = True
            toggle = get_text(ctx.guild, 'settings', 'settings.t_on')

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            json.dump(d, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.cat_toggle').format(category.title(), module.title(), toggle))

    @commands.has_permissions(administrator=True)
    @commandExtra(name="toggle-module", category="Settings")
    async def toggle_module(self, ctx, module:str):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            d = json.load(f)

        enabled = 0
        disabled = 0
        if module.lower() in ["*", get_text(ctx.guild, 'settings', 'settings.all')]:
            for m in ["Fun", "Music", "Info", "Moderation", "Images", "Utility"]:
                if d["Guild_Info"]["Modules"][m]["Toggle"] == True:
                    enabled += 1
                if d["Guild_Info"]["Modules"][m]["Toggle"] == False:
                    disabled += 1

            if enabled >= disabled:
                for m in ["Fun", "Music", "Info", "Moderation", "Images", "Utility"]:
                    d["Guild_Info"]["Modules"][m]["Toggle"] = False
                    toggle = get_text(ctx.guild, 'settings', 'settings.t_off')
            if disabled > enabled:
                for m in ["Fun", "Music", "Info", "Moderation", "Images", "Utility"]:
                    d["Guild_Info"]["Modules"][m]["Toggle"] = True
                    toggle = get_text(ctx.guild, 'settings', 'settings.t_on')

            with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
                json.dump(d, f, indent=4)

            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.mod_toggle_all').format(toggle))

        if not module.title() in d["Guild_Info"]["Modules"]:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.invalid_module'))

        if module.title() in ["Owner", "Help", "DBL", "Events", "Jishaku", "Settings"]:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.no_toggle'))

        if d["Guild_Info"]["Modules"][module.title()]["Toggle"] == True:
            d["Guild_Info"]["Modules"][module.title()]["Toggle"] = False
            toggle = get_text(ctx.guild, 'settings', 'settings.t_off')
        elif d["Guild_Info"]["Modules"][module.title()]["Toggle"] == False:
            d["Guild_Info"]["Modules"][module.title()]["Toggle"] = True
            toggle = get_text(ctx.guild, 'settings', 'settings.t_on')

        with open(f"db/guilds/{ctx.guild.id}.json", "w") as f:
            json.dump(d, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.mod_toggle').format(module.title(),toggle))

    @commandExtra(category="Server Backups", name="delete-backup")
    async def delete_backup(self, ctx, id:int):
        i = str(id)

        if not os.path.exists(f'db/backups/{str(ctx.author.id)}.json'):
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.no_backups'))

        with open(f'db/backups/{str(ctx.author.id)}.json', 'r') as f:
            d = json.load(f)

        if not i in d:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.invalid_id'))

        msg = await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.delete_confirm').format(i))
        await msg.add_reaction("<:tickYes:315009125694177281>")
        await msg.add_reaction("<:tickNo:315009174163685377>")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["<:tickYes:315009125694177281>", "<:tickNo:315009174163685377>"]

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.timed_out'))
        else:
            if str(reaction.emoji) == "<:tickNo:315009174163685377>":
                await msg.delete()
                return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.cancel'), delete_after=10)
            elif str(reaction.emoji) == "<:tickYes:315009125694177281>":
                await msg.delete()
                d.pop(i)
                with open(f'db/backups/{str(ctx.author.id)}.json', 'w') as f:
                    json.dump(d, f)
                await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.deleted').format(i), delete_after=10)

    @commandExtra(category="Server Backups", name="reset-backup")
    async def reset_backup(self, ctx, id:int):
        i = str(id)

        if not os.path.exists(f'db/backups/{str(ctx.author.id)}.json'):
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.no_backups'))

        with open(f'db/backups/{str(ctx.author.id)}.json', 'r') as f:
            d = json.load(f)

        if not i in d:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.invalid_id'))

        for entry in d[i]["Channels"]["Cat"]:
            entry["restore"] = True

        for entry in d[i]["Channels"]["Text"]:
            entry["restore"] = True

        for entry in d[i]["Channels"]["Voice"]:
            entry["restore"] = True

        for entry in d[i]["Roles"]:
            entry["restore"] = True

        for entry in d[i]["Emoji"]:
            entry["restore"] = True

        d[i]["Guild-ID"] = None

        with open(f'db/backups/{str(ctx.author.id)}.json', 'w') as f:
            json.dump(d, f)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.reset').format(i))

    @commandExtra(category="Server Backups", name="backup-list", aliases=['restore-list'])
    async def list_backups(self, ctx):
        if not os.path.exists(f'db/backups/{str(ctx.author.id)}.json'):
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.no_backups'))

        with open(f'db/backups/{str(ctx.author.id)}.json', 'r') as f:
            d = json.load(f)

        if len(d) == 0:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.no_backups'))

        e = discord.Embed(color=self.bot.embed_color, title=get_text(ctx.guild, 'settings', 'settings.bu.made'))
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

        for entry in d:
            e.add_field(name=get_text(ctx.guild, 'settings', 'settings.bu.id').format(entry), value=get_text(ctx.guild, 'settings', 'settings.bu.info').format(d[entry]['Server'], d[entry]['Backup-Time']), inline=False)

        await ctx.send(embed=e)

    @commandExtra(category="Server Backups")
    async def backup(self, ctx):
        perms = dict(ctx.author.guild_permissions)
        if not perms['administrator'] == True:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.missing_perm'))

        if not os.path.exists(f'db/backups/{str(ctx.author.id)}.json'):
            f = open(f'db/backups/{str(ctx.author.id)}.json', 'x')
            f.write("{}")
            f.close()

        with open(f'db/backups/{str(ctx.author.id)}.json', 'r') as f:
            d = json.load(f)

        cat_list = []
        for cat in ctx.guild.categories:
            cat_list.append(dict({"name": cat.name, "restore": True}))

        txt_list = []
        for c in ctx.guild.text_channels:
            if c.category != None:
                cat = c.category.name
            else:
                cat = None
            txt_list.append(dict({"name": c.name, "topic": c.topic, "pos": c.position, "slow": c.slowmode_delay, "nsfw": c.is_nsfw(), "cat": cat, "restore": True}))

        voice_list = []
        for v in ctx.guild.voice_channels:
            if v.category != None:
                cat = v.category.name
            else:
                cat = None
            voice_list.append(dict({"name": v.name, "pos": v.position, "cat": cat, "limit": v.user_limit, "restore": True}))

        role_list = []
        for r in ctx.guild.roles:
            if r.name == "@everyone":
                continue
            role_list.append(dict({"name": r.name, "perms": dict(r.permissions), "color": str(r.color), "mentionable": r.mentionable, "hoist": r.hoist, "restore": True}))

        emoji_list = []
        for e in ctx.guild.emojis:
            emoji_list.append(dict({"name": e.name, "img": str(e.url), "restore": True}))

        randID = random.randint(1111, 9999)

        d[str(randID)] = {
            "Backup-Time": str(datetime.datetime.utcnow().strftime("%b %d, %Y - %H:%M:%S")),
            "Server": ctx.guild.name,
            "Usable": True,
            "Fix-Only": False,
            "Guild-ID": None,
            "Channels": {
                "Cat": cat_list,
                "Text": txt_list,
                "Voice": voice_list
                },
            "Roles": role_list,
            "Emoji": emoji_list
            }

        with open(f'db/backups/{str(ctx.author.id)}.json', 'w') as f:
            json.dump(d, f, indent=4)

        await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.created').format(str(randID)))

    @commandExtra(category="Server Backups")
    async def restore(self, ctx, id:int, guild:int):
        g = self.bot.get_guild(guild)
        if g is None:
            return await ctx.send("Could not find a guild with that ID. Are you sure I am in that guild?")
        i = str(id)

        if len(g.channels) > 0:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.channels_error'))

        if len(g.roles) > 5:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.roles_error'))


        if len(g.emojis) > 0:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.emoji_error'))
        if not os.path.exists(f'db/backups/{str(ctx.author.id)}.json'):
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.no_backups'))

        if g.owner_id != ctx.author.id:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.not_owner'))

        failures = False

        # Open backup file
        with open(f'db/backups/{str(ctx.author.id)}.json', 'r') as f:
            d = json.load(f)

        if not i in d:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.invalid_id'))

        d[i]["Guild-ID"] = g.id

        if d[i]["Usable"] == False:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.not_usable').format(i))

        if d[i]["Fix-Only"] == True:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.need_fix'))

        m = "<:tick:528774982067814441> | " + get_text(ctx.guild, 'settings', 'settings.restore.init_complete')

        msg = await ctx.send("<a:discord_loading:587812494089912340> | " + get_text(ctx.guild, 'settings', 'settings.restore.init'))

        await asyncio.sleep(1.5)

        # Start creating categories
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.restore.categories')}")

        # Function to create categories
        async def create_category():
            await g.create_category_channel(name=c["name"])

        # Loop through all categories
        c_count = 0
        for c in d[i]["Channels"]["Cat"]:
            try:
                await asyncio.wait_for(create_category(), timeout=10.0)
                c_count = c_count + 1
                c["restore"] = False
            except (asyncio.TimeoutError, discord.HTTPException):
                m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.restore.categories_complete")} {str(c_count)}/{str(len(d[i]["Channels"]["Cat"]))}'
                failures = True
                break
        else:
            m += f"\n<:tick:528774982067814441> | {str(c_count)} {get_text(ctx.guild, 'settings', 'settings.restore.categories_complete')}"



        # Start creating text channels
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.restore.text')}")

        # Function to create text channels
        async def create_text():
            if t["cat"] != None:
                cat = discord.utils.get(g.categories, name=t["cat"])
            else:
                cat = None
            await g.create_text_channel(name=t["name"], position=t["pos"], topic=t["topic"], slowmode_delay=t["slow"], nsfw=t["nsfw"], category=cat, reason="Server Backup")

        # Loop through all text channels
        t_count = 0
        for t in d[i]["Channels"]["Text"]:
            try:
                await asyncio.wait_for(create_text(), timeout=10.0)
                t_count = t_count + 1
                t["restore"] = False
            except (asyncio.TimeoutError, discord.HTTPException): 
                m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.restore.text_complete")} {str(t_count)}/{str(len(d[i]["Channels"]["Text"]))}'
                failures = True
                break
        else:
            m += f"\n<:tick:528774982067814441> | {str(t_count)} {get_text(ctx.guild, 'settings', 'settings.restore.text_complete')}"

        # Start creating voice channels
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.restore.voice')}")

        # Function to create voice channels
        async def create_voice():
            if v["cat"] != None:
                cat = discord.utils.get(g.categories, name=v["cat"])
            else:
                cat = None
            await g.create_voice_channel(name=v["name"], position=v["pos"], category=cat, user_limit=v["limit"], reason="Server Backup")

        # Loop through all voice channels
        v_count = 0
        for v in d[i]["Channels"]["Voice"]:
            try:
                await asyncio.wait_for(create_voice(), timeout=10.0)
                v_count = v_count + 1
                v["restore"] = False
            except (asyncio.TimeoutError, discord.HTTPException): 
                m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.restore.voice_complete")} {str(v_count)}/{str(len(d[i]["Channels"]["Voice"]))}'
                failures = True
                break
        else:
            m += f"\n<:tick:528774982067814441> | {str(v_count)} {get_text(ctx.guild, 'settings', 'settings.restore.voice_complete')}"

        # Start creating roles
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.restore.roles')}")

        # Function to create roles
        async def create_role():
            perms = discord.Permissions()
            perms.update(**r["perms"])
            col = r["color"].replace("#", "0x")
            color = discord.Color(int(col, 16))
            await g.create_role(name=r["name"], permissions=perms, color=color, mentionable=r["mentionable"], hoist=r["hoist"], reason="Server Backup")

        # Loop through all roles
        r_count = 0
        for r in d[i]["Roles"][::-1]:
            try:
                await asyncio.wait_for(create_role(), timeout=10.0)
                r_count = r_count + 1
                r["restore"] = False
            except (asyncio.TimeoutError, discord.HTTPException):
                m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.restore.roles_complete")} {str(r_count)}/{str(len(d[i]["Roles"]))}'
                failures = True
                break
        else:
            m += f"\n<:tick:528774982067814441> | {str(r_count)} {get_text(ctx.guild, 'settings', 'settings.restore.roles_complete')}"

        # Start creating emojis
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.restore.emoji')}")

        # Function to create the emoji
        async def create_emoji():
            async with aiohttp.ClientSession() as c:
                async with c.get(e["img"]) as r:
                    img = await r.read()
            await g.create_custom_emoji(name=e["name"], image=img, reason="Server Backup")

        # Loop through all emojis
        e_count = 0
        for e in d[i]["Emoji"]:
            try:
                await asyncio.wait_for(create_emoji(), timeout=10.0)
                e_count = e_count + 1
                e["restore"] = False
            except (asyncio.TimeoutError, discord.HTTPException): 
                m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.restore.emoji_complete")} {str(e_count)}/{str(len(d[i]["Emoji"]))}'
                failures = True
                break
        else:
            m += f"\n<:tick:528774982067814441> | {str(e_count)} {get_text(ctx.guild, 'settings', 'settings.restore.emoji_complete')}"

        # Backup completed!
        if failures == True:
            await msg.edit(content=f"{m}\n\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.restore.complete_x')}")
        else:
            await msg.edit(content=f"{m}\n\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.restore.complete')}")
            if c_count == 0 and t_count == 0 and v_count == 0 and r_count == 0 and e_count == 0:
                d[i]["Usable"] = False

        d[i]["Fix-Only"] = True
        # Save backup file
        with open(f'db/backups/{str(ctx.author.id)}.json', 'w') as f:
            json.dump(d, f, indent=4)

    @commandExtra(category="Server Backups", name="fix-restore")
    async def fix_restore(self, ctx, id:int):
        i = str(id)

        if not os.path.exists(f'db/backups/{str(ctx.author.id)}.json'):
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.no_backups'))

        failures = False


        # Open backup file
        with open(f'db/backups/{str(ctx.author.id)}.json', 'r') as f:
            d = json.load(f)

        if not i in d:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.bu.invalid_id'))


        if d[i]["Usable"] == False:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.not_usable').format(i))

        if d[i]["Fix-Only"] == False:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.fix.cant_fix'))

        g = self.bot.get_guild(d[i]["Guild-ID"])
        if g is None:
            return await ctx.send("I could not find the guild this backup was ysed in. Are you sure I am (still) in that guild?")

        if g.owner_id != ctx.author.id:
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.restore.not_owner'))

        m = "<:tick:528774982067814441> | " + get_text(ctx.guild, 'settings', 'settings.fix.init_complete')
        msg = await ctx.send("<a:discord_loading:587812494089912340> | Initiating fix...")
        await asyncio.sleep(1.5)

        # Start creating categories
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.fix.cat')}")

        # Function to create categories
        async def create_category():
            await g.create_category_channel(name=c["name"])

        # Loop through all categories
        c_count = 0
        for c in d[i]["Channels"]["Cat"]:
            if c["restore"] == True:
                try:
                    await asyncio.wait_for(create_category(), timeout=10.0)
                    c_count = c_count + 1
                    c["restore"] = False
                except (asyncio.TimeoutError, discord.HTTPException):
                    m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.fix.cat_cant_fix").format(str(c_count))}'
                    failures = True
                    break
        else:
            if c_count == 0:
                m += f"\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.cat_no_fix')}"
            else:
                m += f"\n<:tick:528774982067814441> | {str(c_count)} {get_text(ctx.guild, 'settings', 'settings.fix.cat_fix')}"

        # Start creating text channels
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.fix.text')}")

        # Function to create text channels
        async def create_text():
            if t["cat"] != None:
                cat = discord.utils.get(g.categories, name=t["cat"])
            else:
                cat = None
            await g.create_text_channel(name=t["name"], position=t["pos"], topic=t["topic"], slowmode_delay=t["slow"], nsfw=t["nsfw"], category=cat, reason="Server Backup")

        # Loop through all text channels
        t_count = 0
        for t in d[i]["Channels"]["Text"]:
            if t["restore"] == True:
                try:
                    await asyncio.wait_for(create_text(), timeout=10.0)
                    t_count = t_count + 1
                    t["restore"] = False
                except (asyncio.TimeoutError, discord.HTTPException):
                    m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.fix.text_cant_fix").format(str(t_count))}'
                    failures = True
                    break
        else:
            if t_count == 0:
                m += f"\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.text_no_fix')}"
            else:
                m += f"\n<:tick:528774982067814441> | {str(t_count)} {get_text(ctx.guild, 'settings', 'settings.fix.text_fix')}"

        # Start creating voice channels
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.fix.voice')}")

        # Function to create voice channels
        async def create_voice():
            if v["cat"] != None:
                cat = discord.utils.get(g.categories, name=v["cat"])
            else:
                cat = None
            await g.create_voice_channel(name=v["name"], position=v["pos"], category=cat, user_limit=v["limit"], reason="Server Backup")

        # Loop through all voice channels
        v_count = 0
        for v in d[i]["Channels"]["Voice"]:
            if v["restore"] == True:
                try:
                    await asyncio.wait_for(create_voice(), timeout=10.0)
                    v_count = v_count + 1
                    v["restore"] = False
                except (asyncio.TimeoutError, discord.HTTPException): 
                    m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.fix.voice_cant_fix").format(str(v_count))}'
                    failures = True
                    break
        else:
            if v_count == 0:
                m += f"\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.voice_no_fix')}"
            else:
                m += f"\n<:tick:528774982067814441> | {str(v_count)} {get_text(ctx.guild, 'settings', 'settings.fix.voice_fix')}"

        # Start creating roles
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.fix.roles')}")

        # Function to create roles
        async def create_role():
            perms = discord.Permissions()
            perms.update(**r["perms"])
            col = r["color"].replace("#", "0x")
            color = discord.Color(int(col, 16))
            await g.create_role(name=r["name"], permissions=perms, color=color, mentionable=r["mentionable"], hoist=r["hoist"], reason="Server Backup")

        # Loop through all roles
        r_count = 0
        for r in d[i]["Roles"][::-1]:
            if r["restore"] == True:
                try:
                    await asyncio.wait_for(create_role(), timeout=10.0)
                    r_count = r_count + 1
                    r["restore"] = False
                except (asyncio.TimeoutError, discord.HTTPException):
                    m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.fix.roles_cant_fix").format(str(r_count))}'
                    failures = True
                    break
        else:
            if r_count == 0:
                m += f"\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.roles_no_fix')}"
            else:
                m += f"\n<:tick:528774982067814441> | {str(r_count)} {get_text(ctx.guild, 'settings', 'settings.fix.roles_fix')}"

        # Start creating emojis
        await msg.edit(content=f"{m}\n<a:discord_loading:587812494089912340> | {get_text(ctx.guild, 'settings', 'settings.fix.emoji')}")

        # Function to create the emoji
        async def create_emoji():
            async with aiohttp.ClientSession() as c:
                async with c.get(e["img"]) as r:
                    img = await r.read()
            await g.create_custom_emoji(name=e["name"], image=img, reason="Server Backup")

        # Loop through all emojis
        e_count = 0
        for e in d[i]["Emoji"]:
            if e["restore"] == True:
                try:
                    await asyncio.wait_for(create_emoji(), timeout=10.0)
                    e_count = e_count + 1
                    e["restore"] = False
                except (asyncio.TimeoutError, discord.HTTPException): 
                    m += f'\n<:warn:620414236010741783> | {get_text(ctx.guild, "settings", "settings.fix.emoji_cant_fix").format(str(e_count))}'
                    failures = True
                    break
        else:
            if e_count == 0:
                m += f"\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.emoji_no_fix')}"
            else:
                m += f"\n<:tick:528774982067814441> | {str(e_count)} {get_text(ctx.guild, 'settings', 'settings.fix.emoji_fix')}"

        # Backup completed!
        if failures == True:
            await msg.edit(content=f"{m}\n\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.complete_x')}")
        else:
            await msg.edit(content=f"{m}\n\n<:tick:528774982067814441> | {get_text(ctx.guild, 'settings', 'settings.fix.complete')}")
            if c_count == 0 and t_count == 0 and v_count == 0 and r_count == 0 and e_count == 0:
                d[i]["Usable"] = False

        # Save backup file
        with open(f'db/backups/{str(ctx.author.id)}.json', 'w') as f:
            json.dump(d, f, indent=4)

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

    @leaving.command(name="delete-after")
    async def delete_msg_after(self, ctx, time:int=None):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if time is None:
            data['Guild_Logs']['Leave_Msg']['Delete_After'] = None
            msg = get_text(ctx.guild, 'settings', 'settings.leaving.delete_after_none')

        else:
            data['Guild_Logs']['Leave_Msg']['Delete_After'] = time
            msg = get_text(ctx.guild, 'settings', 'settings.leaving.delete_after')

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(msg)

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

    @welcoming.command(name="delete-after")
    async def _delete_msg_after(self, ctx, time:int=None):
        with open(f'db/guilds/{ctx.guild.id}.json', 'r') as f:
            data = json.load(f)

        if time is None:
            data['Guild_Logs']['Welcome_Msg']['Delete_After'] = None
            msg = get_text(ctx.guild, 'settings', 'settings.welcoming.delete_after_none')

        else:
            data['Guild_Logs']['Welcome_Msg']['Delete_After'] = time
            msg = get_text(ctx.guild, 'settings', 'settings.welcoming.delete_after')

        with open(f'db/guilds/{ctx.guild.id}.json', 'w') as f:
            data = json.dump(data, f, indent=4)

        await ctx.send(msg)

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

        if not HEX.match(color):
            return await ctx.send(get_text(ctx.guild, 'settings', 'settings.emb_invalid_hex'))

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
        cant_disable = ["help", "jishaku", "disable-command", "enable-command", "toggle-module", "toggle-category", "modules", "categories"]

        if command.title() in self.bot.cogs.keys():
            return await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_is_cog").format(command, ctx.prefix))

        cmd = self.bot.get_command(command.strip("<>"))

        if cmd is None:
            return await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_not_found").format(command.strip("<>")))

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

        if command.title() in self.bot.cogs.keys():
            return await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_is_cog").format(command, ctx.prefix))

        cmd = self.bot.get_command(command.strip("<>"))

        if cmd is None:
            return await ctx.send(get_text(ctx.guild, "settings", "settings.cmd_not_found").format(command.strip("<>")))

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
