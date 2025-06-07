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


# Tool mapping for dynamic tool assignment
AVAILABLE_TOOLS = {
    "internet_search_tool": internet_search_tool
}


def get_tools_from_names(tool_names: List[str]) -> List:
    """Convert tool names to actual tool objects with early return for empty list."""
    if not tool_names:
        return []
    
    return [AVAILABLE_TOOLS[name] for name in tool_names if name in AVAILABLE_TOOLS]