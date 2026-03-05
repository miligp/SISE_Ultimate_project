import customtkinter as ctk
from datetime import datetime
from .ui import COLORS, FONTS

class ConsoleWidget(ctk.CTkTextbox):
    """
    Composant spécialisé pour l'affichage des logs et des résultats.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Configuration de base
        self.configure(
            fg_color=COLORS["BG"],
            text_color=COLORS["TEXT"],
            font=FONTS["CONSOLE"],
            border_width=1,
            border_color=COLORS["BORDER"],
            corner_radius=8,
            wrap="word",
            state="disabled"
        )
        self._setup_tags()

    def _setup_tags(self):
        """Configure les styles de texte (couleurs, gras)."""
        tb = self._textbox
        # Création automatique des tags à partir du dictionnaire COLORS
        for name, hex_code in COLORS.items():
            tb.tag_configure(name.lower(), foreground=hex_code)
            # Version gras pour chaque couleur
            tb.tag_configure(f"bold_{name.lower()}", foreground=hex_code, font=(FONTS["CONSOLE"][0], FONTS["CONSOLE"][1], "bold"))
        
        tb.tag_configure("dim", foreground=COLORS["DIM"])
        tb.tag_configure("dimmer", foreground=COLORS.get("DIMMER", "#45475A"))

    def write_step(self, icon: str, label: str, text: str, color: str = "text"):
        """Affiche une étape du processus (ex: 🎤 STT)."""
        self.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        
        self.insert("end", f"  {ts}  ", "dimmer")
        self.insert("end", f"{icon}  ", color.lower())
        self.insert("end", f"{label:<10} ", f"bold_{color.lower()}")
        self.insert("end", f"{text}\n", "text")
        
        self.configure(state="disabled")
        self.see("end")

    def write_result(self, text: str):
        """Affiche la réponse finale de l'IA en grand et en vert."""
        self.configure(state="normal")
        self.insert("end", "\n")
        for line in text.split("\n"):
            self.insert("end", f"  {line}\n", "green")
        self.insert("end", "\n")
        self.configure(state="disabled")
        self.see("end")

    def write_detail(self, text: str):
        """Affiche un détail indenté en gris."""
        self.configure(state="normal")
        self.insert("end", f"{'':>24}{text}\n", "dim")
        self.configure(state="disabled")
        self.see("end")

    def write_separator(self):
        """Affiche une ligne de séparation."""
        self.configure(state="normal")
        self.insert("end", f"  {'─' * 54}\n", "dimmer")
        self.configure(state="disabled")
        self.see("end")

    def write_tts(self, text: str):
        """Affiche le texte TTS (🔊) en mauve."""
        short = text[:80] + ("..." if len(text) > 80 else "")
        self.configure(state="normal")
        self.insert("end", f"{'':>24}🔊  ", "text")
        self.insert("end", f'"{short}"\n\n', "mauve")
        self.configure(state="disabled")
        self.see("end")

    def write_boot(self, items: list):
        """Affiche la séquence de boot (✓ item)."""
        self.configure(state="normal")
        self.insert("end", "\n")
        for item in items:
            self.insert("end", "  ✓ ", "green")
            self.insert("end", f"{item}\n", "dim")
        self.insert("end", "\n")
        self.insert("end", "  ─ Prêt. Appuyez sur Entrée pour parler ─────────────\n", "dimmer")
        self.insert("end", "\n")
        self.configure(state="disabled")
        self.see("end")

class MicButton(ctk.CTkButton):
    """
    Bouton personnalisé pour le micro avec un style prédéfini.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            text="  🎤  Parler  (Entrée)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#164E63", 
            hover_color="#0E7490", 
            text_color=COLORS["CYAN"],
            height=42, 
            width=220, 
            corner_radius=8
        )

    def set_listening(self):
        """Change l'apparence du bouton quand il écoute."""
        self.configure(
            state="disabled", 
            fg_color=COLORS["BORDER"], 
            text_color=COLORS["DIM"],
            text="  🎤  Écoute en cours..."
        )

    def set_ready(self):
        """Réinitialise le bouton après le traitement."""
        self.configure(
            state="normal", 
            fg_color="#164E63", 
            text_color=COLORS["CYAN"],
            text="  🎤  Parler  (Entrée)"
        )