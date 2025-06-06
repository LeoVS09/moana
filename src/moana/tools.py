from typing import List, Dict
from duckduckgo_search import DDGS


def internet_search_tool(query: str) -> List[Dict]:
    """
    Perform Internet Search
    """
    results = []
    ddgs = DDGS()
    for result in ddgs.text(keywords=query, max_results=5):
        results.append({
            "title": result.get("title", ""),
            "url": result.get("href", ""),
            "snippet": result.get("body", "")
        })
    return results