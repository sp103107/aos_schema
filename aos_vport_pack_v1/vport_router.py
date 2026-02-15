from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from jsonschema import Draft7Validator


@dataclass
class RegistryEntry:
    vport: str
    call_type: str
    target: Dict[str, Any]
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    default_timeout_ms: int = 30000
    enabled: bool = True
    raw: Dict[str, Any] = None


class VPortRouterError(Exception):
    pass


class VPortNotFoundError(VPortRouterError):
    pass


class VPortDisabledError(VPortRouterError):
    pass


class VPortExecutionError(VPortRouterError):
    pass


class VPortRouter:
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        registry_path: Optional[Path] = None,
        schema_dir: Optional[Path] = None,
    ) -> None:
        self.base_dir = base_dir or Path(__file__).parent
        self.config_dir = self.base_dir / "config"
        self.schemas_dir = schema_dir or (self.base_dir / "schemas" / "vport")

        self.registry_path = registry_path or (
            self.config_dir / "vports.registry.v1.jsonl"
        )

        self._schema_registry_entry = self._load_schema(
            "vport.registry_entry.schema.v1.json"
        )
        self._schema_call = self._load_schema("vport.call.schema.v1.json")
        self._schema_result = self._load_schema("vport.result.schema.v1.json")

        self._validator_registry_entry = Draft7Validator(
            self._schema_registry_entry
        )
        self._validator_call = Draft7Validator(self._schema_call)
        self._validator_result = Draft7Validator(self._schema_result)

        self._registry: Dict[str, RegistryEntry] = {}
        self._load_registry()

    def _load_schema(self, filename: str) -> Dict[str, Any]:
        path = self.schemas_dir / filename
        if not path.exists():
            raise RuntimeError(f"Schema not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_registry(self) -> None:
        if not self.registry_path.exists():
            raise RuntimeError(f"Registry file not found: {self.registry_path}")

        registry: Dict[str, RegistryEntry] = {}
        with self.registry_path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        f"Invalid JSON on line {lineno} of {self.registry_path}: {e}"
                    ) from e

                errors = sorted(
                    self._validator_registry_entry.iter_errors(data),
                    key=lambda e: e.path,
                )
                if errors:
                    msg = "; ".join(
                        [f"{'/'.join(str(p) for p in err.path)}: {err.message}"
                         for err in errors]
                    )
                    raise RuntimeError(
                        f"Registry entry on line {lineno} is invalid: {msg}"
                    )

                entry = RegistryEntry(
                    vport=data["vport"],
                    call_type=data["call_type"],
                    target=data["target"],
                    description=data.get("description"),
                    tags=data.get("tags"),
                    default_timeout_ms=data.get("default_timeout_ms", 30000),
                    enabled=data.get("enabled", True),
                    raw=data,
                )

                registry[entry.vport] = entry

        self._registry = registry

    def list_vports(self) -> List[str]:
        return sorted(self._registry.keys())

    def get_entry(self, vport: str) -> RegistryEntry:
        try:
            entry = self._registry[vport]
        except KeyError as e:
            raise VPortNotFoundError(f"Unknown vPort: {vport}") from e

        if not entry.enabled:
            raise VPortDisabledError(f"vPort is disabled: {vport}")

        return entry

    def call_vport(self, call_envelope: Dict[str, Any]) -> Dict[str, Any]:
        errors = sorted(
            self._validator_call.iter_errors(call_envelope),
            key=lambda e: e.path,
        )
        if errors:
            msg = "; ".join(
                [f"{'/'.join(str(p) for p in err.path)}: {err.message}"
                 for err in errors]
            )
            raise VPortRouterError(f"Invalid vPort call envelope: {msg}")

        vport = call_envelope["vport"]
        payload = call_envelope.get("payload", {})
        request_id = call_envelope.get("request_id")
        options = call_envelope.get("options", {}) or {}
        timeout_ms = options.get("timeout_ms")

        entry = self.get_entry(vport)
        effective_timeout_ms = timeout_ms or entry.default_timeout_ms

        start_time = time.monotonic()
        try:
            if entry.call_type == "python":
                output = self._execute_python(entry, payload, effective_timeout_ms)
            elif entry.call_type == "bin":
                output = self._execute_bin(entry, payload, effective_timeout_ms)
            elif entry.call_type == "http":
                output = self._execute_http(entry, payload, effective_timeout_ms)
            elif entry.call_type == "mcp":
                raise VPortExecutionError(
                    f"MCP call_type not implemented for vPort: {vport}"
                )
            else:
                raise VPortExecutionError(
                    f"Unsupported call_type '{entry.call_type}' for vPort: {vport}"
                )

            status = "success"
            error_obj = None
        except VPortExecutionError as e:
            status = "error"
            output = {}
            error_obj = {
                "message": str(e),
                "code": "EXECUTION_ERROR",
                "details": {}
            }
        except Exception as e:
            status = "error"
            output = {}
            error_obj = {
                "message": f"Unexpected error: {e}",
                "code": "UNEXPECTED_ERROR",
                "details": {}
            }

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        result_envelope: Dict[str, Any] = {
            "request_id": request_id,
            "vport": vport,
            "status": status,
            "output": output,
            "error": error_obj,
            "meta": {
                "elapsed_ms": elapsed_ms,
                "call_type": entry.call_type
            }
        }

        errors = sorted(
            self._validator_result.iter_errors(result_envelope),
            key=lambda e: e.path,
        )
        if errors:
            msg = "; ".join(
                [f"{'/'.join(str(p) for p in err.path)}: {err.message}"
                 for err in errors]
            )
            raise VPortRouterError(
                f"vPort result envelope failed schema validation: {msg}"
            )

        return result_envelope

    def _execute_python(
        self,
        entry: RegistryEntry,
        payload: Dict[str, Any],
        timeout_ms: int,
    ) -> Dict[str, Any]:
        module_path = entry.target.get("python_module")
        handler_name = entry.target.get("python_handler")

        if not module_path or not handler_name:
            raise VPortExecutionError(
                f"Missing python_module or python_handler for vPort: {entry.vport}"
            )

        try:
            module = import_module(module_path)
        except ImportError as e:
            raise VPortExecutionError(
                f"Failed to import module '{module_path}' for vPort {entry.vport}: {e}"
            ) from e

        handler = getattr(module, handler_name, None)
        if handler is None or not callable(handler):
            raise VPortExecutionError(
                f"Handler '{handler_name}' not found or not callable in module '{module_path}'"
            )

        result = handler(payload)
        if not isinstance(result, dict):
            raise VPortExecutionError(
                f"Python handler for vPort {entry.vport} returned non-dict: {type(result)}"
            )

        return result

    def _execute_bin(
        self,
        entry: RegistryEntry,
        payload: Dict[str, Any],
        timeout_ms: int,
    ) -> Dict[str, Any]:
        bin_command = entry.target.get("bin_command")
        args_template = entry.target.get("bin_args_template", [])

        if not bin_command:
            raise VPortExecutionError(
                f"Missing bin_command for vPort: {entry.vport}"
            )

        payload_json = json.dumps(payload)
        args: List[str] = []
        for item in args_template:
            if "{payload_json}" in item:
                args.append(item.replace("{payload_json}", payload_json))
            else:
                args.append(item)

        cmd = [bin_command] + args

        try:
            completed = subprocess.run(
                cmd,
                input=None,
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000.0,
            )
        except subprocess.TimeoutExpired as e:
            raise VPortExecutionError(
                f"Binary command timed out for vPort {entry.vport}: {e}"
            ) from e
        except OSError as e:
            raise VPortExecutionError(
                f"Failed to execute binary for vPort {entry.vport}: {e}"
            ) from e

        if completed.returncode != 0:
            raise VPortExecutionError(
                f"Binary returned non-zero exit code {completed.returncode} "
                f"for vPort {entry.vport}: {completed.stderr.strip()}"
            )

        stdout = completed.stdout.strip()
        try:
            parsed = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            parsed = {"stdout": stdout}

        return parsed

    def _execute_http(
        self,
        entry: RegistryEntry,
        payload: Dict[str, Any],
        timeout_ms: int,
    ) -> Dict[str, Any]:
        method = entry.target.get("http_method")
        url_template = entry.target.get("http_url_template")
        headers_template = entry.target.get("http_headers_template", {})

        if not method or not url_template:
            raise VPortExecutionError(
                f"Missing http_method or http_url_template for vPort: {entry.vport}"
            )

        payload_json = json.dumps(payload)
        url = url_template.replace("{payload_json}", payload_json)

        headers = dict(headers_template or {})
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=payload_json if method in ("POST", "PUT", "PATCH") else None,
                timeout=timeout_ms / 1000.0,
            )
        except requests.RequestException as e:
            raise VPortExecutionError(
                f"HTTP request failed for vPort {entry.vport}: {e}"
            ) from e

        try:
            body = resp.json()
        except ValueError:
            body = {"text": resp.text}

        if not resp.ok:
            raise VPortExecutionError(
                f"HTTP {resp.status_code} for vPort {entry.vport}: {body}"
            )

        if not isinstance(body, dict):
            body = {"response": body}

        return body
