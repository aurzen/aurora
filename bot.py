from __future__ import annotations

import asyncio
import contextlib
from loguru import logger
import aurflux
import aurcore
import typing as ty
import TOKENS
import sys

logger.add(sys.stderr, level="INFO")

if ty.TYPE_CHECKING:
   pass


class Aurora:
   def __init__(self):
      self.event_router = aurcore.event.EventRouterHost(name=self.__class__.__name__.lower())
      self.flux = aurflux.FluxClient(
         "aurora",
         admin_id=TOKENS.ADMIN_ID,
         parent_router=self.event_router,
         status="",
      )

   async def startup(self, token: str):
      await self.flux.start(token)

   async def shutdown(self):
      await self.flux.logout()


bot = Aurora()

aurcore.aiorun(bot.startup(token=TOKENS.AURORA), bot.shutdown())
