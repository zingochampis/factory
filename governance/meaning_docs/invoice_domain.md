# Invoice Domain Notes

The pilot chatbot helps internal users answer questions about unpaid invoice
lines. It is not a payment system and must not mutate invoice data.

Key domain meanings:

- "Unpaid" means status `unpaid` or `overdue`.
- "Overdue" means unpaid and past the due date.
- "Amount due" is the remaining amount for a line, shown with currency.
- "Visible" always means visible after row-level security filtering.
- A user asking for "all invoices" still only gets all invoices they are
  allowed to see.

The assistant should be boring and precise. It should prefer a short factual
answer with citations over broad narrative.

