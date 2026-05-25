# PolyRouter

**Deterministic failover and rotation for Large Language Models.**

PolyRouter is a lightweight Python library that routes requests across multiple LLM providers (like Groq, Google Gemini, and Cerebras). It helps applications achieve operational resilience by automatically rotating API keys, client providers, and model candidates when requests fail or get rate-limited.

## Key Features

* **Provider Rotation:** Seamlessly failover between different LLM providers (e.g., Groq → Gemini).
* **Key Pool Management:** Attach multiple API keys to a single provider to survive rate limits and expirations.
* **Model Fallback:** Define a preference chain of models to try before surfacing a failure to the user.
* **Zero App-Code Changes:** Handle complex failover logic at the orchestration layer, keeping your application logic clean.

## Installation

```bash
pip install polyrouter
```

## Project Contribution
This project is a Open Source Project, users add/contribute by adding more client as per requirement.
```
https://github.com/prathamtomar99/PolyRouter
```