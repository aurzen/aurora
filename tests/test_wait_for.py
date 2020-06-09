import uuid
import pytest
import aurcore
import asyncio
def dat():
    return uuid.uuid4().hex


@pytest.fixture
def simple_router():
    return aurcore.EventRouter(name="test_router")

@pytest.mark.asyncio
async def test_simple_wait(event_loop, simple_router: aurcore.EventRouter):
    message = None
    _payload = dat()
    async def clock():
        while True:
            await asyncio.sleep(1)
            await simple_router.submit(aurcore.Event(":clock tick", payload=_payload))
    task = asyncio.get_event_loop().create_task(clock())

    payload = await simple_router.wait_for(":clock tick")

    assert _payload == payload.kwargs["payload"]

    task.cancel()
    asyncio.ensure_future(task)


