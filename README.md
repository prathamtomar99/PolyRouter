# PolyRouter

![Python](https://img.shields.io/badge/Python-3-blue)
![Architecture](https://img.shields.io/badge/Architecture-Config--Driven%20LLM%20Router-0A84FF)
![License](https://img.shields.io/badge/License-TBD-lightgrey)

PolyRouter is a lightweight Python library that routes requests across multiple LLM providers. It helps applications achieve deterministic failover by rotating API keys, client providers, and model candidates when requests fail.

## Overview

This repository provides an orchestration layer that can be embedded in your application to manage provider rotation, API-key pools, and model fallbacks. Keys are loaded from the environment (see `.env`), and the orchestrator tries configured provider/model/key combinations until a request succeeds or all combinations are exhausted.

Example provider adapters included in this snapshot:

- Groq
- Google Gemini
- Cerebras

## Badges

| Badge                                                                                           | Meaning                                |
| ----------------------------------------------------------------------------------------------- | -------------------------------------- |
| ![Python](https://img.shields.io/badge/Python-3-blue)                                           | Python implementation                  |
| ![Architecture](https://img.shields.io/badge/Architecture-Config--Driven%20LLM%20Router-0A84FF) | Multi-provider failover design         |
| ![License](https://img.shields.io/badge/License-TBD-lightgrey)                                  | Update once a formal license is chosen |

## Key Features

| Capability                | Technical Detail                                                                                                                 |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Provider rotation         | Requests can move across Groq, Gemini, and Cerebras client pools without changing application code.                              |
| Key pool management       | Each provider can be backed by multiple API keys, allowing the runtime to continue when a single key expires or is rate-limited. |
| Model pool fallback       | Ordered model lists in `config.py` act as a preference chain, so the router can try alternate models before surfacing a failure. |
| Debug visibility          | `DEBUG` and `IN_DEPTH_DEBUG` control log verbosity so you can switch between concise operational logs and deep request tracing.  |
| Centralized configuration | Provider counts, model lists, and debug mode live in one place instead of being duplicated across call sites.                    |
| Failure isolation         | Provider-specific errors do not have to terminate the entire workflow if another valid key/model combination is still available. |

## How It Works

```mermaid
flowchart TD
	A[Application request] --> B[Load config.py]
	B --> C[Load .env API keys]
	C --> D[Try primary provider]
	D --> E{Request succeeds?}
	E -->|Yes| F[Return response]
	E -->|No| G[Rotate key / model / client]
	G --> H{Any combinations left?}
	H -->|Yes| D
	H -->|No| I[Raise exhaustion error]
```

The intended behavior is simple:

1. Read provider preferences, model lists, and key counts from `config.py`.
2. Load API credentials from the environment.
3. Attempt a request with the active provider/model combination.
4. On provider failure, rotate through the next key or model.
5. When a provider pool is exhausted, move to the next client family.
6. Stop only when every configured combination has been tried.

> The repo is built for operational resilience, not for single-provider purity.

## Project Structure

```text
PolyRouter/
├── examples/                # Example usage scenarios
│   └── basic_usage.py
├── polyrouter/              # Library source
│   ├── Exceptions.py
│   ├── LLMClients.py
│   ├── LLMOrchestrator.py
│   └── __init__.py
├── .env                     # (example present in repo snapshot)
├── requirements-dev.txt     # Development / runtime deps
└── README.md
```

## Installation

Local setup (recommended):

```bash
git clone <repository-url>
cd PolyRouter
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Environment variables

This repo includes a `.env` file in the snapshot. In normal usage copy and populate a local `.env` (do not commit secrets):

```bash
cp .env .env.local
# edit .env.local and export provider API keys, e.g.:
# GROQ_API_KEY0=...
# GEMINI_API_KEY0=...
```

The examples use environment variables named like `GROQ_API_KEY0`, `GEMINI_API_KEY0`, etc.

### Dependencies

Dependencies used by examples and adapters may include provider SDKs and `python-dotenv`. Install via `requirements-dev.txt`.

<details>
<summary>Build / verification steps</summary>

This repository is a Python library-style project rather than a packaged service, so the essential validation step is import verification plus a smoke test in your host application.

```bash
python -m compileall .
python - <<'PY'
from config import DEBUG, IN_DEPTH_DEBUG, GROQ_MODEL
print("config loaded:", DEBUG, IN_DEPTH_DEBUG, GROQ_MODEL)
PY
```

</details>

## Configuration

`config.py` is the primary customization point.

| Setting          | Role                                                         |
| ---------------- | ------------------------------------------------------------ |
| `DEBUG`          | Enables the main debug statement stream.                     |
| `IN_DEPTH_DEBUG` | Enables detailed trace output for low-level troubleshooting. |
| `GROQ_MODEL`     | Ordered Groq model preference list.                          |
| `GEMINI_MODEL`   | Ordered Gemini model preference list.                        |
| `CEREBRAS_MODEL` | Ordered Cerebras model preference list.                      |
| `GROQ_KEY`       | Number of Groq API keys to scan.                             |
| `GEMINI_KEY`     | Number of Gemini API keys to scan.                           |
| `CEREBRAS_KEY`   | Number of Cerebras API keys to scan.                         |

Recommended operating model:

```python
DEBUG = 1
IN_DEPTH_DEBUG = 0

GROQ_MODEL = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"]
GEMINI_MODEL = ["gemini-2.5-flash"]
CEREBRAS_MODEL = ["gpt-oss-120b"]

GROQ_KEY = 2
GEMINI_KEY = 1
CEREBRAS_KEY = 1
```

## Usage

See `examples/basic_usage.py` for a minimal example. The orchestrator can be constructed directly in your application; you do not need a `config.py` file if you prefer to pass provider settings programmatically.

Minimal usage:

```python
from dotenv import load_dotenv
from polyrouter.LLMOrchestrator import LLMOrchestrator
import os

load_dotenv()

llm = LLMOrchestrator(
	groq={
		"groq_models": ["openai/gpt-oss-120b"],
		"groq_keys": [os.getenv("GROQ_API_KEY0")],
	},
	debug=True,
	verbose=True,
	prompt="You are a helpful assistant",
)

response = llm.request()
print(response)
```

When `debug`/`verbose` are enabled the orchestrator prints provider, model and key selection and rotation decisions.

## API / CLI

No standalone CLI or HTTP API is exposed in this repository snapshot.

The public surface is intentionally library-oriented:

- `config.py` controls behavior
- `LLMClients.py` defines the client abstraction
- `LLMOrchestrator.py` is the orchestration boundary

If you add a CLI later, document it here with exact command syntax and exit codes.

## Deployment

Because this project is a routing library, deployment usually means shipping it as part of a larger Python service or worker.

### Recommended deployment checklist

1. Pin dependencies with `requirements.txt`.
2. Inject secrets through the runtime environment, not source control.
3. Set `DEBUG = 0` and `IN_DEPTH_DEBUG = 0` for production unless you are actively diagnosing issues.
4. Validate all required API keys are present before starting the process.
5. Run the host service behind your preferred process manager, container runtime, or platform scheduler.

### Containerized deployment

If you package the project into a container, copy only the source files, install requirements, and mount secrets through environment variables or secret storage.

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "-c", "import config; print('LLM-Gateway-Service ready')"]
```

## Screenshots

> Screenshot placeholder: add an architecture diagram or runtime trace capture here once the project has a visual demo surface.

Suggested assets for a production repository:

- request-routing diagram
- provider rotation log snippet
- environment setup screenshot

## Troubleshooting

| Symptom                                | Likely Cause                                                 | Resolution                                                                 |
| -------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| Import error for a provider SDK        | Dependencies are missing from the active virtual environment | Re-run `pip install -r requirements.txt` inside the activated environment. |
| Requests stop after one provider fails | No fallback keys or models are configured                    | Add more keys to `.env` and expand the model pool in `config.py`.          |
| All requests fail immediately          | Environment variables are missing or misnamed                | Verify `.env` matches `.env.template` exactly.                             |
| Debug logs are too noisy               | Verbosity flags are enabled                                  | Set `DEBUG = 0` and `IN_DEPTH_DEBUG = 0` for normal operation.             |
| A specific model keeps failing         | The model is unsupported, rate-limited, or exhausted         | Remove it from the preference list or move it later in the rotation order. |

## Contributing

Contributions are welcome if they improve correctness, observability, or provider coverage.

Please keep pull requests focused and include:

- a concise description of the routing behavior being changed
- reproduction steps for any failure-handling update
- updates to `.env.template` and `config.py` when configuration contracts change
- tests or a clear validation checklist when the orchestration flow changes

Guidelines:

1. Do not hard-code secrets.
2. Preserve backward-compatible configuration names whenever possible.
3. Keep provider rotation behavior deterministic and well logged.
4. Prefer small, isolated changes to client adapters and error handling.

## Roadmap

Planned improvements that would strengthen the project further:

- formal public orchestration API with documented inputs and return types
- structured logging with request IDs and provider attempt history
- health checks for provider pools and exhausted key detection
- test coverage for failover, invalid-key handling, and model rotation
- optional CLI for smoke testing provider credentials
- metrics hooks for success rate, fallback rate, and exhaustion rate

## Acknowledgements

LLM-Gateway-Service builds on the ecosystem provided by:

- Groq
- Google Gemini / Google Gen AI SDK
- Cerebras Cloud SDK
- python-dotenv
- tenacity

It also follows a common open-source reliability pattern: fail over without forcing callers to understand vendor-specific error recovery.

## License

License: TBD.

Add the repository's chosen license here once it is finalized, and keep the license file in sync with this section.
