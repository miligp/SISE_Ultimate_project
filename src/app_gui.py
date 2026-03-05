"""
SISE-CLAW Voice Assistant (GUI)

Application fenêtrée avec CustomTkinter.
Lancement : python src/app_gui.py
"""

import asyncio
import threading
import time
import sys
from pathlib import Path
from typing import List, Optional

# Ajoute la racine du projet à sys.path pour que "src" soit importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import customtkinter as ctk
from pydantic_ai.messages import ModelMessage

from src.dashboard_ui.ui import BG, SURFACE, TEXT, DIMMER, CYAN, BLUE, GREEN
from src.dashboard_ui.components import ConsoleWidget, MicButton

from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager
from src.agent_logic.pydantic_ai_agent import agent


class SiseClawApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # ── Fenêtre ───────────────────────────────────────
        self.title("SISE-CLAW — Voice Assistant")
        self.geometry("780x700")
        self.minsize(650, 500)
        self.configure(fg_color=BG)

        # ── State ─────────────────────────────────────────
        self._running = False
        self._message_history: List[ModelMessage] = []
        self._recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
        self._provider = WhisperSTT(model_name="base")
        self._manager = TranscriptionManager(provider=self._provider)

        # ── Loop asyncio persistant ───────────────────────
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

        # ── Build UI ──────────────────────────────────────
        self._build_header()
        self._build_console()
        self._build_controls()

        # ── Raccourci clavier ─────────────────────────────
        self.bind_all("<Return>", lambda _: self._on_mic_click())

        # ── Boot sequence ─────────────────────────────────
        self.after(300, self._boot_sequence)

    # ────────────────────────────────────────────────────────
    # UI BUILD
    # ────────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=SURFACE, height=56, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            title_frame, text="🎙️ SISE-CLAW",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=TEXT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame, text="  v0.1.0  │  PydanticAI · WorkspaceMCP",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=DIMMER,
        ).pack(side="left", padx=(10, 0))

        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side="right", padx=20, pady=10)

        self._status_dot = ctk.CTkLabel(
            status_frame, text="●",
            font=ctk.CTkFont(size=14), text_color=GREEN,
        )
        self._status_dot.pack(side="left")

        self._status_label = ctk.CTkLabel(
            status_frame, text="PRÊT",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=GREEN,
        )
        self._status_label.pack(side="left", padx=(6, 0))

    def _build_console(self):
        console_frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        console_frame.pack(fill="both", expand=True, padx=16, pady=(12, 8))

        self.console = ConsoleWidget(console_frame)
        self.console.pack(fill="both", expand=True)

    def _build_controls(self):
        controls = ctk.CTkFrame(self, fg_color=SURFACE, height=70, corner_radius=0)
        controls.pack(fill="x", padx=0, pady=0, side="bottom")
        controls.pack_propagate(False)

        inner = ctk.CTkFrame(controls, fg_color="transparent")
        inner.pack(pady=12)

        self.mic_btn = MicButton(inner, command=self._on_mic_click)
        self.mic_btn.pack(side="left", padx=8)

        ctk.CTkLabel(
            controls,
            text="SISE-CLAW  ·  Projet Master 2 SISE  ·  2026",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=DIMMER,
        ).pack(side="bottom", pady=(0, 4))

    # ────────────────────────────────────────────────────────
    # STATUS
    # ────────────────────────────────────────────────────────

    def _set_status(self, label: str, color: str):
        self._status_dot.configure(text_color=color)
        self._status_label.configure(text=label, text_color=color)

    # ────────────────────────────────────────────────────────
    # DECORATION ENTREE   # (affichage dans la console)
    # ────────────────────────────────────────────────────────

    def _boot_sequence(self):
        self.console.write_boot([
            "Agent PydanticAI chargé",
            "MCP connecté : workspace-mcp (gmail, calendar)",
            "STT initialisé : whisper-base (fr)",
            "Micro prêt : 16000Hz mono",
        ])

    # ────────────────────────────────────────────────────────
    # ACTION
    # ────────────────────────────────────────────────────────

    def _on_mic_click(self):
        if self._running:
            return
        self._running = True
        self.mic_btn.set_listening()
        threading.Thread(target=self._pipeline_thread, daemon=True).start()

    # ────────────────────────────────────────────────────────
    # PIPELINE
    # ────────────────────────────────────────────────────────

    def _pipeline_thread(self):
        audio_path: Optional[Path] = None
        t_start = time.time()

        try:
            self.after(0, self.console.write_separator)

            # ── 1. Écoute ─────────────────────────────────
            self.after(0, lambda: self._set_status("ÉCOUTE", CYAN))
            self.after(0, lambda: self.console.write_step("🎤", "STT", "Écoute en cours...", "cyan"))

            audio_path = self._recorder.record_until_silence()
            name = audio_path.name
            self.after(0, lambda: self.console.write_detail(f"→ audio capturé : {name}"))

            # ── 2. Transcription ──────────────────────────
            self.after(0, lambda: self._set_status("TRANSCRIPTION", CYAN))
            self.after(0, lambda: self.console.write_step("🎤", "STT", "Transcription...", "cyan"))

            result_stt = self._manager.process_audio(audio_path, language="fr")
            query: str = result_stt.text.strip()

            if not query or len(query) < 2:
                self.after(0, lambda: self.console.write_detail("→ transcription vide, ignoré"))
                return

            q = query
            self.after(0, lambda: self.console.write_step("▶", "USER", f'"{q}"', "text"))
            self.after(0, lambda: self.console.write_detail(f"→ {len(q)} caractères"))

            # ── 3. Agent LLM ──────────────────────────────
            self.after(0, lambda: self._set_status("RÉFLEXION", BLUE))
            self.after(0, lambda: self.console.write_step("🧠", "LLM", "Analyse et réflexion...", "blue"))

            future = asyncio.run_coroutine_threadsafe(
                agent.run(q, message_history=self._message_history),
                self._loop,
            )
            result = future.result()

            self._message_history.extend(result.new_messages())
            response: str = result.output
            r = response
            self.after(0, lambda: self.console.write_detail(f"→ réponse ({len(r)} car.)"))

            # ── Tool calls ────────────────────────────────
            for msg in result.new_messages():
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        if hasattr(part, "tool_name"):
                            tn = part.tool_name
                            self.after(0, lambda t=tn: self.console.write_step(
                                "🔧", "MCP", f"Appel {t}()", "peach"
                            ))

            # ── 4. Résultat ───────────────────────────────
            elapsed = time.time() - t_start
            e = elapsed
            self.after(0, lambda: self._set_status("RÉSULTAT", GREEN))
            self.after(0, lambda: self.console.write_step("✅", "DONE", "Réponse reçue", "green"))
            self.after(0, lambda: self.console.write_result(r))
            self.after(0, lambda: self.console.write_tts(r))
            self.after(0, lambda: self.console.write_detail(f"→ terminé en {e:.1f}s"))

        except Exception as ex:
            err = str(ex)
            self.after(0, lambda: self.console.write_step("❌", "ERREUR", err, "red"))

        finally:
            if audio_path and audio_path.exists():
                audio_path.unlink()
            self.after(0, lambda: self._set_status("PRÊT", GREEN))
            self.after(0, self.mic_btn.set_ready)
            self._running = False


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = SiseClawApp()
    app.mainloop()
