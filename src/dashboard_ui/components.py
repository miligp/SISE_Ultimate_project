import re
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
        # Tags Markdown
        tb.tag_configure("md_h1",   foreground=COLORS["GREEN"], font=(FONTS["CONSOLE"][0], 15, "bold"))
        tb.tag_configure("md_h2",   foreground=COLORS["GREEN"], font=(FONTS["CONSOLE"][0], 13, "bold"))
        tb.tag_configure("md_h3",   foreground=COLORS["GREEN"], font=(FONTS["CONSOLE"][0], 13, "bold"))
        tb.tag_configure("md_bold", foreground=COLORS["GREEN"], font=(FONTS["CONSOLE"][0], FONTS["CONSOLE"][1], "bold"))
        tb.tag_configure("md_code", foreground=COLORS["YELLOW"])
        tb.tag_configure("md_bullet", foreground=COLORS["BLUE"])

    def write_step(self, icon: str, label: str, text: str, color: str = "text"):
        """Affiche une étape du processus (ex: 🎤 STT)."""
        self.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        
        self.insert("end", f"  {ts}  ", "dimmer")
        self.insert("end", f"{icon}  ", color.lower())
        self.insert("end", f"{label:<10} ", f"bold_{color.lower()}")
        self.insert("end", f"{text}\n", color.lower())
        
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

    def _insert_inline(self, tb, text: str, base_tag: str = None):
        """
        Insère du texte dans le Textbox en gérant le Markdown (gras) et les tags de base.
        Version robuste contre les crashs Tcl/Tkinter (wrong # args).
        """
        import re
        m = re.search(r'\*\*(.*?)\*\*', text)
        
        if m:
            # 1. On insère le texte AVANT le gras (s'il n'est pas vide)
            before_text = text[:m.start()]
            if before_text:
                if base_tag:
                    tb.insert("end", before_text, base_tag)
                else:
                    tb.insert("end", before_text)
            
            # 2. On insère le texte EN GRAS (s'il n'est pas vide)
            bold_text = m.group(2)
            if bold_text:
                # L'astuce Lead : On combine les tags dans un Tuple pour Tcl
                tags = ("md_bold", base_tag) if base_tag else ("md_bold",)
                tb.insert("end", bold_text, tags)
            
            # 3. On traite le RESTE du texte (Récursivité)
            after_text = text[m.end():]
            if after_text:
                self._insert_inline(tb, after_text, base_tag)
                
        else:
            # Aucun Markdown détecté, on insère le texte brut
            if text:
                if base_tag:
                    tb.insert("end", text, base_tag)
                else:
                    tb.insert("end", text)

    def write_markdown(self, text: str):
        """Affiche une réponse avec rendu Markdown (titres, gras, code, listes)."""
        self.configure(state="normal")
        tb = self._textbox
        tb.insert("end", "\n")
        for line in text.split("\n"):
            if line.startswith("### "):
                self._insert_inline(tb, f"  {line[4:]}\n", "md_h3")
            elif line.startswith("## "):
                self._insert_inline(tb, f"  {line[3:]}\n", "md_h2")
            elif line.startswith("# "):
                self._insert_inline(tb, f"  {line[2:]}\n", "md_h1")
            elif line.strip() == "---":
                tb.insert("end", f"  {'─' * 40}\n", "dimmer")
            elif re.match(r'^[\-\*] ', line):
                tb.insert("end", "  • ", "md_bullet")
                self._insert_inline(tb, f"{line[2:]}\n", "green")
            elif re.match(r'^\d+\. ', line):
                m = re.match(r'^(\d+\. )(.*)', line)
                tb.insert("end", f"  {m.group(1)}", "md_bullet")
                self._insert_inline(tb, f"{m.group(2)}\n", "green")
            elif not line.strip():
                tb.insert("end", "\n")
            else:
                self._insert_inline(tb, f"  {line}\n", "green")
        tb.insert("end", "\n")
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

    def write_streaming_start(self):
        """Commence un bloc de texte streamé. Pose un mark pour remplacement final."""
        self.configure(state="normal")
        self._textbox.insert("end", "\n", "")
        # Mark posé APRÈS le \n : on supprimera depuis ici à la fin
        self._textbox.mark_set("stream_start", "end-1c")
        self.configure(state="disabled")
        self.see("end")

    def write_streaming_chunk(self, chunk: str):
        """Ajoute un fragment de texte brut au bloc de streaming en cours."""
        self.configure(state="normal")
        self._textbox.insert("end", chunk, "green")
        self.configure(state="disabled")
        self.see("end")

    def write_streaming_end_markdown(self, full_text: str):
        """Remplace le texte brut streamé par le rendu Markdown final."""
        self.configure(state="normal")
        tb = self._textbox
        try:
            tb.delete("stream_start", "end")
        except Exception:
            pass
        for line in full_text.split("\n"):
            if line.startswith("### "):
                self._insert_inline(tb, f"  {line[4:]}\n", "md_h3")
            elif line.startswith("## "):
                self._insert_inline(tb, f"  {line[3:]}\n", "md_h2")
            elif line.startswith("# "):
                self._insert_inline(tb, f"  {line[2:]}\n", "md_h1")
            elif line.strip() == "---":
                tb.insert("end", f"  {'─' * 40}\n", "dimmer")
            elif re.match(r'^[\-\*] ', line):
                tb.insert("end", "  • ", "md_bullet")
                self._insert_inline(tb, f"{line[2:]}\n", "green")
            elif re.match(r'^\d+\. ', line):
                m = re.match(r'^(\d+\. )(.*)', line)
                tb.insert("end", f"  {m.group(1)}", "md_bullet")
                self._insert_inline(tb, f"{m.group(2)}\n", "green")
            elif not line.strip():
                tb.insert("end", "\n")
            else:
                self._insert_inline(tb, f"  {line}\n", "green")
        tb.insert("end", "\n")
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
            self.insert("end", f"{item}\n", "blanc")
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