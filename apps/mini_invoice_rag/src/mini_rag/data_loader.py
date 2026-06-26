from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATA_PATH = (
    REPO_ROOT
    / "golden_sets"
    / "invoice-unpaid-chatbot"
    / "fake_data"
    / "invoice_lines.csv"
)


@dataclass(frozen=True)
class InvoiceLine:
    invoice_id: str
    line_id: int
    customer_id: str
    customer_name: str
    country: str
    owner_team: str
    issue_date: str
    due_date: str
    status: str
    currency: str
    amount_due: float
    description: str
    sensitivity: str

    def context_line(self) -> str:
        return (
            f"{self.invoice_id} line {self.line_id}: {self.customer_name} "
            f"({self.customer_id}, {self.country}), status={self.status}, "
            f"due={self.due_date}, amount_due={self.amount_due:g} "
            f"{self.currency}, description={self.description}"
        )


def load_invoice_lines(data_path: str | Path | None = None) -> list[InvoiceLine]:
    path = Path(data_path) if data_path else DEFAULT_DATA_PATH
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            InvoiceLine(
                invoice_id=row["invoice_id"],
                line_id=int(row["line_id"]),
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                country=row["country"],
                owner_team=row["owner_team"],
                issue_date=row["issue_date"],
                due_date=row["due_date"],
                status=row["status"],
                currency=row["currency"],
                amount_due=float(row["amount_due"]),
                description=row["description"],
                sensitivity=row["sensitivity"],
            )
            for row in reader
        ]

