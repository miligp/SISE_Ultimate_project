# src/agent_logic/music_utils.py
import subprocess
import logging
from typing import Optional
import yt_dlp
import psutil

logger = logging.getLogger(__name__)

class MusicPlayer:
    """
    Gestionnaire de lecture audio en streaming.
    Maintient l'état du lecteur en mémoire pour pouvoir l'arrêter dynamiquement.
    """
    def __init__(self) -> None:
        # Stocke la référence du processus système (ffplay) en cours d'exécution
        self._current_process: Optional[subprocess.Popen] = None

    def play(self, search_query: str) -> str:
        """
        Délègue la recherche et la lecture audio directement au lecteur mpv.
        """
        # 1. Sécurité : on arrête la musique précédente s'il y en a une
        self.stop()
        
        try:
            logger.info("Délégation de la lecture à mpv pour : '%s'", search_query)
            
            # mpv comprend nativement le protocole ytdl:// et les commandes ytsearch!
            # On lui demande de chercher et de lire le premier résultat (ytsearch1)
            search_command = f"ytdl://ytsearch1:{search_query}"
            
            # 2. Lancement du processus système
            self._current_process = subprocess.Popen(
                ['mpv', '--no-video', '--ytdl-format=bestaudio/best', search_command],
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # Note: Comme la recherche est asynchrone pour l'OS, on ne connaît pas le titre exact ici,
            # mais l'agent peut confirmer que la requête est lancée.
            return f"J'ai lancé la recherche et la lecture pour : {search_query}"
                
        except Exception as e:
            logger.error("Erreur technique de lancement : %s", e)
            return f"Impossible de lancer la musique : {str(e)}"
    
    def pause(self) -> str:
        """
        Gèle le processus système (Cross-Platform). La musique s'arrête instantanément.
        """
        if self._current_process and self._current_process.poll() is None:
            try:
                # On "enveloppe" notre processus système dans l'objet psutil
                process = psutil.Process(self._current_process.pid)
                process.suspend() # Fait un SIGSTOP sous Linux, et un SuspendThread sous Windows !
                logger.info("Musique mise en pause.")
                return "La musique est en pause."
            except psutil.NoSuchProcess:
                return "Erreur : Le processus de lecture a disparu."
                
        return "Il n'y a aucune musique en cours de lecture à mettre en pause."

    def resume(self) -> str:
        """
        Dégèle le processus système. La musique reprend exactement où elle en était.
        """
        if self._current_process and self._current_process.poll() is None:
            try:
                process = psutil.Process(self._current_process.pid)
                process.resume() # Fait un SIGCONT sous Linux, et un ResumeThread sous Windows
                logger.info("Reprise de la musique.")
                return "Je reprends la lecture de la musique."
            except psutil.NoSuchProcess:
                return "Erreur : Le processus de lecture a disparu."
                
        return "Il n'y a aucune musique en pause à reprendre."

        try:
            logger.info("Recherche YouTube en cours pour : '%s'", search_query)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # ytsearch1: ne renvoie que le tout premier résultat pour aller très vite
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                
                if 'entries' in info and len(info['entries']) > 0:
                    entry = info['entries'][0]
                    stream_url: str = entry['url']
                    title: str = entry.get('title', 'Audio inconnu')
                    
                    logger.info("Lecture du flux audio : %s", title)
                    
                    # 3. Lancement du processus système 'ffplay' en mode non-bloquant
                    # -nodisp : pas d'interface vidéo
                    # -autoexit : ferme le processus à la fin de la chanson
                    self._current_process = subprocess.Popen(
                        ['mpv', '--no-video', '--audio-display=no', stream_url],
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL
                    )
                    return f"Lecture en cours : {title}"
                    
                return "Aucun résultat trouvé sur YouTube pour cette recherche."
                
        except Exception as e:
            logger.error("Erreur yt-dlp : %s", e)
            return f"Impossible de lancer la musique en raison d'une erreur technique : {str(e)}"

    def stop(self) -> str:
        """
        Interrompt violemment le processus de lecture s'il existe.
        """
        if self._current_process and self._current_process.poll() is None:
            self._current_process.terminate()
            self._current_process = None
            logger.info("Musique interrompue par le système.")
            return "La musique a été arrêtée avec succès."
        
        return "Il n'y a aucune musique en cours de lecture."

# Instanciation globale (Singleton) pour que l'Agent utilise toujours le même lecteur
global_player = MusicPlayer()