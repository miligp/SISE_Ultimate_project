"""
Client de connexion au serveur MCP Google Workspace.

Le serveur MCP tourne localement via FastMCP en transport streamable-http.
Ce module fournit la configuration et l'instance de connexion réutilisable.
"""

import os
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerHTTP

load_dotenv()

# URL de base du serveur MCP (configurable via .env)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")


def get_mcp_server() -> MCPServerHTTP:
    """
    Retourne un client MCP configuré pour le serveur Google Workspace.

    Le serveur doit être démarré séparément dans mcp_workspace/ via :
        cd mcp_workspace && fastmcp run fastmcp_server.py

    Returns:
        MCPServerHTTP connecté au serveur MCP local.
    """
    return MCPServerHTTP(url=MCP_SERVER_URL)
