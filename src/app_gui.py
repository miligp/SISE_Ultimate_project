"""
SISE-CLAW Voice Assistant (GUI)

Application fenêtrée avec CustomTkinter.
Lancement : python src/app_gui.py
"""

import asyncio
import logging
import threading
import time
import sys
from pathlib import Path
from typing import List, Optional

import math

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

# Ajoute la racine du projet à sys.path pour que "src" soit importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Chargement des clés API (.env)
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_project_root / ".env")

import customtkinter as ctk
from pydantic_ai.messages import ModelMessage

from src.dashboard_ui.ui import BG, RED, SURFACE, TEXT, DIMMER, CYAN, BLUE, GREEN, PEACH, MAUVE, BORDER, YELLOW, FONTS
from src.dashboard_ui.components import ConsoleWidget, MicButton

from src.voice_processing.audio_capture import MicrophoneRecorder
from src.voice_processing.stt.deepgram_provider import DeepgramSTTProvider
from src.voice_processing.stt.groq_provider import GroqSTTProvider
from src.voice_processing.stt.whisper_provider import WhisperSTT
from src.voice_processing.stt.transcription_manager import TranscriptionManager
from src.voice_processing.tts.edge_tts_provider import EdgeTTSProvider
from src.voice_processing.tts.synthesis_manager import SynthesisManager
from src.voice_processing.audio_playback import AudioSpeaker
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
        self._playing = False   # True uniquement pendant la lecture TTS
        self._message_history: List[ModelMessage] = []
        self._recorder = MicrophoneRecorder(sample_rate=16000, channels=1)
        self._manager = TranscriptionManager(providers=[
            DeepgramSTTProvider(),
            GroqSTTProvider(),
            WhisperSTT(model_name="small"),
        ])
        self._tts = SynthesisManager(EdgeTTSProvider(voice="fr-FR-DeniseNeural"))
        self._speaker = AudioSpeaker()

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
        controls = ctk.CTkFrame(self, fg_color=SURFACE, height=110, corner_radius=0)
        controls.pack(fill="x", padx=0, pady=0, side="bottom")
        controls.pack_propagate(False)

        inner = ctk.CTkFrame(controls, fg_color="transparent")
        inner.pack(side="top", pady=(8, 2))

        self.mic_btn = MicButton(inner, command=self._on_mic_click)
        self.mic_btn.pack(side="left", padx=8)

        # ── Hint ──────────────────────────────────────────
        self._hint_label = ctk.CTkLabel(
            controls,
            text="Prêt. Appuyez sur Entrée pour parler.",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=DIMMER,
        )
        self._hint_label.pack(side="top", pady=(0, 1))

        # ── Jauge de volume ───────────────────────────────
        self._vol_label = ctk.CTkLabel(
            controls,
            text="",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=TEXT,
        )
        self._vol_label.pack(side="top", pady=(0, 2))

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

    def _start_vol_monitor(self) -> threading.Event:
        """Lance un thread qui lit le micro et affiche une sinusoïde animée."""
        stop = threading.Event()
        threshold = self._recorder.threshold
        _WAVE = " ▁▂▃▄▅▆▇█"
        W = 20  # largeur de la courbe

        def _monitor():
            phase = 0.0
            try:
                with sd.InputStream(samplerate=16000, channels=1, dtype="float32") as stream:
                    while not stop.is_set():
                        data, _ = stream.read(1600)  # ~100 ms
                        volume = float(np.sqrt(np.mean(data ** 2)))
                        amplitude = min(volume * 18, 1.0)
                        wave = ""
                        for i in range(W):
                            val = 0.5 + 0.5 * math.sin(phase + i * 2 * math.pi / 8)
                            idx = round(val * amplitude * 8)
                            wave += _WAVE[max(0, min(8, idx))]
                        phase = (phase + 0.4) % (2 * math.pi)
                        status = "🗣️ REC" if volume >= threshold else "⏳ ATTENTE"
                        text = f"Vol: {volume:.4f}  {wave}  [{status}]"
                        self.after(0, lambda t=text: self._vol_label.configure(text=t))
            except Exception:
                pass

        threading.Thread(target=_monitor, daemon=True).start()
        return stop

    def _clear_vol(self):
        self._vol_label.configure(text="")

    # ────────────────────────────────────────────────────────
    # BOOT
    # ────────────────────────────────────────────────────────

    def _boot_sequence(self):
        self.console.write_boot([
            "Agent PydanticAI chargé",
            "MCP connecté : workspace-mcp (gmail, doc, web)",
            "STT initialisé : Deepgram → Groq → Whisper-small (fr)",
            "Micro prêt : 16000Hz mono",
        ])

    # ────────────────────────────────────────────────────────
    # ACTION
    # ────────────────────────────────────────────────────────

    def _on_mic_click(self):
        if self._running:
            # Interruption de la lecture TTS en cours
            if self._playing:
                sd.stop()
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
            self.after(0, lambda: self._set_status("ÉCOUTE", RED))
            self.after(0, lambda: self.console.write_step("🎤", "STT", "Écoute en cours...", "red"))

            _vol_stop = self._start_vol_monitor()
            audio_path = self._recorder.record_until_silence()
            _vol_stop.set()
            self.after(0, self._clear_vol)
            name = audio_path.name
            self.after(0, lambda: self.console.write_detail(f"→ audio capturé : {name}"))

            # ── 2. Transcription ──────────────────────────
            self.after(0, lambda: self._set_status("TRANSCRIPTION", PEACH))
            self.after(0, lambda: self.console.write_step("🎤", "STT", "Transcription...", "peach"))

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

            # ── Tool calls → terminal uniquement ──────────
            for msg in result.new_messages():
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        if hasattr(part, "tool_name"):
                            logger.info("🔧 MCP → %s()", part.tool_name)

            # ── 4. Résultat ───────────────────────────────
            elapsed = time.time() - t_start
            e = elapsed
            self.after(0, lambda: self._set_status("RÉSULTAT", MAUVE))
            self.after(0, lambda: self.console.write_step("✅", "DONE", "Réponse reçue", "mauve"))
            self.after(0, lambda: self.console.write_markdown(r))
            self.after(0, lambda: self.console.write_tts(r))

            # ── 5. TTS audio ──────────────────────────────
            tts_future = asyncio.run_coroutine_threadsafe(
                self._tts.process_text_to_audio_file(r),
                self._loop,
            )
            tts_path = tts_future.result()
            self._playing = True
            self._speaker.play_file(tts_path)   # bloque jusqu'à fin ou sd.stop()
            self._playing = False
            tts_path.unlink(missing_ok=True)

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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = SiseClawApp()
    app.mainloop()
