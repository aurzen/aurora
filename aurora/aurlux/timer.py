import asyncio
import aurora.utils.zutils
import functools

@aurora.utils.zutils.parametrized
def every(func: callable, ms: int = 0, s: int = 0, mins: int = 0, hours: int = 0):
    s += ms / 1000
    s += mins / 60
    s += hours / 60 / 60

    @functools.wraps(func)
    async def every_wrapper(*args, **kwargs):
        print("entering wrapper")
        while True:
            print("loop")
            await func(*args, **kwargs)
            await asyncio.sleep(s)

    return every_wrapper
