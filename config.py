import os
from dotenv import load_dotenv

load_dotenv()

MESSENGER_VERIFY_TOKEN = os.environ.get('MESSENGER_VERIFY_TOKEN')
MESSENGER_PAGE_ACCESS_TOKEN = os.environ.get('MESSENGER_PAGE_ACCESS_TOKEN')
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')

def verify_webhook(request):
    print("Verification request received with parameters:", request.args)
    
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print("Mode:", mode)
    print("Token received:", token)
    print("Challenge:", challenge)
    print("Expected token:", MESSENGER_VERIFY_TOKEN)
    
    if mode and token:
        if mode == "subscribe" and token == MESSENGER_VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            print("Verification failed - Incorrect token or invalid mode")
            print(f"Mode received: {mode}, Expected mode: subscribe")
            print(f"Token received: {token}, Expected token: {MESSENGER_VERIFY_TOKEN}")
            return "", 403
    else:
        print("Missing parameters in request")
        return "", 400

