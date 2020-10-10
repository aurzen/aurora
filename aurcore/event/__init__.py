from __future__ import annotations

import asyncio as aio
import dataclasses as dtc
import functools as fnt
import itertools as itt
import collections as clc

import typing as ty
import time
from aurcore import util


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


# @dtc.dataclass(frozen=True)
class EventWaiter:
   future: aio.Future

   def __init__(self, check: ty.Callable[[Event], ty.Awaitable[bool]], timeout: ty.Optional[float], max_matches: ty.Optional[int]):
      self.check = check
      self.timeout = timeout
      self.start = time.perf_counter()
      self.max_results = max_matches
      self.queue = aio.Queue()
      self.done = False

   async def listener(self, event: Event):
      if self.done:
         return True
      if self.timeout is not None and (time.perf_counter() - self.start) > self.timeout:
         raise aio.TimeoutError()
      if await self.check(event):
         await self.queue.put(event)

   async def producer(self):
      try:
         results = 0
         while self.max_results is None or results < self.max_results:
            yield await self.queue.get()
            if self.max_results:
               results += 1
      except GeneratorExit:
         self.done = True
         raise GeneratorExit()


class Eventful:
   EventableFunc: ty.TypeAlias = ty.Callable[[Event], ty.Awaitable[ty.Optional[bool]]]
   f: EventableFunc

   def __init__(self, muxer: EventMuxer, eventable: EventableFunc):
      self.retain = True
      self.muxer = muxer
      self.f = util.coroify(eventable)
      self.f_orig = self.f

   def __call__(self, event: Event) -> ty.Awaitable[ty.Optional[bool]]:
      # Listeners return True to delete themselves, anything else (None) to
      async def should_retain(event_: Event):
         should_delete = await self.f(event_)
         if should_delete is True:
            return False
         if should_delete is None:
            return True
         raise RuntimeError(f"{self.f} returned something other than [True, None]")

      return should_retain(event)

   @staticmethod
   def decompose(func: ty.Callable[..., ty.Union[None, ty.Awaitable[None]]]) -> ty.Callable[[Event], ty.Awaitable[None]]:
      func_ = util.coroify(func)

      @fnt.wraps(func_)
      async def __decompose_wrapper(event: Event):
         return await func_(*event.args, **event.kwargs)

      return __decompose_wrapper


class EventMuxer:
   def __init__(self, name: str, router: EventRouter):
      self.name = name
      self.router = router
      self.eventfuls: ty.Set[Eventful] = set()
      # self.__lock = aio.Lock(

   def eventful_fut_handler(self, eventful: Eventful, fut: aio.Future):
      if isinstance(fut.exception(), aio.exceptions.TimeoutError) or fut.result() is False:
         self.eventfuls.remove(eventful)
         fut.result()


   async def fire(self, ev: Event) -> None:
      # print("Firing!")
      # print(ev)
      # async with self.__lock:
      for eventful in self.eventfuls:
         aio.create_task(eventful(ev)).add_done_callback(fnt.partial(self.eventful_fut_handler, eventful))
      #    results: ty.List[ty.Union[bool, BaseException]] = await aio.gather(
      #       *[eventful(ev) for eventful in self.eventfuls],
      #       return_exceptions=True)
      #    self.eventfuls = list(itt.compress(self.eventfuls, results))  # Exceptions are truthy
      # for result in results:
      #    if isinstance(result, Exception):
      #       raise result

   def register(self, eventful: Eventful):
      self.eventfuls.add(eventful)

   def __repr__(self):
      return f"EventMuxer(router={self.router.name}, eventfuls={[ev.f.__name__ for ev in self.eventfuls]})"

   def __str__(self):
      return f"EventMuxer {self.name}:\n{len(self.eventfuls)} eventfuls"


class EventRouterHost:
   def __init__(self, name: str = "Unnamed"):
      self.name = name.lower()
      self.routers: ty.Dict[str, ty.List[EventRouter]] = clc.defaultdict(list)

   def __repr__(self):
      router_block = ["\t" + f"{router}" + "\n" for router in self.routers.values()]
      return f"EventRouterHost(name={self.name}, routers={router_block})"

   # def __str__(self):
   #    return f"EventRouterHost {self.name} | Routers: {[r for r in self.routers]}"

   def register(self, router: EventRouter) -> None:
      if router.name in self.routers:
         raise RuntimeError(f"[{self}] already has an event router named {router.name}")
      self.routers[router.name].append(router)

   def deregister(self, router: EventRouter) -> None:
      if router in self.routers:
         self.routers[router.name].remove(router)
      else:
         raise RuntimeError(f"[{self}] attempted to deregister an unregistered router {router}")

   # noinspection PyProtectedMember
   async def submit(self, event: Event):
      await aio.gather(*[router._dispatch(event) for router_group in self.routers.values() for router in router_group])


class EventRouter(util.AutoRepr):
   def __init__(self, name: str, host: EventRouterHost):
      self.name = name.lower()
      self.host = host
      self.host.register(self)
      self.muxers: ty.Dict[str, EventMuxer] = {}

   def _register_listener(self, event_name: str, listener: Eventful.EventableFunc):
      event_name = Event.hoist_name(event_name.lower(), self)

      if event_name not in self.muxers:
         self.muxers[event_name] = EventMuxer(name=event_name, router=self)
      muxer = self.muxers[event_name]

      listener = Eventful(muxer=muxer, eventable=listener)
      muxer.register(listener)

   def listen_for(self, event_name: str):
      event_name = Event.hoist_name(event_name.lower(), self)

      def listen_deco(func: Eventful.EventableFunc):
         func_ = util.coroify(func)
         self._register_listener(event_name, func_)
         return func_

      return listen_deco

   def wait_for(self, event_name: str, check: ty.Callable[[Event], bool], timeout: float = None, max_matches=1) -> util.AwaitableAiter:
      ev_waiter: EventWaiter = EventWaiter(check=util.coroify(check), timeout=timeout, max_matches=max_matches)
      self._register_listener(event_name=event_name, listener=ev_waiter.listener)
      return util.AwaitableAiter(ev_waiter.producer())

   async def submit(self, event: Event) -> None:
      event.hoist(self)
      await self.host.submit(event)

   async def _dispatch(self, event: Event) -> None:
      await aio.gather(*[
         muxer.fire(event) for listen_name, muxer in self.muxers.items()
         if (listen_name.endswith(":") and event.name.startswith(listen_name[:-1])) or event.name == listen_name
      ])

   def detach(self):
      self.host.deregister(self)

   def __str__(self):
      return f"[Router: {self.name} |  <{self.muxers}>]"

   def __repr__(self):
      return f"Router(name={self.name}, muxers={[m for m in self.muxers]})"
