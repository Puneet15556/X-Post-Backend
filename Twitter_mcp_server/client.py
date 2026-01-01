import os
from langchain_mcp_adapters.client import MultiServerMCPClient



async def create_client():
    
    
    base_path = os.path.dirname(os.path.abspath(__file__))

    
    mcp_server_path = os.path.join(base_path, "twitter_mcp_server4.py")
    return MultiServerMCPClient({
        "twitter": {
            "command": "python",
            "args": [mcp_server_path],
            "transport": "stdio"
        }
    })
