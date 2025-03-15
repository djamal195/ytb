import requests
import json
import logging
import re
import os
from config import MESSENGER_PAGE_ACCESS_TOKEN
from mistral_api import generate_mistral_response
from youtube_api import search_youtube, download_youtube_video
from user_states import (
    set_user_state, get_user_state, clear_user_state,
    NORMAL, WAITING_FOR_YOUTUBE_QUERY
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Commandes
YT_COMMAND = "/yt"
CANCEL_COMMAND = "/cancel"

async def handle_message(sender_id, received_message):
    """Gère les messages reçus du Messenger"""
    logger.info(f"Début de handle_message pour sender_id: {sender_id}")
    logger.info(f"Message reçu: {json.dumps(received_message)}")
    
    try:
        # Récupérer l'état actuel de l'utilisateur
        current_state, state_data = get_user_state(sender_id)
        
        # Vérifier si c'est un message texte
        if "text" in received_message:
            message_text = received_message["text"].strip()
            
            # Commande d'annulation
            if message_text.lower() == CANCEL_COMMAND:
                clear_user_state(sender_id)
                await send_text_message(sender_id, "Commande annulée. Comment puis-je vous aider ?")
                return
            
            # Commande YouTube
            if message_text.lower() == YT_COMMAND:
                set_user_state(sender_id, WAITING_FOR_YOUTUBE_QUERY)
                await send_text_message(sender_id, "Bienvenue dans JekleTube ! Donnez-moi les mots clés pour rechercher une vidéo.")
                return
            
            # Traitement selon l'état
            if current_state == WAITING_FOR_YOUTUBE_QUERY:
                await handle_youtube_search_query(sender_id, message_text)
                return
            
            # Message normal, utiliser Mistral AI
            logger.info("Génération de la réponse Mistral...")
            response = generate_mistral_response(message_text)
            logger.info(f"Réponse Mistral générée: {response}")
            await send_text_message(sender_id, response)
            logger.info("Message envoyé avec succès")
        
        # Vérifier si c'est un postback (clic sur un bouton)
        elif "postback" in received_message:
            await handle_postback(sender_id, received_message["postback"])
        
        else:
            logger.info("Message reçu sans texte ni postback")
            await send_text_message(sender_id, "Désolé, je ne peux traiter que des messages texte.")
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {e}")
        error_message = "Désolé, j'ai rencontré une erreur en traitant votre message. Veuillez réessayer plus tard."
        if "timeout" in str(e).lower():
            error_message = "Désolé, la génération de la réponse a pris trop de temps. Veuillez réessayer avec une question plus courte ou plus simple."
        await send_text_message(sender_id, error_message)
    
    logger.info("Fin de handle_message")

async def handle_youtube_search_query(sender_id, query):
    """Gère une recherche YouTube"""
    try:
        await send_text_message(sender_id, f"Recherche de vidéos pour: {query}...")
        
        # Rechercher les vidéos
        results = search_youtube(query, limit=5)
        
        if not results:
            await send_text_message(sender_id, "Aucun résultat trouvé pour cette recherche.")
            clear_user_state(sender_id)
            return
        
        # Envoyer les résultats avec des boutons
        await send_youtube_results(sender_id, results)
        
        # Réinitialiser l'état
        clear_user_state(sender_id)
    
    except Exception as e:
        logger.error(f"Erreur lors de la recherche YouTube: {e}")
        await send_text_message(sender_id, "Désolé, une erreur s'est produite lors de la recherche YouTube.")
        clear_user_state(sender_id)

async def handle_postback(sender_id, postback):
    """Gère les postbacks (clics sur boutons)"""
    logger.info(f"Postback reçu: {json.dumps(postback)}")
    
    try:
        payload = postback.get("payload", "")
        
        # Vérifier si c'est un postback pour regarder une vidéo
        if payload.startswith("WATCH_VIDEO:"):
            video_id = payload.split("WATCH_VIDEO:")[1]
            await handle_watch_video(sender_id, video_id)
    
    except Exception as e:
        logger.error(f"Erreur lors du traitement du postback: {e}")
        await send_text_message(sender_id, "Désolé, une erreur s'est produite lors du traitement de votre action.")

async def handle_watch_video(sender_id, video_id):
    """Gère la demande de visionnage d'une vidéo"""
    try:
        await send_text_message(sender_id, "Téléchargement de la vidéo en cours... Cela peut prendre quelques instants.")
        
        # Télécharger la vidéo
        video_path, file_size_mb = download_youtube_video(video_id)
        
        if file_size_mb > 25:
            await send_text_message(
                sender_id, 
                f"Désolé, la vidéo est trop volumineuse ({file_size_mb:.1f} Mo) pour être envoyée via Messenger (limite de 25 Mo). "
                f"Voici le lien YouTube: https://www.youtube.com/watch?v={video_id}"
            )
            return
        
        # Envoyer la vidéo
        await send_video_attachment(sender_id, video_path)
        
        # Supprimer le fichier temporaire
        try:
            os.remove(video_path)
            logger.info(f"Fichier temporaire supprimé: {video_path}")
        except Exception as e:
            logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
    
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement/envoi de la vidéo: {e}")
        await send_text_message(
            sender_id, 
            "Désolé, une erreur s'est produite lors du téléchargement de la vidéo. "
            f"Voici le lien YouTube: https://www.youtube.com/watch?v={video_id}"
        )

async def send_youtube_results(sender_id, results):
    """Envoie les résultats de recherche YouTube avec des boutons"""
    try:
        elements = []
        
        for video in results:
            element = {
                "title": video["title"][:80],  # Limiter la longueur du titre
                "subtitle": f"Chaîne: {video['channel']} | Durée: {video['duration']}",
                "image_url": video["thumbnail"] or "https://via.placeholder.com/320x180?text=Pas+de+miniature",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "Regarder",
                        "payload": f"WATCH_VIDEO:{video['id']}"
                    },
                    {
                        "type": "web_url",
                        "title": "Voir sur YouTube",
                        "url": video["url"]
                    }
                ]
            }
            elements.append(element)
        
        message_data = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": elements
                    }
                }
            }
        }
        
        await call_send_api(message_data)
        logger.info("Résultats YouTube envoyés avec succès")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des résultats YouTube: {e}")
        await send_text_message(sender_id, "Désolé, une erreur s'est produite lors de l'affichage des résultats.")

