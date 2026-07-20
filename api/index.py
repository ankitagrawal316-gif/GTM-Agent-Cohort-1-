from fastapi import FastAPI, HTTPException
import requests
import re

app = FastAPI()

# IMPORTANT: You must get a free API key from serpapi.com and paste it here
SERPAPI_KEY = "YOUR_SERPAPI_KEY_HERE"

@app.get("/api/search")
def search_linkedin_posts(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # Format the query to specifically target public LinkedIn posts
    formatted_query = f'site:linkedin.com/posts {query}'
    
    # Send the request to SerpApi to execute the Google search safely
    params = {
        "engine": "google",
        "q": formatted_query,
        "api_key": SERPAPI_KEY,
        "num": 10 
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Search API error: {str(e)}")

    if "organic_results" not in data:
        return {"leads": []}

    leads = []
    
    # Parse the search results into a clean format
    for result in data["organic_results"]:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")
        
        # Extract the user's name from the title
        name_match = re.split(r" on LinkedIn| - LinkedIn| \| LinkedIn", title)
        name = name_match[0] if name_match else "Unknown User"

        leads.append({
            "name": name,
            "title": "View Profile for Details", 
            "company": "N/A",
            "content": snippet,
            "url": link,
            "date": "Recent",
            "engagement": "N/A",
            "query": query
        })

    return {"leads": leads}