from __future__ import annotations
import aurflux
from aurflux.types_ import GuildCommandCtx
import asyncpg
import asyncpg.pool
import dateparser
from datetime import datetime, timedelta
import pytz
from . import reminder
import re
import typing as ty


class Remind(aurflux.FluxCog):
   AT_REG = re.compile(r"\\.\\.at (.*?),")
   IN_REG = re.compile(r"\\.\\.in (.*?),")
   UNTIL_REG = re.compile("\\.\\.until (.*?),")
   TO_REG = re.compile("\\.\\.to (.*)")
   EVERY_REG = re.compile("..every (.*),")

   def load(self) -> None:
      @self._commandeer("remindme")
      async def __remindme(ctx: GuildCommandCtx, args: str):
         """
         remindme [type] args*
         ==
         Reminder!
         ===
         [type]: [at/in/every]
         :param ctx:
         :param args:
         :return:
         """
         tz = pytz.timezone(self.flux.CONFIG.of(ctx.msg_ctx)["tz"])

         def get_start(text: str) -> datetime:

            start = None
            at_raw = self.AT_REG.search(text)
            in_raw = self.AT_REG.search(text)
            if not (bool(at_raw) ^ bool(in_raw)):
               raise aurflux.CommandError(f"Must specify exactly one of `..at` or `..in`")
            if at_raw:
               start = dateparser.parse(at_raw.group(1))
            if in_raw:
               start = dateparser.parse(f"in {in_raw.group(1)}")
            if not start:
               raise aurflux.CommandError(f"dateparser failed to parse `{at_raw.group(1) if at_raw else in_raw.group(1)}`")

            return start
         start = get_start(args)

         def get_until(text: str) -> ty.Optional[datetime]:
            until_raw = self.UNTIL_REG.search(text)
            if until_raw:
               end_date = dateparser.parse(until_raw.group(1))
               return end_date

         until = get_until(args)

         def get_every(text: str) -> ty.Optional[datetime]:
