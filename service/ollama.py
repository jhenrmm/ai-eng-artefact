import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL


class OllamaError(RuntimeError):
    pass


def chat(
    messages: list[dict],
    model: str = OLLAMA_MODEL,
    timeout: float = OLLAMA_TIMEOUT,
    url: str = OLLAMA_URL,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": False,
        }
    ).encode("utf-8")

    request = Request(
        f"{url.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OllamaError(
            f"Ollama returned HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise OllamaError(
            f"Could not connect to Ollama at {url}: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise OllamaError(
            f"Ollama did not respond within {timeout:.0f}s ({url})."
        ) from exc
    except json.JSONDecodeError as exc:
        raise OllamaError("Ollama returned invalid JSON.") from exc

    content = (body.get("message") or {}).get("content")
    if not content:
        raise OllamaError("Ollama returned a response without content.")

    return content.strip()
