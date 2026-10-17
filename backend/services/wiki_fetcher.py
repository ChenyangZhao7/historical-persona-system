import requests

def fetch_wikipedia_text(name: str) -> str:
    url = "https://en.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "titles": name,
        "prop": "extracts",
        "explaintext": True,
        "format": "json",
        "redirects": 1
    }
    
    headers = {"User-Agent": "HistoricalPersonaSystem/1.0"}
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        return None
    
    try:
        data = response.json()
        pages = data["query"]["pages"]
        page = next(iter(pages.values()))
    except (KeyError, StopIteration, ValueError):
        return None

    if "extract" not in page:
        return None

    return page["extract"][:5000]