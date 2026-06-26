from __future__ import annotations

from dataclasses import dataclass

from .data_loader import InvoiceLine


@dataclass(frozen=True)
class UserContext:
    role: str


FORBIDDEN_PHRASES = (
    "bypass rls",
    "ignore rls",
    "regardless of access",
    "hidden fields",
    "bank account",
    "personal data",
)


def visible_invoice_lines(
    rows: list[InvoiceLine], user_context: UserContext
) -> list[InvoiceLine]:
    role = user_context.role
    if role == "finance_all":
        return rows
    if role == "finance_se":
        return [
            row
            for row in rows
            if row.country == "SE" and row.sensitivity != "confidential"
        ]
    if role == "finance_de":
        return [
            row
            for row in rows
            if row.country == "DE" and row.sensitivity != "confidential"
        ]
    if role == "sales_acme":
        return [
            row
            for row in rows
            if row.customer_id == "CUST-100" and row.sensitivity != "confidential"
        ]
    return []


def refusal_reason(question: str) -> str | None:
    normalized = question.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in normalized:
            return f"Request contains forbidden policy phrase: {phrase}"
    if "confidential" in normalized and "finance_all" not in normalized:
        return "Request asks for confidential data without explicit allowed scope."
    return None


def describe_access(user_context: UserContext) -> str:
    descriptions = {
        "finance_all": "all pilot invoice rows",
        "finance_se": "non-confidential Sweden invoice rows",
        "finance_de": "non-confidential Germany invoice rows",
        "sales_acme": "non-confidential Acme invoice rows",
        "external_viewer": "no direct invoice-line rows",
    }
    return descriptions.get(user_context.role, "no configured invoice access")

