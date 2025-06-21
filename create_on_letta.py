import os

import dotenv
from letta_client import Letta


def upload_to_letta(name: str, prompt: str):
    dotenv.load_dotenv()

    key = os.getenv("LETTA_API_KEY")
    id = 'cf1f587f-461d-44c7-8511-4b7cdd7839f8'
    client = Letta(token=key)
    agent_state = client.agents.create(
        name=name,
        system=prompt,
        llm_config={
            "model": "openai/gpt-4o-mini",
            "model_endpoint_type": "openai",
            "context_window": 8192,
            "temperature": 0.2,
        },
    )
    print("New agent id:", agent_state.id)
    return agent_state.id
