# AoS Watcher + Optional API (v1)

This addon gives you two ways to "drop an envelope and run":

## 1) Folder Watcher (no server required)
- Drop `*.json` into `inbox/`
- It moves files through: `processing/` -> `done/` or `failed/`
- Writes logs to `logs/`
- Optionally writes CLI stdout to `outbox/`

## 2) Optional HTTP API (FastAPI)
- POST /submit to upload an envelope/bundle JSON
- The API saves the file into `inbox/` so the same watcher processes it
- GET /status/{id}
- GET /result/{id}

## Install
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# mac/linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Run watcher
```bash
python watcher/watcher.py --root .
```

## Run API (optional)
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8787
```

## Configure
Edit `config/watcher_config.json`:
- `watch_dir`: where envelopes are dropped (default: inbox)
- `runner_mode`: "cli" (default) or "module"
- `cli_command`: command used when runner_mode="cli"

### Using with your AoS runtime
If your AoS runtime package lives next to this folder:
- Put this folder at the repo root
- Ensure `python -m aos_runtime.cli <path>` works from that root
- Keep `runner_mode: "cli"`.

If you prefer to import your runner as a module, set:
- `runner_mode: "module"`
- and fill `module_entrypoint` (see config file comments).
