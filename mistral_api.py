import re
import requests
import json
from config import MISTRAL_API_KEY

def check_creator_question(prompt):
    lower_prompt = prompt.lower()
    patterns = [
        r"qui (t'a|ta|t as) (créé|cree|construit|développé|developpe|conçu|concu|fabriqué|fabrique|inventé|invente)",
        r"par qui as[- ]?tu (été|ete) (créé|cree|développé|developpe|construit|conçu|concu)",
        r"qui est (ton|responsable de|derrière|derriere) (créateur|createur|développeur|developpeur|toi)",
        r"d['oòo]u viens[- ]?tu"
    ]
    
    for pattern in patterns:
        if re.search(pattern, lower_prompt):
            return True
    return False

def generate_mistral_response(prompt):
    print(f"Starting generate_mistral_response for prompt: {prompt}")
    
    # Check if the question is about the creator
    if check_creator_question(prompt):
        print("Creator question detected. Sending custom response.")
        return "J'ai été créé par Djamaldine Montana avec l'aide de Mistral. C'est un développeur talentueux qui m'a conçu pour aider les gens comme vous !"
    
    try:
        print("Sending request to Mistral API...")
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MISTRAL_API_KEY}"
            },
            json={
                "model": "mistral-large-latest",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            },
            timeout=50  # 50 seconds timeout
        )
        
        print(f"Response received from Mistral API. Status: {response.status_code}")
        
        if not response.ok:
            print(f"Mistral API Error: {response.status_code} - {response.text}")
            raise Exception(f"HTTP error! status: {response.status_code}")
        
        data = response.json()
        print(f"Data received from Mistral API: {json.dumps(data)}")
        
        generated_response = data["choices"][0]["message"]["content"]
        
        if len(generated_response) > 4000:
            generated_response = generated_response[:4000] + "... (réponse tronquée)"
        
        print(f"Generated response: {generated_response}")
        return generated_response
        
    except requests.exceptions.Timeout:
        print("Timeout error during Mistral response generation")
        return "Désolé, la génération de la réponse a pris trop de temps. Veuillez réessayer avec une question plus courte ou plus simple."
    except Exception as e:
        print(f"Detailed error during Mistral response generation: {e}")
        return "Je suis désolé, mais je ne peux pas répondre pour le moment. Veuillez réessayer plus tard."

