import asyncio as aio
import functools as fnt
import typing as ty
from .tb import full_exc_info

def int_to_ordinal(n: int) -> str:
   return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


class AutoRepr:
   def __repr__(self):
      return f'<{self.__class__.__name__} {vars(self)!r}>'


def delay(coro: ty.Coroutine, seconds: float = 0):
   async def __delay_coro():
      await aio.sleep(seconds)
      await coro

   return __delay_coro()


class AwaitableAiter:
   aiter: ty.AsyncGenerator

   def __init__(self, obj: ty.Union[ty.Coroutine, ty.AsyncIterable, ty.Awaitable]):
      if aio.iscoroutine(obj) or aio.isfuture(obj):
         async def gen():
            yield await obj

         self.aiter = gen()

      elif isinstance(obj, ty.AsyncGenerator):
         self.aiter = obj

   def __aiter__(self):
      return self.aiter.__aiter__()

   def __await__(self):
      async def results():
         res = await self.aiter.__anext__()
         c = await self.aiter.aclose()
         return res
      return results().__await__()



def aiterify(obj: ty.Union[ty.Coroutine, ty.AsyncIterable]):
   if aio.iscoroutine(obj) or aio.isfuture(obj):
      class AiterCoro:
         def __aiter__(self):
            async def gen():
               yield await obj

            return gen()

      return AiterCoro()
   else:
      return obj


def coroify(func):
   if aio.iscoroutinefunction(func):
      return func

   @fnt.wraps(func)
   async def __async_wrapper(*args, **kwargs):
      return func(*args, **kwargs)

   return __async_wrapper


class Singleton(type):
   _instances = {}

   def __call__(cls, *args, **kwargs):
      if cls not in cls._instances:
         cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
      return cls._instances[cls]


