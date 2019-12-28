import aursync
import logging
import action
from tenebris import Tenebris
import TOKENS
import aiorun
class Borealis:

    def __init__(self):
        self.identifier = "borealis"
        self.sync = aursync.Sync(name=self.identifier)
        self.runner = action.ActionRunner()
        self.tenebris = Tenebris(actioner=self.runner)

    async def init(self):
        await self.sync.init()
        await self.tenebris.start(TOKENS.tenebris, bot=False)


    async def register_heartbeat(self):
        async def respond(message):
            await self.sync.publish(f"{message}|{self.sync.name}", "_heartbeat")

        await self.sync.subscribe(respond, "_heartbeat")

    async def log(self, level: int, message):
        await self.sync.publish(f"[LEVEL:{level}]{message}", channels=f"log.{level}")



async def main():
    borealis = Borealis()
    await borealis.init()


if __name__ == '__main__':
    aiorun.run(main())