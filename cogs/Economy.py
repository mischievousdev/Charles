import discord
import json
import humanize
import time
import random

#from utils.default import commandExtra
from discord.ext import commands
from utils import checks, ReadableTime
from datetime import datetime, timedelta

class Economy(commands.Cog, name="Economy"):
    def __init__(self, bot):
        self.bot = bot

    def load_data(self, ctx):
        with open(f'db/guilds/{str(ctx.guild.id)}.json', 'r') as f:
            data = json.load(f)

        return data

    def dump_data(self, ctx, data):
        with open(f'db/guilds/{str(ctx.guild.id)}.json', 'w') as f:
            json.dump(data, f, indent=4)

    @checks.testcommand()
    @commands.group()
    async def account(self, ctx):
        pass

    @checks.testcommand()
    @account.command()
    async def create(self, ctx):
        d = self.load_data(ctx)

        if str(ctx.author.id) in d['Economy']['Users']:
            return await ctx.send("You already have an account.")

        d['Economy']['Users'][str(ctx.author.id)] = {
            "Balance": 100,
            "Bank": 0,
            "NextDaily": 1571340018
        }
        self.dump_data(ctx, d)
        await ctx.send('Economy account succesfully created!')

    @checks.testcommand()
    @account.command()
    async def delete(self, ctx):
        d = self.load_data(ctx)

        if not str(ctx.author.id) in d['Economy']['Users']:
            return await ctx.send("You do not have an account yet.")

        d['Economy']['Users'].pop(str(ctx.author.id))
        self.dump_data(ctx, d)
        await ctx.send('Economy account succesfully deleted!')

    @checks.testcommand()
    @commands.command(aliases=['bal'])
    async def balance(self, ctx, user:discord.Member=None):
        if user == None:
            user = ctx.author

        d = self.load_data(ctx)

        if not str(user.id) in d['Economy']['Users']:
            return await ctx.send("This user does not have an account yet.")

        totalmoney = int(d['Economy']['Users'][str(user.id)]['Balance']) + int(d['Economy']['Users'][str(user.id)]['Bank'])
        await ctx.send(f">>> **User:** {user.name}\n\n**Cash:** {str(d['Economy']['Users'][str(user.id)]['Balance'])}\n**Bank:** {str(d['Economy']['Users'][str(user.id)]['Bank'])}\n**Total:** {totalmoney}")

    @checks.testcommand()
    @commands.command()
    async def daily(self, ctx):
        d = self.load_data(ctx)

        if not str(ctx.author.id) in d['Economy']['Users']:
            return await ctx.send("You do not have an account yet.")

        now = int(time.time())
        tomorrow = now + 86400

        next_d = d['Economy']['Users'][str(ctx.author.id)]['NextDaily']
        d_now = time.time()

        if next_d == d_now or d_now > next_d:
            bal = d['Economy']['Users'][str(ctx.author.id)]['Balance']
            random_cash = random.randint(10, 250)

            d['Economy']['Users'][str(ctx.author.id)]['Balance'] = bal + random_cash
            d['Economy']['Users'][str(ctx.author.id)]['NextDaily'] = tomorrow

            self.dump_data(ctx, d)

            return await ctx.send(f"You received ${str(random_cash)} as your daily reward!")

        else:
            timeBetween = int(next_d - d_now)

            weeks   = int(timeBetween/604800)
            days    = int((timeBetween-(weeks*604800))/86400)
            hours   = int((timeBetween-(days*86400 + weeks*604800))/3600)
            minutes = int((timeBetween-(hours*3600 + days*86400 + weeks*604800))/60)
            seconds = int(timeBetween-(minutes*60 + hours*3600 + days*86400 + weeks*604800))

            readable_time = f"{hours} hours, {minutes} minutes and {seconds} seconds."

            await ctx.send(f"Next daily claim in {readable_time}")

    @checks.testcommand()
    @commands.command()
    async def give(self, ctx, user:discord.Member, *, amount:int):
    	d = self.load_data(ctx)

    	author_balance = d['Economy']['Users'][str(ctx.author.id)]['Balance']

    	d['Economy']['Users'][str(ctx.author.id)]['Balance'] = author_balance - amount

    	user_balance = d['Economy']['Users'][str(user.id)]['Balance']

    	d['Economy']['Users'][str(user.id)]['Balance'] = user_balance + amount

    	self.dump_data(ctx, d)

    	await ctx.send(f'Paid ${str(amount)} to {user}')

    @checks.testcommand()
    @commands.command()
    async def bet(self, ctx, *, amount:int):
        d = self.load_data(ctx)
        bal = d['Economy']['Users'][str(ctx.author.id)]['Balance']

        if amount > bal:
            return await ctx.send("You do not have enough money for that!")

        num = random.randint(1, 10)

        if num in [1, 3, 5, 7, 9]:
            d['Economy']['Users'][str(ctx.author.id)]['Balance'] = bal + amount
            await ctx.send(f"You won! ${str(amount)} has been added to your account.")
        else:
            d['Economy']['Users'][str(ctx.author.id)]['Balance'] = bal - amount
            await ctx.send(f"You lost... ${str(amount)} has been removed from your account.")

        self.dump_data(ctx, d)

    @checks.testcommand()
    @commands.command()
    async def lb(self, ctx):
        d = self.load_data(ctx)
        show_max = 10
        lb_msg = ""

        if len(d['Economy']['Users']) <= 10:
            show_max = len(d['Economy']['Users'])

        #keep with the alphanumerical sorting, but sort by Balance instead of user ID
        def key(data): 
            return data["Balance"]

        bal_list = sorted([{"user":user, **data} for user, data in d['Economy']['Users'].items()], key=key, reverse=True)

        for index, data in enumerate(bal_list[:int(show_max)], start=1):
            lb_msg += f"`{index}.` **{self.bot.get_user(int(data['user']))}** - ${str(data['Balance'])}\n"

        e = discord.Embed(color=self.bot.embed_color)
        e.set_author(name=f"Leaderboard for - {ctx.guild.name}", icon_url=ctx.guild.icon_url)
        e.description = lb_msg

        await ctx.send(embed=e)

    @checks.testcommand()
    @commands.command()
    async def deposit(self, ctx, amount):
        d = self.load_data(ctx)

        if not str(ctx.author.id) in d['Economy']['Users']:
            return await ctx.send("You do not have an account yet.")

        balance = d['Economy']['Users'][str(ctx.author.id)]['Balance']
        bank = d['Economy']['Users'][str(ctx.author.id)]['Bank']

        if d['Economy']['Users'][str(ctx.author.id)]['Balance'] == 0:
            return await ctx.send("You do not have any money to deposit.")

        if amount.lower() == "all":
            amount = d['Economy']['Users'][str(ctx.author.id)]['Balance']

        if int(amount) > d['Economy']['Users'][str(ctx.author.id)]['Balance']:
            return await ctx.send("You do not have so much money to deposit.")

        d['Economy']['Users'][str(ctx.author.id)]['Balance'] = balance - int(amount)
        d['Economy']['Users'][str(ctx.author.id)]['Bank'] = bank + int(amount)

        self.dump_data(ctx, d)

        await ctx.send(f"Deposited ${amount} to your bank!")

    @checks.testcommand()
    @commands.command()
    async def withdraw(self, ctx, amount):
        d = self.load_data(ctx)

        if not str(ctx.author.id) in d['Economy']['Users']:
            return await ctx.send("You do not have an account yet.")

        balance = d['Economy']['Users'][str(ctx.author.id)]['Balance']
        bank = d['Economy']['Users'][str(ctx.author.id)]['Bank']

        if d['Economy']['Users'][str(ctx.author.id)]['Bank'] == 0:
            return await ctx.send("You do not have any money to withdraw.")

        if amount.lower() == "all":
            amount = d['Economy']['Users'][str(ctx.author.id)]['Bank']

        if int(amount) > d['Economy']['Users'][str(ctx.author.id)]['Bank']:
            return await ctx.send("You do not have so much money to withdraw.")

        d['Economy']['Users'][str(ctx.author.id)]['Balance'] = balance + int(amount)
        d['Economy']['Users'][str(ctx.author.id)]['Bank'] = bank - int(amount)

        self.dump_data(ctx, d)

        await ctx.send(f"Withdrew ${amount} from your bank!")



def setup(bot):
    bot.add_cog(Economy(bot))