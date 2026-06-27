# How To Work Locally

This repository is a small governed invoice RAG factory. The app under
`apps/mini_invoice_rag/` is replaceable; the durable source of truth is the use
case spec, data contract, semantic layer, RLS policy, golden sets, and evals.

This guide covers three things:

1. How to run the app locally as it works today.
2. Which governance YAML changes alter app behaviour.
3. How to extend the app to Postgres — where to change, and the exact prompt to
   give a builder LLM.

## 1. Run locally (current behaviour)

### Setup

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .\apps\mini_invoice_rag
```

This installs the `mini-invoice-rag` package with two equivalent entrypoints:

- `python -m mini_rag.app ...`
- `mini-invoice-rag ...`

### Run

Deterministic offline mode (no Ollama; this is what the evals use):

```powershell
python -m mini_rag.app "Which unpaid invoices can I see?" --role finance_se --offline
```

With local Ollama (default model `ministral-3:3b`):

```powershell
python -m mini_rag.app "Which unpaid invoices can I see?" --role finance_se
```

If the model is not pulled yet:

```powershell
ollama pull ministral-3:3b
```

Settings come from environment variables (current defaults shown):

- `OLLAMA_HOST` — `http://localhost:11434`
- `OLLAMA_MODEL` — `ministral-3:3b`
- `OLLAMA_TEMPERATURE` — `0.1`
- `MINI_RAG_TOP_K` — `5`

CLI flags:

- `--role` — user role for RLS (default `finance_se`)
- `--offline` — deterministic synthesis, skips Ollama
- `--top-k` — override `MINI_RAG_TOP_K`

### Request flow

The entrypoint is `apps/mini_invoice_rag/src/mini_rag/app.py`.

1. `main()` parses the question, `--role`, `--offline`, and `--top-k`.
2. `answer_question()` loads settings, builds a `UserContext(role=...)`, and calls
   `retrieve()` in `retriever.py`.
3. `retrieve()` refuses first: if the question contains a forbidden phrase from
   `rls_policies.yaml`, it returns a refusal before touching any data.
4. Otherwise it loads invoice rows from
   `golden_sets/invoice-unpaid-chatbot/fake_data/invoice_lines.csv` via
   `data_loader.py`.
5. It applies RLS **before** building retrieval context. `policies.py` reads role
   visibility from `rls_policies.yaml` rather than hardcoding it.
6. It applies question filters: explicit `INV-` ids, unpaid/overdue status,
   Sweden / outside Sweden, and Acme.
7. It scores and ranks the visible candidates and keeps `top_k`.
8. With `--offline`, `offline_synthesize()` returns deterministic JSON. Otherwise
   `ollama_synthesize()` sends only the visible context rows to Ollama via
   `ollama_client.py`.

Output is JSON with `status`, `answer`, `citations`, `refusal_reason`, `role`,
`access_scope`, and `model` (only when Ollama was called).

Behaviour worth knowing:

- Invoices live in a CSV fixture, not a database.
- `policies.py` is a development/eval test double, not a production security
  boundary.
- Hidden rows are filtered out before they are ranked, summarized, or sent to
  Ollama.
- Refused requests and no-data answers never call Ollama.
- All LLM provider logic stays behind `ollama_client.py`.

### Eval gate

Run before proposing a merge:

```powershell
python .\evals\run_evals.py --offline
```

If `python` is not on PATH, use `py .\evals\run_evals.py --offline`. The helper
`.\scripts\run_offline_evals.ps1` locates the bundled runtime when running inside
Codex Desktop. The offline eval checks golden questions, RLS visibility, refusal
behaviour, and forbidden citations.

## 2. Which governance YAML changes app behaviour

The running app reads exactly one governance file at runtime:
`governance/security/rls_policies.yaml`, loaded by `policies.py`. Editing it
changes retrieval and answers with no code change. The other governed files (data
contract, semantic layer, access contract) are contracts enforced by humans and
evals — the app does not load them at runtime, so editing them alone does not
change app behaviour.

`rls_policies.yaml` has two levers.

**Role visibility (`roles.<role>.allow`)** controls which rows a role sees,
applied before retrieval. For example, give the Acme sales team visibility into
Beta Foods.

Current:

```yaml
sales_acme:
  description: Acme account team can see non-confidential Acme rows only.
  allow:
    - customer_id_equals: CUST-100
      sensitivity_not: confidential
```

Changed:

```yaml
sales_acme:
  description: Acme account team can see non-confidential Acme and Beta Foods rows.
  allow:
    - customer_id_equals: CUST-100
      sensitivity_not: confidential
    - customer_id_equals: CUST-200
      sensitivity_not: confidential
```

In the CSV fixture `CUST-200` is `INV-1003` (Beta Foods, overdue). After this
change, `sales_acme` asking "Which unpaid invoices can I see?" gains a visible
row, offline and Ollama answers can cite `INV-1003`, and
`golden_sets/invoice-unpaid-chatbot/rls_cases.json` will fail until it is updated
to match the new intent. That failure is the point: if the change was
intentional, update the golden set; if it was accidental, the offline eval
catches it before merge.

