from langchain_mcp_adapters.client import MultiServerMCPClient

async def create_client():
    return MultiServerMCPClient({
        "twitter": {
            "command": "python",
            "args": [r"C:\Users\PUNEET\Desktop\DESKTOP\Projects\Monolithic_Generator\Twitter_mcp_server\twitter_mcp_server4.py"],
            "transport": "stdio"
        }
    })
