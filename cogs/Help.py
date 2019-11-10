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

        self.owner_cogs = ['OWNER', 'JISHAKU', 'EVENTS', 'DBL', 'TEST', 'ECONOMY']
        self.ignore_cogs = ["Help", "DBL", "Events", "Test"]
    
    
    def get_command_signature(self, command):
        return f"[{command.cog_name}] > {command.qualified_name}"
    
    def common_command_formatting(self, emb, command):
        emb.title = self.get_command_signature(command)
        cmd_brief = get_text(self.context.guild, f"{command.cog_name.lower()}_help", f"{command.name}_brief")
        emb.set_thumbnail(url=command.cog.big_icon)
        try: # try to get as a grouped command, if error its not a group command
            emb.description = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.parent}_{command.name}_description")
        except:
            emb.description = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.name}_description")
        usage = get_text(self.context.guild, "help", "help.command_help.usage")
        try:
            usg = get_text(self.context.guild, f"{command.cog.qualified_name.lower()}_help", f"{command.qualified_name}_usage")
            emb.add_field(name=usage, value=f"{self.context.prefix}{command.qualified_name} " + usg)
        except KeyError:
            emb.add_field(name=usage, value=f"{self.context.prefix}{command.qualified_name}")
        aliases = "`" + '`, `'.join(command.aliases) + "`"
        if aliases == "``":
            aliases = get_text(self.context.guild, "help", "help.command_help.no_aliases")
        emb.add_field(name=get_text(self.context.guild, "help", "help.command_help.aliases"), value=aliases)
        return emb

    async def send_bot_help(self, mapping):
        emb = discord.Embed(color=self.context.bot.embed_color)
        emb.description = get_text(self.context.guild, "help", "help.main_page.description").format(str(self.context.bot.owner))
        emb.set_thumbnail(url="https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024")
        emb.set_author(icon_url=self.context.author.avatar_url, name=self.context.author)

        cogs = ""
        for extension in self.context.bot.cogs.values():
            if self.context.author != self.context.bot.owner and not extension.commands or extension.qualified_name.upper() in self.owner_cogs:
                    continue
            if self.context.author == self.context.bot.owner and extension.qualified_name in self.ignore_cogs :
                continue
            cogs += f"- {extension.icon} {extension.qualified_name}\n"

        emb.add_field(name=get_text(self.context.guild, "help", "help.main_page.field_title.categories"), value=cogs)
        s = get_text(self.context.guild, "help", "help.main_page.links_field.support")
        i = get_text(self.context.guild, "help", "help.main_page.links_field.invite")
        v = get_text(self.context.guild, "help", "help.main_page.links_field.vote")
        d =    get_text(self.context.guild, "help", "help.main_page.links_field.donate")
        emb.add_field(name=get_text(self.context.guild, "help", "help.main_page.field_title.links"), value=f"- [{s}](https://discord.gg/wZSH7pz)\n- [{i}](https://discordapp.com/api/oauth2/authorize?client_id=505532526257766411&permissions=1609952598&scope=bot)\n- [{v}](https://discordbots.org/bot/505532526257766411/vote)\n- [{d}](https://donatebot.io/checkout/514232441498763279)\n- [Website](https://charles-bot.xyz/)\n- [Source](https://github.com/iDutchy/Charles)")
        ac = self.context.bot.get_channel(519281320686518283)
        a_msg = await ac.fetch_message(int(self.data["NEWS"]["ID"]))
        a_date = a_msg.created_at.strftime("%b %d, %Y")
        news_msg = self.data["NEWS"]["MESSAGE"]
        emb.add_field(name=f"<:news:633059687557890070> Latest News - {a_date}", value=f"[Jump to full news message!]({a_msg.jump_url})\n\n{news_msg}")
        emb.set_footer(text=get_text(self.context.guild, "help", "help.main_page.footer_info").format(self.context.prefix))
        await self.context.send(embed=emb)
    
    async def send_command_help(self, command):
        formatted = self.common_command_formatting(discord.Embed(color=discord.Color.from_rgb(54,57,62)), command)
        await self.context.send(embed=formatted)
    
    async def send_group_help(self, group):
        formatted = self.common_command_formatting(discord.Embed(color=discord.Color.from_rgb(54,57,62)), group)
        for group_command in group.commands:
            try:
                sub_cmd_list += f"`╚╡` **{group_command.name}** - {get_text(self.context.guild, f'{group.cog.qualified_name.lower()}_help', f'{group_command.parent}_{group_command.name}_brief')}\n"
            except Exception:
                sub_cmd_list += f"`╚╡` **{group_command.name}** - {get_text(self.context.guild, f'{group.cog.qualified_name.lower()}_help', f'{group_command.name}_brief')}\n"
        subcommands = get_text(self.context.guild, "help", "help.command_help.subcommands")
        emb.add_field(name=subcommands, value=sub_cmd_list, inline=False)
        await self.context.send(embed=formatted)
    
    async def send_cog_help(self, cog):
        if (cog.qualified_name.upper() in self.owner_cogs and not await self.context.bot.is_owner(self.context.author)) or cog.qualified_name.upper() in self.ignore_cogs:
            return
        pages = {}
        for cmd in cog.get_commands():
            if not await self.context.bot.is_owner(self.context.author) and (cmd.hidden or cmd.category=="Hidden"):
                continue
            if not cmd.category in pages:
                pages[cmd.category] = "```asciidoc\n"
            cmd_brief = get_text(self.context.guild, f"{cmd.cog_name.lower()}_help", f"{cmd.name}_brief")
            pages[cmd.category] += f"{cmd.name}{' '*int(17-len(cmd.name))}:: {cmd_brief}\n"
            if isinstance(cmd, commands.Group):
                for group_command in cmd.commands:
                    try:
                        cmd_brief = get_text(self.context.guild, f"{cog.qualified_name.lower()}_help", f"{group_command.parent}_{group_command.name}_brief")
                    except Exception:
                        cmd_brief = get_text(self.context.guild, f"{cog.qualified_name.lower()}_help", f"{group_command.name}_brief")
                    pages[cmd.category] += f"━ {group_command.name}{' '*int(15-len(group_command.name))}:: {cmd_brief}\n"
            else:
                cmd_brief = get_text(self.context.guild, f"{cog.qualified_name.lower()}_help", f"{cmd.name}_brief")
                pages[cmd.category] += f"{cmd.name}{' '*int(17-len(cmd.name))}:: {cmd_brief}\n"
        formatted = []
        for name, cont in pages.items():
            formatted.append(f"{name}\n{cont}")
        footer_text = get_text(self.context.guild, "help", "help.category_page.footer_info").format(self.context.prefix)
        pages = FieldPages(self.context,
                           entries=formatted,
                           title = cog.qualified_name.upper(),
                           thumbnail = cog.big_icon,
                           footericon = "https://cdn.discordapp.com/avatars/505532526257766411/d1cde11602889bd799dec9a82e29609f.webp?size=1024",
                           footertext = footer_text,
                           per_page=1)
        await pages.paginate()
