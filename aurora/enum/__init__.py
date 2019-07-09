import enum


@enum.unique
class EventType(enum.Enum):
    DISCORD_MESSAGE = enum.auto()
