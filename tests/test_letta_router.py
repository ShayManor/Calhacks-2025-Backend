import os, json, socket, subprocess, time, tempfile, uuid, importlib.util
from pathlib import Path

import httpx, pytest, respx
from fastapi.encoders import jsonable_encoder
from sentence_transformers import SentenceTransformer
from registry import AgentRegistry         # ← your module
from services.create_agent import create_agent  # real func, mocked below

LETTA_URL = "https://api.letta.com/v1"

@pytest.fixture(scope="session")
def router(tmp_path_factory):
    """Fresh registry file in a temp dir so we don't clobber prod."""
    tmp_dir = tmp_path_factory.mktemp("router")
    (tmp_dir / "agents.pkl").write_bytes(b"")          # empty registry
    # monkey-patch expected global path
    import registry as reg_mod; reg_mod.REGISTRY_FILE = tmp_dir/"agents.pkl"
    return AgentRegistry()

def test_router_reuse(router, monkeypatch):
    enc = SentenceTransformer("all-MiniLM-L6-v2")
    prompt = "Write me a haiku about quantum entanglement"
    # fake first agent creation
    monkeypatch.setattr("services.create_agent.create_agent",
                        lambda name, p=prompt: f"let-{uuid.uuid4()}")
    agent = router.search(prompt)
    if agent is None:                                 # cold-start
        router.add("A0", prompt, "let-123")
    # second call must find same agent
    assert router.search(prompt).id == router.agents[0].id

def fake_create_agent(name, p):
    r = httpx.post(f"{LETTA_URL}/agents/", json={"name": name, "prompt": p})
    return r.json()["id"]

@respx.mock
def test_router_cold_start(monkeypatch, router):
    # 1  mock the outgoing POST
    route = respx.post(f"{LETTA_URL}/agents/").mock(
        return_value=httpx.Response(201, json={"id": "let-new"})
    )

    # 2  stub create_agent so it *makes* that POST
    def fake_create_agent(name, prompt):
        resp = httpx.post(f"{LETTA_URL}/agents/", json={"name": name, "prompt": prompt})
        return resp.json()["id"]

    monkeypatch.setattr("services.create_agent.create_agent", fake_create_agent)

    # 3  trigger cold-start logic (router sees no match)
    prompt = "Kubernetes YAML won't apply, help"
    assert router.search(prompt) is None          # still cold
    router.add("A1", prompt, fake_create_agent("A1", prompt))

    # 4  now the mock should have been hit exactly once
    assert route.call_count == 1
