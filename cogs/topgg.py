from discord.ext import commands
from aiohttp import web
import discord

class TopGG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_port = 5000
        self.webhook_path = "/dblwebhook"
        self.webhook_auth = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjUwNTUzMjUyNjI1Nzc2NjQxMSIsImJvdCI6dHJ1ZSwiaWF0IjoxNTc2Mjk1NzU3fQ.EBoXH4K6cqUlw5DkIuX5C3o6rW6tJ6IQFqICB9ZGyxI"
        self.bot.loop.create_task(self.webhook())
        self.icon = ""
        self.big_icon = ""

    async def webhook(self):
        async def vote_handler(request):
            req_auth = request.headers.get('Authorization')
            if self.webhook_auth == req_auth:
                data = await request.json()
                if data.get('type') == 'upvote':
                    event_name = 'dbl_vote'
                elif data.get('type') == 'test':
                    event_name = 'dbl_test'
                self.bot.dispatch(event_name, data)
                return web.Response()
            else:
                return web.Response(status=401)
            c = await self.bot.fetch_channel(381963689470984203)
            await c.send("{} just voted/tested.".format(request['user']))

        app = web.Application(loop=self.bot.loop)
        app.router.add_post(self.webhook_path, vote_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        self._webserver = web.TCPSite(runner, '0.0.0.0', self.webhook_port)
        await self._webserver.start()

def setup(bot):
    bot.add_cog(TopGG(bot))