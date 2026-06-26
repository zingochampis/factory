# Invoice Lineage

Pilot fixture lineage:

1. `golden_sets/invoice-unpaid-chatbot/fake_data/invoice_lines.csv`
2. Loaded by `apps/mini_invoice_rag/src/mini_rag/data_loader.py`
3. Filtered by `apps/mini_invoice_rag/src/mini_rag/policies.py`
4. Retrieved by `apps/mini_invoice_rag/src/mini_rag/retriever.py`
5. Answered by either the offline synthesizer or Ollama adapter
6. Evaluated by `evals/run_evals.py`

Production lineage placeholder:

- Source ERP table
- Curated invoice mart
- Governed semantic layer
- RLS policy service
- RAG retrieval index
- App runtime
- Audit sink

