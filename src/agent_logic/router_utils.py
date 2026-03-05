# src/agent_logic/router_utils.py
import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
import httpx
import asyncio
from ddgs import DDGS

logger = logging.getLogger(__name__)

# ─── 1. CONTRATS DE DONNÉES (PYDANTIC) ───

class WeatherResponse(BaseModel):
    type: Literal["weather"] = "weather"
    city: str = Field(description="Nom de la ville recherchée")
    temperature: float = Field(description="Température en degrés Celsius")
    summary: str = Field(description="Conditions actuelles (vent, etc.)")

class NewsResponse(BaseModel):
    type: Literal["news"] = "news"
    topic: str
    headlines: List[str]

class MapsResponse(BaseModel):
    type: Literal["maps"] = "maps"
    origin: str
    destination: str
    duration_mins: int
    distance_km: float

class PlacesResponse(BaseModel):
    type: Literal["places"] = "places"
    query: str
    results: List[str]

class SearchResponse(BaseModel):
    type: Literal["web_search"] = "web_search"
    query: str
    results: List[dict]


# ─── 2. SERVICES ASYNCHRONES (KEYLESS APIs) ───

async def fetch_weather(city: str) -> dict:
    """Récupère la météo via Open-Meteo (Gratuit, sans clé)."""
    logger.info("🌤️ API Open-Meteo : Météo pour %s", city)
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # 1. Géocodage (Trouver la latitude/longitude de la ville)
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=fr"
            geo_resp = await client.get(geo_url)
            geo_data = geo_resp.json()
            
            if not geo_data.get("results"):
                return {"error": f"Ville '{city}' introuvable."}
                
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
            
            # 2. Récupération de la météo
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            w_resp = await client.get(weather_url)
            w_data = w_resp.json().get("current_weather", {})
            
            return WeatherResponse(
                city=city,
                temperature=w_data.get("temperature", 0.0),
                summary=f"Vitesse du vent : {w_data.get('windspeed', 0)} km/h"
            ).model_dump()
            
        except Exception as e:
            logger.error("Erreur Météo : %s", e)
            return {"error": "Service météo temporairement indisponible."}

async def fetch_places(category: str, location: str) -> dict:
    """Recherche des lieux via Nominatim / OpenStreetMap (Gratuit, sans clé)."""
    logger.info("📍 API Nominatim : %s à %s", category, location)
    
    # OpenStreetMap exige un User-Agent valide pour ses API gratuites
    headers = {"User-Agent": "SISE-CLAW-Agent/1.0 (student-project)"}
    query = f"{category} {location}"
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=3"
            resp = await client.get(url)
            data = resp.json()
            
            places = [item.get("display_name", "").split(",")[0] for item in data if "display_name" in item]
            
            return PlacesResponse(
                query=query,
                results=places if places else ["Aucun lieu précis trouvé."]
            ).model_dump()
            
        except Exception as e:
            logger.error("Erreur Lieux : %s", e)
            return {"error": "Recherche de lieux indisponible."}

def _sync_fetch_news(topic: str) -> dict:
    """Fonction synchrone interne (Worker) pour scrapper les actualités."""
    try:
        # On utilise le DDGS standard (robuste)
        with DDGS() as ddgs:
            # On force l'évaluation du générateur en liste
            results = list(ddgs.news(topic, region="fr-fr", safesearch="moderate", max_results=3))
            headlines = [f"{r.get('title')} ({r.get('source')})" for r in results]
            
            return NewsResponse(
                topic=topic,
                headlines=headlines if headlines else ["Aucune actualité récente trouvée."]
            ).model_dump()
    except Exception as e:
        logger.error("Erreur interne News : %s", e)
        return {"error": "Recherche d'actualités indisponible."}

async def fetch_news(topic: str) -> dict:
    """Interface asynchrone publique exposée à l'Agent Pydantic."""
    logger.info("📰 API DDGS (Thread) : Actualités sur %s", topic)
    # Décharge l'exécution réseau dans un thread séparé pour ne pas bloquer le GUI
    return await asyncio.to_thread(_sync_fetch_news, topic)

def _sync_web_search(query: str) -> dict:
    """Fonction synchrone interne (Worker) pour la recherche Web."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region="fr-fr", safesearch="moderate", max_results=2))
            
            formatted_results = [
                {"title": r.get("title"), "snippet": r.get("body"), "url": r.get("href")} 
                for r in results
            ]
            
            return SearchResponse(
                query=query,
                results=formatted_results
            ).model_dump()
    except Exception as e:
        logger.error("Erreur interne Web Search : %s", e)
        return {"error": "Moteur de recherche indisponible."}

async def web_search(query: str) -> dict:
    """Interface asynchrone publique exposée à l'Agent Pydantic."""
    logger.info("🌐 API DDGS (Thread) : Recherche Web pour '%s'", query)
    return await asyncio.to_thread(_sync_web_search, query)

async def _geocode(address: str, client: httpx.AsyncClient) -> Optional[tuple[float, float]]:
    """
    Fonction utilitaire privée (Worker) : Convertit une adresse en coordonnées (Lat, Lon).
    Utilise Nominatim (OpenStreetMap).
    """
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
    try:
        resp = await client.get(url)
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logger.error("Erreur géocodage pour '%s' : %s", address, e)
    return None

async def fetch_route(origin: str, destination: str, mode: Literal["driving", "cycling", "walking"] = "cycling") -> dict:
    """
    Calcule l'itinéraire exact entre deux points via OSRM.
    - mode: 'driving' (voiture), 'cycling' (vélo), 'walking' (à pied).
    """
    logger.info("🗺️ API OSRM : Itinéraire %s de '%s' à '%s'", mode, origin, destination)
    
    # Mapping des modes de transport pour l'API OSRM
    osrm_profiles = {
        "driving": "car",
        "cycling": "bike",
        "walking": "foot"
    }
    profile = osrm_profiles.get(mode, "bike")

    # Header obligatoire pour Nominatim (Respect des Conditions d'Utilisation)
    headers = {"User-Agent": "SISE-CLAW-Agent/1.0 (student-project)"}
    
    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        try:
            # 1. Étape de Géocodage (Parallélisation avec asyncio.gather pour aller 2x plus vite)
            coords = await asyncio.gather(
                _geocode(origin, client),
                _geocode(destination, client)
            )
            
            origin_coords, dest_coords = coords[0], coords[1]
            
            if not origin_coords or not dest_coords:
                return {"error": "Impossible de localiser avec précision le départ ou l'arrivée."}
            
            # 2. Étape de Routage (Appel OSRM)
            # Attention: OSRM prend les coordonnées au format Longitude,Latitude (et non Lat,Lon)
            osrm_url = (
                f"http://router.project-osrm.org/route/v1/{profile}/"
                f"{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}?overview=false"
            )
            
            route_resp = await client.get(osrm_url)
            route_data = route_resp.json()
            
            if route_data.get("code") != "Ok":
                return {"error": "Aucun itinéraire routier trouvé entre ces deux points."}
                
            # Extraction des données (OSRM renvoie la distance en mètres et la durée en secondes)
            route_info = route_data["routes"][0]
            distance_km = round(route_info["distance"] / 1000, 1)
            duration_mins = round(route_info["duration"] / 60)
            
            return MapsResponse(
                origin=origin,
                destination=destination,
                duration_mins=duration_mins,
                distance_km=distance_km
            ).model_dump()
            
        except Exception as e:
            logger.error("Erreur OSRM Routage : %s", e)
            return {"error": "Service de calcul d'itinéraire indisponible."}