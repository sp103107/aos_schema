"""
Validate AoS schemas and examples for the master meta v4 contract.
"""
import argparse
import json
import os
import sys

try:
    from jsonschema import Draft202012Validator, RefResolver
    from jsonschema import exceptions as jsonschema_exceptions
except ImportError:  # pragma: no cover - environment guard
    print(
        "ERROR: jsonschema is not installed. Install with "
        "`pip install -r requirements-dev.txt`."
    )
    sys.exit(2)


ROOT = os.path.dirname(os.path.dirname(__file__))


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def parse_args(default_schema):
    parser = argparse.ArgumentParser(
        description="Validate AoS schema and optional example."
    )
    parser.add_argument(
        "--schema",
        default=default_schema,
        help="Path to schema JSON (default: v4 master meta schema).",
    )
    parser.add_argument(
        "--example",
        default=None,
        help="Optional path to example JSON.",
    )
    return parser.parse_args()


def load_schema_store():
    store = {}
    schemas_root = os.path.join(ROOT, "schemas")
    for root, _, files in os.walk(schemas_root):
        for name in files:
            if not name.endswith(".schema.json"):
                continue
            path = os.path.join(root, name)
            schema = load_json(path)
            schema_id = schema.get("$id")
            if schema_id:
                store[schema_id] = schema
            store[path] = schema
            store[f"file:///{path.replace(os.sep, '/')}"] = schema
    return store


def main():
    default_schema = os.path.join(
        ROOT, "schemas", "master", "aos.master.meta.v4.schema.json"
    )
    default_example = os.path.join(
        ROOT, "examples", "aos.master.meta.v4.example.json"
    )
    args = parse_args(default_schema)
    schema_path = os.path.abspath(args.schema)
    example_path = None
    if args.example is not None:
        example_path = os.path.abspath(args.example)
    elif schema_path == os.path.abspath(default_schema):
        example_path = os.path.abspath(default_example)

    schema = load_json(schema_path)

    try:
        Draft202012Validator.check_schema(schema)
    except jsonschema_exceptions.SchemaError as exc:
        print(f"ERROR: schema is invalid: {exc}")
        sys.exit(3)

    if example_path is not None:
        example = load_json(example_path)
        resolver = RefResolver.from_schema(schema, store=load_schema_store())
        try:
            Draft202012Validator(schema, resolver=resolver).validate(example)
        except jsonschema_exceptions.ValidationError as exc:
            print(f"ERROR: example does not validate: {exc}")
            sys.exit(4)

    if example_path is None:
        print("OK: schema validates")
    else:
        print("OK: schema and example validate")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, OSError) as exc:  # pragma: no cover
        print(f"ERROR: {exc}")
        sys.exit(1)
