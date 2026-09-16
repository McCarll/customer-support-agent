from .mcp_server import mcp
from .store import init_db

if __name__ == "__main__":
    init_db()
    mcp.run(transport="streamable-http")
