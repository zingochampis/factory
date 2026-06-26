from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import Settings


@dataclass(frozen=True)
class OllamaClient:
    settings: Settings

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.settings.temperature},
        }
        request = urllib.request.Request(
            f"{self.settings.ollama_host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise RuntimeError(
                    f"Ollama is running but model {self.settings.ollama_model!r} is "
                    f"not installed. Run `ollama pull {self.settings.ollama_model}` "
                    f"or set OLLAMA_MODEL to an installed model."
                ) from exc
            raise RuntimeError(f"Ollama request failed (HTTP {exc.code}).") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not reach Ollama. Start Ollama or run with --offline."
            ) from exc
        return body.get("message", {}).get("content", "")

