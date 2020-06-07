import pytest
import uuid
import aurcore
import asyncio



def dat():
    return uuid.uuid4().hex

@pytest.fixture
def nested_routers():
    top_router = aurcore.EventRouter(name="top")

    left_router = aurcore.EventRouter(name="left", parent=top_router)
    right_router = aurcore.EventRouter(name="right", parent=top_router)

    left_left_router = aurcore.EventRouter(name="left_left", parent=left_router)
    left_right_router = aurcore.EventRouter(name="left_right", parent=left_router)

    right_left_router = aurcore.EventRouter(name="right_left", parent=right_router)
    right_right_router = aurcore.EventRouter(name="right_right", parent=right_router)

    return {"top_router"        : top_router,
            "left_router"       : left_router,
            "right_router"      : right_router,
            "left_left_router"  : left_left_router,
            "left_right_router" : left_right_router,
            "right_left_router" : right_left_router,
            "right_right_router": right_right_router, }


@pytest.mark.asyncio
async def test_local_endpoint(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["top_router"].endpoint(":test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["top_router"].submit(aurcore.Event(":test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload

@pytest.mark.asyncio
async def test_multilevel_listen(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["top_router"].endpoint(":left:left_left:test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["top_router"].submit(aurcore.Event(":left:left_left:test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload


@pytest.mark.asyncio
async def test_multilevel_child_listen(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["top_router"].endpoint(":left:left_left:test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["left_left_router"].submit(aurcore.Event(":test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload


@pytest.mark.asyncio
async def test_fullname_endpoint(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["top_router"].endpoint("top:left:test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["top_router"].submit(aurcore.Event("top:left:test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload
open = 5

@pytest.mark.asyncio
async def test_children_sibling_events(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["left_router"].endpoint(":left_test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["right_router"].submit(aurcore.Event("top:left:left_test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload

@pytest.mark.asyncio
async def test_grandchildren_sibling_events(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["left_left_router"].endpoint(":test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["left_right_router"].submit(aurcore.Event("left:left_left:test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload


@pytest.mark.asyncio
async def test_grandchildren_cousins(event_loop, nested_routers):
    message = None

    payload = dat()



    @nested_routers["left_left_router"].endpoint(":test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await nested_routers["right_right_router"].submit(aurcore.Event("top:left:left_left:test", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload

@pytest.mark.asyncio
async def test_router_synonym(event_loop, nested_routers):
    message = ""

    payload = dat()



    @nested_routers["top_router"].endpoint(":left")
    async def _(x):
        nonlocal message
        message += x.args[0]

    @nested_routers["left_router"].endpoint(":sub")
    async def _(x):
        nonlocal message
        message += x.args[0]


    await nested_routers["right_right_router"].submit(aurcore.Event("top:left", payload))
    await nested_routers["right_right_router"].submit(aurcore.Event("top:left:sub", payload))
    await asyncio.sleep(0)  # idk

    assert message == payload*3 # 2 triggers on left, 1 trigger on sub
