from fastapi import FastAPI, HTTPException
import requests
import os
import time
from datetime import datetime, timezone

app = FastAPI()

# =============================================================================
# SECTION 1 — EXPLICIT STATED INTENT
# =============================================================================

# --- Reddit: ON HOLD -----------------------------------------------------
# Reddit closed self-service API registration under its "Responsible Builder
# Policy" — new apps now require manual approval, and commercial use requires
# express written approval. Left disabled until that's resolved.

def search_reddit(query: str):
    raise HTTPException(
        status_code=501,
        detail=(
            "Reddit is on hold. Self-service API access is closed under Reddit's "
            "Responsible Builder Policy — commercial use now requires explicit "
            "written approval from Reddit before any access. See README."
        )
    )


# --- Hacker News: LIVE — Algolia public search API, no auth required -----

def search_hn(query: str):
    params = {"query": query, "tags": "story", "hitsPerPage": 20}
    try:
        resp = requests.get("https://hn.algolia.com/api/v1/search_by_date", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Hacker News search failed: {str(e)}")

    leads = []
    for hit in data.get("hits", []):
        created_at = hit.get("created_at", "")
        date_str = created_at[:10] if created_at else "Unknown"
        title = hit.get("title") or ""
        story_text = hit.get("story_text") or ""
        content = f"{title} — {story_text}".strip(" —") if story_text else title
        object_id = hit.get("objectID")
        url = hit.get("url") or (f"https://news.ycombinator.com/item?id={object_id}" if object_id else "")

        leads.append({
            "platform": "Hacker News",
            "name": hit.get("author", "unknown"),
            "source": "news.ycombinator.com",
            "content": content[:600],
            "url": url,
            "date": date_str,
            "engagement": f"{hit.get('points', 0)} points · {hit.get('num_comments', 0)} comments",
            "query": query
        })
    return leads


# --- Upwork: PENDING -------------------------------------------------------

def search_upwork(query: str):
    raise HTTPException(
        status_code=501,
        detail="Upwork connector pending API approval and anti-circumvention ToS review. See README."
    )


@app.get("/api/search")
def search(platform: str, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    if platform == "reddit":
        return {"leads": search_reddit(query)}
    elif platform == "hn":
        return {"leads": search_hn(query)}
    elif platform == "upwork":
        return {"leads": search_upwork(query)}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")


# =============================================================================
# SECTION 2 — FIRMOGRAPHIC & TECHNOGRAPHIC TRIGGERS
# =============================================================================

# --- GDELT: LIVE — free global news search, no key required --------------
# Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

def search_gdelt(query: str):
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": 20,
        "format": "json",
        "sort": "datedesc"
    }
    try:
        resp = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"GDELT search failed: {str(e)}")
    except ValueError:
        # GDELT sometimes returns non-JSON (e.g. empty/error) for malformed queries
        raise HTTPException(status_code=502, detail="GDELT returned an unexpected response — try simplifying the query.")

    triggers = []
    for article in data.get("articles", []):
        seendate = article.get("seendate", "")
        date_str = f"{seendate[0:4]}-{seendate[4:6]}-{seendate[6:8]}" if len(seendate) >= 8 else "Unknown"
        triggers.append({
            "source": "GDELT News",
            "headline": article.get("title", ""),
            "detail": "News mention matching trigger query",
            "domain": article.get("domain", ""),
            "country": article.get("sourcecountry", ""),
            "url": article.get("url", ""),
            "date": date_str,
            "query": query
        })
    return triggers


# --- SEC EDGAR: LIVE — free official full-text search, no key required ---
# Docs: https://www.sec.gov/edgar/search/

def search_sec(query: str):
    headers = {"User-Agent": "Mirai Labs Signal Radar contact@themirailabs.com"}
    params = {"q": query, "forms": "8-K"}
    try:
        resp = requests.get("https://efts.sec.gov/LATEST/search-index", headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"SEC EDGAR search failed: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=502, detail="SEC EDGAR returned an unexpected response.")

    triggers = []
    for hit in data.get("hits", {}).get("hits", []):
        src = hit.get("_source", {})
        display_names = src.get("display_names", [])
        company = display_names[0] if display_names else "Unknown company"
        filed_date = src.get("file_date", "Unknown")
        ciks = src.get("ciks", [])
        cik = ciks[0] if ciks else None
        filing_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K"
            if cik else "https://www.sec.gov/cgi-bin/browse-edgar"
        )

        triggers.append({
            "source": "SEC EDGAR",
            "headline": company,
            "detail": f"{src.get('form', '8-K')} filing",
            "domain": "sec.gov",
            "country": "US",
            "url": filing_url,
            "date": filed_date,
            "query": query
        })
    return triggers


# --- Tech stack (BuiltWith / Wappalyzer): PENDING -------------------------
# Both require a paid API key for programmatic domain lookups at any real
# volume. Add BUILTWITH_API_KEY as an env var and implement here if you
# decide to proceed.

def search_techstack(query: str):
    raise HTTPException(
        status_code=501,
        detail="Tech-stack detection pending a paid BuiltWith/Wappalyzer API key. Not wired up yet."
    )


@app.get("/api/triggers")
def triggers(source: str, query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    if source == "gdelt":
        return {"triggers": search_gdelt(query)}
    elif source == "sec":
        return {"triggers": search_sec(query)}
    elif source == "techstack":
        return {"triggers": search_techstack(query)}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
