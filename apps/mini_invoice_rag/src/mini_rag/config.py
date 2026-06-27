from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "ministral-3:3b"
    temperature: float = 0.1
    top_k: int = 5


def load_settings() -> Settings:
    return Settings(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "ministral-3:3b"),
        temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
        top_k=int(os.getenv("MINI_RAG_TOP_K", "5")),
    )

