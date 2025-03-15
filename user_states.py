# Gestion des états utilisateurs pour suivre les conversations
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# États possibles
NORMAL = "normal"
WAITING_FOR_YOUTUBE_QUERY = "waiting_for_youtube_query"

# Stockage des états utilisateurs
user_states = {}

def set_user_state(user_id, state, data=None):
    """
    Définit l'état d'un utilisateur
    """
    user_states[user_id] = {
        "state": state,
        "data": data or {},
        "timestamp": datetime.now()
    }
    logger.info(f"État utilisateur défini pour {user_id}: {state}")

def get_user_state(user_id):
    """
    Récupère l'état actuel d'un utilisateur
    """
    if user_id not in user_states:
        return NORMAL, {}
    
    user_data = user_states[user_id]
    
    # Vérifier si l'état a expiré (30 minutes)
    if datetime.now() - user_data["timestamp"] > timedelta(minutes=30):
        logger.info(f"État expiré pour l'utilisateur {user_id}, retour à l'état normal")
        del user_states[user_id]
        return NORMAL, {}
    
    return user_data["state"], user_data["data"]

def clear_user_state(user_id):
    """
    Réinitialise l'état d'un utilisateur
    """
    if user_id in user_states:
        del user_states[user_id]
        logger.info(f"État utilisateur effacé pour {user_id}")

