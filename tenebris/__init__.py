import asyncio
import collections
import logging
import typing as ty
import action as ac
import action.filter
import discord


class Tenebris(discord.Client):
    commands = {}
    events = collections.defaultdict(lambda: [None, []])

    def __init__(self, actioner: ac.ActionRunner, *args, **kwargs):
        super(Tenebris, self).__init__(*args, **kwargs)
        self.actioner = actioner
        self.register_builtins()

    async def on_ready(self):
        logging.info("Ready!")

    async def on_connect(self):
        logging.info("Connected")

    async def on_message(self, message):
        await self.actioner.submit_event(
            ctx=ac.context.MessageContext(message=message)
        )

    # def run_forever(self, func, delay=1, *args, **kwargs):
    #     async def forevered(*args_, **kwargs_):
    #         while True:
    #             func(*args_, **kwargs_)
    #             await asyncio.sleep(delay)
    #
    #     self.loop.run_until_complete(forevered(*args, **kwargs))
    #

    def register_builtins(self):
        @self.actioner.register_auto(trigger=ac.event.Message,
                                     filters=[ac.filter.CommandMessage(command_prefix="test")])
        async def test(ctx: ac.context.CommandContext):
            print("Test")
            print(ctx)
            # return zutils.execute("aexec", ctx.deprefixed_content[6:], ctx=ctx)



        # @lux.command(name="eval", onlyme=True)
        # async def eval_(ctx):
        #     return zutils.execute("eval", ctx.deprefixed_content[5:], ctx=ctx)
        #
        # @lux.command(name="exec", onlyme=True)
        # async def exec_(ctx):
        #     return zutils.execute("exec", ctx.deprefixed_content[5:], ctx=ctx)
        #
        # @lux.command(name="aeval", onlyme=True)
        # async def aeval_(ctx):
        #     return await zutils.aeval(ctx.deprefixed_content[6:], ctx=ctx)
        #
        # @lux.command(name="ping", onlyme=True)
        # async def ping(ctx):
        #     return "pong!"
