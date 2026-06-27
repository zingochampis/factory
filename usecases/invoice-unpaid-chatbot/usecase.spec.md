# Use Case Spec: Invoice Unpaid Chatbot

Version: 0.1.0

This document is the contract between business intent, governed data,
generated application code, and measurable release quality.

## Intent

Build a small chatbot that answers questions about unpaid invoice lines using
governed invoice data. The chatbot must answer only from visible data, cite
invoice ids, and refuse requests that try to bypass policy.

## Users

- `finance_all` can see all pilot fixture rows.
- `finance_se` can see non-confidential Sweden rows.
- `finance_de` can see non-confidential Germany rows.
- `sales_acme` can see non-confidential Acme rows.
- `external_viewer` has no direct invoice-line access.

## Data

The pilot fixture is:

`golden_sets/invoice-unpaid-chatbot/fake_data/invoice_lines.csv`

The data contract is:

`governance/data_contracts/invoice_lines.schema.yaml`

## Behavior

The app must:

- apply RLS before retrieval
- answer from retrieved context only
- cite `invoice_id` values
- say when no accessible matching rows were found
- refuse bypass, hidden-data, bank-detail, or personal-data requests

The app must not:

- show rows denied by RLS
- infer facts absent from the data
- mutate invoice data
- promise payment or collection actions

## Release Quality

The release candidate is acceptable when:

- golden question pass rate is 100 percent
- RLS case pass rate is 100 percent
- refusal case pass rate is 100 percent
- no answer contains a forbidden invoice id
- local Ollama testing with `ministral-3:3b` has no obvious prompt-format breakage

## Replaceability

The app may move from Python CLI to a web app, from Ollama to another model, or
from this retriever to a vector database. Such changes should not alter the
meaning of unpaid invoices, RLS behavior, or golden expected outcomes unless
the governance artifacts and use case spec are updated first.

