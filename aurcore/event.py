from __future__ import annotations

import typing as ty
import asyncio
import collections as clc
import functools as fnt

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
class Event:
    def __init__(self, __event_name, *args, **kwargs):
        self.name: str = __event_name
        self.args: ty.Tuple = args
        self.kwargs: ty.Dict = kwargs

    def elevate(self, router: EventRouter):
        if self.name.startswith(":"):
            self.name = f"{router.name}{self.name}"
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
            self.name = f":{self.name}"
            self.parent.register_listener(self.name, self)
        self.listeners: ty.Dict[str, list] = clc.defaultdict(list)



    def endpoint(self, name: str, decompose=False):
        # print(f"attaching endpoint {name} to {self}")
        # print(f"{self} now has endpoint {self.name}")

        def __decorator(func: ty.Callable[[...], ty.Awaitable]):
            @fnt.wraps(func)
            async def __decompose(event: Event):
                await func(*event.args, **event.kwargs)

            self.register_listener(name=name, listener=__decompose if decompose else func)

        return __decorator



    def register_listener(self, name: str, listener: ty.Union[ty.Callable]):

        if name.startswith(":"):
            name = name[1:]
            final_listener = listener
            if isinstance(listener, EventRouter):
                final_listener.parent = self
            elif isinstance(listener, ty.Callable) and not asyncio.iscoroutinefunction(listener):
                async def __coro_wrapper(*args, **kwargs):
                    return listener(*args, **kwargs)

                final_listener = __coro_wrapper
            self.listeners[name].append(final_listener)
        else:
            if name.split(":")[0] != self.name:
                if not self.parent:
                    raise ValueError(f"Attempting to register invalid listener {self.name} on {self}")
                self.parent.register_listener(name, listener)


    async def submit(self, event: Event):
        event.elevate(self)

        if self.parent:
            await self.parent.submit(event)
        else:
            await self.dispatch(event)

    async def dispatch(self, event: Event):
        chunked = event.name.split(":")
        # Try from most to least specific
        # while event_chunk := event.lower() != "":
        for i in range(len(chunked), 1, -1):
            event_chunk = ":".join(chunked[1:i])
            # print(f"Testing event_chunk {event_chunk}")
            if event_chunk in self.listeners:
                # print(f"Chunk detected with {event_chunk}, listeners: {self.listeners[event_chunk]}")
                for listener in self.listeners[event_chunk]:
                    # print(f"DISPATCHING TO A LISTENER: {listener}")
                    res = await listener(event.lower())
                    # print(f"LISTENER PRODUCED: {res}")
                # res = await asyncio.gather(*[listener(event.lower()) for listener in self.listeners[event_chunk]])
                # print(f"GATHER RESULTS: {res}")
                # await self.listeners[event.name](event)
                break

    def __call__(self, event: Event) -> ty.Awaitable:
        # print("called!")
        return self.dispatch(event=event)
        # return await asyncio.gather(*[listener(*args, **kwargs) for listener in self.listeners])

    def __repr__(self):
        return f"EventRouter(name={self.name}, parent={self.parent})"
