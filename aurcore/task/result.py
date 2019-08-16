import typing as ty

import discord

from aurcore.utils.discord import send_to


class Result:
    def __init__(self, target: ty.Union[discord.abc.Messageable], report_args=(), report_kwargs=None):
        if report_kwargs is None:
            report_kwargs = {}
        self.target = target
        self.report_args = report_args
        self.report_kwargs = report_kwargs

    def report(self):
        if isinstance(self.target, discord.abc.Messageable):
            send_to(self.target, *self.report_args, **self.report_kwargs)
