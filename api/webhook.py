from flask import Flask, request
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Récupérer les variables d'environnement
MESSENGER_VERIFY_TOKEN = os.environ.get('MESSENGER_VERIFY_TOKEN')

@app.route('/', methods=['GET'])
def home():
    return "Le serveur est en ligne!", 200

@app.route('/api/webhook', methods=['GET'])
def webhook_verification():
    logger.info("GET request received for webhook verification")
    
    # Récupérer les paramètres de la requête
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    logger.info(f"Mode: {mode}, Token: {token}, Challenge: {challenge}")
    
    # Vérifier le token
    if mode and token:
        if mode == "subscribe" and token == MESSENGER_VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            logger.info("Verification failed - Incorrect token or invalid mode")
            return "", 403
    else:
        logger.info("Missing parameters in request")
        return "", 400

@app.route('/api/webhook', methods=['POST'])
def webhook_handler():
    logger.info("POST request received from webhook")
    return "EVENT_RECEIVED", 200

# Point d'entrée pour Vercel
handler = app

