"""
Tests de la boucle LLM ↔ MCP avec requêtes codées en dur.

Prérequis :
    1. Démarrer le serveur MCP dans mcp_workspace/ :
           cd mcp_workspace && uv run fastmcp run fastmcp_server.py --transport streamable-http
    2. Configurer .env à la racine du projet :
           ANTHROPIC_API_KEY=sk-ant-...
           MCP_SERVER_URL=http://localhost:8000/mcp   # optionnel, valeur par défaut

Lancement :
    uv run python -m src.agent_logic.test_agent
"""

import asyncio
import sys
import time

from src.agent_logic.pydantic_ai_agent import run_query, stream_query

# ─── Scénarios de test ────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "label": "Lecture emails",
        "query": "Lis le dernier mail et donne-moi un résumé.",
    }
]


async def test_standard(scenario: dict) -> bool:
    """Test run_query (réponse complète)."""
    print(f"\n[{scenario['label']}] {scenario['query']}")
    print("─" * 60)
    t0 = time.perf_counter()
    try:
        response = await run_query(scenario["query"])
        elapsed = time.perf_counter() - t0
        print(response)
        print(f"\n  ✓ {elapsed:.1f}s")
        return True
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {e}")
        return False


async def test_stream(query: str) -> bool:
    """Test stream_query (tokens en temps réel)."""
    print(f"\n[Streaming] {query}")
    print("─" * 60)
    try:
        async for chunk in stream_query(query):
            print(chunk, end="", flush=True)
        print("\n  ✓ stream OK")
        return True
    except Exception as e:
        print(f"\n  ✗ {type(e).__name__}: {e}")
        return False


async def main():
    print("=" * 60)
    print("  Test boucle LLM ↔ MCP")
    print("=" * 60)

    results = []

    # Tests standards
    for scenario in SCENARIOS:
        ok = await test_standard(scenario)
        results.append(ok)

    # Test streaming sur la première requête
    ok = await test_stream("Combien d'emails non lus ai-je ?")
    results.append(ok)

    # Bilan
    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"  Résultat : {passed}/{total} tests réussis")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