**Forbidden requests (`forbidden_requests`)** refuse any question containing one
of the listed phrases, before retrieval. Add a phrase like `routing number` and
questions mentioning it are refused with no change to `app.py` or `retriever.py`.

## 3. Extend the app to Postgres

Goal: make the invoice-table home selectable at call time, while keeping CSV as
the deterministic default:

```powershell
python -m mini_rag.app "Which unpaid invoices can I see?" --role finance_se --invoice-store sqlite --sqlite-path .\local\invoice_lines.db
python -m mini_rag.app "Which unpaid invoices can I see?" --role finance_se --invoice-store postgres --postgres-dsn $env:POSTGRES_DSN
```

### Where to change

Contracts and docs (update these with, or before, the code):

- `usecases/invoice-unpaid-chatbot/usecase.spec.{md,yaml}` — record SQLite and
  Postgres as supported homes for the same `invoice_lines` data product, and the
  intended default.
- `governance/access_contracts/llm_read_access.yaml` — add the approved read
  surfaces (a local SQLite table/view; a Postgres RLS-protected table/view/RPC).
  Keep the rule that denied rows never reach retrieval or the model.
- `governance/data_contracts/invoice_lines.schema.yaml` — only if the table
  *shape* changes. A storage move with the same columns needs no change here.
- `governance/security/rls_policies.yaml` — only if role visibility or forbidden
  rules change. For Postgres, implement the same policy in native DB RLS or
  secured views; do not weaken the YAML to fit the database.
- `governance/semantic_layer/invoice_lines.semantic.yaml` — only if business
  meaning changes (for example the definition of "unpaid" or "visible").
- `golden_sets/invoice-unpaid-chatbot/` — only if expected behaviour changes. A
  pure storage move should not change expected citations, rows, or refusals; keep
  the CSV fixture as eval seed data.
- `evals/README.md` and `README.md` — document the new flags and any storage
  selector used by evals.

Code (keep current behaviour stable; change storage only):

- Add `apps/mini_invoice_rag/src/mini_rag/invoice_store.py` with
  `CsvInvoiceStore`, `SqliteInvoiceStore`, and `PostgresInvoiceStore`, all
  returning the existing `InvoiceLine` shape so `retriever.py`, `policies.py`, and
  evals stay simple.
- Add `--invoice-store {csv,sqlite,postgres}`, `--sqlite-path`, and
  `--postgres-dsn` in `app.py`, with `MINI_RAG_INVOICE_STORE`,
  `MINI_RAG_SQLITE_PATH`, and `POSTGRES_DSN` fallbacks in `config.py`.
- Thread the selected store through `answer_question()` and `retrieve()`; keep CSV
  the offline default.
- SQLite has no native RLS, so the local `policies.py` filter still applies before
  retrieval. For Postgres, prefer DB-side RLS or a secured read surface so denied
  rows never return.
- Keep Ollama behind `ollama_client.py`. Extend tests to cover store selection and
  to prove RLS still runs before retrieval in each mode.

`PRODUCTION.md` already describes Postgres/Supabase as a possible runtime harness.
If this work commits runtime-target files, add them under a new
`governance/runtime_targets/` folder and update `PRODUCTION.md`.

### Exact prompt for the builder LLM

```text
Read AGENTS.md first, then read these factory contracts before changing code:

- usecases/invoice-unpaid-chatbot/usecase.spec.md
- usecases/invoice-unpaid-chatbot/usecase.spec.yaml
- governance/data_contracts/invoice_lines.schema.yaml
- governance/semantic_layer/invoice_lines.semantic.yaml
- governance/security/rls_policies.yaml
- governance/access_contracts/llm_read_access.yaml
- golden_sets/invoice-unpaid-chatbot/
- evals/README.md

Task: add a storage-selectable invoice source to apps/mini_invoice_rag.

Requirements:
- Preserve current app behaviour and offline eval expectations.
- Keep CSV as the default deterministic local source unless the spec says otherwise.
- Add --invoice-store {csv,sqlite,postgres}, plus --sqlite-path and --postgres-dsn with env-var fallbacks (MINI_RAG_INVOICE_STORE, MINI_RAG_SQLITE_PATH, POSTGRES_DSN).
- Introduce an invoice store / data adapter abstraction instead of hardcoding CSV loading in retrieval.
- Keep LLM provider logic behind ollama_client.py.
- Apply RLS before retrieval context is ranked, summarized, or sent to Ollama.
- For SQLite, use the existing policies.py interpreter as the local RLS test double.
- For Postgres, use a DB-side RLS-protected table/view/RPC; never fetch denied rows and rely on prompts.
- Update tests and eval wiring as needed.
- Do not change golden sets unless a contract document explicitly changed expected behaviour.
- Run python .\evals\run_evals.py --offline before proposing a merge (py ... if python is unavailable).
```
