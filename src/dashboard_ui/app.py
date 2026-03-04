"""
Interface Streamlit — Assistant IA (Mistral via pydantic-ai)
"""

import asyncio
import queue
import sys
import os
import threading
import time

import streamlit as st

# ── Résolution du chemin racine ──────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agent_logic.pydantic_ai_agent import stream_query  # noqa: E402

# ── Config page ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Assistant IA",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 Assistant IA")
st.caption("Donnez un ordre en langage naturel — Mistral s'en charge.")
st.divider()

# ── Session state ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Historique de conversation ───────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Saisie de l'ordre ────────────────────────────────────────────────────────
prompt = st.chat_input("Ex : Lis-moi les 3 derniers messages…")

if prompt:
    # Affiche le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ── Réponse de l'assistant ───────────────────────────────────────────────
    with st.chat_message("assistant"):

        full_response = ""

        # Pont async → sync via thread + queue
        result_queue: queue.Queue = queue.Queue()

        def _run_stream() -> None:
            async def _async() -> None:
                try:
                    async for chunk in stream_query(prompt):
                        result_queue.put(("chunk", chunk))
                    result_queue.put(("done", None))
                except Exception as exc:  # noqa: BLE001
                    result_queue.put(("error", str(exc)))

            asyncio.run(_async())

        thread = threading.Thread(target=_run_stream, daemon=True)
        thread.start()

        # ── Phase "thinking" avec st.status ──────────────────────────────────
        start = time.time()
        first_chunk = True

        with st.status("⏳ Mistral réfléchit…", expanded=True) as status:
            log_placeholder = st.empty()
            stream_placeholder = st.empty()

            log_lines: list[str] = ["🧠 Analyse de votre demande…"]

            def _refresh_log() -> None:
                log_placeholder.markdown(
                    "\n\n".join(f"- {line}" for line in log_lines[-6:])
                )

            _refresh_log()

            while True:
                try:
                    kind, data = result_queue.get(timeout=0.4)
                except queue.Empty:
                    elapsed = time.time() - start
                    log_lines.append(f"⚙️ En attente de Mistral… ({elapsed:.1f}s)")
                    _refresh_log()
                    continue

                if kind == "chunk":
                    if first_chunk:
                        elapsed = time.time() - start
                        log_lines.append(
                            f"📨 Première réponse reçue après {elapsed:.1f}s"
                        )
                        log_lines.append("✍️ Génération en cours…")
                        _refresh_log()
                        status.update(
                            label="✍️ Génération de la réponse…", state="running"
                        )
                        first_chunk = False

                    full_response += data
                    # Affiche le texte en cours de génération (dans le status)
                    stream_placeholder.markdown(full_response + "▌")

                elif kind == "done":
                    elapsed = time.time() - start
                    log_lines.append(f"✅ Réponse complète — {elapsed:.1f}s au total")
                    _refresh_log()
                    stream_placeholder.empty()  # Vidé, rendu proprement dessous
                    status.update(
                        label=f"✅ Terminé en {elapsed:.1f}s",
                        state="complete",
                        expanded=False,
                    )
                    break

                elif kind == "error":
                    log_lines.append(f"❌ Erreur : {data}")
                    _refresh_log()
                    stream_placeholder.error(f"Erreur : {data}")
                    status.update(label="❌ Erreur", state="error", expanded=True)
                    break

        # Rendu final propre sous le status replié
        if full_response:
            st.markdown(full_response)

        thread.join(timeout=5)

    # Sauvegarde dans l'historique
    if full_response:
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
