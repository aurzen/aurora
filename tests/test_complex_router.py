import asyncio
import uuid

import pytest

import aurcore


def dat():
   return uuid.uuid4().hex


# @pytest.fixture(scope="class")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("event_name,listen_str_1,listen_str_2,expected", [
   ("test", "test", "test", ""),  # Specific
   ("test", "test", "honk", "1"),  # Specific don't match fails
   ("test", "honk", "test", "2"),  # ^
   ("test~", "test", "test", ""),  #
   ("test", "t", "te", ""),  #
   ("test", "", "", ""),
   ("test", "", "", ""),
   ("test", "test", "test~", "1"),
   ("test", "test~", "test", "2"),

])
async def test_two_router_test_from_host(
      event_loop,
      event_name,
      listen_str_1,
      listen_str_2,
      expected
):
   print("EL:")
   print(event_loop)
   host = aurcore.EventRouterHost("test_host")

   child_1 = aurcore.EventRouter(name="child_1", host=host)
   child_2 = aurcore.EventRouter(name="child_2", host=host)

   res_1 = None
   res_2 = None

   data_ = dat()

   @child_1.listen_for(listen_str_1, decompose=True)
   def _(data):
      nonlocal res_1
      res_1 = data

   @child_2.listen_for(listen_str_2, decompose=True)
   def _(data):
      nonlocal res_2
      res_2 = data

   await host.submit(event=aurcore.Event(event_name, data=data_))
   await asyncio.sleep(0.25)

   if expected == "1":
      assert res_1 == data_
      assert res_2 is None
   elif expected == "2":
      assert res_2 == data_
      assert res_1 is None
   else:
      assert res_1 == data_ and res_2 == data_
