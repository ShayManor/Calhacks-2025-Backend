import os
import requests

from pydantic import BaseModel, Field
from uagents import Agent, Context


class Prompt(BaseModel):
    prompt: str = Field(...)


class Reply(BaseModel):
    result: str


AGENT = Agent(
    name="ping-llm2",
    seed=os.getenv("FETCH_SEED", "auto-generated"),
    port=8000,
    endpoint=["http://0.0.0.0:8000/submit"]
)

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")


@AGENT.on_message(model=Prompt, replies=Reply)
async def call_backend(ctx: Context, sender: str, msg: Prompt):
    r = requests.post(f"{BACKEND}/generate", json={"prompt": msg.prompt, "llm": "gpt"})
    ctx.logger.info("backend status %s", r.status_code)
    await ctx.send(sender, Reply(result=r.json().get("result", "")))


if __name__ == "__main__":
    AGENT.run()
