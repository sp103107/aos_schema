#!/usr/bin/env python3
"""
unify_tools.py — AoS Tools Bootstrap v2

What it does
- Scans an inbox directory for candidate tool roots
- Groups tool roots into batches (default size 25)
- Produces a REVIEW report (JSON + JSONL per file/root)
- Writes PROPOSED registry entries (does not modify live catalogs unless --apply)

Design constraints
- No hallucinated fields: only writes to registries using schema-locked formats
- Mobile-callable: can be wrapped by HTTP or MCP or vPort
- Deterministic: stable sorting + sha256 tree hashes

Usage
  python scripts/unify_tools.py --scan-root inbox --batch-size 25
  python scripts/unify_tools.py --scan-root inbox --batch-size 25 --apply
"""
from __future__ import annotations

import argparse, json, hashlib, os
from pathlib import Path
from datetime import datetime

SIGNAL_FILES = [
  ("pyproject.toml", "python_module"),
  ("requirements.txt", "python_module"),
  ("setup.py", "python_module"),
  ("package.json", "node_module"),
  ("Pipfile", "python_module"),
  ("Dockerfile", "http_service"),
  ("main.py", "python_module"),
  ("app.py", "python_module"),
  ("index.js", "node_module"),
  ("README.md", "document_only"),
]

def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_tree(root: Path) -> str:
    """Hash of (relative_path + file_sha256) over all files, sorted."""
    items = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(root)).replace("\\", "/")
            items.append((rel, sha256_file(p)))
    payload = "\n".join([f"{rel}\t{h}" for rel, h in items]).encode("utf-8")
    return sha256_bytes(payload)

def detect_tool_root(dir_path: Path) -> tuple[bool, dict]:
    signals = []
    kind = "document_only"
    entry_hint = ""
    for fname, k in SIGNAL_FILES:
        if (dir_path / fname).exists():
            signals.append(fname)
            # first strong signal wins (but keep collecting)
            if kind == "document_only" and k != "document_only":
                kind = k
            if not entry_hint and fname in ("main.py","app.py","index.js"):
                entry_hint = fname
    if not signals:
        return False, {}
    if not entry_hint:
        # fallback entrypoints
        if (dir_path/"pyproject.toml").exists() or (dir_path/"requirements.txt").exists():
            entry_hint = "python -m <module> (to be set)"
        elif (dir_path/"package.json").exists():
            entry_hint = "node <entry> (to be set)"
        else:
            entry_hint = "README.md"
    return True, {"kind": kind, "entrypoint_hint": entry_hint, "signals": signals}

