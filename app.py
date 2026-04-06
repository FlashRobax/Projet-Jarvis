from core.brain import ask_jarvis, store_web_result
from core.voice import VoiceManager
from tools.web_tools import search_web


WAKE_WORD = "jarvis"

SLEEP_WORDS = {
    "merci",
    "merci jarvis",
    "c'est bon merci",
    "cest bon merci",
    "merci beaucoup",
}

YES_WORDS = {
    "oui",
    "oui oui",
    "vas-y",
    "vas y",
    "ok",
    "okay",
    "d'accord",
    "accord",
    "oui bien sûr",
    "bien sûr",
    "fais la recherche",
    "cherche",
    "recherche",
    "oui fais la recherche",
}

NO_WORDS = {
    "non",
    "pas besoin",
    "laisse",
    "annule",
    "non merci",
}


def contains_wake_word(text: str) -> bool:
    return WAKE_WORD in text.lower()


def is_sleep_request(text: str) -> bool:
    normalized = text.lower().strip()
    return normalized in SLEEP_WORDS


def remove_wake_word(text: str) -> str:
    lower_text = text.lower()
    return lower_text.replace(WAKE_WORD, "", 1).strip(" ,;:.!?-")


def is_yes(text: str) -> bool:
    normalized = text.lower().strip()
    return any(word in normalized for word in YES_WORDS)


def is_no(text: str) -> bool:
    normalized = text.lower().strip()
    return any(word in normalized for word in NO_WORDS)


def say(voice, message: str) -> None:
    if voice is not None:
        voice.speak(message)


def interrupt_if_needed(voice) -> None:
    if voice is not None and voice.is_speaking:
        voice.stop_speaking()


def handle_jarvis_result(result: dict, voice) -> bool:
    result_type = result.get("type")

    if result_type == "action_result":
        message = result.get("message", "")

        if message == "__SHUTDOWN__":
            farewell = "Extinction du système. À votre service, Monsieur."
            print(f"Jarvis > {farewell}")
            say(voice, farewell)
            return False

        print(f"Jarvis > {message}\n")
        say(voice, message)
        return True

    if result_type == "response":
        message = result.get("message", "")
        print(f"Jarvis > {message}\n")
        say(voice, message)
        return True

    return True


