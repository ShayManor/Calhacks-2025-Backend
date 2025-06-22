"""
fetch_wrapper_example.py
------------------------
Generic adapter that exposes *any* Letta agent as both
(1) a Fetch.ai uAgent endpoint (P2P + REST) and
(2) a simple HTTP /prompt route for local health checks.

Copy this file unchanged into every container; pass two env-vars:
  LETTA_AGENT_ID   – the UUID of the Letta agent this wrapper fronts
  LETTA_API_KEY    – your Letta API key
Optional env-vars:
  UAGENT_PORT      – port for the uAgent (default 8000)
  LETTA_BASE_URL   – override if self-hosting Letta
  FETCH_SEED       – deterministic seed for agent keys
"""
import os, asyncio, httpx
from typing import Optional

from dotenv import load_dotenv
from uagents import Agent, Model, Context
load_dotenv()
LETTA_URL = os.getenv("LETTA_BASE_URL", "https://api.letta.com/v1")
LETTA_KEY = os.environ["LETTA_API_KEY"]
AGENT_ID = os.environ["LETTA_AGENT_ID"]
AGENT_PORT = int(os.getenv("UAGENT_PORT", "8000"))


# ---------- Data models ----------
class Prompt(Model):
    prompt: str


class Answer(Model):
    result: str
    agent_id: str


# ---------- Helper that calls Letta ----------
async def _call_letta(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {LETTA_KEY}"}
    payload = {"messages": [{"role": "user", "content": prompt}]}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{LETTA_URL}/agents/{AGENT_ID}/messages",
                              json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["messages"][-1]["content"]


# ---------- uAgent definition ----------
service = Agent(
    name=f"wrapper-{AGENT_ID[:6]}",
    port=AGENT_PORT,
    endpoint=[f"http://0.0.0.0:{AGENT_PORT}/submit"],
    seed=os.getenv("FETCH_SEED", "auto-generated"),
)


@service.on_message(model=Prompt, replies=Answer)
async def handle_prompt(ctx: Context, sender: str, msg: Prompt):
    ctx.logger.info("Received from %s: %s", sender, msg.prompt[:120])
    reply = await _call_letta(msg.prompt)
    await ctx.send(sender, Answer(result=reply, agent_id=AGENT_ID))


# Optional REST surface (useful on Cloud Run)
@service.on_rest_post("/prompt", expected_model=Prompt, responses=[Answer])
async def rest_prompt(ctx: Context, data: Prompt):
    reply = await _call_letta(data.prompt)
    return Answer(result=reply, agent_id=AGENT_ID)


if __name__ == "__main__":
    service.run()
