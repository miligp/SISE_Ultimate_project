# src/dashboard_ui/hacker_console.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Log
from textual.containers import Container
from datetime import datetime

class HackerConsole(App):
    """
    Console visuelle inspirée de Mr. Robot pour l'affichage des logs et du TTS.
    """
    # On définit le CSS directement ici pour le thème "Mister Robot"
    CSS = """
    Screen {
        background: #0a0a0a;
    }

    #terminal_container {
        border: solid #00ff00;
        background: #000000;
        margin: 1 2;
        padding: 1;
        height: 100%;
    }

    Log {
        color: #00ff00;
        text-style: bold;
        background: #000000;
    }

    .system_msg {
        color: #ff0000;
        text-style: italic;
    }

    .tts_msg {
        color: #ffffff;
        background: #1a1a1a;
        border: left double #00ff00;
    }
    """

    def compose(self) -> ComposeResult:
        """Structure de l'interface."""
        yield Header(show_clock=True)
        with Container(id="terminal_container"):
            yield Static(">>> [ FSOCIETY_SYSTEM_INITIALIZED ]", classes="system_msg")
            yield Log(id="main_log")
        yield Footer()

    def on_mount(self) -> None:
        """Actions au démarrage de l'UI."""
        log = self.query_one("#main_log", Log)
        log.write_line(f"[{datetime.now().strftime('%H:%M:%S')}] Connection to agent established...")

    def display_tts_text(self, text: str) -> None:
        """Méthode pour pousser du texte dans la console."""
        log = self.query_one("#main_log", Log)
        log.write_line(f" \n[AGENT_REPLY] > {text}")
        log.write_line("-" * 40)

# Note : Pour l'intégration, Textual peut tourner dans un thread séparé 
# ou être piloté via un système de messages.