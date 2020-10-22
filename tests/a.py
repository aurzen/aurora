import aurcore as aur
import asyncio as aio
async def c():
   while True:
      await aio.sleep(5)
      print("a")


aur.aiorun(c(), None)