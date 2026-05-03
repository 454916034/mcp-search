import asyncio
import os
import time
import uvicorn
import feedparser
from fastmcp import FastMCP

mcp = FastMCP("web-search")

_last_call = 0
MIN_INTERVAL = 2


@mcp.tool()
async def search_web(query: str) -> str:
    """Search the web for general information. NOT for news."""
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
        return "\n".join(
            f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---"
            for r in results
        )
    except Exception as e:
        return f"Search error: {e}"


@mcp.tool()
async def get_chinese_news(topic: str = "今日热点") -> str:
    """Get latest Chinese news. Use this when user asks about news, current events, what happened recently, or daily events in China. This is the BEST tool for Chinese news."""
    global _last_call
    now = time.time()
    if now - _last_call < MIN_INTERVAL:
        await asyncio.sleep(MIN_INTERVAL - (now - _last_call))
    _last_call = time.time()

    def _fetch(t):
        url = f"https://news.google.com/rss/search?q={t}+when:3d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries[:10]:
            source = ""
            if hasattr(e, "source") and hasattr(e.source, "title"):
                source = e.source.title
            items.append(
                f"Title: {e.get('title','')}\nSource: {source}\nURL: {e.get('link','')}\nDate: {e.get('published','')}\n---"
            )
        return "\n".join(items) if items else "No news found."

    try:
        return await asyncio.to_thread(_fetch, topic)
    except Exception as e:
        return f"News error: {e}"


if __name__ == "__main__":
    app = mcp.http_app()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
