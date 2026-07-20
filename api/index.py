from fastapi import FastAPI, HTTPException
import requests
import re
import os

app = FastAPI()

# Set this in Vercel's dashboard: Project Settings -> Environment Variables -> SERPAPI_KEY
# Never hardcode API keys in source once this is pushed to a public GitHub repo.
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")


@app.get("/api/search")
def search_linkedin_posts(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    if not SERPAPI_KEY:
        raise HTTPException(
            status_code=500,
            detail="SERPAPI_KEY is not configured. Add it in Vercel's project environment variables."
        )

    # Format the query to specifically target public LinkedIn posts
    formatted_query = f'site:linkedin.com/posts {query}'

    params = {
        "engine": "google",
        "q": formatted_query,
        "api_key": SERPAPI_KEY,
        "num": 10
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Search API error: {str(e)}")

    if "organic_results" not in data:
        return {"leads": []}

    leads = []

    for result in data["organic_results"]:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")

        # Extract the user's name from the title
        name_parts = re.split(r" on LinkedIn| - LinkedIn| \| LinkedIn", title)
        name = name_parts[0].strip() if name_parts and name_parts[0].strip() else "Unknown user"

        leads.append({
            "name": name,
            "title": "View profile for role",
            "company": "N/A",
            "content": snippet,
            "url": link,
            "date": "Recent",
            "engagement": "N/A",
            "query": query
        })

    return {"leads": leads}
