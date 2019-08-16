import aurcore.aurlux as aurlux
import discord
import collections
import typing as ty


class CommandContext:
    def __init__(self, config, cmd_msg: discord.Message, cmd_name: str):
        self.config = config
        self.cmd_msg = cmd_msg
        self.cmd_name = cmd_name

        self.m: discord.Message = cmd_msg

        self.args = self.m.content[(len(config["PREFIX"]) + len(cmd_name)):]

        pass


class Command:
    def __init__(self, func, f_name: str = None, f_aliases: ty.Iterable[str] = None):
        self.f_name = f_name or func.__name__.lower()
        self.f_aliases = f_aliases or []

    async def execute(self, ctx: aurlux.contexter):
        pass
