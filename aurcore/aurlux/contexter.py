import discord

from aurcore.utils import zutils
from aurcore.utils.zutils import k_bool


class Contexter:
    called_with = {}

    def __init__(self, message: discord.Message = None, guild: discord.Guild = None, configs: dict = None, auth_func=None):
        self.config = configs
        self.m = message  # type: discord.Message
        self.guild = guild if guild else (message.guild if message else None)
        self.deprefixed_content = None if not (self.m and self.config) else self.m.content[len(self.config["PREFIX"]):]
        self.auth_func = auth_func

    def check_auth(self, *args, **kwargs):
        if not self.auth_func:
            return True
        return self.auth_func(self, *args, **kwargs)

    def find_role(self, query):
        if k_bool(self.config, "ROLE_BY_CONFIG"):
            return self.find_role_config(query)
        else:
            return self.find_role_dynamic(query)

    def find_role_config(self, query):
        return self.guild.get_role(zutils.query_dict_softcase(self.config["ROLE_TO_ID"], query))

    def find_role_dynamic(self, query):

        if zutils.check_int(query):
            return self.guild.get_role(zutils.check_int(query))
        if isinstance(query, str):
            try:
                return next(role for role in self.guild.roles if role.name == query)
            except StopIteration:
                try:
                    return next(role for role in self.guild.roles if role.name.lower() == query.lower())
                except StopIteration:
                    return None

    def find_channel(self, query, dynamic=True):
        if "ROLE_TO_ID" in self.config and query in self.config["ROLE_TO_ID"]:
            return self.m.guild.get_role(zutils.query_dict_softcase(self.config["ROLE_TO_ID"][query], query))
        else:
            if not dynamic:
                return
            if isinstance(query, int):
                return self.m.guild.get_channel(query)
            if isinstance(query, str):
                try:
                    res = next(channel for channel in self.m.guild.channels if channel.name == query)
                except StopIteration:
                    res = next(channel for channel in self.m.guild.channels if channel.name.lower() == query.lower())
                return res
