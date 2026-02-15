"""
Run validation for v4 + v5 + v5.1 schemas and examples using tools/validate_schema.py.
"""
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))
VALIDATOR = os.path.join(ROOT, "tools", "validate_schema.py")


def run(args):
    completed = subprocess.run(
        [sys.executable, VALIDATOR, *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip())
    if completed.returncode != 0:
        sys.exit(completed.returncode)


def main():
    run(["--schema", "schemas/master/aos.master.meta.v4.schema.json"])
    run(["--schema", "schemas/envelope/aos.master.envelope.v4.schema.json"])
    run(["--schema", "schemas/temporal/aos.scene.v4.schema.json"])
    run(["--schema", "schemas/master/aos.master.meta.v5.schema.json"])
    run([
        "--schema",
        "schemas/envelope/aos.master.envelope.v5.schema.json",
        "--example",
        "examples/aos.master.envelope.v5.task_request.example.json",
    ])
    run(["--schema", "schemas/temporal/aos.scene.v5.schema.json"])
    run([
        "--schema",
        "schemas/aos.schema_pack.manifest.v1.schema.json",
        "--example",
        "examples/aos.schema_pack.manifest.v1.example.json",
    ])
    run([
        "--schema",
        "schemas/aos.validation_report.v1.schema.json",
        "--example",
        "examples/aos.validation_report.v1.example.json",
    ])
    run(["--schema", "schemas/master/aos.master.meta.v5_1.schema.json"])
    run([
        "--schema",
        "schemas/envelope/aos.master.envelope.v5_1.schema.json",
        "--example",
        "examples/aos.master.envelope.v5_1.task_request.example.json",
    ])
    run(["--schema", "schemas/temporal/aos.scene.v5_1.schema.json"])
    run([
        "--schema",
        "schemas/aos.schema_pack.manifest.v1_1.schema.json",
        "--example",
        "examples/aos.schema_pack.manifest.v1_1.example.json",
    ])


if __name__ == "__main__":
    main()
