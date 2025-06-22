import json
import os
import time
import uuid

import openai
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from letta_client import Letta

from registry import AgentRegistry
from services.create_agent import create_agent
from pathlib import Path, PurePosixPath

app = Flask(__name__)

AGENTS_CSV = Path(__file__).resolve().parent / "agents.csv"
@app.route("/ping")
def ping():
    return jsonify({'ping': 'pong'})


load_dotenv()
reg, letta = AgentRegistry(), Letta(token=os.environ["LETTA_API_KEY"])


@app.post("/prompt")
def handle():
    print("test")
    # data = request.get_json(force=True)
    user_prompt = "Find me 10 things to do in berkeley California this saturday for someone who is 21."

    agent = reg.search(user_prompt)
    if agent is None:  # cold start
        name = f"A{uuid.uuid4().hex[:6]}"
        letta_id = create_agent(user_prompt, None)
        reg.add(name, user_prompt, letta_id)
        agent = reg.search(user_prompt)  # guaranteed hit

    # short-running → sync call to Letta
    resp = letta.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return jsonify({"agent": agent.name, "response": resp.messages[-1].content})


GMAPS = """
You are to rebuild the Google Maps Utility Agent as a Flask microservice using the Google Maps Platform (Geocoding API + Places API v1). Follow these exact specifications:

1 Overall Service Requirements
Expose four JSON POST endpoints: /geocode, /reverse_geocode, /nearby, /textsearch. 
Use Flask for routing, Pydantic for request validation, and requests (or httpx) for outbound calls. 

Use this GOOGLE_API_KEY everywhere:AIzaSyARrvLp5k2yA23PoawhD6bcpND3qcA3boA

Return HTTP 200 with valid JSON on success; map Google’s "ZERO_RESULTS" → empty list or 404 where appropriate; propagate upstream errors as 502 or 400. 

2 Endpoint Specifications
2.1 /geocode
Input:

json
Copy
Edit
{ "address": "1600 Amphitheatre Pkwy, Mountain View CA" }
Validation: Pydantic AddressIn(address: str). 
developers.google.com

Call:

pgsql
Copy
Edit
GET https://maps.googleapis.com/maps/api/geocode/json
    ?address={address}&key={API_KEY}
per Geocoding API docs 
developers.google.com
.

Success:

{
  "lat": <number>,
  "lng": <number>,
  "formatted_address": "<string>",
  "place_id": "<string>"
}
Errors:

404 if "results" is empty.

502 for non-200 HTTP.

400 if Google returns status ≠ OK|ZERO_RESULTS. 

2.2 /reverse_geocode
Input:

{ "lat": 37.422, "lng": -122.084 }
Validation: Pydantic LatLngIn(lat: float, lng: float).

Call:

GET https://maps.googleapis.com/maps/api/geocode/json
    ?latlng={lat},{lng}&key={API_KEY}
per reverse geocoding in the same Geocoding API.

Success:
{
  "formatted_address": "<string>",
  "place_id": "<string>"
}
Errors:

404 if no results.

Same HTTP/status mapping as /geocode.

2.3 /nearby (Places API – New)
Input:

{
  "lat": 37.422,
  "lng": -122.084,
  "type": "restaurant",
  "radius": 500
}
Validate with NearbyIn(lat: float, lng: float, type: str, radius: int) and 1 ≤ radius ≤ 50 000.

Call:

POST https://places.googleapis.com/v1/places:searchNearby
Headers:
  X-Goog-Api-Key: {API_KEY}
  X-Goog-FieldMask: places.displayName,places.formattedAddress
JSON body:
{
  "locationRestriction": {
    "circle": {
      "center": { "latitude": lat, "longitude": lng },
      "radius": radius
    }
  },
  "includedTypes": [ type ]
}
per Nearby Search (New) docs.

Success:

{ "places": [ /* Place objects with displayName & formattedAddress */ ] }
Errors:

400 if missing required field mask.

502 for HTTP ≠ 200.

2.4 /textsearch (Places API – New)
Input:
{
  "query": "pizza in New York",
  "lat": <optional>,
  "lng": <optional>,
  "radius": <optional>
}
Validate with TextSearchIn(query: str, lat: float | None, lng: float | None, radius: int | None).

Call:
POST https://places.googleapis.com/v1/places:searchText
Headers:
  X-Goog-Api-Key: {API_KEY}
  X-Goog-FieldMask: places.displayName,places.formattedAddress
JSON body:
{
  "textQuery": query,
  // optional:
  "locationRestriction": { "circle": { "center": { "latitude": lat, "longitude": lng }, "radius": radius } }
}
per Text Search (New) reference 
Success:
{ "results": [ /* Place objects */ ] }
3 Error Handling & Best Practices
Always check data["status"] against {"OK","ZERO_RESULTS"} before using data["results"]. 
Timeouts: use timeout=10 seconds on all HTTP calls.

Logging: on non-200 or status≠OK, log the raw response and return structured JSON { "error": ... }.

FieldMask: required on all new Places v1 calls or you’ll get HTTP 400. 
developers.google.com

4 Flask + Pydantic Boilerplate Example
from flask import Flask, request, jsonify
from pydantic import BaseModel, Field, ValidationError
import os, requests

API_KEY = os.environ["GOOGLE_API_KEY"]
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBY_URL  = "https://places.googleapis.com/v1/places:searchNearby"
TEXT_URL    = "https://places.googleapis.com/v1/places:searchText"

app = Flask(__name__)

class AddressIn(BaseModel):
    address: str = Field(...)

# (Define LatLngIn, NearbyIn, TextSearchIn similarly)

def gmap_get(url, params):
    params["key"] = API_KEY
    r = requests.get(url, params=params, timeout=10)
    # ...status & JSON checks as above...

"""


