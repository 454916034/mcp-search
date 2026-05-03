import asyncio
import os
import time
import uvicorn
from fastmcp import FastMCP

mcp = FastMCP("web-search")

_last_call = 0
MIN_INTERVAL = 2


@mcp.tool()
async def search_web(query: str) -> str:
    """Search the web using DuckDuckGo. Supports both Chinese and English."""
    global _last_call
    now = time.time()
    if now - _last_call < MIN_INTERVAL:
        await asyncio.sleep(MIN_INTERVAL - (now - _last_call))
    _last_call = time.time()

    from duckduckgo_search import DDGS

    def _search(q):
        with DDGS() as ddgs:
            results = list(ddgs.text(q, max_results=8, region="cn-zh"))
            if not results:
                results = list(ddgs.text(q, max_results=8))
            return results

    try:
        results = await asyncio.to_thread(_search, query)
        if not results:
            return "No results found."
        formatted = []
        for r in results:
            formatted.append(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---"
            )
        return "\n".join(formatted)
    except Exception as e:
        return f"Search error: {e}"


if __name__ == "__main__":
    app = mcp.http_app()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
