from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pytz
import dataclasses as dtcs
import typing as ty

@dtcs.dataclass
class Reminder:
   text: str
   start_at: datetime
   end_at: ty.Optional[datetime]
   repeat_type: ty.Optional[ty.Literal["dow","dom,","doy","dur"]] # day of week (Sunday-Saturday), day of month (1-31), day of year (1-365), dur=s
   repeat_base: ty.Optional[int]
   repeat_interval: ty.Optional[int]