import discord
import action.context
import abc


class Filter(abc.ABC):
    @abc.abstractmethod
    def accepts(self, ctx: action.context.Context):
        ...


class CommandMessage(Filter):
    def __init__(self, command_prefix):
        self.command_prefix = command_prefix

    def accepts(self, ctx: action.context.MessageContext):
        return ctx.message.content.startswith(self.command_prefix)
