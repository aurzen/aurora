from __future__ import annotations

import typing as ty
import asyncio
import logging
import collections as clc
import functools as fnt
import dataclasses as dtc

logging.basicConfig()
log = logging.getLogger("aurevent")


class AutoRepr:
    def __repr__(self):
        items = []
        for prop, value in self.__dict__.items():
            try:
                item = "%s = %r" % (prop, value)
                assert len(item) < 100
            except:
                item = "%s: <%s>" % (prop, value.__class__.__name__)
            items.append(item)

        return "%s(%s)" % (self.__class__.__name__, ', '.join(items))

    # class AutoRepr:


#     @staticmethod
#     def repr(obj):
#         items = []
#         for prop, value in obj.__dict__.items():
#             try:
#                 item = "%s = %r" % (prop, value)
#                 assert len(item) < 100
#             except:
#                 item = "%s: <%s>" % (prop, value.__class__.__name__)
#             items.append(item)
#
#         return "%s(%s)" % (obj.__class__.__name__, ', '.join(items))
#
#     def __init__(self, cls):
#         cls.__repr__ = AutoRepr.repr
#         self.cls = cls
#
#     def __call__(self, *args, **kwargs):
#         return self.cls(*args, **kwargs)


class Event(AutoRepr):
    def __init__(self, __event_name: str, *args, **kwargs):
        self.name: str = __event_name.lower()
        self.args: ty.Tuple = args
        self.kwargs: ty.Dict = kwargs

    def elevate(self, router: EventRouter):
        if self.name.startswith(":"):
            self.name = f"{router.name}{self.name}"
            if router.parent:
                self.name = f":{self.name}"

        elif self.name.startswith(router.name) and router.parent:
            self.name = f":{self.name}"

        return self

    def lower(self):
        self.name: str = self.name.partition(":")[2]
        # print(f"new name: {self.name}")
        return self


EventFunction: ty.TypeAlias = ty.Callable[[Event], ty.Coroutine]


@dtc.dataclass(frozen=True)
class EventWaiter:
    future: asyncio.Future
    check: ty.Callable[[Event], ty.Coroutine[bool]]


class EventMuxer(AutoRepr):
    __router = None
    __lock = asyncio.Lock()

    def __init__(self, name):
        self.name = name
        self.router: ty.Optional[EventRouter] = None
        self.funcs: ty.Set[EventFunction] = set()
        self.waiters: ty.Set[EventWaiter] = set()

    async def fire(self, ev: Event):

        # if self.router: await self.router.dispatch(ev)
        async with self.__lock:
            new_waiters: ty.Set[EventWaiter] = set()
            for waiter in self.waiters:
                if waiter.future.cancelled():
                    continue
                if await waiter.check(ev):
                    waiter.future.set_result(ev)
                else:
                    new_waiters.add(waiter)
            self.waiters = new_waiters

        coros = [func(ev) for func in self.funcs]
        if self.router: coros.append(self.router.dispatch(ev))
        return await asyncio.gather(*coros)

    def remove_listener(self, func: ty.Union[EventFunction, EventWaiter]):
        container = self.waiters if isinstance(func, EventWaiter) else self.funcs
        container.remove(func)

    def add_listener(self, func: ty.Union[EventFunction, EventWaiter]):
        container = self.waiters if isinstance(func, EventWaiter) else self.funcs
        print(f"adding {func} on {self}")
        container.add(func)
        # self.one_times.add(one_time)

    @property
    def router(self):
        return self.__router

    @router.setter
    def router(self, router: EventRouter):
        if self.__router and router:
            raise ValueError(f"Attempted to set another router for {self}")
        else:
            self.__router = router


