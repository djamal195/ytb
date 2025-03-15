import sys
import os
from flask import Flask

# Version simplifiée pour le débogage
app = Flask(__name__)

@app.route('/api/webhook', methods=['GET'])
def webhook_verification():
    return "Test webhook", 200

@app.route('/', methods=['GET'])
def home():
    return "Le serveur est en ligne!", 200

# Point d'entrée pour Vercel
handler = app

