import os, pytest, httpx, math, time

BASE = "https://google-geocode-agent-854967522738.us-central1.run.app"

def close(a, b, eps=1e-3): return abs(a - b) < eps

@pytest.mark.parametrize("address", [
    "1600 Amphitheatre Pkwy, Mountain View CA",
    "1 Market St, San Francisco CA"
])
def test_geocode_reverse(address):
    with httpx.Client(timeout=10.0) as client:
        g = client.post(f"{BASE}/geocode", json={"address": address})
        assert g.status_code == 200, g.text
        data = g.json()
        lat, lng = data["lat"], data["lng"]

        r = client.post(f"{BASE}/reverse_geocode", json={"lat": lat, "lng": lng})
        assert r.status_code == 200, r.text
        rev = r.json()
        assert address.split(",")[0].lower() in rev["formatted_address"].lower()

def test_nearby_result_shape():
    here = {"lat": 37.422, "lng": -122.084}
    body = {**here, "type": "restaurant", "radius": 500}
    with httpx.Client() as client:
        res = client.post(f"{BASE}/nearby", json=body)
        assert res.status_code == 200, res.text
        places = res.json()["places"]
        assert isinstance(places, list)

@pytest.mark.skipif("GOOGLE_API_KEY" not in os.environ,
                    reason="Requires quota to hit live Google Text Search")
def test_textsearch_live():
    with httpx.Client() as client:
        res = client.post(f"{BASE}/textsearch",
                          json={"query": "pizza in Palo Alto"})
        assert res.status_code == 200
        assert "results" in res.json()
