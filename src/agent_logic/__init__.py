"""
agent_logic — Orchestration LLM + connexion MCP.

Expose les fonctions publiques de haut niveau pour les autres modules
(dashboard_ui, voice_processing).
"""

from src.agent_logic.pydantic_ai_agent import run_query, stream_query

__all__ = ["run_query", "stream_query"]
