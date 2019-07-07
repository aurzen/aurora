from datetime import datetime, timedelta

import dateparser
from functools import singledispatch

from aurora.utils.text import is_int


@singledispatch
def parse_time(time_inp: datetime) -> datetime:
    return time_inp


@parse_time.register
def _(time_dur: timedelta) -> datetime:
    return datetime.utcnow() + time_dur


@parse_time.register
def _(time_mins: int) -> datetime:
    return datetime.utcnow() + timedelta(minutes=time_mins)


@parse_time.register
def _(time_str: str) -> datetime:
    if is_int(time_str):
        return datetime.utcnow() + timedelta(minutes=int(time_str))
    return dateparser.parse(time_str)
