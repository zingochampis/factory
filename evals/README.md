# Eval Gate

`run_evals.py` is the executable merge gate for the mini factory.

It checks:

- golden question behavior
- RLS visibility
- refusal behavior
- forbidden citations

The default CI mode is deterministic and offline:

```powershell
python .\evals\run_evals.py --offline
```

On Windows without `python` on PATH:

```powershell
py .\evals\run_evals.py --offline
```

Local model smoke mode can use Ollama:

```powershell
$env:OLLAMA_MODEL = "ministral-3:3b"
python .\evals\run_evals.py
```

The offline eval should remain stable even if the LLM provider, app framework,
or retrieval implementation changes.