class EventRouter(AutoRepr):
    def __init__(self, name: str, parent: EventRouter = None):
        self.name = name.lower()
        self.parent = parent
        if self.parent:
            # self.name = f":{self.name}"
            self.parent.register_listener(self.name, self)
        self.listeners: ty.Dict[str, EventMuxer] = {}

    @property
    def root(self):
        return self.parent.root if self.parent else self

    def detatch_child(self, child_router: EventRouter):
        self.listeners[child_router.name].router = None

    def detatch(self):
        self.parent.detatch_child(self)

    def endpoint(self, name: str, decompose=False) -> ty.Callable[[ty.Callable], EventMuxer]:
        def __decorator(func: ty.Callable[[...], ty.Awaitable]):
            if not asyncio.iscoroutinefunction(func):
                @fnt.wraps(func)
                async def __async_wrapper(event: Event):
                    return func(event)

                _func = __async_wrapper
            else:
                _func = func
            if decompose:
                @fnt.wraps(_func)
                async def __decompose(event: Event):
                    return await func(*event.args, **event.kwargs)

                _func = __decompose
            logging.debug("[%s] Attaching endpoint %s as <%s>", self, func, name.lower())

            return self.register_listener(name=name.lower(), listener=_func)
            # return func

        return __decorator

    def register_listener(self, name: str, listener: ty.Union[EventFunction, EventRouter, EventWaiter]) -> EventMuxer:
        name = name.lower()
        logging.debug("[%s] Registering listener %s as <%s>", self, listener, name)
        if isinstance(listener, EventRouter):
            if ":" in name:
                raise ValueError(f"[{self}] : not allowed in listener identifier, register sub-router locally")
            listener.parent = self
            self.listeners.setdefault(listener.name, EventMuxer(name=name))
            # self.listeners[listener.name] = self.listeners.get(listener.name, EventMuxer(name=name))
            self.listeners[listener.name].router = listener
            return self.listeners[listener.name]

        if name.startswith(":"):
            if self.parent:
                return self.parent.register_listener(f":{self.name}{name}", listener)
            else:
                return self.register_listener(f"{self.name}{name}", listener)

        if not name.startswith(self.name):
            if self.parent:
                return self.parent.register_listener(name, listener)
            raise ValueError(f"[{self}] Attempting to register listener with invalid route {name}")

        _, target, remainder, *_ = name.split(":", 2) + ["", ""]
        self.listeners.setdefault(target, EventMuxer(name=target))

        event_muxer = self.listeners[target]
        if remainder:  # target refers to a sub-router
            if sub_router := event_muxer.router:
                return sub_router.register_listener(f"{target}:{remainder}", listener)
            else:
                raise ValueError(f"[{self}] Attempting to descend into nonexistent subrouter {event_muxer} | {name}")
        else:  # target refers to a listener
            event_muxer.add_listener(listener)
            # self.master_lookup[listener] = event_muxer
        logging.debug("[%s] Registered! Listeners[%s] Muxer[%s] Listner [%s]", self, self.listeners, event_muxer, listener)
        print(f"Registering!! {event_muxer} {listener}")
        return event_muxer

        #
        # elif name.startswith(":"):
        #     name = name[1:]
        #     final_listener = listener
        #     if isinstance(listener, ty.Callable) and not asyncio.iscoroutinefunction(listener):
        #         async def __coro_wrapper(*args, **kwargs):
        #             return listener(*args, **kwargs)
        #
        #         final_listener = __coro_wrapper
        #     self.listeners[name].add(final_listener)
        # else:
        #     if not name.startswith(f"{self.name}:"):
        #         if not self.parent:
        #             raise ValueError(f"Attempting to register invalid listener {self.name} on {self}")
        #         self.parent.register_listener(name, listener)
        #     else:
        #         self.register_listener(name.removeprefix(self.name), listener)
        # logging.debug("[%s] Finished registering listener %s as <%s>, new listeners: %s", self, listener, name, self.listeners)

    async def submit(self, event: Event):
        logging.debug("[%s] Submitting event (%s)", self, event)
        event.elevate(self)

        if self.parent:
            await self.parent.submit(event)
        else:
            await self.dispatch(event)

    def wait_for(
            self,
            event_name: str,
            check: ty.Union[ty.Callable[[Event], ty.Awaitable[bool]],
                            ty.Callable[[Event], bool]] = lambda _: True,
            timeout: ty.Optional[float] = None
    ) -> asyncio.Future:
        ev = asyncio.Future()
        if not asyncio.iscoroutinefunction(check):
            @fnt.wraps(check)
            async def _check(event: Event):
                return check(event)
        else:
            _check = check
        event_waiter = EventWaiter(future=ev, check=_check)
        self.register_listener(event_name, event_waiter)

        return asyncio.wait_for(ev, timeout)

    async def dispatch(self, event: Event):
        logging.debug("[%s] Dispatching event (%s), current listeners: %s", self, event, self.listeners)
        chunked = event.name.split(":")
        # Try from most to least specific
        # while event_chunk := event.lower() != "":
        for i in range(len(chunked), 1, -1):
            event_chunk = ":".join(chunked[1:i])
            if event_chunk in self.listeners:
                await self.listeners[event_chunk].fire(event.lower())
                # for listener in self.listeners[event_chunk]:
                #     await listener(event.lower())
                # print(f"LISTENER PRODUCED: {res}")
                # res = await asyncio.gather(*[listener(event.lower()) for listener in self.listeners[event_chunk]])
                # print(f"GATHER RESULTS: {res}")
                # await self.listeners[event.name](event)
                break

    def __call__(self, event: Event) -> ty.Awaitable:
        return self.dispatch(event=event)

    def __repr__(self):
        return f"EventRouter(name={self.name}, parent={self.parent})"
