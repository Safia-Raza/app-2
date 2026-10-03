# BuildPay AI — Construction Payment Review Workforce

A beginner-friendly CrewAI + Groq + Streamlit prototype for construction payment review.

## Important design rule

The agents analyze evidence, calculate, reconcile and flag exceptions. They do **not** release money, call an ERP payment API, approve a payment, or make the final decision.

## Agents

1. Intake & Evidence
2. Contract Compliance
3. Measurement & Valuation
4. Payment Reconciliation
5. Risk & Exceptions
6. Human Review Brief

Each agent is in its own Python file.

## Tools

The agents use CrewAI tools for:

- Reading uploaded PDF/DOCX/XLSX/CSV/TXT/MD documents
- Payment arithmetic
- Required-document checks
- Audit-event recording

## Deployment

This repository is designed for Streamlit Community Cloud.

Set this secret:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Main entrypoint:

```text
app.py
```

Python version:

```text
3.12
```

The project pins the core package versions in `requirements.txt`.

The model is configured through CrewAI's Groq/LiteLLM provider route using `groq/openai/gpt-oss-120b`; the standalone `groq` package is included for compatibility with the Groq SDK ecosystem.
