"""
AoS Watcher v1
- Watches a directory for new JSON files (envelopes or bundles)
- Moves them through a deterministic pipeline:
    inbox -> processing -> done|failed
- Executes AoS runner either via CLI or module import
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Queue, Empty
from typing import Any, Dict, List, Optional, Tuple

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def _now_stamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _safe_id(s: str) -> str:
    return "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in s)[:120] or "item"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs(root: Path, names: List[str]) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for n in names:
        p = root / n
        p.mkdir(parents=True, exist_ok=True)
        out[n] = p
    return out


@dataclass
class WatcherConfig:
    watch_dir: str
    processing_dir: str
    done_dir: str
    failed_dir: str
    outbox_dir: str
    logs_dir: str
    file_glob: str
    debounce_ms: int
    runner_mode: str
    cli_command: List[str]
    module_entrypoint: Dict[str, Any]
    write_stdout_to_outbox: bool
    max_parallel: int

    @staticmethod
    def from_file(path: Path) -> "WatcherConfig":
        data = load_json(path)
        return WatcherConfig(
            watch_dir=data["watch_dir"],
            processing_dir=data["processing_dir"],
            done_dir=data["done_dir"],
            failed_dir=data["failed_dir"],
            outbox_dir=data["outbox_dir"],
            logs_dir=data["logs_dir"],
            file_glob=data.get("file_glob", "*.json"),
            debounce_ms=int(data.get("debounce_ms", 350)),
            runner_mode=data.get("runner_mode", "cli"),
            cli_command=list(data.get("cli_command", ["python", "-m", "aos_runtime.cli"])),
            module_entrypoint=dict(data.get("module_entrypoint", {})),
            write_stdout_to_outbox=bool(data.get("write_stdout_to_outbox", True)),
            max_parallel=int(data.get("max_parallel", 1)),
        )


class DebouncedEventHandler(FileSystemEventHandler):
    """
    Watchdog fires multiple events per write. We debounce to only enqueue once.
    """
    def __init__(self, watch_path: Path, queue: Queue, debounce_ms: int, file_glob: str):
        super().__init__()
        self.watch_path = watch_path
        self.queue = queue
        self.debounce_s = debounce_ms / 1000.0
        self.file_glob = file_glob
        self._last_seen: Dict[Path, float] = {}

    def on_created(self, event):
        if event.is_directory:
            return
        self._maybe_enqueue(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory:
            return
        self._maybe_enqueue(Path(event.dest_path))

    def on_modified(self, event):
        if event.is_directory:
            return
        self._maybe_enqueue(Path(event.src_path))

    def _maybe_enqueue(self, path: Path):
        try:
            if not path.match(self.file_glob):
                return
            if path.parent.resolve() != self.watch_path.resolve():
                return
            now = time.time()
            last = self._last_seen.get(path, 0.0)
            if (now - last) < self.debounce_s:
                return
            self._last_seen[path] = now
            # Give the writer a moment to finish flushing
            time.sleep(self.debounce_s)
            if path.exists() and path.stat().st_size > 0:
                self.queue.put(path)
        except Exception:
            # Never crash the watcher on handler errors
            return


def run_via_cli(cli_command: List[str], file_path: Path, cwd: Path) -> Tuple[int, str, str]:
    cmd = list(cli_command) + [str(file_path)]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_via_module(entry: Dict[str, Any], file_path: Path) -> Tuple[int, str, str]:
    """
    Import module + callable; call with file path. Convention:
      callable(path=<file_path>) -> dict|str|None
    """
    mod_name = entry["module"]
    fn_name = entry["callable"]
    args_cfg = entry.get("args", {})
    path_arg_name = args_cfg.get("path_arg_name", "path")

    mod = __import__(mod_name, fromlist=[fn_name])
    fn = getattr(mod, fn_name)

    kwargs = {path_arg_name: str(file_path)}
    try:
        result = fn(**kwargs)
        if result is None:
            return 0, "", ""
        if isinstance(result, str):
            return 0, result, ""
        return 0, json.dumps(result, indent=2), ""
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def write_log(logs_dir: Path, base_name: str, stdout: str, stderr: str) -> Path:
    log_path = logs_dir / f"{base_name}_{_now_stamp()}.log.txt"
    with log_path.open("w", encoding="utf-8") as f:
        if stdout:
            f.write("=== STDOUT ===\n")
            f.write(stdout)
            f.write("\n\n")
        if stderr:
            f.write("=== STDERR ===\n")
            f.write(stderr)
            f.write("\n")
    return log_path


def write_outbox(outbox_dir: Path, base_name: str, stdout: str) -> Optional[Path]:
    if not stdout.strip():
        return None
    out_path = outbox_dir / f"{base_name}_{_now_stamp()}.out.json"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(stdout)
    return out_path


def derive_base_name(json_path: Path) -> str:
    # Try to parse id from envelope/bundle to create stable filenames
    try:
        obj = load_json(json_path)
        env = obj.get("envelope", obj) if isinstance(obj, dict) else obj
        if isinstance(env, dict):
            task_id = env.get("id") or env.get("task_id") or ""
            if task_id:
                return _safe_id(str(task_id))
    except Exception:
        pass
    return _safe_id(json_path.stem)


def process_one(
    cfg: WatcherConfig,
    root: Path,
    dirs: Dict[str, Path],
    incoming_path: Path,
) -> None:
    base_name = derive_base_name(incoming_path)
    processing_path = dirs[cfg.processing_dir] / incoming_path.name

    # Move into processing for atomicity (and to avoid double-processing)
    try:
        shutil.move(str(incoming_path), str(processing_path))
    except FileNotFoundError:
        return

    rc = 1
    stdout = ""
    stderr = ""
    try:
        if cfg.runner_mode == "module":
            rc, stdout, stderr = run_via_module(cfg.module_entrypoint, processing_path)
        else:
            rc, stdout, stderr = run_via_cli(cfg.cli_command, processing_path, cwd=root)
    except Exception as e:
        rc = 1
        stderr = f"{type(e).__name__}: {e}"

    # Always log
    write_log(dirs[cfg.logs_dir], base_name, stdout, stderr)

    # Optional outbox
    if cfg.write_stdout_to_outbox:
        write_outbox(dirs[cfg.outbox_dir], base_name, stdout)

    # Move to done/failed
    target_dir = dirs[cfg.done_dir] if rc == 0 else dirs[cfg.failed_dir]
    final_path = target_dir / processing_path.name
    try:
        shutil.move(str(processing_path), str(final_path))
    except Exception:
        # If move fails, at least keep it in processing so you can inspect
        pass


def worker_loop(cfg: WatcherConfig, root: Path, dirs: Dict[str, Path], q: Queue, stop_evt: threading.Event):
    while not stop_evt.is_set():
        try:
            path = q.get(timeout=0.25)
        except Empty:
            continue
        try:
            process_one(cfg, root, dirs, path)
        finally:
            q.task_done()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Project root (where inbox/ lives)")
    ap.add_argument("--config", default="config/watcher_config.json")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg = WatcherConfig.from_file(root / args.config)

    dirs = ensure_dirs(root, [
        cfg.watch_dir,
        cfg.processing_dir,
        cfg.done_dir,
        cfg.failed_dir,
        cfg.outbox_dir,
        cfg.logs_dir,
    ])

    q: Queue = Queue()
    stop_evt = threading.Event()

    # Start workers
    workers: List[threading.Thread] = []
    for _ in range(max(1, cfg.max_parallel)):
        t = threading.Thread(target=worker_loop, args=(cfg, root, dirs, q, stop_evt), daemon=True)
        t.start()
        workers.append(t)

    handler = DebouncedEventHandler(dirs[cfg.watch_dir], q, cfg.debounce_ms, cfg.file_glob)
    observer = Observer()
    observer.schedule(handler, str(dirs[cfg.watch_dir]), recursive=False)
    observer.start()

    print(f"[AoS Watcher] Watching: {dirs[cfg.watch_dir]}")
    print(f"[AoS Watcher] Runner mode: {cfg.runner_mode}")
    print("[AoS Watcher] Drop .json files into inbox/ to run.")
    try:
        while True:
            time.sleep(0.75)
    except KeyboardInterrupt:
        print("\n[AoS Watcher] Shutting down...")
    finally:
        stop_evt.set()
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
