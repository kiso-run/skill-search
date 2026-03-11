import json
import os
import signal
import sys
import tomllib
from pathlib import Path

import httpx


def _handle_sigterm(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_sigterm)


def main():
    data = json.load(sys.stdin)
    args = data["args"]

    config = load_config()
    backend = config.get("backend", "brave")

    query = args["query"]
    max_results = min(args.get("max_results", 5), 100)
    language = args.get("language")
    country = args.get("country")

    api_key = os.environ.get("KISO_SKILL_SEARCH_API_KEY", "")
    if not api_key:
        print("Search failed: KISO_SKILL_SEARCH_API_KEY is not set", file=sys.stderr)
        print("Search failed: API key not configured.")
        sys.exit(1)

    try:
        if backend == "brave":
            results = search_brave(query, max_results, language, country, api_key)
        elif backend == "serper":
            results = search_serper(query, max_results, language, country, api_key)
        else:
            print(f"Search failed: unknown backend '{backend}'")
            sys.exit(1)
    except httpx.TimeoutException as exc:
        print(f"Search failed (timeout): {exc}", file=sys.stderr)
        print("Search failed: request timed out.")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        print(f"Search failed ({exc.response.status_code}): {exc.response.text}", file=sys.stderr)
        print(f"Search failed: HTTP {exc.response.status_code}.")
        sys.exit(1)
    except httpx.RequestError as exc:
        print(f"Search failed (network): {exc}", file=sys.stderr)
        print("Search failed: network error.")
        sys.exit(1)

    print(format_results(query, results))


def load_config() -> dict:
    """Load config.toml from the tool directory (where run.py lives)."""
    config_path = Path(__file__).parent / "config.toml"
    if not config_path.exists():
        return {"backend": "brave"}
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def search_brave(query, max_results, language, country, api_key):
    params = {"q": query, "count": max_results}
    if language:
        params["search_lang"] = language
    if country:
        params["country"] = country

    resp = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        params=params,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
        })
    return results


def search_serper(query, max_results, language, country, api_key):
    body = {"q": query, "num": max_results}
    if language:
        body["hl"] = language.lower()
    if country:
        body["gl"] = country.lower()

    resp = httpx.post(
        "https://google.serper.dev/search",
        json=body,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return results


def format_results(query: str, results: list[dict]) -> str:
    """Format results into numbered text output.

    Each result dict has: title, url, snippet.
    """
    if not results:
        return f'No results found for "{query}".'

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        if r.get("snippet"):
            for line in r["snippet"].splitlines():
                lines.append(f"   {line}")
        lines.append("")
    return "\n".join(lines).rstrip()


if __name__ == "__main__":
    main()
