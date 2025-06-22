import asyncio, os, threading, time, httpx, json
import pytest, respx

from uagents import Agent, Model, Context
from examples.fetch_wrapper_example import service as wrapper, _call_letta

@pytest.fixture(scope="session", autouse=True)
def start_wrapper():
    # spin up the uAgent in a thread so tests can hit :8000
    t = threading.Thread(target=wrapper.run, daemon=True)
    t.start()
    time.sleep(2)        # give it a moment
    yield
    # wrapper.run exits with the program so nothing to clean up

class Prompt(Model):
    prompt: str

@respx.mock
@pytest.mark.asyncio
async def test_rest_prompt():
    # mock Letta
    respx.post("https://api.letta.com/v1/agents/").mock(
        return_value=httpx.Response(200, json={"messages": [{"content": "pong"}]}))
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:8000/prompt",
                              json={"prompt": "ping"})
        assert r.status_code == 200
        body = r.json()
        assert body["result"] == "pong"
        assert "agent_id" in body

@respx.mock
@pytest.mark.asyncio
async def test_p2p_loopback():
    # Arrange fake letta again
    respx.post("https://api.letta.com/v1/agents/").mock(
        return_value=httpx.Response(200, json={
            "messages": [{"content": "mesh ok"}]}))
    # Use uAgents in-memory deliverer
    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    @wrapper.on_message(model=Prompt)
    async def _tmp(ctx: Context, sender: str, msg: Prompt):
        fut.set_result(msg.prompt)

    await wrapper.send(wrapper.address, Prompt(prompt="mesh ok"))
    assert await asyncio.wait_for(fut, 3) == "mesh ok"
