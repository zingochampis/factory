from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_SRC = ROOT / "apps" / "mini_invoice_rag" / "src"
sys.path.insert(0, str(APP_SRC))

from mini_rag.app import answer_question  # noqa: E402
from mini_rag.data_loader import load_invoice_lines  # noqa: E402
from mini_rag.policies import UserContext, visible_invoice_lines  # noqa: E402


GOLDEN_DIR = ROOT / "golden_sets" / "invoice-unpaid-chatbot"


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def answer_blob(answer: dict) -> str:
    return " ".join(
        [
            answer.get("status", ""),
            answer.get("answer", ""),
            " ".join(answer.get("citations", [])),
            answer.get("refusal_reason", "") or "",
        ]
    )


def check_expected_status(case: dict, answer: dict) -> list[str]:
    expected = case.get("expected_status")
    actual = answer.get("status")
    if expected and actual != expected:
        return [f"expected status {expected}, got {actual}"]
    return []


def check_must_cite(case: dict, answer: dict) -> list[str]:
    citations = set(answer.get("citations", []))
    return [
        f"missing citation {invoice_id}"
        for invoice_id in case.get("must_cite", [])
        if invoice_id not in citations
    ]


def check_must_not_cite(case: dict, answer: dict) -> list[str]:
    blob = answer_blob(answer)
    return [
        f"forbidden invoice id appeared: {invoice_id}"
        for invoice_id in case.get("must_not_cite", [])
        if invoice_id in blob
    ]


def check_must_contain(case: dict, answer: dict) -> list[str]:
    blob = answer_blob(answer).lower()
    return [
        f"missing expected text: {text}"
        for text in case.get("must_contain", [])
        if text.lower() not in blob
    ]


def run_question_cases(offline: bool) -> list[tuple[str, bool, list[str]]]:
    results = []
    for case in load_json(GOLDEN_DIR / "questions.json"):
        answer = answer_question(case["question"], role=case["role"], offline=offline)
        errors = []
        errors.extend(check_expected_status(case, answer))
        errors.extend(check_must_cite(case, answer))
        errors.extend(check_must_not_cite(case, answer))
        errors.extend(check_must_contain(case, answer))
        results.append((case["id"], not errors, errors))
    return results


def run_refusal_cases(offline: bool) -> list[tuple[str, bool, list[str]]]:
    results = []
    for case in load_json(GOLDEN_DIR / "refusal_cases.json"):
        answer = answer_question(case["question"], role=case["role"], offline=offline)
        errors = []
        errors.extend(check_expected_status(case, answer))
        errors.extend(check_must_not_cite(case, answer))
        results.append((case["id"], not errors, errors))
    return results


def run_rls_cases() -> list[tuple[str, bool, list[str]]]:
    rows = load_invoice_lines()
    results = []
    for case in load_json(GOLDEN_DIR / "rls_cases.json"):
        visible = visible_invoice_lines(rows, UserContext(role=case["role"]))
        visible_ids = {row.invoice_id for row in visible}
        errors = []
        for invoice_id in case["visible_invoice_ids"]:
            if invoice_id not in visible_ids:
                errors.append(f"expected visible invoice missing: {invoice_id}")
        for invoice_id in case["hidden_invoice_ids"]:
            if invoice_id in visible_ids:
                errors.append(f"hidden invoice was visible: {invoice_id}")
        results.append((case["id"], not errors, errors))
    return results


def print_results(results: list[tuple[str, bool, list[str]]]) -> None:
    for case_id, passed, errors in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {case_id}")
        for error in errors:
            print(f"  - {error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use deterministic local synthesizer instead of Ollama.",
    )
    args = parser.parse_args()

    results = []
    results.extend(run_question_cases(offline=args.offline))
    results.extend(run_rls_cases())
    results.extend(run_refusal_cases(offline=args.offline))

    print_results(results)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Summary: {passed}/{total} cases passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

