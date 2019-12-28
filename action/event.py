import enum
import abc
import discord





class Event(abc.ABC):
    pass


class Message(Event):
    pass

class MessageCommand(Message):
    pass
