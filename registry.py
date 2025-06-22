# registry.py
from dataclasses import dataclass, field
from sentence_transformers import SentenceTransformer
from pathlib import Path
import numpy as np, uuid, pickle

ENCODER = SentenceTransformer("all-MiniLM-L6-v2")
REGISTRY_FILE = Path("agents.pkl")

@dataclass
class AgentMeta:
    id: str
    name: str
    sys_prompt: str
    embedding: np.ndarray = field(repr=False)

class AgentRegistry:
    def __init__(self):
        self.agents: list[AgentMeta] = []
        if REGISTRY_FILE.exists() and REGISTRY_FILE.stat().st_size:
            self.agents = pickle.loads(REGISTRY_FILE.read_bytes())

    def _save(self): REGISTRY_FILE.write_bytes(pickle.dumps(self.agents))

    def search(self, prompt: str, thresh: float = 0.83) -> AgentMeta | None:
        if not self.agents: return None
        q = ENCODER.encode(prompt, normalize_embeddings=True)
        sims = [float(q @ a.embedding) for a in self.agents]
        best = max(range(len(sims)), key=sims.__getitem__)
        return self.agents[best] if sims[best] > thresh else None

    def add(self, name: str, sys_prompt: str, letta_id: str):
        vec = ENCODER.encode(sys_prompt, normalize_embeddings=True)
        self.agents.append(AgentMeta(letta_id, name, sys_prompt, vec))
        self._save()
