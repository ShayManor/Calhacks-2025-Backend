# test_agents.py
"""
End-to-end smoke-tests for the research-pipeline agents.

Each test does three things:
1. Calls the agent’s *health* endpoint and asserts HTTP 200 + JSON body.
2. Sends a minimal, valid POST payload to the primary endpoint.
3. Verifies both HTTP 200 and a couple of mandatory JSON keys.

The tests are intentionally lightweight (≤ 2 s total) so you can run
them in CI on every deploy.
"""
import json
import base64
import httpx
import pytest


#
# ---------------------------- helper ----------------------------
#
def post_ok(url: str, payload: dict, must_have: set[str]) -> None:
    """POST payload → url and assert 200 + required keys."""
    with httpx.Client(timeout=15) as c:
        r = c.post(url, json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        missing = must_have - data.keys()
        print(must_have)
        assert not missing, f"response missing keys: {missing}"


#
# ------------------------- text-respondent -----------------------
#
TR_BASE = "https://text-respondent-854967522738.us-central1.run.app"

@pytest.mark.parametrize("model,endpoint", [
    ("gpt4.1-nano",  "/text-generate"),
    ("gpt4.1",       "/text-summarize"),
    ("gpt-o3",       "/text-analyze"),
    ("claude-haiku", "/text-rewrite"),
    ("claude-sonnet","/text-translate"),
])
def test_text_respondent(model, endpoint):
    # health
    with httpx.Client(timeout=10) as c:
        r = c.get(f"{TR_BASE}/ping")
        assert r.status_code == 200

    # minimal happy-path payloads
    if endpoint == "/text-generate":
        post_ok(f"{TR_BASE}{endpoint}",
                {"prompt": "Hello world", "model": model},
                {"prompt", "response"})
    elif endpoint == "/text-summarize":
        post_ok(f"{TR_BASE}{endpoint}",
                {"text": "One two three four five six seven eight nine ten " * 3,
                 "model": model},
                {"original_len", "summary"})
    elif endpoint == "/text-analyze":
        post_ok(f"{TR_BASE}{endpoint}",
                {"text": "Hello world", "model": model},
                {"word_count", "sentiment"})
    elif endpoint == "/text-rewrite":
        post_ok(f"{TR_BASE}{endpoint}",
                {"text": "Rewrite me", "style": "casual", "model": model},
                {"rewritten", "style"})
    else:  # translate
        post_ok(f"{TR_BASE}{endpoint}",
                {"text": "Hello", "target_language": "es", "model": model},
                {"translation", "target_language"})


#
# ------------------------- research-master -----------------------
#
RM_BASE = "https://researchmaster-854967522738.us-central1.run.app"

def test_research_master_health_and_registry():
    with httpx.Client(timeout=10) as c:
        assert c.get(f"{RM_BASE}/health").status_code == 200
        # registry should be json list even if empty
        r = c.get(f"{RM_BASE}/agents")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

def test_research_master_pipeline():
    pipeline = [
        {"name": "researchmaster-crawler", "url": "https://researchmaster-crawler-854967522738.us-central1.run.app"},
    ]
    post_ok(f"{RM_BASE}/research-master",
            {"query": "quantum computing", "pipeline": pipeline},
            {"trace", "result"})


#
# ---------------------------- crawler ----------------------------
#
CRAWLER_BASE = "https://researchmaster-crawler-854967522738.us-central1.run.app"

def test_crawler_health_and_search():
    with httpx.Client(timeout=10) as c:
        assert c.get(f"{CRAWLER_BASE}/crawler/health").status_code == 200
    post_ok(f"{CRAWLER_BASE}/crawler/search",
            {"query": "graph neural networks", "max_results": 3},
            {"papers"})


#
# ---------- content-fetcher  → clean-html → lang-detect ----------
#
CF_BASE   = "https://contentfetcher-854967522738.us-central1.run.app"
CH_BASE   = "https://cleanhtml-854967522738.us-central1.run.app"
LD_BASE   = "https://lang-detect-854967522738.us-central1.run.app"

def test_content_fetcher_chain():
    # fetch a known small HTML page (example.com)
    post_ok(f"{CF_BASE}/crawler/content-fetcher",
            {"links": ["http://example.com"], "timeout": 5},
            {"results"})
    # clean html
    html = "<html><script>bad()</script><body>Hello</body></html>"
    post_ok(f"{CH_BASE}/clean-html", {"html": html},
            {"cleaned_html", "extracted_text"})
    # language detect
    post_ok(f"{LD_BASE}/language-detect",
            {"text": "This is an English sentence."},
            {"language", "is_english"})


#
# --------------- citation extractor → deduplicator --------------
#
CE_BASE = "https://citation-extractor-854967522738.us-central1.run.app"
DD_BASE = "https://citation-duplicate-merger-854967522738.us-central1.run.app"

def test_citation_and_dedupe():
    sample = ("Smith, J. (2022). Deep Learning. Journal of AI.\n"
              "Smith, J. (2022). Deep Learning. Journal of AI.")
    post_ok(f"{CE_BASE}/citation-extractor",
            {"text": sample},
            {"bibliography"})
    citations = [
        {"title": "Deep Learning", "authors": "Smith", "year": 2022},
        {"title": "Deep Learning", "authors": "Smith", "year": 2022},
    ]
    post_ok(f"{DD_BASE}/deduplicate",
            {"citations": citations},
            {"deduplicated", "removed"})


#
# -------- pdf-downloader → pdf-text-extractor → section-splitter -
#
PD_BASE = "https://pdf-downloader-854967522738.us-central1.run.app"
PT_BASE = "https://pdf-text-extractor-854967522738.us-central1.run.app"
SS_BASE = "https://section-splitter-854967522738.us-central1.run.app"

def test_pdf_flow():
    link = "https://arxiv.org/pdf/2107.03374.pdf"
    # download small PDF
    r = httpx.post(f"{PD_BASE}/download-pdfs",
                   json={"citations": [{"title": "Any", "pdf_link": link}]},
                   timeout=30)
    assert r.status_code == 200
    pdf_url = link                               # in success case we reuse
    # extract text
    payload = {"pdf_url": pdf_url, "use_ocr": False, "extract_metadata": False}
    post_ok(f"{PT_BASE}/extract-pdf-text", payload,
            {"text", "page_count"})
    # split sections
    sample_txt = "Introduction\nA\nMethods\nB\nResults\nC\nDiscussion\nD"
    post_ok(f"{SS_BASE}/split-sections",
            {"text": sample_txt},
            {"sections", "count"})
