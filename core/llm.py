import requests
from config import OLLAMA_URL, MODEL_NAME


def chat_with_ollama(messages: list[dict]) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "format": "json"
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    return data["message"]["content"].strip()