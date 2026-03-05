<div align="center">

# 🎙️ SISE-CLAW

### *Listen. Think. Speak.*

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white)
![PydanticAI](https://img.shields.io/badge/PydanticAI-Agent-E92063?style=flat-square)
![Mistral](https://img.shields.io/badge/LLM-Mistral_Large-FF7000?style=flat-square)
![TTS](https://img.shields.io/badge/TTS-Edge_TTS-0078D4?style=flat-square&logo=microsoft&logoColor=white)
![STT](https://img.shields.io/badge/STT-Deepgram_·_Groq_·_Whisper-00B388?style=flat-square)
![UI](https://img.shields.io/badge/UI-CustomTkinter-1F6AA5?style=flat-square)
![License](https://img.shields.io/badge/License-Académique-gray?style=flat-square)

**Assistant personnel intelligent contrôlé à la voix**

*Projet de Master 2 SISE — Data Science*
*Université Lumière Lyon 2 · 2025–2026*

[Contexte](#contexte-et-problématique) • [Approche](#solution-proposée) • [Architecture](#-architecture) • [Technologies](#-technologies) • [Installation](#-installation) • [Mode d'emploi](#-mode-demploi)

</div>

---

## Approche

### Contexte et problématique

Les interfaces numériques actuelles — formulaires, menus, clavier, souris — constituent une **barrière d'accès** pour deux populations en forte croissance :

- **Les personnes âgées** : difficultés motrices (arthrose, tremblements), baisse de la vue, anxiété face aux interfaces complexes. Beaucoup abandonnent l'usage du numérique faute d'accompagnement adapté.
- **Les personnes malvoyantes ou non-voyantes** : les lecteurs d'écran existants (NVDA, VoiceOver) restent techniques et peu intuitifs pour des tâches courantes comme rédiger un email ou chercher une information.


### Solution proposée

SISE-CLAW est un **assistant vocal personnel de bureau** conçu pour être utilisé entièrement à la voix, sans clavier. L'objectif est de centraliser dans une seule interface les tâches quotidiennes : email, bureautique, recherche web, musique, météo.

Concrètement, une personne âgée ou malvoyante peut :

| Besoin | Commande vocale |
|--------|----------------|
| Lire ses emails | *"Quels sont mes derniers emails ?"* |
| Écrire un message | *"Envoie un email à ma fille pour lui souhaiter bon anniversaire"* |
| Écouter de la musique | *"Lance la macarena"* |
| Savoir la météo | *"Quel temps fait-il à Lyon aujourd'hui ?"* |
| Retrouver un itinéraire | *"Quelle est la distance entre Lyon à Annecy ?"* |
| Créer un document | *"Écris une liste de courses dans un fichier Word"* |

L'agent répond toujours **vocalement et en français**, de façon concise. Il est configuré pour **décrire systématiquement ses actions** (ex : *"J'ai bien trouvé 3 emails de votre médecin, voici le dernier..."*) pour que l'utilisateur suive sans regarder l'écran.

### Idée centrale

L'utilisateur parle → l'agent LLM comprend l'intention → il appelle les bons outils → il répond oralement.

### Valeur ajoutée par rapport à l'existant

Ce projet s'inspire des architectures d'agents LLM open-source (LangChain, AutoGPT) mais s'en distingue sur plusieurs points :

| Aspect | Approche classique | SISE-CLAW |
|--------|--------------------|-----------|
| Interface | Web ou terminal | Desktop natif (CustomTkinter) |
| STT | Modèle unique | Cascade failover (Deepgram → Groq → Whisper local) |
| TTS | Brut (texte → voix) | Normalisation orale via LLM avant synthèse |
| Outils | Génériques | Spécialisés (email IMAP, Excel xlwings, VLC, GPS) |
                                  
---

## Architecture

```
src/
├── app_gui.py                     # Point d'entrée — GUI CustomTkinter
│
├── dashboard_ui/
│   ├── ui.py                      # Thème couleurs (Catppuccin)
│   └── components.py              # ConsoleWidget, MicButton
│
├── voice_processing/
│   ├── audio_capture.py           # Enregistrement micro + VAD (détection silence)
│   ├── audio_playback.py          # Lecture fichier audio (sounddevice)
│   ├── stt/
│   │   ├── deepgram_provider.py   # API Deepgram (primaire, rapide)
│   │   ├── groq_provider.py       # API Groq/Whisper (secondaire)
│   │   ├── whisper_provider.py    # Whisper local small (fallback hors-ligne)
│   │   └── transcription_manager.py  # Orchestration cascade STT
│   └── tts/
│       ├── edge_tts_provider.py   # Synthèse Microsoft Edge TTS
│       ├── synthesis_manager.py   # Gestionnaire TTS
│       └── text_processor.py      # Normalisation orale (Mistral Small)
│
└── agent_logic/
    ├── pydantic_ai_agent.py       # Agent PydanticAI + 13 outils déclarés
    ├── email_utils.py             # Lecture/envoi email IMAP/SMTP
    ├── doc_utils.py               # Word (.docx) et Excel (.xlsx)
    ├── music_utils.py             # Lecteur YouTube + VLC
    └── router_utils.py            # Météo, actualités, lieux, GPS, DuckDuckGo
```

---

## Technologies

### Langages et runtime

| Outil | Version | Rôle |
|-------|---------|------|
| Python | 3.13+ | Langage principal |
| uv | latest | Gestionnaire de paquets et environnements |

### Intelligence artificielle

| Bibliothèque / Service | Version | Rôle |
|-----------------------|---------|------|
| [pydantic-ai](https://ai.pydantic.dev/) | ≥ 0.0.14 | Framework agent LLM |
| [Mistral Large](https://mistral.ai/) | API cloud | LLM principal (raisonnement + outils) |
| Mistral Small | API cloud | Normalisation du texte pour la synthèse vocale |
| [openai-whisper](https://github.com/openai/whisper) | ≥ 20250625 | STT local (fallback hors-ligne) |
| [Deepgram](https://deepgram.com/) | API REST | STT principal (temps réel, rapide) |
| [Groq](https://groq.com/) | API REST | STT secondaire (Whisper hébergé) |
| [edge-tts](https://github.com/rany2/edge-tts) | ≥ 7.2.7 | Synthèse vocale (Microsoft Neural TTS) |

### Interface et audio

| Bibliothèque | Version | Rôle |
|-------------|---------|------|
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | ≥ 5.2.2 | Interface graphique desktop |
| sounddevice | ≥ 0.5.5 | Capture et lecture audio |
| soundfile | ≥ 0.13.1 | Lecture de fichiers audio |
| numpy | ≥ 2.4.2 | Calcul RMS pour le VAD |
| [python-vlc](https://pypi.org/project/python-vlc/) | ≥ 3.0.21203 | Lecture streaming YouTube via VLC |

### Outils métier

| Bibliothèque | Version | Rôle |
|-------------|---------|------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | ≥ 2026.3.3 | Extraction flux audio YouTube |
| [python-docx](https://python-docx.readthedocs.io/) | ≥ 1.2.0 | Création/édition Word (.docx) |
| [openpyxl](https://openpyxl.readthedocs.io/) | ≥ 3.1.5 | Lecture/écriture Excel (.xlsx) |
| [xlwings](https://www.xlwings.org/) | ≥ 0.33.20 | Actualisation des formules Excel |
| [httpx](https://www.python-httpx.org/) | ≥ 0.28.1 | Requêtes HTTP asynchrones |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ≥ 1.1.0 | Chargement des variables `.env` |
| [duckduckgo-search](https://pypi.org/project/duckduckgo-search/) | ≥ 8.1.1 | Recherche web |
| psutil | ≥ 7.2.2 | Informations système |

### Services externes (APIs)

| Service | Usage | Clé requise |
|---------|-------|-------------|
| [Mistral AI](https://console.mistral.ai/) | LLM Large + Small | `MISTRAL_API_KEY` |
| [Deepgram](https://console.deepgram.com/) | STT principal | `DEEPGRAM_API_KEY` |
| [Groq](https://console.groq.com/) | STT secondaire | `GROQ_API_KEY` |
| Microsoft Edge TTS | Synthèse vocale | Aucune (gratuit) |
| DuckDuckGo | Recherche web | Aucune |
| YouTube (via yt-dlp) | Streaming musical | Aucune |
| Gmail IMAP/SMTP | Email | `EMAIL_USER` + `EMAIL_PASSWORD` |

---

## Installation

### 1. Prérequis système

- **Python 3.13+** — [télécharger](https://www.python.org/downloads/)
- **uv** — gestionnaire de paquets :
  ```bash
  pip install uv
  # ou (Windows PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **VLC Media Player** (uniquement pour la musique) — [télécharger](https://www.videolan.org/vlc/) en version **64-bit**

### 2. Cloner et installer

```bash
git clone <url-du-repo>
cd SISE_Ultimate_project

# Créer l'environnement et installer toutes les dépendances
uv sync
```

### 3. Configurer les clés API

Créer un fichier `.env` à la racine du projet :

```env
# ── LLM (obligatoire) ──────────────────────────────────
MISTRAL_API_KEY=votre_clé_mistral

# ── STT (au moins Deepgram ou Groq recommandé) ─────────
DEEPGRAM_API_KEY=votre_clé_deepgram
GROQ_API_KEY=votre_clé_groq

# ── Email Gmail ────────────────────────────────────────
EMAIL_USER=votre_adresse@gmail.com
EMAIL_PASSWORD=xxxx_xxxx_xxxx_xxxx   # mot de passe d'application (pas le mdp du compte)
EMAIL_IMAP_SERVER=imap.gmail.com
```

> **Obtenir les clés :**
> - Mistral : [console.mistral.ai](https://console.mistral.ai/) → API Keys
> - Deepgram : [console.deepgram.com](https://console.deepgram.com/) → Create API Key
> - Groq : [console.groq.com](https://console.groq.com/) → API Keys
> - Gmail : Compte Google → Sécurité → Validation en 2 étapes → **Mots de passe des applications**

---

## Mode d'emploi

### Lancement

```bash
uv run python src/app_gui.py
```

### Utilisation

| Étape | Action |
|-------|--------|
| 1 | L'application s'ouvre, attendre le message "Prêt" |
| 2 | Appuyer sur **Entrée** ou cliquer sur **🎤 Parler** |
| 3 | Parler clairement — l'enregistrement s'arrête automatiquement au silence |
| 4 | L'agent traite la demande, la réponse s'affiche et se lit vocalement |
| 5 | Appuyer sur **Entrée** pendant la lecture pour l'interrompre |
| 6 | Répéter depuis l'étape 2 pour poser une nouvelle question |

### Exemples de commandes

```
"Quels sont mes 3 derniers emails ?"
"Envoie un email à Marie pour confirmer le rendez-vous de demain"
"Crée un fichier Word pour mon rapport de stage"
"Lance du jazz sur YouTube"
"Quel temps fait-il à Lyon ?"
"Combien de temps pour aller à Paris en voiture depuis Lyon ?"
"Quelles sont les dernières nouvelles en intelligence artificielle ?"
"Trouve-moi un restaurant italien à Lyon"
```

### Tester l'agent sans l'interface graphique

```bash
uv run python -m src.agent_logic.test_agent
```

---

<div align="center">

*Master 2 SISE — Université Lumière Lyon 2 · 2025–2026*

</div>