@app.route("/create_agent")
def create():
    start = time.time()
    res = """
    Create an agent that has 5 endpoints. Each endpoint should either ping chatGPT or claude. Make sure the name has something to do with text as these models only do text. The option for models should be gpt4.1 nano, gpt4.1, gpt o3, claude haiku 3.5, claude sonnet 4. It should work well and be easy to use with relevant and good docs and description. It should use these api keys exactly: ANTHROPIC_API_KEY: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 OPENAI_API_KEY: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. This is the openai quickstart:
    from openai import OpenAI
    client = OpenAI(api_key)
    
    response = client.responses.create(
        model="gpt-4.1",
        input="Write a one-sentence bedtime story about a unicorn."
    )
    
    print(response.output_text) 
    
    This is the claude quickstart:
    client = anthropic.Anthropic(api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        system=system,
        max_tokens=10_000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )
    return response.content[0].text
    """
    resp = create_agent(res, None)
    print(f'Total time: {time.time() - start}')
    return jsonify({'response': resp})


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
AGENTS_CSV = Path(os.getenv("AGENTS_CSV", BASE_DIR / "agents.csv"))
AGENTS_CSV.parent.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """
You are a helpful assistant that turns a flat list of agent records into a
tree suitable for a React d3.js visualiser.

**Output format (MUST be valid JSON):**
{
  "name": "<root-name>",
  "description": "<one-sentence description>",
  "children": [ ...same shape recursively... ]
}

Rules:
1. Use the agent with the word "Master", "Root", or "Orchestrator" in its
   name (if any) as the top-level node.  If multiple, pick the first.
2. If no obvious root exists, create a synthetic root named "RootAgent".
3. Group agents whose names share a common prefix (e.g. "Crawler-LinkParser")
   under the parent ("Crawler").
4. Preserve each agent’s description verbatim.
"""

@app.get("/agents/tree")
def gpt_tree():
    # 1) build the flat list from the existing registry
    flat = [
        {"name": a.name, "description": a.sys_prompt.split(".")[0]}
        for a in reg.agents
    ] or [
        # fallback demo list if registry is still empty
        {"name": "ResearchMaster", "description": "Root agent orchestrating all sub-tasks."},
        {"name": "Crawler", "description": "Collects relevant papers."},
        {"name": "Crawler-LinkParser", "description": "Parses and deduplicates links."},
        {"name": "Analyzer", "description": "Runs statistical models."},
        {"name": "Summarizer", "description": "Produces concise briefs."}
    ]

    # 2) ask GPT to build the hierarchy
    resp = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": json.dumps(flat)}
        ]
    )

    # 3) return JSON to the frontend
    try:
        tree = json.loads(resp.choices[0].message.content)
    except Exception:
        # GPT replied with non-JSON → fall back to hard-coded demo
        tree = {
            "name": "ResearchMaster",
            "description": "Root agent orchestrating all sub-tasks.",
            "children": [
                {
                    "name": "Crawler",
                    "description": "Collects relevant papers from multiple scholarly databases.",
                    "children": [
                        {"name": "LinkParser",
                         "description": "Parses and deduplicates citation links for the crawler."}
                    ]
                },
                {"name": "Analyzer", "description": "Runs statistical models and ML pipelines on harvested data."},
                {"name": "Summarizer", "description": "Produces concise, executive-level briefs from analysis results."}
            ]
        }
    return jsonify(tree)

@app.get("/registry")
def registry():
    rows = AGENTS_CSV.read_text().strip().splitlines()
    registry = [
        {"name": r.split(",")[0], "description": r.split(",")[1], "url": r.split(",")[2], "documentation": r.split(",")[3]}
        for r in rows if r
    ]
    return jsonify(registry)


@app.post("/register")
def register():
    data = request.get_json()
    with AGENTS_CSV.open("a", encoding="utf-8") as f:
        f.write(f"{data['name']},{data['id']},{data['url']}\n")
    return "", 204


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
