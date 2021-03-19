from __future__ import annotations

import typing as ty
import aurflux
from aurflux.command import Response

import aurflux.auth
import discord
import base64
import asyncio as aio
import subprocess
import aurcore as aur
import pickle
from loguru import logger
from aurflux.types_ import GuildCommandCtx

aur.log.setup()

if ty.TYPE_CHECKING:
   import datetime

VERSION = subprocess.check_output(["poetry", "version"]).decode().split(" ")[1]


class Interface(aurflux.cog.FluxCog):
   def load(self):
      @self._commandeer(name="purge")
      async def __purge(ctx: GuildCommandCtx, args:str):
         num = int(args.strip())
         with aurflux.utils.Timer() as t:
            purged = await ctx.msg_ctx.channel.purge(limit=num)
         return Response(f"Purged {len(purged)} messages in {aurflux.utils.hum.elapsed}")