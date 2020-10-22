import asyncio
import contextlib

from .event import Event, EventRouter, EventRouterHost, Eventful
from . import util
from . import log

from loguru import logger
log.setup()

def aiorun(startup, cleanup):
   loop = asyncio.get_event_loop()
   try:
      loop.create_task(startup)
      loop.run_forever()
   except KeyboardInterrupt:
      logger.info("KeyboardInterrupt detected. Cleaning up.")
      loop.run_until_complete(cleanup)
      all_tasks = asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True)
      all_tasks.cancel()
      with contextlib.suppress(asyncio.CancelledError):
         loop.run_until_complete(all_tasks)
      loop.run_until_complete(loop.shutdown_asyncgens())

      logger.info("Cleaned up! Shutting down.")
      loop.close()


__all__ = ["Event", "Eventful", "EventRouterHost", "EventRouter", "log", "util"]
