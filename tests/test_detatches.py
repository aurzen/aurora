import asyncio
import uuid

import pytest

import aurcore


# logging.basicConfig()
# log = logging.getLogger("aurevent")

# log.setLevel(logging.DEBUG)


def dat():
   return uuid.uuid4().hex


@pytest.fixture
def host():
   return aurcore.EventRouterHost(name="test_host")


# @pytest.fixture
# def child(host):
#     return aurcore.EventRouter(name=dat()[:12], host=host)

@pytest.mark.asyncio
async def test_detatches(event_loop, host):
   results = []

   child = aurcore.EventRouter(name="child", host=host)

   async def clock():
      for i in range(5):
         await asyncio.sleep(0.1)
         await child.submit(aurcore.Event(":clock tick", i))

   recieved = 0
   @child.listen_for(":clock tick")
   @aurcore.Eventful.decompose
   def x(data):
      nonlocal recieved
      if recieved > 2:
         return True
      results.append(data)
      recieved += 1

   # asyncio.get_running_loop().run_until_complete(clock())
   await clock()
   assert len(results) == 3
