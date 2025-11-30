from typing import List, Dict
from tavily import TavilyClient
from .config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

def web_blurbs(query: str, k: int = 3) -> List[Dict]:
    """
    Query Tavily for supplemental web results.
    Returns up to k items with title, url, and a short summary.
    """
    if client is None:
        return []

    try:
        res = client.search(
            query,
            search_depth="advanced",
            max_results=k,
            include_answer=False
        )
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "summary": (r.get("content", "") or "")[:800]
            }
            for r in res.get("results", [])
        ]
    except Exception as e:
        # On error, return a single entry with the exception text
        return [{"title": "error", "url": "", "summary": str(e)}]
