import asyncio
import typing as ty


def int_to_ordinal(n: int):
    return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def delay(coro: ty.Coroutine, seconds: float = 0):
    async def __delay_coro():
        await asyncio.sleep(seconds)
        await coro

    return __delay_coro()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