def write_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_jsonl(path: Path, records: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-root", default="inbox")
    ap.add_argument("--batch-size", type=int, default=25)
    ap.add_argument("--apply", action="store_true", help="Apply proposed entries to live registries (append).")
    ap.add_argument("--repo-root", default=".", help="Path to repo root (where registry/ and state/ exist).")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    scan_root = (repo_root / args.scan_root).resolve()

    out_review_json = repo_root / "state" / "review_report.json"
    out_review_jsonl = repo_root / "state" / "review_report.jsonl"
    proposed_tools = repo_root / "registry" / "tools_catalog.proposed.jsonl"
    proposed_vports = repo_root / "registry" / "vport_registry.proposed.jsonl"
    proposed_batch_plan = repo_root / "registry" / "batch_plan.proposed.jsonl"

    findings: list[str] = []
    file_count = 0
    dir_count = 0

    if not scan_root.exists():
        findings.append(f"scan_root missing: {scan_root}")
        scan_root.mkdir(parents=True, exist_ok=True)
        findings.append("scan_root created. Place tool folders under inbox/ and rerun.")

    # Strategy: treat each top-level directory under scan_root as a candidate tool root.
    tool_roots = []
    for child in sorted(scan_root.iterdir(), key=lambda p: p.name.lower()):
        if child.is_dir():
            dir_count += 1
            ok, meta = detect_tool_root(child)
            if ok:
                tool_roots.append((child, meta))
        elif child.is_file():
            file_count += 1

    # Batch tool roots
    batches = []
    for i in range(0, len(tool_roots), args.batch_size):
        chunk = tool_roots[i:i+args.batch_size]
        batches.append({
            "batch_id": f"batch_{i//args.batch_size:03d}",
            "index": i//args.batch_size,
            "size": len(chunk),
            "tool_roots": [str(p.relative_to(repo_root)).replace("\\","/") for p,_ in chunk]
        })

    # Per-root records (batch plan entries)
    batch_plan_entries = []
    for batch in batches:
        bid = batch["batch_id"]
        for rel in batch["tool_roots"]:
            abs_root = repo_root / rel
            # re-detect to keep stable
            ok, meta = detect_tool_root(abs_root)
            tree_hash = sha256_tree(abs_root) if ok else ""
            batch_plan_entries.append({
                "id": f"batch_plan.{bid}.{abs_root.name}",
                "type": "aos.batch_plan_entry",
                "created_at": utc_now(),
                "batch_id": bid,
                "tool_root": rel,
                "detected": {
                    "kind": meta.get("kind","document_only"),
                    "entrypoint_hint": meta.get("entrypoint_hint",""),
                    "signals": meta.get("signals",[]),
                },
                "sha256_tree": tree_hash,
                "status": "planned"
            })

    # Proposed tool catalog entries (minimal skeletons; user fills details later)
    tool_records = []
    for root, meta in tool_roots:
        tool_records.append({
            "id": f"tool.{root.name}.v1",
            "type": "aos.tool_record",
            "created_at": utc_now(),
            "name": root.name,
            "kind": meta["kind"],
            "entrypoint": f"{args.scan_root}/{root.name}/{meta['entrypoint_hint']}",
            "capabilities": [],
            "interfaces": {"mcp": None, "vport": None, "http": None},
            "versioning": {"semver": "0.0.0", "api_version": "v1"},
            "status": "planned"
        })

    # Proposed vport entries (none by default; requires explicit mapping later)
    vport_records = [{
        "id":"vport_registry.proposed.meta",
        "type":"aos.vport_registry_proposed_meta",
        "created_at": utc_now(),
        "notes":"No vports auto-created. Add explicit vport mapping per tool when ready."
    }]

    report = {
        "id": "review_report.v1",
        "type": "aos.review_report",
        "created_at": utc_now(),
        "scan_root": str(scan_root).replace("\\","/"),
        "summary": {
            "files_total": file_count,
            "dirs_total": dir_count,
            "tool_candidates": len(tool_roots),
            "tool_roots": len(tool_roots),
            "errors": 0
        },
        "batches": batches,
        "findings": findings if findings else (["No tool folders found under inbox/."] if len(tool_roots)==0 else []),
        "outputs": {
            "review_report_json": str(out_review_json.relative_to(repo_root)).replace("\\","/"),
            "review_report_jsonl": str(out_review_jsonl.relative_to(repo_root)).replace("\\","/"),
            "proposed_tools_catalog_jsonl": str(proposed_tools.relative_to(repo_root)).replace("\\","/"),
            "proposed_vport_registry_jsonl": str(proposed_vports.relative_to(repo_root)).replace("\\","/")
        }
    }

    # Write outputs
    write_json(out_review_json, report)
    # JSONL detail: first line = report header, then each batch_plan entry
    jsonl_records = [{"type":"aos.review_report_header","created_at": report["created_at"], "scan_root": report["scan_root"], "tool_roots": report["summary"]["tool_roots"]}]
    jsonl_records.extend(batch_plan_entries)
    write_jsonl(out_review_jsonl, jsonl_records)

    write_jsonl(proposed_tools, tool_records if tool_records else [{
        "id":"tools_catalog.proposed.meta",
        "type":"aos.tools_catalog_proposed_meta",
        "created_at": utc_now(),
        "notes":"No tools detected. Add tool folders to inbox/ and rerun."
    }])
    write_jsonl(proposed_vports, vport_records)
    write_jsonl(proposed_batch_plan, batch_plan_entries if batch_plan_entries else [{
        "id":"batch_plan.proposed.meta",
        "type":"aos.batch_plan_proposed_meta",
        "created_at": utc_now(),
        "notes":"No tool roots detected."
    }])

    if args.apply:
        # Append proposed tools to live catalogs (append-only)
        live_tools = repo_root / "registry" / "tools_catalog.jsonl"
        live_batch = repo_root / "registry" / "batch_plan.jsonl"
        # Read existing to keep meta line(s) and append
        with open(live_tools, "a", encoding="utf-8") as f:
            for r in tool_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(live_batch, "a", encoding="utf-8") as f:
            for r in batch_plan_entries:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
