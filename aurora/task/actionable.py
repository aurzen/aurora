import asyncio
import typing as ty
from datetime import datetime, timedelta

import discord
import functools

from aurora.utils.time import parse_time
from aurora.utils.discord import send_to


class Action:
    pass


class AutoAction(Action):
    pass


class InstantAction(Action):
    pass


class ActionRunner:
    def __init__(self):
        pass
        self.autos: ty.List[AutoAction] = []

    def handle(self, action: Action):
        if isinstance(action, AutoAction):
            self.autos.append(action)

        pass


class TimedAutoAction(AutoAction):
    def __init__(self, dt_end: datetime, action: callable,
                 callback: callable = lambda x: x,
                 action_kwargs: dict = None):
        self.dt_end = dt_end
        self.action = action
        self.action_kwargs = action_kwargs or {}
        self.asynchro = False
        self.callback = callback

    def is_done(self):
        return datetime.utcnow() > self.dt_end

    def tick(self):
        if datetime.utcnow() > self.dt_end:
            self.execute()

    def execute(self):
        if isinstance(self.action):
            task = asyncio.create_task(self.action(**self.action_kwargs))
            task.add_done_callback(self.callback)
        else:
            return self.callback(self.action(**self.action_kwargs))


class Reminder(TimedAutoAction):
    def __init__(self, text, time_inp: ty.Union[datetime, timedelta, str, int],
                 output: ty.Union[discord.abc.Messageable, int] = None):
        action = functools.partial(send_to, destination=output, content=text)
        super().__init__(dt_end=parse_time(time_inp), action=action)
