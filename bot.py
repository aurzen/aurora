import logging


import TOKENS
import aurcore
from aurcore import aurlux
logging.basicConfig(level=logging.INFO)



config = {"PREFIX": "!"}
client = aurcore.aurlux.client.Lux(config)
# aurcore.aurlux.client = client


@aurcore.aurlux.timer.every(s=1, ms=500)
async def test():
    await client.get_channel(596464529253203971).send("pong!")


@client.command(name="test")
async def testerino(ctx: aurlux.Contexter):
    await test()


@client.command(name="remindme")
async def remind_me(ctx: aurlux.CommandContext):
    return aurcore.task.action.Reminder()


@client.command(name="ping")
async def ping(ctx: aurlux.command.CommandContext):
    pass


client.run(TOKENS.discord_token, bot=True)
