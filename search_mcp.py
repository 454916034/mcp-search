import asyncio
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("web-search")


@mcp.tool()
async def search_web(query: str) -> str:
    """Search the web using DuckDuckGo"""
    from duckduckgo_search import DDGS

    def _search(q):
        with DDGS() as ddgs:
            return list(ddgs.text(q, max_results=5))

    try:
        results = await asyncio.to_thread(_search, query)
        if not results:
            return "No results found."
        formatted = []
        for r in results:
            formatted.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---")
        return "\n".join(formatted)
    except Exception as e:
        return f"Search error: {e}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
