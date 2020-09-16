from __future__ import annotations

import asyncio as aio
import dataclasses as dtc
import functools as fnt
import itertools as itt
import typing as ty

import util


class Event(util.AutoRepr):
   def __init__(self, __event_name: str, *args, **kwargs):
      self.name: str = __event_name.lower()
      self.args: ty.Tuple = args
      self.kwargs: ty.Dict = kwargs

   @staticmethod
   def hoist_name(event_name: str, router: EventRouter):
      return f"{router.name if event_name.startswith(':') else ''}{event_name}"

   def hoist(self, router: EventRouter):
      self.name = Event.hoist_name(self.name, router)


@dtc.dataclass(frozen=True)
class EventWaiter:
   future: aio.Future
   check: ty.Callable[[Event], ty.Coroutine[bool]]


class Eventful(util.AutoRepr):
   f: ty.Callable
   EventableFunc: ty.TypeAlias = ty.Callable[[Event], ty.Coroutine]
   Eventable: ty.TypeAlias = ty.Union[EventableFunc, EventWaiter]

   def __init__(self, muxer: EventMuxer, eventable: Eventable):
      self.retain = True
      self.muxer = muxer
      if isinstance(eventable, EventWaiter):
         async def __waiter_wrapper(event: Event):
            if eventable.future.cancelled():
               self.retain = False
            elif await eventable.check(event):
               eventable.future.set_result(event)
               self.retain = False

         self.f = __waiter_wrapper
      else:
         self.f = util.coroify(eventable)

   def __call__(self, event: Event) -> ty.Coroutine:
      async def __retain_wrapper(ev: Event):
         await self.f(ev)
         return self.retain

      return __retain_wrapper(event)

   @staticmethod
   def decompose(func: ty.Callable[[...], ty.Coroutine]) -> EventableFunc:
      @fnt.wraps(func)
      def __decompose_wrapper(event: Event):
         return func(*event.args, **event.kwargs)

      return __decompose_wrapper


class EventMuxer(util.AutoRepr):
   def __init__(self, name: str, router: EventRouter):
      self.name = name
      self.router = router
      self.eventfuls: ty.List[Eventful] = []
      self.__lock = aio.Lock()

   async def fire(self, ev: Event) -> None:
      async with self.__lock:
         results: ty.List[ty.Union[bool, BaseException]] = await aio.gather(
            *[eventful(ev) for eventful in self.eventfuls],
            return_exceptions=True)
         self.eventfuls = list(itt.compress(self.eventfuls, results))  # Exceptions are truthy
      for result in results:
         if isinstance(result, Exception):
            raise result

   def register(self, eventful: Eventful):
      self.eventfuls.append(eventful)

   def __str__(self):
      return f"EventMuxer {self.name} | Router: {self.router} | Eventfuls: {self.eventfuls}"


class EventRouterHost(util.AutoRepr):
   def __init__(self, name: ty.Optional[str] = "Unnamed"):
      self.name = name
      self.routers: ty.Dict[str, EventRouter] = {}

   def __str__(self):
      return f"EventRouterHost {self.name} | Routers: {self.routers}"

   def register(self, router: EventRouter) -> None:
      if router.name in self.routers:
         raise RuntimeError(f"[{self}] already has an event router named {router.name}")
      self.routers[router.name] = router

   def deregister(self, router: EventRouter) -> None:
      if router.name in self.routers:
         del self.routers[router.name]
      else:
         raise RuntimeError(f"[{self}] attempted to deregister an unregistered router {router}")

   # noinspection PyProtectedMember
   async def submit(self, event: Event):
      await aio.gather(*[router._dispatch(event) for router in self.routers.values()])



class EventRouter(util.AutoRepr):
   def __init__(self, name: str, host: EventRouterHost):
      self.name = name
      self.host = host
      self.host.register(self)
      self.muxers: ty.Dict[str, EventMuxer] = {}

   def _register_listener(self, event_name: str, listener: Eventful.Eventable):
      event_name = Event.hoist_name(event_name.lower(), self)

      if event_name not in self.muxers:
         self.muxers[event_name] = EventMuxer(name=event_name, router=self)
      muxer = self.muxers[event_name]

      listener = Eventful(muxer=muxer, eventable=listener)
      muxer.register(listener)

   def listen_for(self, event_name: str, decompose=False):
      event_name = Event.hoist_name(event_name.lower(), self)

      def listen_deco(func: Eventful.EventableFunc):
         if decompose:
            self._register_listener(event_name, Eventful.decompose(func))
         else:
            self._register_listener(event_name, func)
         return func

      return listen_deco

   def wait_for(self, event_name: str, check: ty.Callable[[Event], bool], timeout: float) -> aio.Future:
      fut = aio.Future()
      ev_waiter: EventWaiter = EventWaiter(future=fut, check=util.coroify(check))
      self._register_listener(event_name=event_name, listener=ev_waiter)
      return aio.wait_for(fut, timeout=timeout)

   async def submit(self, event: Event) -> None:
      event.hoist(self)
      await self.host.submit(event)

   async def _dispatch(self, event: Event) -> None:
      await aio.gather(*[muxer.fire(event) for listen_name, muxer in self.muxers.items() if event.name.startswith(listen_name)])

   def detach(self):
      self.host.deregister(self)