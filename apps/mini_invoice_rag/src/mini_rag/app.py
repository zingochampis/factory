from __future__ import annotations

import argparse
import json
from typing import Any

from .config import load_settings
from .ollama_client import OllamaClient
from .policies import UserContext, describe_access
from .retriever import UNPAID_STATUSES, RetrievalResult, retrieve, wants_unpaid


SYSTEM_PROMPT = """You are a governed invoice assistant.
Use only the provided context rows.
Apply the access contract: never reveal rows that are not in context.
For invoice facts, cite invoice_id values.
If the request asks to bypass RLS, reveal hidden data, or use unavailable data, refuse.
Be concise and factual."""


def offline_synthesize(question: str, retrieval: RetrievalResult) -> dict[str, Any]:
    if retrieval.refused:
        return {
            "status": "refused",
            "answer": "I cannot answer that request because it conflicts with the access policy.",
            "citations": [],
            "refusal_reason": retrieval.refusal_reason,
        }

    if not retrieval.rows:
        return {
            "status": "answered",
            "answer": "No accessible matching invoice rows were found.",
            "citations": [],
            "refusal_reason": None,
        }

    lines = []
    for row in retrieval.rows:
        if wants_unpaid(question) and row.status not in UNPAID_STATUSES:
            sentence = (
                f"{row.invoice_id} is {row.status}, not unpaid "
                f"({row.customer_name}, {row.amount_due:g} {row.currency})."
            )
        else:
            sentence = (
                f"{row.invoice_id}: {row.customer_name}, status {row.status}, "
                f"due {row.due_date}, amount {row.amount_due:g} {row.currency}."
            )
        lines.append(sentence)

    return {
        "status": "answered",
        "answer": " ".join(lines),
        "citations": [row.invoice_id for row in retrieval.rows],
        "refusal_reason": None,
    }


def ollama_synthesize(question: str, retrieval: RetrievalResult) -> dict[str, Any]:
    if retrieval.refused or not retrieval.rows:
        return offline_synthesize(question, retrieval)

    settings = load_settings()
    context = "\n".join(row.context_line() for row in retrieval.rows)
    client = OllamaClient(settings=settings)
    answer = client.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Visible invoice context:\n{context}\n\n"
                    "Answer using only this context."
                ),
            },
        ]
    )
    return {
        "status": "answered",
        "answer": answer.strip(),
        "citations": [row.invoice_id for row in retrieval.rows],
        "refusal_reason": None,
        "model": settings.ollama_model,
    }


def answer_question(
    question: str,
    role: str = "finance_se",
    offline: bool = False,
    top_k: int | None = None,
) -> dict[str, Any]:
    settings = load_settings()
    user_context = UserContext(role=role)
    retrieval = retrieve(
        question,
        user_context=user_context,
        top_k=top_k if top_k is not None else settings.top_k,
    )
    answer = offline_synthesize(question, retrieval) if offline else ollama_synthesize(question, retrieval)
    answer["role"] = role
    answer["access_scope"] = describe_access(user_context)
    return answer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Invoice question to answer.")
    parser.add_argument("--role", default="finance_se", help="User role for RLS.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use deterministic synthesizer instead of Ollama.",
    )
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()

    answer = answer_question(
        args.question,
        role=args.role,
        offline=args.offline,
        top_k=args.top_k,
    )
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

