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

async def basic_test(listen_str, event_name, host, submit_from="child", should_catch=True):
   message = None
   data_ = dat()

   child = aurcore.EventRouter(name="child", host=host)

   @child.listen_for(listen_str)
   @aurcore.Eventful.decompose
   def x(data) -> None:
      nonlocal message
      message = data

   # child.listen_for(listen_str, decompose=True)(func=x)

   if submit_from == "child":
      await child.submit(aurcore.Event(event_name, data=data_))
   else:
      await host.submit(aurcore.Event(event_name, data=data_))
   await asyncio.sleep(0.1)
   assert not ((data_ == message) ^ should_catch)


@pytest.mark.asyncio
async def test_child_catch_specific(event_loop, host):
   await basic_test(listen_str="child:test", event_name="cHiLd:TeST", host=host)


# From Child

@pytest.mark.asyncio
async def test_child_catch_specific(event_loop, host):
   await basic_test(listen_str="child:test", event_name="child:test", host=host)


@pytest.mark.asyncio
async def test_child_catch_specific_not(event_loop, host):
   await basic_test(listen_str="child:test", event_name="child:t3st", host=host, should_catch=False)


@pytest.mark.asyncio
async def test_child_catch_prefix(event_loop, host):
   await basic_test(listen_str="chil:", event_name="child:test", host=host)


@pytest.mark.asyncio
async def test_child_catch_all(event_loop, host):
   await basic_test(listen_str=":", event_name="child:test", host=host)


@pytest.mark.asyncio
async def test_child_submit_local(event_loop, host):
   await basic_test(listen_str="child:test", event_name=":test", host=host)


@pytest.mark.asyncio
async def test_child_submit_local(event_loop, host):
   await basic_test(listen_str="notchild:test", event_name=":test", host=host, should_catch=False)


# From Parent

@pytest.mark.asyncio
async def test_parent_catch_specific(event_loop, host):
   await basic_test(listen_str="child:test", event_name="child:test", host=host, submit_from="parent")


@pytest.mark.asyncio
async def test_parent_catch_prefix(event_loop, host):
   await basic_test(listen_str="chil:", event_name="child:test", host=host, submit_from="parent")


@pytest.mark.asyncio
async def test_parent_catch_all(event_loop, host):
   await basic_test(listen_str=":", event_name="child:test", host=host, submit_from="parent")

#
# @pytest.mark.asyncio
# async def test_local_event_submit_endpoint_receive(event_loop, simple_router):
#     message = None
#
#     @simple_router.endpoint(":test")
#     async def _(x):
#         nonlocal message
#         message = x
#
#     await simple_router.submit(aurcore.Event(":test", payload=dat()))
#     await asyncio.sleep(0)  # idk
#
#     assert message is not None

#
# @pytest.mark.asyncio
# async def test_absolute_event_submit_endpoint_receive(event_loop, simple_router):
#     message = None
#
#     @simple_router.endpoint("test_router:test")
#     async def _(x):
#         nonlocal message
#         message = x
#
#     await simple_router.submit(aurcore.Event(":test", payload=dat()))
#     await asyncio.sleep(0)  # idk
#     assert message is not None
#
#
# @pytest.mark.asyncio
# async def test_local_event_submit_endpoint_data(event_loop, simple_router):
#     message = None
#
#     payload = dat()
#
#     @simple_router.endpoint(":test")
#     async def _(x):
#         nonlocal message
#         message = x.args[0]
#
#     await simple_router.submit(aurcore.Event(":test", payload))
#     await asyncio.sleep(0.1)  # idk
#
#     assert message == payload
#
#
# @pytest.mark.asyncio
# async def test_synoynms(event_loop, simple_router):
#     message = ""
#
#     payload = dat()
#
#     @simple_router.endpoint(":test")
#     async def _(x):
#         nonlocal message
#         message += x.args[0]
#
#     @simple_router.endpoint(":test")
#     async def _(x):
#         nonlocal message
#         message += x.args[0]
#
#     await simple_router.submit(aurcore.Event(":test", payload))
#     await asyncio.sleep(0.1)  # idk
#
#     assert message == payload * 2
