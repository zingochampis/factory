# Builder Agent Contract

This repo may be edited by different builder LLMs, including Codex and Claude.
The app generator is replaceable; the factory contracts are the stable source
of truth.

Before changing application behavior, read:

1. `usecases/invoice-unpaid-chatbot/usecase.spec.md`
2. `usecases/invoice-unpaid-chatbot/usecase.spec.yaml`
3. `governance/data_contracts/invoice_lines.schema.yaml`
4. `governance/semantic_layer/invoice_lines.semantic.yaml`
5. `governance/security/rls_policies.yaml`
6. `golden_sets/invoice-unpaid-chatbot/`
7. `evals/README.md`

Rules for builder agents:

- Do not bypass RLS in app code, tests, evals, or prompts.
- Do not make the app depend on one generator, framework, or model provider.
- Keep LLM provider logic behind an adapter.
- Update golden sets when pilot feedback changes expected behavior.
- Update the use case spec when business intent, risk, data, or release
  criteria change.
- Run `python .\evals\run_evals.py --offline` before proposing a merge.
  On Windows without `python` on PATH, run `py .\evals\run_evals.py --offline`.
