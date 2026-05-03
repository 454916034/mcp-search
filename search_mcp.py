import asyncio
import os
import time
import uvicorn
import requests
from fastmcp import FastMCP

mcp = FastMCP("web-search")

_last_call = 0
MIN_INTERVAL = 2


def _do_search(query):
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=8, region="cn-zh"))
        if not results:
            results = list(ddgs.text(query, max_results=8))
    return results


def _do_news(topic):
    results = []

    try:
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {"pageid": "153", "lid": "2509", "k": "", "num": "30"}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        for item in data.get("result", {}).get("data", [])[:10]:
            results.append(
                f"Title: {item.get('title','')}\nSource: {item.get('media_name','')}\nURL: {item.get('url','')}\nDate: {item.get('ctime','')}\n---"
            )
    except Exception:
        pass

    if not results:
        try:
            url = "https://tenapi.cn/v2/toutiaohot"
            r = requests.get(url, timeout=10)
            data = r.json()
            for item in data.get("data", [])[:10]:
                results.append(
                    f"Title: {item.get('name','')}\nURL: {item.get('url','')}\nHot: {item.get('hot','')}\n---"
                )
        except Exception:
            pass

    if not results:
        results.append("No news available from any source.")

    return "\n".join(results)


@mcp.tool()
async def search_web(query: str) -> str:
    """Search the web for general information. NOT for news or current events."""
    global _last_call
    now = time.time()
    if now - _last_call < MIN_INTERVAL:
        await asyncio.sleep(MIN_INTERVAL - (now - _last_call))
    _last_call = time.time()
    try:
        results = await asyncio.to_thread(_do_search, query)
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
    try:
        return await asyncio.to_thread(_do_news, topic)
    except Exception as e:
        return f"News error: {e}"


if __name__ == "__main__":
    app = mcp.http_app()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
