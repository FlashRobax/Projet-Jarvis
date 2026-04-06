import json
import os

from config import MEMORY_FILE, DEBUG
from core.prompts import build_system_prompt
from core.llm import chat_with_ollama
from tools.registry import TOOLS


def load_history() -> list[dict]:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history: list[dict]) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def build_messages(user_input: str, history: list[dict]) -> list[dict]:
    system_prompt = build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_input})
    return messages


def execute_action(action_name: str, parameters: dict) -> str:
    if action_name == "shutdown":
        return "__SHUTDOWN__"

    tool = TOOLS.get(action_name)

    if not tool:
        return "Monsieur, vous ne m'avez pas encore doté de cette fonctionnalité."

    function = tool["function"]

    try:
        if parameters:
            return function(**parameters)
        return function()
    except TypeError:
        return (
            "Monsieur, l'action demandée a bien été identifiée, "
            "mais ses paramètres sont invalides."
        )
    except Exception as e:
        return f"Je suis navré, Monsieur. Une erreur est survenue : {e}"


def parse_llm_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")

        if start != -1 and end != -1 and end > start:
            candidate = raw_text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    return {
        "type": "response",
        "message": (
            "Monsieur, je crains que ma réponse n'ait été quelque peu désordonnée. "
            "Veuillez réessayer."
        )
    }


def ask_jarvis(user_input: str):
    history = load_history()
    messages = build_messages(user_input, history)

    raw_answer = chat_with_ollama(messages)

    if DEBUG:
        print(f"[DEBUG LLM RAW] {raw_answer}")

    parsed = parse_llm_json(raw_answer)

    response_type = parsed.get("type")

    if response_type == "action":
        action_name = parsed.get("action", "")
        parameters = parsed.get("parameters", {})
        result = execute_action(action_name, parameters)

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)})
        history.append({"role": "tool", "content": result})
        save_history(history)

        return {
            "type": "action_result",
            "message": result
        }

    if response_type == "need_web_search":
        query = parsed.get("query", "").strip()

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)})
        save_history(history)

        return {
            "type": "need_web_search",
            "query": query
        }

    message = parsed.get(
        "message",
        "Monsieur, vous ne m'avez pas encore doté de cette fonctionnalité."
    )

    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": json.dumps(parsed, ensure_ascii=False)})
    save_history(history)

    return {
        "type": "response",
        "message": message
    }
def store_web_result(user_query: str, web_query: str, web_result: str) -> None:
    history = load_history()

    history.append({
        "role": "user",
        "content": f"Recherche web autorisée pour : {user_query}"
    })
    history.append({
        "role": "tool",
        "content": f"Résultat web pour '{web_query}' : {web_result}"
    })

    save_history(history)