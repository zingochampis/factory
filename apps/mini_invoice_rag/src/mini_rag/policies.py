"""Local test double for the governed access policy.

This module is NOT the production security boundary. It is a deterministic
implementation of the access policy contract for local development and evals.

The single source of truth is the access policy contract at
``governance/security/rls_policies.yaml``. Role visibility, forbidden request
phrases, and access descriptions are read from that file rather than hardcoded
here, so the local mock cannot drift from the contract.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

from .data_loader import InvoiceLine


# Location of the access policy contract, relative to the repository root.
POLICY_RELPATH = ("governance", "security", "rls_policies.yaml")

# Operator suffixes supported in role allow-clauses.
_OPERATORS = ("_equals", "_not")

# Special allow token meaning "every row is visible to this role".
ALL_ROWS = "all_rows"


@dataclass(frozen=True)
class UserContext:
    role: str


def _find_policy_path() -> Path:
    """Locate the access policy contract.

    Honors the FACTORY_ACCESS_POLICY override, otherwise walks up from this
    module until it finds governance/security/rls_policies.yaml.
    """
    override = os.getenv("FACTORY_ACCESS_POLICY")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent.joinpath(*POLICY_RELPATH)
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate governance/security/rls_policies.yaml. "
        "Set FACTORY_ACCESS_POLICY to the access policy contract path."
    )


@lru_cache(maxsize=None)
def load_access_policy(path: Optional[str] = None) -> dict:
    """Load and cache the access policy contract."""
    policy_path = Path(path) if path else _find_policy_path()
    with policy_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _split_operator(key: str) -> tuple:
    for suffix in _OPERATORS:
        if key.endswith(suffix):
            return key[: -len(suffix)], suffix
    raise ValueError(f"Unsupported access policy condition: {key!r}")


def _clause_matches(row: InvoiceLine, clause: dict) -> bool:
    """A clause is a set of field conditions combined with AND."""
    for key, expected in clause.items():
        field, operator = _split_operator(key)
        actual = getattr(row, field)
        if operator == "_equals" and actual != expected:
            return False
        if operator == "_not" and actual == expected:
            return False
    return True


def visible_invoice_lines(
    rows: list, user_context: UserContext
) -> list:
    """Return rows visible to the role per the access policy contract.

    Default decision is deny: unknown roles and roles with an empty allow list
    see nothing. Allow-clauses are combined with OR; conditions within a clause
    are combined with AND.
    """
    policy = load_access_policy()
    role_def = policy.get("roles", {}).get(user_context.role)
    if not role_def:
        return []
    allow = role_def.get("allow") or []
    if any(clause == ALL_ROWS for clause in allow):
        return list(rows)
    return [
        row
        for row in rows
        if any(
            isinstance(clause, dict) and _clause_matches(row, clause)
            for clause in allow
        )
    ]


def refusal_reason(question: str) -> Optional[str]:
    """Refuse questions that contain a forbidden phrase from the contract."""
    normalized = question.lower()
    for phrase in load_access_policy().get("forbidden_requests", []):
        if str(phrase).lower() in normalized:
            return f"Request contains forbidden policy phrase: {phrase}"
    return None


def describe_access(user_context: UserContext) -> str:
    """Human-readable access scope, from the contract's role descriptions."""
    role_def = load_access_policy().get("roles", {}).get(user_context.role)
    if role_def and role_def.get("description"):
        return role_def["description"]
    return "no configured invoice access"
