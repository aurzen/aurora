import asyncio
import uuid

import pytest

import aurcore


@pytest.fixture
def dat():
   return uuid.uuid4().hex


@pytest.fixture
def host():
   return aurcore.EventRouterHost(name="test_router")


@pytest.mark.asyncio
async def test_simple_wait(event_loop, host: aurcore.EventRouterHost, dat):
   child = aurcore.EventRouter(name="child", host=host)

   _payload = dat
   stop = False

   async def clock():
      while not stop:
         await asyncio.sleep(1)
         await child.submit(aurcore.Event(":clock tick", payload=_payload))

   task = asyncio.get_event_loop().create_task(clock())

   payload = await child.wait_for(":clock tick", check=lambda _: True, timeout=3)
   stop = True
   assert _payload == payload.kwargs["payload"]

   await task


@pytest.mark.asyncio
async def test_wait_generator(event_loop, host: aurcore.EventRouterHost):
   child = aurcore.EventRouter(name="child", host=host)

   inputs = [uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex]
   input_index = 0

   _payload = dat
   stop = False

   async def clock():
      nonlocal input_index
      while not stop:
         await asyncio.sleep(1)
         await child.submit(aurcore.Event(":clock tick", payload=inputs[input_index]))
         input_index += 1

   task = asyncio.get_event_loop().create_task(clock())

   _results = []
   async for payload in child.wait_for(":clock tick", check=lambda _: True, max_matches=3):
      _results.append(payload.kwargs["payload"])
   stop = True
   assert inputs == _results

   await task
