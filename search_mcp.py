import asyncio, logging
from mcp import types
from mcp.server import Server, ServerRequestContext
from duckduckgo_search import DDGS
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
async def handle_list_tools(ctx, params):
    return types.ListToolsResult(tools=[types.Tool(
        name="search_web", description="Search the web using DuckDuckGo",
        inputSchema={"type":"object","properties":{"query":{"type":"string","description":"Search query"}},"required":["query"]})])
async def handle_call_tool(ctx, params):
    if params.name == "search_web":
        query = (params.arguments or {}).get("query", "")
        def _search(q):
            with DDGS() as ddgs:
                return list(ddgs.text(q, max_results=5))
        try:
            results = await asyncio.to_thread(_search, query)
            text = "\n".join(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n---" for r in results) or "No results found."
            return types.CallToolResult(content=[types.TextContent(type="text", text=text)])
        except Exception as e:
            return types.CallToolResult(content=[types.TextContent(type="text", text=f"Error: {e}")], isError=True)
    return types.CallToolResult(content=[types.TextContent(type="text", text=f"Unknown tool: {params.name}")], isError=True)
app = Server("web-search", on_list_tools=handle_list_tools, on_call_tool=handle_call_tool)
if __name__ == "__main__":
    import uvicorn
    from event_store import InMemoryEventStore
    from starlette.middleware.cors import CORSMiddleware
    store = InMemoryEventStore()
    starlette_app = app.streamable_http_app(event_store=store, json_response=True)
    starlette_app = CORSMiddleware(starlette_app, allow_origins=["*"], allow_methods=["GET","POST","DELETE"], expose_headers=["Mcp-Session-Id"])
    logger.info("Starting on http://0.0.0.0:3000")
    uvicorn.run(starlette_app, host="0.0.0.0", port=3000)
