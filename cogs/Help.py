import discord
import json

from discord.ext import commands
from utils.translate import get_text
from utils.default import commandsPlus, GroupPlus
from utils.paginator import FieldPages




class Help(commands.Cog, name="Help", command_attrs=dict(hidden=True)):
    """Get help for a category or a command"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, case_insensitive=True)
    async def help(self, ctx, *, command_or_cog=None):
        with open("db/config.json", "r") as f:
            data = json.load(f)

        owner = self.bot.get_user(data["BOT_OWNER"])
        owner_cogs = ['OWNER', 'JISHAKU', 'EVENTS', 'DBL', 'TEST', 'ECONOMY']
        if command_or_cog is None:
            emb = discord.Embed(color=self.bot.embed_color)
            emb.description = get_text(ctx.guild, "help", "help.main_page.description").format(owner)
            emb.set_thumbnail(url="https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024")
            emb.set_author(icon_url=ctx.author.avatar_url, name=ctx.author)

            cogs = ""
            for extension in self.bot.cogs.values():
                if ctx.author != owner:
                    if sum(1 for command in extension.get_commands() if not command.hidden) == 0 or extension.qualified_name.upper() in owner_cogs:
                        continue
                if ctx.author == owner:
                    ignore_cogs = ["Help", "DBL", "Events", "Test"]
                    if extension.qualified_name in ignore_cogs:
                        continue
                cogs += f"- {extension.icon} {extension.qualified_name}\n"

            emb.add_field(name=get_text(ctx.guild, "help", "help.main_page.field_title.categories"), value=cogs)
            s = get_text(ctx.guild, "help", "help.main_page.links_field.support")
            i = get_text(ctx.guild, "help", "help.main_page.links_field.invite")
            v = get_text(ctx.guild, "help", "help.main_page.links_field.vote")
            d =    get_text(ctx.guild, "help", "help.main_page.links_field.donate")   
            emb.add_field(name=get_text(ctx.guild, "help", "help.main_page.field_title.links"), value=f"- [{s}](https://discord.gg/wZSH7pz)\n- [{i}](https://discordapp.com/api/oauth2/authorize?client_id=505532526257766411&permissions=1609952598&scope=bot)\n- [{v}](https://discordbots.org/bot/505532526257766411/vote)\n- [{d}](https://donatebot.io/checkout/514232441498763279)\n- [Website](https://charles-bot.xyz/)\n- [Source](https://github.com/iDutchy/Charles)")
            ac = self.bot.get_channel(519281320686518283)
            a_msg = await ac.fetch_message(int(data["NEWS"]["ID"]))
            a_date = a_msg.created_at.strftime("%b %d, %Y")
            news_msg = data["NEWS"]["MESSAGE"]
            emb.add_field(name=f"<:news:633059687557890070> Latest News - {a_date}", value=f"[Jump to full news message!]({a_msg.jump_url})\n\n{news_msg}")
            emb.set_footer(text=get_text(ctx.guild, "help", "help.main_page.footer_info").format(ctx.prefix))
            await ctx.send(embed=emb)
            return



        try:
            command_or_cog = command_or_cog.title()
            c = self.bot.get_cog(command_or_cog)
            if ctx.author != owner:
                if c.qualified_name.upper() in owner_cogs:
                    return
            emb = discord.Embed(color=self.bot.embed_color)
            emb.title = c.qualified_name.upper()
            #cmds = "```asciidoc\n"
            cmdlist = []
            for command in c.get_commands():
                if isinstance(command, commandsPlus) or isinstance(command, GroupPlus):
                    cat = getattr(command, 'category')
                    if cat:
                        if ctx.author != owner:
                            if cat != "Hidden":
                                cmdlist.append(cat)
                        else:
                            cmdlist.append(cat)

            cmdlist = sorted(set(cmdlist))
            somelist = []
            for entry in cmdlist:
                cmds = "```asciidoc\n"
                for command in c.walk_commands():
                    if isinstance(command, commandsPlus) or isinstance(command, GroupPlus):
                        cat = getattr(command, 'category')
                        if cat:
                            if cat == entry:
                                if ctx.author != owner:
                                    if not command.hidden is True:
                                        if isinstance(command, commands.Group):
                                            cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{command.name}_brief")
                                            cmds += f"{command.name}{' '*int(17-len(command.name))}:: {cmd_brief}\n"
                                            for group_command in command.commands:
                                                try:
                                                    cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{group_command.parent}_{group_command.name}_brief")
                                                except Exception:
                                                    cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{group_command.name}_brief")
                                                cmds += f"━ {group_command.name}{' '*int(15-len(group_command.name))}:: {cmd_brief}\n"
                                        else:
                                            cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{command.name}_brief")
                                            cmds += f"{command.name}{' '*int(17-len(command.name))}:: {cmd_brief}\n"
                                else:
                                    if isinstance(command, commands.Group):
                                        cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{command.name}_brief")
                                        cmds += f"{command.name}{' '*int(17-len(command.name))}:: {cmd_brief}\n"
                                        for group_command in command.commands:
                                            try:
                                                cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{group_command.parent}_{group_command.name}_brief")
                                            except Exception: 
                                                cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{group_command.name}_brief")
                                            cmds += f"━ {group_command.name}{' '*int(15-len(group_command.name))}:: {cmd_brief}\n"
                                    else:
                                        cmd_brief = get_text(ctx.guild, f"{c.qualified_name.lower()}_help", f"{command.name}_brief")
                                        cmds += f"{command.name}{' '*int(17-len(command.name))}:: {cmd_brief}\n"

                cmds += "```"
                emb.add_field(name=entry, value=cmds)
                somelist.append((entry, cmds))
            

                    #if ctx.author != owner:
                    #    if not command.hidden is True:
                    #        #cmd_brief = get_text(ctx.guild, f"{command.name}_brief")
                    #        cmds += f"**{command.name}** - {command.brief}\n"
                    #else:
                    #    #cmd_brief = get_text(ctx.guild, f"{command.name}_brief")
                    #    cmds += f"**{command.name}** - {command.brief}\n"
            #cmds = cmds.splitlines()
            #cmds = sorted(cmds)
            #cmds = '\n'.join(cmds)
            emb.set_thumbnail(url=c.big_icon)
            footer_text = get_text(ctx.guild, "help", "help.category_page.footer_info").format(ctx.prefix)
            emb.set_footer(icon_url="https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024", text=footer_text)
            #await ctx.send(embed=emb)
            f = FieldPages(ctx,
                           entries=somelist,
                           title = c.qualified_name.upper(),
                           thumbnail = c.big_icon,
                           footericon = "https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024",
                           footertext = footer_text,
                           per_page=1)
            await f.paginate()
            return
        except AttributeError:
            try:
                command_or_cog = command_or_cog.lower()
                c = self.bot.get_command(command_or_cog)
                if ctx.author != owner:
                    if c.cog_name.upper() in owner_cogs:
                        return
                emb = discord.Embed(color=self.bot.embed_color)
                sub_cmd_list = ""
                if isinstance(c, commands.Group):
                    emb.title = f"[{c.cog_name}] > {c.name}"
                    for group_command in c.commands:
                        try:
                            sub_cmd_list += f"`╚╡` **{group_command.name}** - {get_text(ctx.guild, f'{c.cog.qualified_name.lower()}_help', f'{group_command.parent}_{group_command.name}_brief')}\n"
                        except Exception:
                            sub_cmd_list += f"`╚╡` **{group_command.name}** - {get_text(ctx.guild, f'{c.cog.qualified_name.lower()}_help', f'{group_command.name}_brief')}\n"
                    subcommands = get_text(ctx.guild, "help", "help.command_help.subcommands")
                    emb.add_field(name=subcommands, value=sub_cmd_list, inline=False)
                else:
                    if c.parent:
                        emb.title = f"[{str(c.cog_name).upper()}] > {c.parent} {c.name}"
                    else:
                        emb.title = f"[{str(c.cog_name).upper()}] > {c.name}"
                #emb.set_thumbnail(url="https://media.discordapp.net/attachments/562784997962940476/583376984571379722/naamloos.png")
                emb.set_thumbnail(url=self.bot.get_cog(c.cog_name).big_icon)

                try: # try to get as a grouped command, if error its not a group command
                    emb.description = get_text(ctx.guild, f"{c.cog.qualified_name.lower()}_help", f"{c.parent}_{c.name}_description")
                except Exception:
                    emb.description = get_text(ctx.guild, f"{c.cog.qualified_name.lower()}_help", f"{c.name}_description")
                usage = get_text(ctx.guild, "help", "help.command_help.usage")
                try:
                    if c.parent:
                        try:
                            usg = get_text(ctx.guild, f"{c.cog.qualified_name.lower()}_help", f"{c.parent}{c.name}_usage")
                        except Exception:
                            usg = get_text(ctx.guild, f"{c.cog.qualified_name.lower()}_help", f"{c.name}_usage")
                        emb.add_field(name=usage, value=f"{ctx.prefix}{c.parent} {c.name} " + usg)
                    else:
                        emb.add_field(name=usage, value=f"{ctx.prefix}{c.name} " + get_text(ctx.guild, f"{c.cog.qualified_name.lower()}_help", f"{c.name}_usage"))
                except KeyError:
                    if c.parent:
                        emb.add_field(name=usage, value=f"{ctx.prefix}{c.parent} {c.name}")
                    else:
                        emb.add_field(name=usage, value=f"{ctx.prefix}{c.name}")
                aliases = '`, `'.join(c.aliases)
                aliases = f"`{aliases}`"
                if aliases == "``":
                    aliases = get_text(ctx.guild, "help", "help.command_help.no_aliases")
                aliases_t = get_text(ctx.guild, "help", "help.command_help.aliases")
                emb.add_field(name=aliases_t, value=aliases)
                await ctx.send(embed=emb)
                return
            except AttributeError:
                not_found = get_text(ctx.guild, "help", "help.command_not_found").format(command_or_cog.capitalize())
                await ctx.send(not_found)
                return

def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Help(bot))
