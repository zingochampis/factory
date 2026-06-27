# Agentic Software Factory - Mini Invoice RAG

This repository is a small factory scaffold for a governed RAG use case:
a chatbot that answers questions about unpaid invoice lines.

The app is intentionally replaceable. The durable assets are the governed
data contracts, semantic definitions, use case spec, golden sets, eval gates,
and pilot feedback loop.

## What Is In The Factory

- `governance/` - data contracts, RLS, semantic layer, lineage, audit, and
  LLM-readable access contracts.
- `usecases/invoice-unpaid-chatbot/` - versioned use case spec, acceptance
  criteria, and pilot run templates.
- `golden_sets/invoice-unpaid-chatbot/` - fake invoice data, expected answers,
  RLS cases, and refusal cases.
- `evals/` - executable eval gate. CI should fail if quality, RLS, or refusal
  behavior regresses.
- `apps/mini_invoice_rag/` - a minimal Python RAG app using a thin Ollama
  adapter. This is output-like and can be replaced.

## Quick Start

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .\apps\mini_invoice_rag
python .\evals\run_evals.py --offline
```

Run the app in deterministic offline mode:

```powershell
python -m mini_rag.app "Which unpaid invoices can I see?" --role finance_se --offline
```

Run with local Ollama and Ministral-3:3b:

```powershell
$env:OLLAMA_MODEL = "ministral-3:3b"
python -m mini_rag.app "Which unpaid invoices can I see?" --role finance_se
```

The default Ollama host is `http://localhost:11434`.

If `python` is not on PATH yet, use the Windows launcher directly:

```powershell
py .\evals\run_evals.py --offline
```

Inside Codex Desktop, this repo can also use the bundled runtime via:

```powershell
.\scripts\run_offline_evals.ps1
```

## Factory Rule

Generated application code can change. The factory assets should move more
slowly and should be treated as contracts:

- data and access contracts
- semantic definitions
- use case spec
- golden sets
- eval gates
- pilot learnings

Any builder LLM or developer should read those contracts before changing the
app.
