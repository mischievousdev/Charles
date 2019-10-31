import discord
import json
import humanize
import time
import random

#from utils.default import commandExtra
from discord.ext import commands
from utils import checks, ReadableTime
from datetime import datetime, timedelta

card_list = {
    "2": random.choice(["<:2D:638905315680845875>", "<:2C:638905316645273605>", "<:2H:638904540543844376>", "<:2S:638904816176857098>"]),
    "3": random.choice(["<:3D:638905315894493185>", "<:3C:638905317014372382>", "<:3H:638904540665479208>", "<:3S:638904816298360832>"]),
    "4": random.choice(["<:4D:638905315156295681>", "<:4C:638905316322312192>", "<:4H:638904540065955863>", "<:4S:638904816017604649>"]),
    "5": random.choice(["<:5D:638905315844161546>", "<:5C:638905316402135052>", "<:5H:638904542242799659>", "<:5S:638904816126394388>"]),
    "6": random.choice(["<:6D:638905315840229395>", "<:6C:638905316788142110>", "<:6H:638904540418015253>", "<:6S:638904816168599572>"]),
    "7": random.choice(["<:7D:638905315324330004>", "<:7C:638905316670701599>", "<:7H:638904540711747584>", "<:7S:638904816021667840>"]),
    "8": random.choice(["<:8D:638905316502929438>", "<:8C:638905316691542016>", "<:8H:638904540405694478>", "<:8S:638904816256548864>"]),
    "9": random.choice(["<:9D:638905315735371787>", "<:9C:638905316645273635>", "<:9H:638904540799959040>", "<:9S:638904816067805185>"]),
    "10": random.choice(["<:10D:638905315311616036>", "<:10C:638905316368449557>", "<:10H:638904540862742557>", "<:10S:638904816130719745>"]),
    "11": random.choice(["<:AD:638905314992848906>", "<:AC:638905316381032461>", "<:AH:638904540690644992>", "<:AS:638904816248029184>"]),
    "K": random.choice(["<:KD:638905315206627380>", "<:KC:638905316519706654>", "<:KH:638904540665610299>", "<:KS:638904816160079872>"]),
    "Q": random.choice(["<:QD:638905315487645706>", "<:QC:638905316435820556>", "<:QH:638904543987367937>", "<:QS:638904816281583616>"]),
    "J": random.choice(["<:JD:638905315395633162>", "<:JC:638905316339220503>", "<:JH:638904540703358976>", "<:JS:638904816474783744>"])
}

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


    @staticmethod
    def generate_cards():
        cards_out = list()
        cards_out_n = list()
        amount = 0
        cards = [card for card in card_list]
        has_hit = False
        while True:
            card = random.choice(cards)
            if card not in cards_out:
                cards_out.append(card)
                if card in ["K", "Q", "J"]:
                    card = 10
                if card == "11":
                    if not has_hit or not amount > 11:
                        card = 11
                        has_hit = True
                    else:
                        card = 1
                amount += int(card)
                cards_out_n.append(int(card))
            if len(cards_out) == 5:
                break
        return cards_out, cards_out_n, amount

    async def blackjack_input(self, ctx):
        while True:
            x = await self.bot.wait_for("message", check=lambda m: m.channel == ctx.message.channel and m.author == ctx.author)

            if str(x.content).lower() == "hit":
                move = 0
                break
            elif str(x.content).lower() == "stay":
                move = 1
                break
            else:
                pass
        try:
            await x.delete()
        except:
            pass
        return move

    @checks.testcommand()
    @commands.command(aliases=["bjtest"])
    async def blackjacktest(self, ctx, amount: int):
        """blackjack"""

        if amount <= 0:
            return await ctx.send("You can't bet that low...")
#        if (author_balance - amount) < 0:
#            return await ctx.send("You don't have that much to bet...")
        if amount > 50000:
            return await ctx.send("You can't bet past 50k")

