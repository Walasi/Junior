import aiohttp
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def search_web(query: str) -> str:
    """Search using Tavily API and return summarized answer."""
    api_key = settings.tavily_api_key
    if not api_key or api_key == "":
        logger.warning("Tavily API key missing")
        return "Web search is not configured. Please set TAVILY_API_KEY in your environment."
    
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 3,
        "include_answer": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                answer = data.get("answer", "")
                if answer:
                    return answer
                results = data.get("results", [])
                if results:
                    snippets = [r["snippet"] for r in results[:2]]
                    return " ".join(snippets)
                return "No relevant information found."
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        # Use the LLM to answer from its own knowledge
        reply = "I couldn't search the web, but here's what I know: ..."