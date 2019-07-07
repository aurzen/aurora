import logging

import TOKENS
import aurora
from aurora import aurlux
logging.basicConfig(level=logging.INFO)

config = {"PREFIX": "!"}
client = aurora.aurlux.client.Lux(config)
aurora.aurlux.client = client


@aurora.aurlux.timer.every(s=1, ms=500)
async def test():
    await client.get_channel(596464529253203971).send("pong!")


@client.command(name="test")
async def testerino(ctx: aurlux.Contexter):
    await test()


@client.command(name="remindme")
async def remind_me(ctx: aurlux.Contexter):
    reminder = aurora.task.actionable.Reminder()
    pass

@client.command(name="ping")
async def ping(ctx: aurlux.Contexter):
    pass


client.run(TOKENS.discord_token, bot=True)