#        await self.__update_balance(ctx.author.id, author_balance - amount)
#        await self.__add_bettime(ctx.author.id)

        author_deck, author_deck_n, author_amount = self.generate_cards()
        bot_deck, bot_deck_n, bot_amount = self.generate_cards()
        get_amount = lambda i, a: [i[z] for z in range(a)]

        em = discord.Embed(color=self.bot.embed_color, title="Blackjack", description="Type `hit` or `stay`.")
        em.add_field(name="Your Cards ({})".format(sum(get_amount(author_deck_n, 2))),
                     value=" ".join([card_list[x] for x in get_amount(author_deck, 2)]),
                     inline=True)
        em.add_field(name="My Cards (?)",
                     value=" ".join(["<:cardback:638904890302660628>" for x in get_amount(bot_deck, 2)]),
                     inline=True)

        msg = await ctx.send(embed=em)

        bot_val = 2
        bot_stay = False
        for i, x in enumerate(range(3), start=3):
            move = await self.blackjack_input(ctx)
            em = discord.Embed(color=self.bot.embed_color, title="Blackjack", description="Type `hit` or `stay`.")

            if not bot_stay:
                if bot_val == 4:
                    bot_stay = True
                elif sum(get_amount(bot_deck_n, bot_val)) <= 16:
                    bot_val += 1
                elif sum(get_amount(bot_deck_n, bot_val)) == 21:
                    bot_stay = True
                else:
                    if random.randint(0, 1) == 0:
                        bot_stay = True
                    else:
                        bot_val += 1

            if move == 1:
                i -= 1
                em.add_field(name="Your Cards ({})".format(sum(get_amount(author_deck_n, i))),
                             value=" ".join([card_list[x] for x in get_amount(author_deck, i)]),
                             inline=True)
                em.add_field(name="My Cards ({})".format(sum(get_amount(bot_deck_n, bot_val))),
                             value=" ".join([card_list[x] for x in get_amount(bot_deck, bot_val)]),
                             inline=True)

                if sum(get_amount(author_deck_n, i)) == sum(get_amount(bot_deck_n, bot_val)):
                    em.description = "Nobody won."
#                    await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + amount)
                elif sum(get_amount(author_deck_n, i)) > 21 and sum(get_amount(bot_deck_n, bot_val)) > 21:
                    em.description = "Nobody won."
#                    await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + amount)
                elif sum(get_amount(author_deck_n, i)) > sum(get_amount(bot_deck_n, bot_val)) or \
                    sum(get_amount(bot_deck_n, bot_val)) > 21:
                    em.description = "You beat me"
#                    await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + int(amount * 1.75))
                else:
                    em.description = "I beat you"

                await msg.edit(embed=em)
                return

            if sum(get_amount(bot_deck_n, bot_val)) > 21 or sum(get_amount(author_deck_n, i)) > 21:
                if sum(get_amount(author_deck_n, i)) > 21 and sum(get_amount(bot_deck_n, bot_val)) > 21:
                    em.description = "Nobody won."
#                    await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + amount)
                elif sum(get_amount(author_deck_n, i)) > 21:
                    em.description = "You went over 21 and I won"
                else:
                    em.description = "I went over 21 and you won"
#                    await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + int(amount * 1.75))
                em.add_field(name="Your Cards ({})".format(sum(get_amount(author_deck_n, i))),
                             value=" ".join([card_list[x] for x in get_amount(author_deck, i)]),
                             inline=True)
                em.add_field(name="My Cards ({})".format(sum(get_amount(bot_deck_n, bot_val))),
                             value=" ".join([card_list[x] for x in get_amount(bot_deck, bot_val)]),
                             inline=True)
                await msg.edit(embed=em)
                return

            em.add_field(name="Your Cards ({})".format(sum(get_amount(author_deck_n, i))),
                         value=" ".join([card_list[x] for x in get_amount(author_deck, i)]),
                         inline=True)
            em.add_field(name="My Cards (?)",
                         value=" ".join(["<:cardback:638904890302660628>" for x in get_amount(bot_deck, bot_val)]),
                         inline=True)
            await msg.edit(embed=em)
        if sum(get_amount(bot_deck_n, 5)) > 21 or sum(get_amount(author_deck_n, 5)) > 21:
            if sum(get_amount(author_deck_n, i)) > 21 and sum(get_amount(bot_deck_n, bot_val)) > 21:
                em.description = "Nobody won."
#                await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + amount)
            elif sum(get_amount(author_deck_n, i)) > 21:
                em.description = "You went over 21 and I won"
            else:
                em.description = "I went over 21 and you won"
#                await self.__update_balance(ctx.author.id, (await self.__get_balance(ctx.author.id)) + int(amount * 1.75))
            em.add_field(name="Your Cards ({})".format(sum(get_amount(author_deck_n, i))),
                         value=" ".join([card_list[x] for x in get_amount(author_deck, i)]),
                         inline=True)
            em.add_field(name="My Cards ({})".format(sum(get_amount(bot_deck_n, bot_val))),
                         value=" ".join([card_list[x] for x in get_amount(bot_deck, bot_val)]),
                         inline=True)
            await msg.edit(embed=em)



def setup(bot):
    bot.add_cog(Economy(bot))
