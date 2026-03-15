import asyncio
from typing import List, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import settings


MCP_SERVERS: Dict = {
    "jobs": {
        "url": f"http://{settings.MCP_JOBS_HOST}:{settings.MCP_JOBS_PORT}/mcp",
        "transport": "streamable_http",
    }
}

_tools: List[BaseTool] = []
_tool_server_map: Dict[str, str] = {}

async def get_mcp_tools(servers: Optional[List[str]] = None) -> List[BaseTool]:
    """
    Returns the list of tools available via the FastMCP JobSpy server using Langchain MCP Adapters.
    """
    global _tools, _tool_server_map

    if not _tools:
        try:
            target = {k: v for k, v in MCP_SERVERS.items()}
            print(f"[MCP] Connecting to servers: {target}")
            client = MultiServerMCPClient(target)
            all_tools = await client.get_tools()

            _tool_server_map = {}
            for server_key in MCP_SERVERS:
                try:
                    single_client = MultiServerMCPClient({server_key: MCP_SERVERS[server_key]})
                    server_tools = await single_client.get_tools()
                    for t in server_tools:
                        _tool_server_map[t.name] = server_key
                except Exception as e:
                    print(f"[MCP] Warning: could not map tools for server '{server_key}': {e}")

            _tools = all_tools
            print(f"[MCP] Loaded {len(_tools)} tools: {[t.name for t in _tools]}")
            print(f"[MCP] Server map: {_tool_server_map}")
        except Exception as e:
            print(f"[MCP] Error initializing MCP client: {e}")
            _tools = []  # Return empty if MCP fails

    if servers:
        return [t for t in _tools if _tool_server_map.get(t.name) in servers]

    return _tools

async def reset_mcp_client():
    """Clear the cached MCP tools."""
    global _tools
    _tools = []
    return await get_mcp_tools()
