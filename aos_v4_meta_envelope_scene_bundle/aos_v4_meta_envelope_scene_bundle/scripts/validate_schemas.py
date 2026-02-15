import json
import os
from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(__file__))

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    meta = load(os.path.join(ROOT, "schemas", "master", "aos.master.meta.v4.schema.json"))
    env = load(os.path.join(ROOT, "schemas", "envelope", "aos.master.envelope.v4.schema.json"))
    scene = load(os.path.join(ROOT, "schemas", "temporal", "aos.scene.v4.schema.json"))

    Draft202012Validator.check_schema(meta)
    Draft202012Validator.check_schema(env)
    Draft202012Validator.check_schema(scene)

    print("OK: schemas validate as Draft 2020-12")

if __name__ == "__main__":
    main()