async def send_video_attachment(sender_id, video_path):
    """Envoie une vidéo en pièce jointe"""
    try:
        # Vérifier si le fichier existe
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Le fichier vidéo n'existe pas: {video_path}")
        
        # Vérifier la taille du fichier
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(f"Le fichier est trop volumineux: {file_size_mb:.2f} Mo (limite: 25 Mo)")
        
        # URL pour l'upload de pièces jointes
        url = f"https://graph.facebook.com/v13.0/me/messages?access_token={MESSENGER_PAGE_ACCESS_TOKEN}"
        
        # Préparer les données multipart
        files = {
            'filedata': (os.path.basename(video_path), open(video_path, 'rb'), 'video/mp4')
        }
        
        payload = {
            'recipient': json.dumps({
                'id': sender_id
            }),
            'message': json.dumps({
                'attachment': {
                    'type': 'video', 
                    'payload': {}
                }
            })
        }
        
        # Envoyer la requête
        response = requests.post(url, files=files, data=payload)
        
        # Vérifier la réponse
        if response.status_code != 200:
            logger.error(f"Erreur lors de l'envoi de la vidéo: {response.status_code} - {response.text}")
            raise Exception(f"Erreur HTTP: {response.status_code}")
        
        response_data = response.json()
        if "error" in response_data:
            logger.error(f"Erreur API lors de l'envoi de la vidéo: {response_data['error']}")
            raise Exception(response_data["error"]["message"])
        
        logger.info("Vidéo envoyée avec succès")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la vidéo: {e}")
        raise

async def send_text_message(recipient_id, message_text):
    """Envoie un message texte à un utilisateur Messenger"""
    logger.info(f"Début de send_text_message pour recipient_id: {recipient_id}")
    logger.info(f"Message à envoyer: {message_text}")
    
    # Diviser le message en morceaux de 2000 caractères
    chunks = [message_text[i:i+2000] for i in range(0, len(message_text), 2000)]
    
    for chunk in chunks:
        message_data = {
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": chunk
            }
        }
        
        try:
            await call_send_api(message_data)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            raise  # Propager l'erreur pour la gestion dans handle_message
    
    logger.info("Fin de send_text_message")

async def call_send_api(message_data):
    """Appelle l'API Send de Facebook Messenger"""
    logger.info(f"Début de call_send_api avec message_data: {json.dumps(message_data)}")
    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={MESSENGER_PAGE_ACCESS_TOKEN}"
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=message_data
        )
        
        logger.info(f"Réponse reçue de l'API Facebook. Status: {response.status_code}")
        
        body = response.json()
        logger.info(f"Réponse de l'API Facebook: {json.dumps(body)}")
        
        if "error" in body:
            logger.error(f"Erreur lors de l'appel à l'API Send: {body['error']}")
            raise Exception(body["error"]["message"])
        
        logger.info("Message envoyé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API Facebook: {e}")
        raise

