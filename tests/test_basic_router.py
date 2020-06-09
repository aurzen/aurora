import pytest
import uuid
import asyncio
import time
import logging
import aurcore


# logging.basicConfig()
# log = logging.getLogger("aurevent")

# log.setLevel(logging.DEBUG)


def dat():
    return uuid.uuid4().hex


@pytest.fixture
def simple_router():
    return aurcore.EventRouter(name="test_router")


@pytest.mark.asyncio
async def test_nonasync_listener(event_loop, simple_router):
    message = None

    @simple_router.endpoint(":test")
    def _(x):
        nonlocal message
        message = x

    await simple_router.submit(aurcore.Event(":test", payload=dat()))
    await asyncio.sleep(0)  # idk

    assert message is not None


@pytest.mark.asyncio
async def test_local_event_submit_endpoint_receive(event_loop, simple_router):
    message = None

    @simple_router.endpoint(":test")
    async def _(x):
        nonlocal message
        message = x

    await simple_router.submit(aurcore.Event(":test", payload=dat()))
    await asyncio.sleep(0)  # idk

    assert message is not None


@pytest.mark.asyncio
async def test_absolute_event_submit_endpoint_receive(event_loop, simple_router):
    message = None

    @simple_router.endpoint("test_router:test")
    async def _(x):
        nonlocal message
        message = x

    await simple_router.submit(aurcore.Event(":test", payload=dat()))
    await asyncio.sleep(0)  # idk
    assert message is not None


@pytest.mark.asyncio
async def test_local_event_submit_endpoint_data(event_loop, simple_router):
    message = None

    payload = dat()

    @simple_router.endpoint(":test")
    async def _(x):
        nonlocal message
        message = x.args[0]

    await simple_router.submit(aurcore.Event(":test", payload))
    await asyncio.sleep(0.1)  # idk

    assert message == payload


@pytest.mark.asyncio
async def test_synoynms(event_loop, simple_router):
    message = ""

    payload = dat()

    @simple_router.endpoint(":test")
    async def _(x):
        nonlocal message
        message += x.args[0]

    @simple_router.endpoint(":test")
    async def _(x):
        nonlocal message
        message += x.args[0]

    await simple_router.submit(aurcore.Event(":test", payload))
    await asyncio.sleep(0.1)  # idk

    assert message == payload * 2
