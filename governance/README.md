# Governance Layer

This folder contains the persistent context that the RAG app must obey.

The governance layer is not an implementation detail of the Python app. It is
the contract between business intent, governed data, generated app code, and
measurable release quality.

Subfolders:

- `data_contracts/` - source tables and column-level meaning.
- `semantic_layer/` - business definitions and synonyms.
- `security/` - row-level access rules.
- `access_contracts/` - what an LLM-facing app may read and return.
- `meaning_docs/` - LLM-readable domain explanations.
- `lineage/` - source and transformation notes.
- `audit/` - event schema for runtime traces and governance review.

