from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pytz
import dataclasses as dtcs
import typing as ty
import abc

def wd(day:int) -> int:
   return ((day + 1) % 7) + 1

def dw(day:int) -> int:
   return ((day - 2) % 7)

class Clock(abc.ABC):
   def __init__(self):
      pass

   @abc.abstractmethod
   def iterate(self):
      pass


class OrdinalClock(Clock):
   def __init__(self, base: datetime, ordinal:ty.Tuple[int], interval: ty.Literal["month","week"]):
      self.base = base
      self.ordinal = [dw(o) for o in ordinal]
      self.interval = interval


   def iterate(self):
      if self.interval == "month":
         pass
      elif self.interval == "week":
         pass

   def next(self):
      next_ordinal = min([(o-datetime.today().weekday()) % 7 for o in self.ordinal])
      return self.base + timedelta(days=((self.base.weekday())%7))

@dtcs.dataclass
class Reminder:
   text: str
   start_at: datetime
   end_at: ty.Optional[datetime]
   repeat_type: ty.Optional[ty.Literal["dow", "dom,", "doy", "dur"]]  # day of week (Sunday-Saturday), day of month (1-31), day of year (1-365), dur=s
   repeat_base: ty.Optional[int]
   repeat_interval: ty.Optional[int]
