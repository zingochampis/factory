# Golden Sets: Invoice Unpaid Chatbot

This folder contains executable truth for the mini use case.

- `fake_data/invoice_lines.csv` is the governed pilot fixture.
- `questions.json` contains expected answer behavior.
- `rls_cases.json` contains row-level access expectations.
- `refusal_cases.json` contains requests the app must refuse.

Golden sets are business assets. Update them when the domain understanding
changes, not merely to make a weak app pass.

