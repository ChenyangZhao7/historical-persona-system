"""Provider-agnostic chat completion.

Two backends, selected with `LLM_PROVIDER`:

- ``anthropic`` (default) — official SDK, model from ``ANTHROPIC_MODEL``
- ``deepseek``          — DeepSeek's OpenAI-compatible REST API, called with
                          ``requests`` so no extra dependency is needed

Everything else in the app calls `complete()` and never imports a vendor SDK.
"""
from __future__ import annotations

import os

import requests
from fastapi import HTTPException

DEFAULT_TIMEOUT = 90.0

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


def provider() -> str:
    return (os.environ.get("LLM_PROVIDER") or "anthropic").strip().lower()


def _settings() -> tuple[str, str, str]:
    """Return (kind, api_key, model) for the configured provider."""
    kind = provider()
    if kind == "deepseek":
        return (
            kind,
            os.environ.get("DEEPSEEK_API_KEY", ""),
            os.environ.get("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
        )
    return (
        "anthropic",
        os.environ.get("ANTHROPIC_API_KEY", ""),
        os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL),
    )


def available() -> bool:
    """True when the configured provider has a key."""
    return bool(_settings()[1])


def describe() -> str:
    kind, _, model = _settings()
    return f"{kind}:{model}"


def _missing_key_message(kind: str) -> str:
    if kind == "deepseek":
        return "DEEPSEEK_API_KEY is not set. Put it in .env or export it before starting the server."
    return "ANTHROPIC_API_KEY is not set. Put it in .env or export it before starting the server."


def _complete_anthropic(
    api_key: str,
    model: str,
    system: str | None,
    user: str,
    max_tokens: int,
    temperature: float | None = None,
) -> str:
    import anthropic

    kwargs = {}
    if system:
        kwargs["system"] = system
    if temperature is not None:
        kwargs["temperature"] = temperature
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=DEFAULT_TIMEOUT)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
            **kwargs,
        )
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {exc}")
    return response.content[0].text


def _complete_openai_compatible(
    api_key: str,
    model: str,
    system: str | None,
    user: str,
    max_tokens: int,
    temperature: float | None = None,
) -> str:
    base_url = os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).rstrip("/")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})

    payload = {"model": model, "max_tokens": max_tokens, "messages": messages, "stream": False}
    if temperature is not None:
        payload["temperature"] = temperature

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach {base_url}: {exc}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"{provider()} returned HTTP {response.status_code}: {response.text[:300]}",
        )

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail=f"Unexpected {provider()} response: {exc}")


def complete(
    user: str,
    *,
    system: str | None = None,
    max_tokens: int = 1000,
    temperature: float | None = None,
) -> str:
    """Send one prompt to the configured provider and return the text.

    `temperature` is left to the provider unless given. Scoring calls pass 0 so
    the same text always yields the same profile; creative calls do not.
    """
    kind, api_key, model = _settings()
    if not api_key:
        raise HTTPException(status_code=500, detail=_missing_key_message(kind))
    if not user or not user.strip():
        raise HTTPException(status_code=400, detail="Prompt is empty")

    if kind == "deepseek":
        return _complete_openai_compatible(api_key, model, system, user, max_tokens, temperature)
    return _complete_anthropic(api_key, model, system, user, max_tokens, temperature)
