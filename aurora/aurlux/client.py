import asyncio
import collections
import itertools
import logging
import pprint
import typing as ty

import discord

from aurora.aurlux import Command, Contexter
from aurora.utils import zutils
import aurora.task as task


class Lux(discord.Client):
    commands = {}
    events = collections.defaultdict(lambda: [None, []])

    actionables: ty.List[task.actionable] = []

    # def append_event(self, func, event_name=None):
    #     if not event_name:
    #         event_name = func.__name__
    #     exiting_event = getattr(self, event_name, None)
    #     if exiting_event:
    #         self.events[event_name][0] = exiting_event
    #
    #     self.events[event_name][1].append(func)
    #
    #     async def multihandler(*args, **kwargs):
    #         for command in itertools.chain([self.events[event_name][0]], self.events[event_name][1]):
    #             if command:
    #                 await command(*args, **kwargs)
    #
    #     setattr(self, event_name, multihandler)

    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.auth_function = kwargs.get("auth_function")
        if not zutils.k_bool(kwargs, "disable_builtins"):
            register_builtins(self)

    async def on_ready(self):
        logging.info("Ready!")

    async def on_connect(self):
        logging.info("Connected")

    async def on_message(self, message):
        ctx = Contexter(message=message, configs=self.config, auth_func=self.auth_function)
        if message.content.startswith(ctx.config["PREFIX"]):
            command_raw = ctx.deprefixed_content.lower()
            if command_raw in self.commands:
                await self.commands[command_raw].execute(ctx)
            elif command_raw.split(" ")[0] in self.commands:
                await self.commands[command_raw.split(" ")[0]].execute(ctx)

    async def process_command(self, result: ty.Union[task.actionable, task.result]):
        pass

    @zutils.parametrized
    def command(func, self, name: str = None, **attrs):
        logging.info(
            f"Registered function: func: {func.__name__}, override name = {name}, attrs: {pprint.pformat(attrs)}")
        command = Command(func, fname=name, **attrs)
        self.add_command(command)
        return command

    def add_command(self, command):
        self.commands[command.fname] = command

    def run_forever(self, func, delay=1, *args, **kwargs):
        async def forevered(*args_, **kwargs_):
            while True:
                func(*args_, **kwargs_)
                asyncio.sleep(delay)

        self.loop.run_until_complete(forevered(*args, **kwargs))


def register_builtins(lux: Lux):
    print("registering builtins?")

    @lux.command(name="aexec", onlyme=True)
    async def aexec_(ctx):
        return zutils.execute("aexec", ctx.deprefixed_content[6:], ctx=ctx)

    @lux.command(name="eval", onlyme=True)
    async def eval_(ctx):
        return zutils.execute("eval", ctx.deprefixed_content[5:], ctx=ctx)

    @lux.command(name="exec", onlyme=True)
    async def exec_(ctx):
        return zutils.execute("exec", ctx.deprefixed_content[5:], ctx=ctx)

    @lux.command(name="aeval", onlyme=True)
    async def aeval_(ctx):
        return await zutils.aeval(ctx.deprefixed_content[6:], ctx=ctx)

    @lux.command(name="ping", onlyme=True)
    async def ping(ctx):
        return "pong!"
