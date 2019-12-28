import abc
import collections
import typing as ty

from action.event import Event
from action.filter import Filter
from action.context import Context
import logging
import traceback
import pprint
import aurcore.utils.zutils
import asyncio

logger = logging.getLogger(__name__)
syslog = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(name)s-%(funcName)s:%(message)s')
syslog.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(syslog)

logger = logging.LoggerAdapter(logger, {'app_name': 'Super App'})


class Action(abc.ABC):
    def __init__(self, func: ty.Callable, filters: ty.List[Filter], name=None):
        self.filters = filters
        if asyncio.iscoroutinefunction(func):
            self.func = func
        else:
            def f(*args, **kwargs):
                return asyncio.get_event_loop().run_in_executor(None, func(*args, **kwargs))

            self.func = f

        self.name = name or self.func.__name__

    def __repr__(self):
        return f"Action {self.name}"


class AutoAction(Action):
    async def execute(self, ctx: Context):
        if all([filter_.accepts(ctx) for filter_ in self.filters]):
            await self.func(ctx)


class ActionRunner:
    def __init__(self):
        self.triggered: ty.Dict[ty.Type[Event], ty.List[AutoAction]] = collections.defaultdict(list)

    async def submit_event(self, ctx: Context):
        event_classes = [key for key in self.triggered.keys() if isinstance(key, ctx.event_type)]

        results = await asyncio.gather(
            *[action for ev_sublist in [self.triggered[event] for event in event_classes] for action in ev_sublist]
            , return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logging.error(repr(result))
            else:
                logging.info(f"")

    @aurcore.utils.zutils.parametrized_im
    def register_auto(self, func, trigger, filters: ty.List[Filter], **attrs):
        logging.info(
            f"Registered function: func: {func.__name__}, attrs: {pprint.pformat(attrs)}")

        action = AutoAction(func, filters=filters)
        self.triggered[trigger].append(action)

        return func


class CommandAction(Action):
    pass

#

# class InstantAutoAction(AutoAction):
#     pass
#
#
# class ResumableAutoAction(AutoAction):
#     pass
#
#
# class EventedAction(Action):
#     @abc.abstractmethod
#     def hooks(self):
#         pass
#
#

#
#
# class TimedAutoAction(AutoAction, abc.ABC):
#
#     def __init__(self, dt_end: datetime, action: callable,
#                  callback: callable = lambda x: x,
#                  action_kwargs: dict = None):
#         self.dt_end = dt_end
#         self.action = action
#         self.action_kwargs = action_kwargs or {}
#         self.asynchro = False
#         self.callback = callback
#
#     def is_done(self):
#         return datetime.utcnow() > self.dt_end
#
#     def tick(self):
#         if datetime.utcnow() > self.dt_end:
#             self.execute()
#
#     def execute(self):
#         if isinstance(self.action):
#             task = asyncio.create_task(self.action(**self.action_kwargs))
#             task.add_done_callback(self.callback)
#         else:
#             return self.callback(self.action(**self.action_kwargs))
#
#
# class Reminder(TimedAutoAction):
#     def __init__(self, text, time_inp: ty.Union[datetime, timedelta, str, int],
#                  output: ty.Union[discord.abc.Messageable, int] = None):
#         action = functools.partial(send_to, destination=output, content=text)
#         super().__init__(dt_end=parse_time(time_inp), action=action)