def main() -> None:
    voice = None
    jarvis_awake = False
    waiting_web_confirmation = False
    pending_web_query = ""
    pending_user_request = ""

    try:
        voice = VoiceManager(
            model_path="models/vosk-model-small-fr-0.22",
            sample_rate=16000,
            piper_model_path="fr_FR-tom-medium.onnx",
        )
        print("Module vocal chargé avec succès.")
    except Exception as e:
        print(f"[INFO] Initialisation vocale impossible : {e}")
        voice = None

    print("Jarvis est en ligne.")
    print("Commandes disponibles :")
    print("  - 't' : mode texte")
    if voice is not None:
        print("  - 'v' : mode écoute continue")
    print()

    while True:
        mode = input("Mode > ").strip().lower()

        if mode in {"quit", "exit", "stop"}:
            print("Jarvis > Veuillez utiliser une commande naturelle pour m'éteindre, Monsieur.\n")
            continue

        # =========================
        # MODE TEXTE
        # =========================
        if mode == "t":
            user_input = input("Vous > ").strip()
            if not user_input:
                continue

            interrupt_if_needed(voice)
            normalized_input = user_input.lower().strip()

            if waiting_web_confirmation:
                if is_yes(normalized_input):
                    web_result = search_web(pending_web_query)
                    store_web_result(pending_user_request, pending_web_query, web_result)
                    print(f"Jarvis > {web_result}\n")
                    say(voice, web_result)

                    waiting_web_confirmation = False
                    pending_web_query = ""
                    pending_user_request = ""
                    continue

                if is_no(normalized_input):
                    decline = "Très bien, Monsieur. Je n'effectuerai aucune recherche en ligne."
                    print(f"Jarvis > {decline}\n")
                    say(voice, decline)

                    waiting_web_confirmation = False
                    pending_web_query = ""
                    pending_user_request = ""
                    continue

                retry_message = "Je n'ai pas bien compris, Monsieur. Veuillez répondre par oui ou par non."
                print(f"Jarvis > {retry_message}\n")
                say(voice, retry_message)
                continue

            if not jarvis_awake:
                if not contains_wake_word(user_input):
                    continue

                jarvis_awake = True
                cleaned_input = remove_wake_word(user_input)

                if not cleaned_input:
                    answer = "Oui, Monsieur ?"
                    print(f"Jarvis > {answer}\n")
                    say(voice, answer)
                    continue

                user_input = cleaned_input
                normalized_input = user_input.lower().strip()

            if is_sleep_request(normalized_input):
                answer = "Toujours un plaisir, Monsieur."
                print(f"Jarvis > {answer}\n")
                say(voice, answer)
                jarvis_awake = False
                continue

            result = ask_jarvis(user_input)

            if result.get("type") == "need_web_search":
                pending_web_query = result.get("query", "").strip()
                pending_user_request = user_input
                waiting_web_confirmation = True

                ask_message = (
                    "Monsieur, je ne dispose pas de cette information avec suffisamment de certitude. "
                    "Souhaitez-vous que j'effectue une recherche en ligne ?"
                )
                print(f"Jarvis > {ask_message}\n")
                say(voice, ask_message)
                continue

            should_continue = handle_jarvis_result(result, voice)
            if not should_continue:
                break

        # =========================
        # MODE VOCAL
        # =========================
        elif mode == "v" and voice is not None:
            print("Jarvis > Écoute continue activée.\n")

            for user_input in voice.listen_forever():
                if not user_input:
                    continue

                # Coupe immédiatement la parole si une nouvelle requête arrive
                interrupt_if_needed(voice)

                print(f"Vous (audio) > {user_input}")
                normalized_input = user_input.lower().strip()

                if normalized_input in {"stop écoute", "arrête écoute", "arrete ecoute"}:
                    message = "Je suspends l'écoute continue, Monsieur."
                    print(f"Jarvis > {message}\n")
                    say(voice, message)
                    break

                if waiting_web_confirmation:
                    if is_yes(normalized_input):
                        web_result = search_web(pending_web_query)
                        store_web_result(pending_user_request, pending_web_query, web_result)
                        print(f"Jarvis > {web_result}\n")
                        say(voice, web_result)

                        waiting_web_confirmation = False
                        pending_web_query = ""
                        pending_user_request = ""
                        continue

                    if is_no(normalized_input):
                        decline = "Très bien, Monsieur. Je n'effectuerai aucune recherche en ligne."
                        print(f"Jarvis > {decline}\n")
                        say(voice, decline)

                        waiting_web_confirmation = False
                        pending_web_query = ""
                        pending_user_request = ""
                        continue

                    retry_message = "Je n'ai pas bien compris, Monsieur. Veuillez répondre par oui ou par non."
                    print(f"Jarvis > {retry_message}\n")
                    say(voice, retry_message)
                    continue

                if not jarvis_awake:
                    if not contains_wake_word(user_input):
                        continue

                    jarvis_awake = True
                    cleaned_input = remove_wake_word(user_input)

                    if not cleaned_input:
                        answer = "Oui, Monsieur ?"
                        print(f"Jarvis > {answer}\n")
                        say(voice, answer)
                        continue

                    user_input = cleaned_input
                    normalized_input = user_input.lower().strip()

                if is_sleep_request(normalized_input):
                    answer = "Toujours un plaisir, Monsieur."
                    print(f"Jarvis > {answer}\n")
                    say(voice, answer)
                    jarvis_awake = False
                    continue

                result = ask_jarvis(user_input)

                if result.get("type") == "need_web_search":
                    pending_web_query = result.get("query", "").strip()
                    pending_user_request = user_input
                    waiting_web_confirmation = True

                    ask_message = (
                        "Monsieur, je ne dispose pas de cette information avec suffisamment de certitude. "
                        "Souhaitez-vous que j'effectue une recherche en ligne ?"
                    )
                    print(f"Jarvis > {ask_message}\n")
                    say(voice, ask_message)
                    continue

                should_continue = handle_jarvis_result(result, voice)
                if not should_continue:
                    return

        else:
            print("Jarvis > Mode inconnu ou voix indisponible.\n")


if __name__ == "__main__":
    main()