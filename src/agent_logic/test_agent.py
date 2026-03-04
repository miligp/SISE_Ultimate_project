"""
Tests de l'agent avec l'outil email_utils intégré.

Prérequis :
    1. Configurer .env à la racine du projet avec les variables requises :
       EMAIL_USER, EMAIL_PASSWORD, EMAIL_IMAP_SERVER, ANTHROPIC_API_KEY (ou autre)

Lancement :
    uv run python -m src.agent_logic.test_agent
"""

import asyncio
import sys
import time

from src.agent_logic.pydantic_ai_agent import run_query, stream_query

SCENARIOS = [
    {
        "label": "Lecture emails",
        "query": "Quels sont mes 2 derniers emails ?",
    }
]


async def test_standard(scenario: dict) -> bool:
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
    print("  Test Agent ↔ email_utils")
    print("=" * 60)

    results = []

    for scenario in SCENARIOS:
        ok = await test_standard(scenario)
        results.append(ok)

    ok = await test_stream("Résume brièvement mon dernier email reçu.")
    results.append(ok)

    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"  Résultat : {passed}/{total} tests réussis")
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())