# AoS Standard Application v1

Schema-first, deterministic AoS runtime that executes **AoS Envelope Overlays** via a **vPort registry**.

## What you get (v1)
- JSON Schemas for:
  - Base agent contracts
  - Foreman / Librarian / Sorcerer / Judge / Messenger contracts
  - Envelope Overlay contract
  - Agent meta contract (v2.1)
- One runtime handler: `aos_runtime.base_agent.BaseAgent`
- A vPort registry loader: `registry/vports.registry.v1.jsonl`
- A CLI runner:
  - `aos-stdapp <path/to/envelope.json>`
- Deterministic run logs:
  - `run_logs/<task_id>/{envelope.json,response.json,run_record.json}`

## Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run examples
```bash
python -m aos_runtime.cli examples/envelopes/foreman_task.json
python -m aos_runtime.cli examples/envelopes/sorcerer_task.json
```

## Docker
```bash
docker build -t aos-stdapp:v1 .
docker run --rm -v "$PWD:/app" aos-stdapp:v1 examples/envelopes/foreman_task.json
```

## Notes
The included agent implementations are **safe stubs** (no external IO). In production, you wire:
- Librarian -> MCP/web/RAG layer
- Messenger -> email/sms/webhook/file writers
- Sorcerer -> your generation backend
- Judge -> schema+policy validators and quality gates

The runtime remains identical: validate -> run -> validate -> log.


## Web Envelope Builder (static)

Open `web/index.html` in a browser to generate a schema-valid `aos.envelope.overlay.v1` JSON file.

- **Download envelope**: a plain envelope JSON.
- **Download bundle**: `{ "envelope": {..}, "agent_profiles": {..} }`.

The CLI runner accepts either format:

```bash
python -m aos_runtime.cli path/to/task_envelope_*.json
python -m aos_runtime.cli path/to/aos_bundle_*.json
```

Note: in v1, `agent_profiles` are saved to `run_logs/agent_profiles.json` for audit/debug but are not enforced as runtime policy.
