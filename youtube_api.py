import os
import pytube
from youtube-search-python import VideosSearch
import requests
import tempfile
import logging
import shutil
from urllib.parse import urlparse, parse_qs

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_video_id(url):
    """
    Extrait l'ID vidéo d'une URL YouTube
    """
    if 'youtube.com' in url:
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query).get('v', [None])[0]
    elif 'youtu.be' in url:
        return urlparse(url).path.lstrip('/')
    return None

def search_youtube(query, limit=5):
    """
    Recherche des vidéos sur YouTube et retourne les résultats.
    """
    logger.info(f"Recherche YouTube pour: {query}")
    try:
        videos_search = VideosSearch(query, limit=limit)
        results = videos_search.result()
        
        # Formater les résultats pour une utilisation facile
        formatted_results = []
        for item in results['result']:
            # Sélectionner la meilleure miniature disponible
            thumbnail_url = None
            if 'thumbnails' in item and len(item['thumbnails']) > 0:
                # Prendre la miniature de meilleure qualité disponible
                for thumb in item['thumbnails']:
                    thumbnail_url = thumb.get('url')
                    if thumb.get('width', 0) >= 320:  # Préférer une taille moyenne
                        break
            
            formatted_results.append({
                'id': item['id'],
                'title': item['title'],
                'thumbnail': thumbnail_url,
                'duration': item.get('duration', ''),
                'channel': item.get('channel', {}).get('name', ''),
                'url': f"https://www.youtube.com/watch?v={item['id']}"
            })
        
        logger.info(f"Recherche terminée, {len(formatted_results)} résultats trouvés")
        return formatted_results
    except Exception as e:
        logger.error(f"Erreur lors de la recherche YouTube: {e}")
        raise

def download_youtube_video(video_id, max_size_mb=25):
    """
    Télécharge une vidéo YouTube et retourne le chemin du fichier.
    Limite la taille à max_size_mb pour respecter les limites de Messenger.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"{video_id}.mp4")
    
    logger.info(f"Téléchargement de la vidéo: {video_id}")
    try:
        # Télécharger la vidéo
        yt = pytube.YouTube(video_url)
        
        # Obtenir les flux disponibles
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        
        # Trier par résolution (de la plus basse à la plus haute)
        streams = sorted(streams, key=lambda x: int(x.resolution[:-1]) if x.resolution else 0)
        
        # Trouver le flux qui respecte la limite de taille
        selected_stream = None
        for stream in streams:
            # Estimer la taille en Mo
            size_mb = stream.filesize / (1024 * 1024)
            logger.info(f"Flux disponible: {stream.resolution}, {size_mb:.2f} Mo")
            
            if size_mb <= max_size_mb:
                selected_stream = stream
            else:
                # Si on dépasse la limite, on prend le dernier flux valide
                break
        
        if not selected_stream and streams:
            # Si aucun flux ne respecte la limite, prendre le plus petit
            selected_stream = streams[0]
            logger.warning(f"Aucun flux ne respecte la limite de {max_size_mb}Mo, utilisation du plus petit: {selected_stream.resolution}")
        
        if not selected_stream:
            logger.error("Aucun flux vidéo trouvé")
            raise Exception("Aucun flux vidéo disponible")
        
        # Télécharger la vidéo
        logger.info(f"Téléchargement du flux {selected_stream.resolution}, taille estimée: {selected_stream.filesize / (1024 * 1024):.2f} Mo")
        selected_stream.download(output_path=temp_dir, filename=f"{video_id}.mp4")
        
        # Vérifier la taille du fichier
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Téléchargement terminé: {output_path}, taille: {file_size_mb:.2f} Mo")
        
        if file_size_mb > max_size_mb:
            logger.warning(f"Le fichier téléchargé ({file_size_mb:.2f} Mo) dépasse la limite de {max_size_mb} Mo")
        
        return output_path, file_size_mb
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement de la vidéo: {e}")
        raise

