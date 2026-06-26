from __future__ import annotations

import re
from dataclasses import dataclass

from .data_loader import InvoiceLine, load_invoice_lines
from .policies import UserContext, refusal_reason, visible_invoice_lines


UNPAID_STATUSES = {"unpaid", "overdue"}


@dataclass(frozen=True)
class RetrievalResult:
    rows: list[InvoiceLine]
    refused: bool = False
    refusal_reason: str | None = None


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9-]+", text.lower()))


def explicit_invoice_ids(question: str) -> set[str]:
    return {match.upper() for match in re.findall(r"INV-\d+", question, re.I)}


def wants_unpaid(question: str) -> bool:
    normalized = question.lower()
    return any(
        phrase in normalized
        for phrase in ("unpaid", "overdue", "outstanding", "open invoice", "not paid")
    )


def apply_question_filters(question: str, rows: list[InvoiceLine]) -> list[InvoiceLine]:
    normalized = question.lower()
    filtered = rows
    invoice_ids = explicit_invoice_ids(question)
    if invoice_ids:
        filtered = [row for row in filtered if row.invoice_id in invoice_ids]
    if wants_unpaid(question) and not invoice_ids:
        filtered = [row for row in filtered if row.status in UNPAID_STATUSES]
    if "outside sweden" in normalized or "outside se" in normalized:
        filtered = [row for row in filtered if row.country != "SE"]
    elif "sweden" in normalized or " in se" in normalized:
        filtered = [row for row in filtered if row.country == "SE"]
    if "acme" in normalized:
        filtered = [row for row in filtered if "acme" in row.customer_name.lower()]
    return filtered


def score_row(question_tokens: set[str], row: InvoiceLine) -> int:
    row_text = " ".join(
        [
            row.invoice_id,
            row.customer_id,
            row.customer_name,
            row.country,
            row.owner_team,
            row.status,
            row.currency,
            row.description,
            row.sensitivity,
        ]
    )
    return len(question_tokens & tokenize(row_text))


def retrieve(
    question: str,
    user_context: UserContext,
    top_k: int = 5,
    data_path: str | None = None,
) -> RetrievalResult:
    reason = refusal_reason(question)
    if reason:
        return RetrievalResult(rows=[], refused=True, refusal_reason=reason)

    all_rows = load_invoice_lines(data_path)
    visible_rows = visible_invoice_lines(all_rows, user_context)
    candidates = apply_question_filters(question, visible_rows)
    question_tokens = tokenize(question)
    ranked = sorted(
        candidates,
        key=lambda row: (score_row(question_tokens, row), row.invoice_id),
        reverse=True,
    )
    return RetrievalResult(rows=ranked[:top_k])

