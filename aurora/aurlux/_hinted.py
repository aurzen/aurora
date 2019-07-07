import typing as ty
import discord

def get_channel(self, id) -> ty.Union[discord.abc.GuildChannel, discord.abc.Messageable]:
    """Optional[Union[:class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`]]: Returns a channel with the
    given ID.

    If not found, returns ``None``.
    """
    return self._connection.get_channel(id)