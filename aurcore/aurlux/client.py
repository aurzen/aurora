import asyncio
import collections
import itertools
import logging
import pprint
import typing as ty

import discord

import aurcore.aurlux as aurlux
from aurcore.aurlux import Command, Contexter

from aurcore.utils import zutils
import aurcore.task as task

import functools


class Lux(discord.Client):
    commands = {}
    events = collections.defaultdict(lambda: [None, []])

    actionables: ty.List[task.action] = []

    def __init__(self, config, action_runner: task.action.ActionRunner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.auth_function = kwargs.get("auth_function")
        self.action_runner = action_runner
        if not zutils.k_bool(kwargs, "disable_builtins"):
            register_builtins(self)

    async def on_ready(self):
        logging.info("Ready!")

    async def on_connect(self):
        logging.info("Connected")

    async def on_message(self, message):
        if message.content.startswith(self.config["PREFIX"]):
            command_name = message.content[len(self.config["PREFIX"]):].split(" ")[0]
            cmd_ctx = aurlux.CommandContext(config=self.config, cmd_msg=message, cmd_name=command_name)
            action = self.commands[command_name].run(cmd_ctx)
            self.action_runner.submit(action)

    async def process_command(self, result: ty.Union[task.action, task.result]):
        pass

    @zutils.parametrized
    def command(func, self, name: str = None, aliases: ty.Iterable[str] = None, **attrs):
        logging.info(
            f"Registered function: func: {func.__name__}, override name = {name}, attrs: {pprint.pformat(attrs)}")
        command = Command(func, f_name=name, f_aliases=aliases)
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
