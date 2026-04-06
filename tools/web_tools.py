import requests
from urllib.parse import quote


def search_duckduckgo(query: str) -> str | None:
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "no_redirect": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    answer = data.get("Answer", "").strip()
    if answer:
        return answer

    abstract = data.get("AbstractText", "").strip()
    if abstract:
        return abstract

    related = data.get("RelatedTopics", [])
    results = []

    for topic in related:
        if isinstance(topic, dict):
            text = topic.get("Text", "").strip()
            if text:
                results.append(text)

            nested = topic.get("Topics", [])
            for subtopic in nested:
                if isinstance(subtopic, dict):
                    subtext = subtopic.get("Text", "").strip()
                    if subtext:
                        results.append(subtext)

        if len(results) >= 3:
            break

    if results:
        return " | ".join(results[:3])

    return None


def search_wikipedia(query: str) -> str | None:
    try:
        search_url = f"https://fr.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("query", {}).get("search", [])
        if not results:
            return None

        title = results[0]["title"]

        summary_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
        summary_response = requests.get(summary_url, timeout=10)
        summary_response.raise_for_status()
        summary_data = summary_response.json()

        extract = summary_data.get("extract", "").strip()
        if extract:
            return extract

        return None

    except Exception:
        return None


def search_web(query: str) -> str:
    query = query.strip()

    if not query:
        return "Je suis navré, Monsieur. La requête est vide."

    result = search_duckduckgo(query)
    if result:
        return result

    result = search_wikipedia(query)
    if result:
        return result

    return (
        "Je suis navré, Monsieur. "
        "Je n'ai trouvé aucune information exploitable en ligne."
    )