from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(APP_SRC))

from mini_rag.data_loader import load_invoice_lines  # noqa: E402
from mini_rag.policies import UserContext, visible_invoice_lines  # noqa: E402


class PolicyTests(unittest.TestCase):
    def test_sales_acme_only_sees_acme_rows(self) -> None:
        rows = load_invoice_lines()
        visible = visible_invoice_lines(rows, UserContext(role="sales_acme"))
        self.assertEqual(
            {row.invoice_id for row in visible},
            {"INV-1001", "INV-1002", "INV-1006"},
        )

    def test_external_viewer_sees_no_rows(self) -> None:
        rows = load_invoice_lines()
        visible = visible_invoice_lines(rows, UserContext(role="external_viewer"))
        self.assertEqual(visible, [])


if __name__ == "__main__":
    unittest.main()

