import discord
import action.event
import typing as ty
class Context:
    event_type: ty.Type[action.event.Event]
    pass

class MessageContext(Context):
    def __init__(self, message: discord.Message):
        self.message = message

class CommandContext(MessageContext):
    def __init__(self, message: discord.Message):
        self.message = message
