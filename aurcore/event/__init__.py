from __future__ import annotations

import typing as ty
import asyncio
import logging
import collections as clc
import functools as fnt

logging.basicConfig()
log = logging.getLogger("aurevent")


class AutoRepr:
    @staticmethod
    def repr(obj):
        items = []
        for prop, value in obj.__dict__.items():
            try:
                item = "%s = %r" % (prop, value)
                assert len(item) < 100
            except:
                item = "%s: <%s>" % (prop, value.__class__.__name__)
            items.append(item)

        return "%s(%s)" % (obj.__class__.__name__, ', '.join(items))

    def __init__(self, cls):
        cls.__repr__ = AutoRepr.repr
        self.cls = cls

    def __call__(self, *args, **kwargs):
        return self.cls(*args, **kwargs)


@AutoRepr
class EventMuxer:
    __router = None

    def __init__(self, name):
        self.name = name
        # self.router : ty.Optional[EventRouter] = None
        self.funcs: ty.List[ty.Callable[[Event], ty.Coroutine]] = []

    async def fire(self, ev: Event):
        # print([self.router.dispatch(ev)] if self.router else [] + [func(ev) for func in self.funcs])
        if self.router: await self.router.dispatch(ev)
        # for func in self.funcs:
        #     await func(ev)
        waiters = [self.router.dispatch(ev)] if self.router else []
        return await asyncio.gather(*(waiters + [func(ev) for func in self.funcs]))

    def add_listener(self, func: ty.Callable[[Event], ty.Awaitable]):
        self.funcs.append(func)

    @property
    def router(self):
        return self.__router

    @router.setter
    def router(self, router: EventRouter):
        print(f"Attaching router {router} to {self}")
        if self.__router:
            raise ValueError(f"Attempted to set another router for {self}")
        else:
            self.__router = router


@AutoRepr
class Event:
    def __init__(self, __event_name, *args, **kwargs):
        self.name: str = __event_name
        self.args: ty.Tuple = args
        self.kwargs: ty.Dict = kwargs

    def elevate(self, router: EventRouter):
        if self.name.startswith(":"):
            self.name = f"{router.name}{self.name}"
            if router.parent:
                self.name = f":{self.name}"

        elif self.name.startswith(router.name) and router.parent:
            self.name = f":{self.name}"

        print(f"{self.name}")
        return self

    def lower(self):
        self.name: str = self.name.partition(":")[2]
        # print(f"new name: {self.name}")
        return self


class EventRouter:
    def __init__(self, name, parent: EventRouter = None):
        self.name = name
        self.parent = parent
        if self.parent:
            # self.name = f":{self.name}"
            self.parent.register_listener(self.name, self)
        self.listeners: ty.Dict[str, EventMuxer] = {}

    def endpoint(self, name: str, decompose=False):
        # print(f"attaching endpoint {name} to {self}")
        # print(f"{self} now has endpoint {self.name}")

        def __decorator(func: ty.Callable[[...], ty.Awaitable]):
            @fnt.wraps(func)
            async def __decompose(event: Event):
                await func(*event.args, **event.kwargs)

            logging.debug("[%s] Attaching endpoint %s:%s as <%s>", self, func.__name__, func.__annotations__, name)

            self.register_listener(name=name, listener=__decompose if decompose else func)

        return __decorator

    def register_listener(self, name: str, listener: ty.Union[ty.Callable[[Event], ty.Awaitable], EventRouter]):
        logging.debug("[%s] Registering listener %s as <%s>", self, listener, name)
        if isinstance(listener, EventRouter):
            if ":" in name:
                raise ValueError(f"[{self}] : not allowed in listener identifier, register sub-router locally")
            listener.parent = self
            self.listeners.setdefault(listener.name, EventMuxer(name=name))
            # self.listeners[listener.name] = self.listeners.get(listener.name, EventMuxer(name=name))
            self.listeners[listener.name].router = listener
            return
        if name.startswith(":"):
            if self.parent:
                self.parent.register_listener(f":{self.name}{name}", listener)
            else:
                self.register_listener(f"{self.name}{name}", listener)
            return
        if not name.startswith(self.name):
            raise ValueError(f"[{self}] Attempting to register listener with invalid route {name}")

        assert not isinstance(listener, EventRouter)  # type check

        # _:target:remainder
        _, target, remainder, *_ = name.split(":", 2) + ["", ""]
        self.listeners.setdefault(target, EventMuxer(name=target))

        # if target not in self.listeners:
        #     raise ValueError(f"[{self}] No listener registered for {target} when resolving {name}. listeners: {self.listeners}")
        event_muxer = self.listeners[target]
        if remainder:  # target refers to a sub-router
            if sub_router := event_muxer.router:
                sub_router.register_listener(f"{target}:{remainder}", listener)
            else:
                raise ValueError(f"[{self}] Attempting to descend into nonexistent subrouter {event_muxer} | {name}")
        else:  # target refers to a listener
            event_muxer.add_listener(listener)
        logging.debug("[%s] Registered! Listeners[%s] Muxer[%s] Listner [%s]", self, self.listeners, event_muxer, listener)

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

    def deregister_listener(self, name: str):
        logging.debug("[%s] Deregistering listener <%s>", self, name)

        #
        # if name.startswith(":"):
        #     self.
        # elif name.startswith(":"):
        #     name = name[1:]
        #     final_listener = listener
        #     if isinstance(listener, ty.Callable) and not asyncio.iscoroutinefunction(listener):
        #         async def __coro_wrapper(*args, **kwargs):
        #             return listener(*args, **kwargs)
        #
        #         final_listener = __coro_wrapper
        #     self.listeners[name].remove(final_listener)
        # else:
        #     if not name.startswith(f"{self.name}:"):
        #         if not self.parent:
        #             raise ValueError(f"Attempting to register invalid listener {self.name} on {self}")
        #         self.parent.deregister_listener(name)
        #     else:
        #         self.register_listener(name.removeprefix(self.name), listener)
        # logging.debug("[%s] Finished registering listener %s as <%s>, new listeners: %s", self, listener, name, self.listeners)
        #

    async def submit(self, event: Event):
        logging.debug("[%s] Submitting event (%s)", self, event)
        event.elevate(self)

        if self.parent:
            await self.parent.submit(event)
        else:
            await self.dispatch(event)

    async def wait_for(self, event_name, check: ty.Optional[ty.Callable[[Event], ty.Awaitable[bool]]] = None, timeout=None) -> asyncio.Future:
        ev = asyncio.Future()
        if not check:
            async def check(*args, **kwargs):
                return True

        async def check_event_setter(event: Event):
            if not check(event):
                return
            # self.n
            return Event

        # self.register_listener(event_name, check_event_setter)

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
