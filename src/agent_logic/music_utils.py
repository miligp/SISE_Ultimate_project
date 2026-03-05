import logging
from typing import Optional, Dict, Any

import vlc
import yt_dlp

logger = logging.getLogger(__name__)

class MusicPlayer:
    def __init__(self) -> None:
        self._instance: vlc.Instance = vlc.Instance('--no-video', '--quiet')
        self._player: Optional[vlc.MediaPlayer] = None

    def search(self, query: str) -> str:
        """Recherche 3 options sans les jouer."""
        ydl_opts: Dict[str, Any] = {
            'extract_flat': True,
            'quiet': True,
            'noplaylist': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch3:{query}", download=False)
                
                if not info or 'entries' not in info or not info['entries']:
                    return "Aucun résultat trouvé sur YouTube."
                    
                results = []
                for i, entry in enumerate(info['entries']):
                    title = entry.get('title', 'Titre inconnu')
                    url = entry.get('url')
                    results.append(f"{i+1}. {title} (URL: {url})")
                    
                return "Résultats trouvés :\n" + "\n".join(results) + "\n\nDemande à l'utilisateur quel numéro il souhaite écouter, puis lance l'outil de lecture avec l'URL correspondante."
        except Exception as e:
            return f"Erreur de recherche : {str(e)}"

    def play(self, url_or_query: str) -> str:
        self.stop()
        
        ydl_opts: Dict[str, Any] = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Si on a une URL, on la lit. Sinon on fait une recherche automatique
                search_str = url_or_query if url_or_query.startswith('http') else f"ytsearch1:{url_or_query}"
                info = ydl.extract_info(search_str, download=False)
                
                if not info:
                    return "Flux audio introuvable."
                    
                # yt-dlp renvoie une structure différente selon si c'est une URL ou une recherche
                entry = info['entries'][0] if 'entries' in info else info
                stream_url: str = entry.get('url')
                title: str = entry.get('title', 'Titre inconnu')

                if not stream_url:
                    return "Impossible d'extraire le flux (vidéo peut-être protégée)."

                self._player = self._instance.media_player_new()
                media = self._instance.media_new(stream_url)
                self._player.set_media(media)
                self._player.play()
                
                return f"Lecture lancée avec succès : {title}"
                
        except Exception as e:
            return f"Erreur technique : {str(e)}"

    def pause(self) -> str:
        if self._player:
            self._player.set_pause(1) # 1 = Force la pause quoiqu'il arrive
            return "La musique est en pause."
        return "Aucune lecture active."

    def resume(self) -> str:
        if self._player:
            self._player.set_pause(0) # 0 = Force la lecture (Play)
            return "La lecture reprend."
        return "Aucune musique en pause."

    def stop(self) -> str:
        if self._player:
            self._player.stop()
            self._player = None
            return "Musique arrêtée."
        return "Aucune lecture en cours."

global_player = MusicPlayer()