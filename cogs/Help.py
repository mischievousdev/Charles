import discord
import json

from discord.ext import commands
from utils.translate import get_text
from utils.default import commandsPlus, GroupPlus
from utils.paginator import FieldPages

def setup(bot):
    bot.help_command = HelpCommand()


class HelpCommand(commands.HelpCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verify_checks = False
        with open("db/config.json", "r") as f:
            self.data = json.load(f)

        self.owner_cogs = ['OWNER', 'JISHAKU', 'EVENTS', 'DBL', 'TEST', 'ECONOMY', 'YTT']
        self.ignore_cogs = ["Help", "DBL", "Events", "Test", "YTT"]
    
    def get_command_signature(self, command):
        return f"[{command.cog.qualified_name.upper()}] > {command.qualified_name}"
    
    def common_command_formatting(self, emb, command):
        emb.title = self.get_command_signature(command)
        if command.cog_name != "Jishaku":
            emb.set_thumbnail(url=command.cog.big_icon)
        try: # try to get as a grouped command, if error its not a group command
            emb.description = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.parent}_{command.name}_description")
        except:
            emb.description = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.name}_description")
        usage = get_text(self.context.guild, "help", "help.command_help.usage")
        try:
            if command.parent:
                try:
                    usg = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.parent}_{command.name}_usage")
                except:
                    usg = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.name}_usage")
            else:
                usg = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.name}_usage")
            emb.add_field(name=usage, value=f"{self.context.prefix}{command.qualified_name} " + usg)
        except KeyError:
            emb.add_field(name=usage, value=f"{self.context.prefix}{command.qualified_name}")
        aliases = "`" + '`, `'.join(command.aliases) + "`"
        if aliases == "``":
            aliases = get_text(self.context.guild, "help", "help.command_help.no_aliases")
        emb.add_field(name=get_text(self.context.guild, "help", "help.command_help.aliases"), value=aliases)
        return emb

    async def command_callback(self, ctx, *, command=None):
        """|coro|

        The actual implementation of the help command.

        It is not recommended to override this method and instead change
        the behaviour through the methods that actually get dispatched.

        - :meth:`send_bot_help`
        - :meth:`send_cog_help`
        - :meth:`send_group_help`
        - :meth:`send_command_help`
        - :meth:`get_destination`
        - :meth:`command_not_found`
        - :meth:`subcommand_not_found`
        - :meth:`send_error_message`
        - :meth:`on_help_command_error`
        - :meth:`prepare_help_command`
        """
        
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        # Check if it's a cog
        cog = ctx.bot.get_cog(command.title())
        if cog is not None:
            return await self.send_cog_help(cog)

        maybe_coro = discord.utils.maybe_coroutine

        # If it's not a cog then it's a command.
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        keys = command.split(' ')
        cmd = ctx.bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found

        if isinstance(cmd, commands.Group):
            return await self.send_group_help(cmd)
        else:
            return await self.send_command_help(cmd)

    async def send_bot_help(self, mapping):
        with open(f'db/guilds/{self.context.guild.id}.json', 'r') as f:
            d = json.load(f)

        owner = self.context.bot.owner
        emb = discord.Embed(color=self.context.bot.embed_color)
        emb.description = get_text(self.context.guild, "help", "help.main_page.description").format(owner)
        emb.set_thumbnail(url="https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024")
        emb.set_author(icon_url=self.context.author.avatar_url, name=self.context.author)

        cogs = ""
        for extension in self.context.bot.cogs.values():
            if self.context.author != owner and extension.qualified_name.upper() in self.owner_cogs:
                continue
            if self.context.author == owner and extension.qualified_name in self.ignore_cogs:
                continue
            if extension.qualified_name == "Jishaku":
                continue
            if d["Guild_Info"]["Modules"][extension.qualified_name]["Toggle"] == False:
                continue
            cogs += f"• {extension.icon} **{extension.qualified_name}**\n"

        emb.add_field(name=get_text(self.context.guild, "help", "help.main_page.field_title.categories"), value=cogs)
        s = get_text(self.context.guild, "help", "help.main_page.links_field.support")
        i = get_text(self.context.guild, "help", "help.main_page.links_field.invite")
        v = get_text(self.context.guild, "help", "help.main_page.links_field.vote")
        d =    get_text(self.context.guild, "help", "help.main_page.links_field.donate")
        emb.add_field(name="\u200b", value="\u200b")
        emb.add_field(name=get_text(self.context.guild, "help", "help.main_page.field_title.links"), value=f"• [{s}](https://discord.gg/wZSH7pz)\n• [{i}](https://discordapp.com/api/oauth2/authorize?client_id=505532526257766411&permissions=1609952598&scope=bot)\n• [{v}](https://discordbots.org/bot/505532526257766411/vote)\n• [{d}](https://donatebot.io/checkout/514232441498763279)\n• [Website](https://charles-bot.xyz/)\n• [Source](https://github.com/iDutchy/Charles)")
        ac = self.context.bot.get_channel(519281320686518283)
        a_msg = await ac.fetch_message(int(self.data["NEWS"]["ID"]))
        a_date = a_msg.created_at.strftime("%b %d, %Y")
        news_msg = self.data["NEWS"]["MESSAGE"]
        emb.add_field(name=f"<:news:633059687557890070> Latest News - {a_date}", value=f"[Jump to full news message!]({a_msg.jump_url})\n\n{news_msg}", inline=False)
        emb.set_footer(text=get_text(self.context.guild, "help", "help.main_page.footer_info").format(self.context.prefix))
        await self.context.send(embed=emb)
    
    async def send_command_help(self, command):
        with open(f'db/guilds/{self.context.guild.id}.json', 'r') as f:
            d = json.load(f)

        if command.cog_name in self.ignore_cogs:
            return await self.send_error_message(self.command_not_found(command.name))

        if d["Guild_Info"]["Modules"][command.cog_name]["Toggle"] == False:
            return await self.send_error_message(self.command_not_found(command.name))
        if isinstance(command, commandsPlus):
            if command.name == "jishaku":
                pass
            elif d["Guild_Info"]["Modules"][command.cog_name]["Categories"][command.category] == False:
                return await self.send_error_message(self.command_not_found(command.name))

        formatted = self.common_command_formatting(discord.Embed(color=self.context.bot.embed_color), command)
        await self.context.send(embed=formatted)
    
    async def send_group_help(self, group):
        with open(f'db/guilds/{self.context.guild.id}.json', 'r') as f:
            d = json.load(f)

        if group.cog_name in self.ignore_cogs:
            return await self.send_error_message(self.command_not_found(group.name))

        if d["Guild_Info"]["Modules"][group.cog_name]["Toggle"] == False:
            return await self.send_error_message(self.command_not_found(group.name))
        if isinstance(group, GroupPlus):
            if d["Guild_Info"]["Modules"][group.cog_name]["Categories"][group.category] == False:
                return await self.send_error_message(self.command_not_found(group.name))


        formatted = self.common_command_formatting(discord.Embed(color=self.context.bot.embed_color), group)
        sub_cmd_list = ""
        for group_command in group.commands:
            try:
                sub_cmd_list += f"`╚╡` **{group_command.name}** - {get_text(self.context.guild, f'{group.cog.qualified_name.lower()}_help', f'{group_command.parent}_{group_command.name}_brief')}\n"
            except Exception:
                sub_cmd_list += f"`╚╡` **{group_command.name}** - {get_text(self.context.guild, f'{group.cog.qualified_name.lower()}_help', f'{group_command.name}_brief')}\n"
        subcommands = get_text(self.context.guild, "help", "help.command_help.subcommands")
        formatted.add_field(name=subcommands, value=sub_cmd_list, inline=False)
        await self.context.send(embed=formatted)
    
    async def send_cog_help(self, cog):
        if (cog.qualified_name.upper() in self.owner_cogs and not await self.context.bot.is_owner(self.context.author)) or cog.qualified_name.upper() in self.ignore_cogs:
            return
        if cog.qualified_name == "Jishaku":
            return
        with open(f'db/guilds/{self.context.guild.id}.json', 'r') as f:
            d = json.load(f)

        if cog.qualified_name in self.ignore_cogs:
            return

        if d["Guild_Info"]["Modules"][cog.qualified_name]["Toggle"] == False:
            return

        pages = {}
        for cmd in cog.get_commands():
            if not await self.context.bot.is_owner(self.context.author) and (cmd.hidden or cmd.category=="Hidden"):
                continue
            if d["Guild_Info"]["Modules"][cog.qualified_name]["Categories"][cmd.category] == False:
                continue
            if not cmd.category in pages:
                pages[cmd.category] = "```asciidoc\n"
            cmd_brief = get_text(self.context.guild, f"{cog.qualified_name.lower()}_help", f"{cmd.name}_brief")
            pages[cmd.category] += f"{cmd.name}{' '*int(17-len(cmd.name))}:: {cmd_brief}\n"
            if isinstance(cmd, commands.Group):
                for group_command in cmd.commands:
                    try:
                        cmd_brief = get_text(self.context.guild, f"{cog.qualified_name.lower()}_help", f"{group_command.parent}_{group_command.name}_brief")
                    except Exception:
                        cmd_brief = get_text(self.context.guild, f"{cog.qualified_name.lower()}_help", f"{group_command.name}_brief")
                    pages[cmd.category] += f"━ {group_command.name}{' '*int(15-len(group_command.name))}:: {cmd_brief}\n"
        for e in pages:
            pages[e] += "```"
        formatted = []
        for name, cont in pages.items():
            formatted.append((name , cont))
        footer_text = get_text(self.context.guild, "help", "help.category_page.footer_info").format(self.context.prefix)
        pages = FieldPages(self.context,
                           embed_color=self.context.bot.embed_color,
                           entries=formatted,
                           title = cog.qualified_name.upper(),
                           thumbnail = cog.big_icon,
                           footericon = "https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024",
                           footertext = footer_text,
                           per_page=1)
        await pages.paginate()

    def command_not_found(self, string):
        return 'No command called "{}" found.'.format(string)
