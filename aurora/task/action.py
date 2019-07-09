import asyncio
import typing as ty
from datetime import datetime, timedelta

import discord
import functools
import abc
import collections
from aurora.utils.discord import send_to
from aurora.utils.time import parse_time
import aurora.event


class Action(abc.ABC):
    pass


class AutoAction(Action):
    pass


class InstantAutoAction(AutoAction):
    pass


class ResumableAutoAction(AutoAction):
    pass


class EventedAction(Action):
    @abc.abstractmethod
    def hooks(self):
        pass


class ActionRunner:
    def __init__(self):
        self.autos: ty.Dict[aurora.event.Event, ty.List[Action]] = collections.defaultdict(list)

    def submit(self, action: Action):
        if isinstance(action, AutoAction):
            for hook in action.hooks():
                self.autos[hook].append(action)

        pass


class TimedAutoAction(AutoAction, abc.ABC):

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
